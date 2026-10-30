from __future__ import annotations

from typing import Any, Callable, Final, Sequence

import numpy as np
import pandas as pd

FEATURES: Final[list[str]] = [
    "ret1",
    "ret2",
    "chg12",
    "month_sin",
    "month_cos",
    "precip_lag1",
    "precip_cum3",
    "precip_cum6",
    "temp_roll3",
    "commodity_code",
    "market_code",
]


def to_m(ym: Any) -> Any:
    if isinstance(ym, str):
        d = pd.to_datetime(ym + "-01")
        return int(d.year * 12 + d.month - 1)
    if isinstance(ym, pd.Period):
        return int(ym.year * 12 + ym.month - 1)
    if hasattr(ym, "dt") and hasattr(ym.dt, "year"):
        return (ym.dt.year * 12 + ym.dt.month - 1).astype(int)
    d = pd.to_datetime(pd.Series(ym).astype(str) + "-01")
    res = (d.dt.year * 12 + d.dt.month - 1).astype(int)
    return res.iloc[0] if len(res) == 1 and not isinstance(ym, (pd.Series, list, np.ndarray)) else res


def from_m(m: int) -> str:
    year = int(m // 12)
    month = int(m % 12) + 1
    return f"{year:04d}-{month:02d}"


def weather_features(weather: pd.DataFrame) -> pd.DataFrame:
    w = weather.copy()
    if "m" not in w.columns:
        w["m"] = to_m(w["year_month"])

    out: list[pd.DataFrame] = []
    for mkt, g in w.groupby("market"):
        g = g.sort_values("m").drop_duplicates("m").set_index("m")
        idx = range(int(g.index.min()), int(g.index.max()) + 1)
        g = g.reindex(idx)
        p = g["precip_total_mm"]
        t = g["temp_mean_c"]
        out.append(
            pd.DataFrame(
                {
                    "market": mkt,
                    "m": g.index.values,
                    "precip_lag1": p.shift(1).values,
                    "precip_cum3": p.shift(1).rolling(3, min_periods=3).sum().values,
                    "precip_cum6": p.shift(1).rolling(6, min_periods=6).sum().values,
                    "temp_roll3": t.shift(1).rolling(3, min_periods=3).mean().values,
                }
            )
        )

    if not out:
        return pd.DataFrame()
    return pd.concat(out, ignore_index=True)


def price_features(prices: pd.DataFrame) -> pd.DataFrame:
    p = prices.copy()
    if "m" not in p.columns:
        p["m"] = to_m(p["year_month"])

    out: list[pd.DataFrame] = []
    for (c, mkt), g in p.groupby(["canonical_commodity", "market"]):
        g = g.sort_values("m").set_index("m")
        idx = range(int(g.index.min()), int(g.index.max()) + 1)
        lp = np.log(g["price_per_kg_kes"]).reindex(idx)
        f = pd.DataFrame(
            {
                "lp": lp,
                "lp1": lp.shift(1),
                "lp2": lp.shift(2),
                "lp3": lp.shift(3),
                "lp12": lp.shift(12),
            }
        )
        f["commodity"] = c
        f["market"] = mkt
        f["m"] = f.index
        out.append(f.reset_index(drop=True))

    if not out:
        return pd.DataFrame()

    f = pd.concat(out, ignore_index=True)
    f["y"] = f["lp"] - f["lp1"]
    f["ret1"] = f["lp1"] - f["lp2"]
    f["ret2"] = f["lp2"] - f["lp3"]
    f["chg12"] = f["lp1"] - f["lp12"]

    mon = (f["m"] % 12) + 1
    f["month_sin"] = np.sin(2 * np.pi * mon / 12)
    f["month_cos"] = np.cos(2 * np.pi * mon / 12)
    f["year"] = f["m"] // 12
    return f


def build_all(prices: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    f = price_features(prices)
    w = weather_features(weather)
    f = f.merge(w, on=["market", "m"], how="left")

    sorted_commodities = sorted(prices["canonical_commodity"].unique())
    sorted_markets = sorted(prices["market"].unique())

    f["commodity_code"] = f["commodity"].map({c: i for i, c in enumerate(sorted_commodities)})
    f["market_code"] = f["market"].map({c: i for i, c in enumerate(sorted_markets)})
    f["series"] = f["commodity"] + " / " + f["market"]
    return f


def leak_check(
    prices: pd.DataFrame,
    weather: pd.DataFrame,
    builder: Callable[[pd.DataFrame, pd.DataFrame], pd.DataFrame] = build_all,
    n: int = 8,
    seed: int = 0,
) -> None:
    p = prices.copy()
    w = weather.copy()
    if "m" not in p.columns:
        p["m"] = to_m(p["year_month"])
    if "m" not in w.columns:
        w["m"] = to_m(w["year_month"])

    base = builder(p, w)

    sample = p.sample(n, random_state=seed)
    for _, r in sample.iterrows():
        p2, w2 = p.copy(), w.copy()
        mask_p = (
            (p2["canonical_commodity"] == r["canonical_commodity"])
            & (p2["market"] == r["market"])
            & (p2["m"] == r["m"])
        )
        p2.loc[mask_p, "price_per_kg_kes"] *= 3.0

        mask_w = (w2["market"] == r["market"]) & (w2["m"] == r["m"])
        w2.loc[mask_w, ["precip_total_mm", "temp_mean_c"]] *= 5.0

        new = builder(p2, w2)

        def extract_features(d: pd.DataFrame) -> np.ndarray:
            subset = d[
                (d["commodity"] == r["canonical_commodity"])
                & (d["market"] == r["market"])
                & (d["m"] == r["m"])
            ]
            return subset[FEATURES].to_numpy(dtype=float)

        base_feat = extract_features(base)
        new_feat = extract_features(new)

        if not np.allclose(base_feat, new_feat, equal_nan=True):
            raise AssertionError(
                f"LEAK: features for {r['canonical_commodity']} / {r['market']} month {r['year_month']} "
                f"use that month's own data"
            )
