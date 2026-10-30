from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from app.features.forecast.features import FEATURES, build_all, leak_check
from app.features.forecast.model import HGB_PARAMS, HistGradientBoostingRegressor
from app.features.forecast.series import load_canonical

FIRST_TEST_YEAR = 2012


def main() -> None:
    df = load_canonical()
    weather_cols = ["market", "year_month", "temp_mean_c", "precip_total_mm", "humidity_mean_pct", "rainy_days_count"]
    weather = df[weather_cols].drop_duplicates().copy()

    leak_check(df, weather)

    feats = build_all(df, weather)
    d = feats[feats["lp"].notna() & feats["lp1"].notna()].copy()
    out = []

    for yr in range(FIRST_TEST_YEAR, int(d["year"].max()) + 1):
        train = d[d["m"] < yr * 12]
        test = d[(d["year"] == yr) & d["lp12"].notna()]
        if len(train) < 200 or test.empty:
            continue

        mdl = HistGradientBoostingRegressor(**HGB_PARAMS).fit(train[FEATURES], train["y"])
        yhat = mdl.predict(test[FEATURES])
        out.append(pd.DataFrame({
            "series": test["series"].values,
            "year": yr,
            "actual": np.exp(test["lp"].values),
            "pred_naive": np.exp(test["lp1"].values),
            "pred_seasonal": np.exp(test["lp12"].values),
            "pred_model": np.exp(test["lp1"].values + yhat),
            "n_train": len(train),
        }))

    res = pd.concat(out, ignore_index=True)
    res.to_csv("eval_v2_predictions.csv", index=False)

    rows = []
    for s, g in res.groupby("series"):
        mae = {k: np.mean(np.abs(g[f"pred_{k}"] - g["actual"])) for k in ("naive", "seasonal", "model")}
        mape = {k: 100 * np.mean(np.abs(g[f"pred_{k}"] - g["actual"]) / g["actual"]) for k in ("naive", "seasonal", "model")}
        rows.append({
            "series": s,
            "n": len(g),
            "MAPE_naive%": mape["naive"],
            "MAPE_seasonal%": mape["seasonal"],
            "MAPE_model%": mape["model"],
            "relMAE_model_vs_naive": mae["model"] / mae["naive"],
        })

    summary = pd.DataFrame(rows)
    summary.to_csv("eval_v2_summary.csv", index=False)
    print(f"Evaluation complete for {len(res)} rows. Summary saved to eval_v2_summary.csv")


if __name__ == "__main__":
    main()
