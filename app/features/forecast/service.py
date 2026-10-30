from __future__ import annotations

import os
from typing import Optional

import numpy as np
import pandas as pd

from app.features.forecast.features import build_all, to_m
from app.features.forecast.model import ChampionModel, ChallengerModel, DEFAULT_CUTOFF, train_challenger
from app.features.forecast.schemas import ForecastResponse, HealthResponse, SeriesItem
from app.features.forecast.series import (
    PERIOD_COL,
    SERIES_DEFINITIONS,
    get_series_metadata,
    load_canonical,
    validate_canonical,
)
from app.shared.exceptions import NotFoundError, ValidationError


class ForecastService:
    def __init__(self) -> None:
        self._df: Optional[pd.DataFrame] = None
        self._features_df: Optional[pd.DataFrame] = None
        self._champion = ChampionModel()
        self._challenger: Optional[ChallengerModel] = None
        self._cutoff: str = os.getenv("BEIWATCH_TRAIN_CUTOFF", DEFAULT_CUTOFF)

    def initialize(self) -> None:
        if self._df is None:
            df = load_canonical()
            validate_canonical(df)
            if "m" not in df.columns:
                df["m"] = to_m(df["year_month"])

            weather_cols = [
                "market",
                "m",
                "year_month",
                "temp_mean_c",
                "precip_total_mm",
                "humidity_mean_pct",
                "rainy_days_count",
            ]
            weather_df = df[weather_cols].drop_duplicates()
            features_df = build_all(df, weather_df)

            self._df = df
            self._features_df = features_df
            self._challenger = train_challenger(df, self._cutoff)

    @property
    def canonical_df(self) -> pd.DataFrame:
        if self._df is None:
            self.initialize()
        assert self._df is not None
        return self._df

    @property
    def features_df(self) -> pd.DataFrame:
        if self._features_df is None:
            self.initialize()
        assert self._features_df is not None
        return self._features_df

    @property
    def challenger(self) -> ChallengerModel:
        if self._challenger is None:
            self.initialize()
        assert self._challenger is not None
        return self._challenger

    def get_health(self) -> HealthResponse:
        self.initialize()
        return HealthResponse(
            status="ok",
            training_cutoff=self._cutoff,
            series_count=len(SERIES_DEFINITIONS),
            data_version="v2",
        )

    def list_series(self) -> list[SeriesItem]:
        self.initialize()
        meta = get_series_metadata(self.canonical_df)
        return [
            SeriesItem(
                commodity=m.commodity,
                market=m.market,
                first_month=m.first_month,
                last_month=m.last_month,
                observations=m.n_obs,
            )
            for m in meta
        ]

    def forecast(
        self,
        commodity: str,
        market: str,
        month: str,
    ) -> ForecastResponse:
        self.initialize()

        match = any(c == commodity and m == market for c, m in SERIES_DEFINITIONS)
        if not match:
            raise NotFoundError(
                message=f"Series '{commodity} / {market}' is not one of the supported 11 series."
            )

        target_m = to_m(month)
        feats = self.features_df
        subset = feats[
            (feats["commodity"] == commodity)
            & (feats["market"] == market)
            & (feats["m"] == target_m)
        ]

        if subset.empty:
            raise NotFoundError(
                message=f"Month '{month}' is outside historical records for '{commodity} / {market}'."
            )

        row = subset.iloc[0]
        lp1 = row["lp1"]

        realised_price = float(np.exp(row["lp"])) if pd.notna(row["lp"]) else None

        if pd.isna(lp1):
            return ForecastResponse(
                commodity=commodity,
                market=market,
                month=month,
                champion=self._champion.name,
                champion_forecast=None,
                challenger_forecast=None,
                last_month_price_kes_per_kg=None,
                realised_price_kes_per_kg=realised_price,
                model_cutoff=self._cutoff,
                note="Last month's price is missing or follows a gap; forecast cannot be calculated.",
            )

        last_price = float(np.exp(lp1))
        champ_pred = float(self._champion.predict(last_price))

        try:
            chal_pred_arr = self.challenger.predict(subset, [last_price])
            chal_pred = float(chal_pred_arr[0])
        except Exception:
            chal_pred = champ_pred

        return ForecastResponse(
            commodity=commodity,
            market=market,
            month=month,
            champion=self._champion.name,
            champion_forecast=round(champ_pred, 2),
            challenger_forecast=round(chal_pred, 2),
            last_month_price_kes_per_kg=round(last_price, 2),
            realised_price_kes_per_kg=round(realised_price, 2) if realised_price else None,
            model_cutoff=self._cutoff,
            note=None,
        )


forecast_service = ForecastService()
