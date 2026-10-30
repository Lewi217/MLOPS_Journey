from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from app.features.forecast.features import FEATURES, build_all, from_m, leak_check
from app.features.forecast.model import HGB_PARAMS, HistGradientBoostingRegressor
from app.features.forecast.monitor import DriftMonitor, compute_robust_z
from app.features.forecast.series import load_canonical

REPLAY_START_YEAR = 2016
Z_ALERT = 3.5


def main() -> None:
    df = load_canonical()
    weather_cols = ["market", "year_month", "temp_mean_c", "precip_total_mm", "humidity_mean_pct", "rainy_days_count"]
    weather = df[weather_cols].drop_duplicates().copy()

    leak_check(df, weather)

    feats = build_all(df, weather)
    d = feats[feats["lp"].notna()].copy()
    fc = d[d["lp1"].notna()].sort_values(["series", "m"]).reset_index(drop=True)

    fc["actual"] = np.exp(fc["lp"])
    fc["pred_champion"] = np.exp(fc["lp1"])
    fc["abs_log_err"] = (fc["lp"] - fc["lp1"]).abs()

    fc["pred_challenger"] = np.nan
    for yr in range(REPLAY_START_YEAR, int(fc["year"].max()) + 1):
        train, test = fc[fc["m"] < yr * 12], fc[fc["year"] == yr]
        if len(train) < 200 or test.empty:
            continue
        mdl = HistGradientBoostingRegressor(**HGB_PARAMS).fit(train[FEATURES], train["y"])
        fc.loc[test.index, "pred_challenger"] = np.exp(test["lp1"] + mdl.predict(test[FEATURES]))

    fc["z"] = np.nan
    for _, g in fc.groupby("series"):
        fc.loc[g.index, "z"] = compute_robust_z(g["abs_log_err"].values)

    log = fc[fc["year"] >= REPLAY_START_YEAR].copy()
    log["year_month"] = log["m"].map(from_m)
    log["alert"] = log["z"] >= Z_ALERT

    cols = ["series", "commodity", "market", "year_month", "actual", "pred_champion", "pred_challenger", "abs_log_err", "z", "alert"]
    log[cols].to_csv("replay_log_v2.csv", index=False)

    alerts = log[log["alert"]][cols].copy()
    alerts.to_csv("replay_alerts_v2.csv", index=False)

    monitor = DriftMonitor()
    incidents = monitor.find_market_wide_incidents(log)

    print(f"Replay complete: {len(log)} forecasts, {len(alerts)} alerts, {len(incidents)} market-wide incidents recorded.")


if __name__ == "__main__":
    main()
