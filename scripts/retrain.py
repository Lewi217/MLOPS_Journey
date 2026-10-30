from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from app.features.forecast.features import FEATURES, build_all, to_m
from app.features.forecast.gate import evaluate_gate
from app.features.forecast.model import HGB_PARAMS, HistGradientBoostingRegressor
from app.features.forecast.series import load_canonical


def run_retrain_and_gate(cutoff_month: str, corrupt_data: bool = False) -> bool:
    df = load_canonical()
    cutoff_m = to_m(cutoff_month)

    if corrupt_data:
        np.random.seed(999)
        train_mask = df["year_month"].map(to_m) < cutoff_m
        df.loc[train_mask, "price_per_kg_kes"] = np.random.permutation(df.loc[train_mask, "price_per_kg_kes"].values)

    weather_cols = ["market", "year_month", "temp_mean_c", "precip_total_mm", "humidity_mean_pct", "rainy_days_count"]
    weather = df[weather_cols].drop_duplicates().copy()

    feats = build_all(df, weather)
    cutoff_m = to_m(cutoff_month)

    train = feats[(feats["m"] < cutoff_m) & feats["lp"].notna() & feats["lp1"].notna()]
    test = feats[(feats["m"] >= cutoff_m) & feats["lp"].notna() & feats["lp1"].notna()]

    if len(train) < 200 or test.empty:
        raise ValueError("Insufficient rows to train or evaluate challenger")

    mdl = HistGradientBoostingRegressor(**HGB_PARAMS).fit(train[FEATURES], train["y"])
    yhat = mdl.predict(test[FEATURES])

    eval_df = pd.DataFrame({
        "series": test["series"].values,
        "year": (test["m"] // 12).values,
        "actual": np.exp(test["lp"].values),
        "pred_champion": np.exp(test["lp1"].values),
        "pred_challenger": np.exp(test["lp1"].values + yhat),
    })

    result = evaluate_gate(eval_df)
    print(f"Retrain Cutoff: {cutoff_month} | Corrupted: {corrupt_data}")
    print(f"Gate Promoted: {result.promoted} | Reason: {result.reason}")
    print(f"Champion MAPE: {result.champ_mape}% vs Challenger MAPE: {result.challenger_mape}%")
    return result.promoted


def main() -> None:
    parser = argparse.ArgumentParser(description="Trigger retraining and evaluate champion vs challenger gate.")
    parser.add_argument("--cutoff", type=str, default="2016-01", help="Training cutoff month (YYYY-MM)")
    parser.add_argument("--safety-test", action="store_true", help="Run safety test on corrupted data")
    args = parser.parse_args()

    promoted = run_retrain_and_gate(cutoff_month=args.cutoff, corrupt_data=args.safety_test)
    if args.safety_test:
        if promoted:
            raise RuntimeError("SAFETY VIOLATION: Gate accepted corrupted data model!")
        print("Safety test passed: Corrupted data correctly rejected by gate.")


if __name__ == "__main__":
    main()
