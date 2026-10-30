from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Final, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from app.features.forecast.features import FEATURES, build_all, to_m
from app.features.forecast.series import CANONICAL_CSV, load_canonical

DEFAULT_CUTOFF: Final[str] = "2016-01"

HGB_PARAMS: Final[dict[str, Any]] = {
    "max_depth": 3,
    "learning_rate": 0.05,
    "max_iter": 200,
    "min_samples_leaf": 20,
    "l2_regularization": 1.0,
    "random_state": 0,
}


@dataclass
class ChampionModel:
    name: str = "naive"

    def predict(self, last_month_price: float) -> float:
        return float(last_month_price)

    def predict_series(self, last_month_prices: pd.Series) -> pd.Series:
        return last_month_prices.copy()


@dataclass
class ChallengerModel:
    name: str = "hist_gradient_boosting"
    cutoff_month: str = DEFAULT_CUTOFF
    model: HistGradientBoostingRegressor = field(
        default_factory=lambda: HistGradientBoostingRegressor(**HGB_PARAMS)
    )
    is_fitted: bool = False
    n_train_samples: int = 0

    def fit(self, train_df: pd.DataFrame) -> ChallengerModel:
        clean = train_df[train_df["y"].notna()].dropna(subset=FEATURES)
        if len(clean) < 50:
            raise ValueError(f"Insufficient training rows ({len(clean)}) to fit Challenger model")

        X = clean[FEATURES]
        y = clean["y"]
        self.model.fit(X, y)
        self.is_fitted = True
        self.n_train_samples = len(clean)
        return self

    def predict_log_change(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Challenger model must be fitted before predict")
        return self.model.predict(X[FEATURES])

    def predict(self, X: pd.DataFrame, last_month_prices: np.ndarray | pd.Series) -> np.ndarray:
        yhat = self.predict_log_change(X)
        lp1 = np.log(np.asarray(last_month_prices, dtype=float))
        return np.exp(lp1 + yhat)


def train_challenger(
    canonical_df: pd.DataFrame,
    cutoff_month: Optional[str] = None,
) -> ChallengerModel:
    cutoff = cutoff_month or os.getenv("BEIWATCH_TRAIN_CUTOFF", DEFAULT_CUTOFF)
    cutoff_m = to_m(cutoff)

    df = canonical_df.copy()
    if "m" not in df.columns:
        df["m"] = to_m(df["year_month"])

    weather_cols = ["market", "m", "year_month", "temp_mean_c", "precip_total_mm", "humidity_mean_pct", "rainy_days_count"]
    weather_df = df[weather_cols].drop_duplicates()

    features_df = build_all(df, weather_df)
    train_mask = (features_df["m"] < cutoff_m) & features_df["lp"].notna() & features_df["lp1"].notna()
    train_data = features_df[train_mask]

    challenger = ChallengerModel(cutoff_month=cutoff)
    challenger.fit(train_data)
    return challenger
