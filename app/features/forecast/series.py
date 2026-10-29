from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Final

import pandas as pd

PROCESSED_DIR: Final[pathlib.Path] = (
    pathlib.Path(__file__).resolve().parents[3] / "data" / "processed"
)

CANONICAL_CSV: Final[pathlib.Path] = (
    PROCESSED_DIR / "canonical_11series_v2_monthly_2006_2022.csv"
)

PRICE_COL: Final[str] = "price_per_kg_kes"
COMMODITY_COL: Final[str] = "canonical_commodity"
MARKET_COL: Final[str] = "market"
PERIOD_COL: Final[str] = "year_month"

WEATHER_COLS: Final[list[str]] = [
    "temp_mean_c",
    "precip_total_mm",
    "humidity_mean_pct",
    "rainy_days_count",
]

EXPECTED_ROWS: Final[int] = 1884
EXPECTED_SERIES: Final[int] = 11


@dataclass(frozen=True)
class SeriesMeta:
    commodity: str
    market: str
    first_month: str
    last_month: str
    n_obs: int

    @property
    def key(self) -> str:
        return f"{self.commodity} / {self.market}"


SERIES_DEFINITIONS: Final[list[tuple[str, str]]] = [
    ("Beans (dry)", "Eldoret"),
    ("Beans (dry)", "Kisumu"),
    ("Beans (dry)", "Mombasa"),
    ("Beans (dry)", "Nairobi"),
    ("Maize", "Eldoret"),
    ("Maize", "Kisumu"),
    ("Maize", "Nairobi"),
    ("Maize", "Nakuru"),
    ("Potatoes (Irish)", "Eldoret"),
    ("Potatoes (Irish)", "Kisumu"),
    ("Potatoes (Irish)", "Nairobi"),
]


def load_canonical() -> pd.DataFrame:
    df = pd.read_csv(CANONICAL_CSV, parse_dates=[PERIOD_COL])
    df[PERIOD_COL] = df[PERIOD_COL].dt.to_period("M")
    return df


def validate_canonical(df: pd.DataFrame) -> None:
    if len(df) != EXPECTED_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_ROWS} rows, got {len(df)}"
        )

    actual_series = df.groupby([COMMODITY_COL, MARKET_COL]).ngroups
    if actual_series != EXPECTED_SERIES:
        raise ValueError(
            f"Expected {EXPECTED_SERIES} series, got {actual_series}"
        )

    price_nans = df[PRICE_COL].isna().sum()
    if price_nans > 0:
        raise ValueError(f"Found {price_nans} NaN values in {PRICE_COL}")

    for col in WEATHER_COLS:
        weather_nans = df[col].isna().sum()
        if weather_nans > 0:
            raise ValueError(f"Found {weather_nans} NaN values in weather column '{col}'")


def get_series_metadata(df: pd.DataFrame) -> list[SeriesMeta]:
    meta: list[SeriesMeta] = []
    for commodity, market in SERIES_DEFINITIONS:
        subset = df[
            (df[COMMODITY_COL] == commodity) & (df[MARKET_COL] == market)
        ].sort_values(PERIOD_COL)
        meta.append(
            SeriesMeta(
                commodity=commodity,
                market=market,
                first_month=str(subset[PERIOD_COL].iloc[0]),
                last_month=str(subset[PERIOD_COL].iloc[-1]),
                n_obs=len(subset),
            )
        )
    return meta


def get_series_df(
    df: pd.DataFrame,
    commodity: str,
    market: str,
) -> pd.DataFrame:
    subset = df[
        (df[COMMODITY_COL] == commodity) & (df[MARKET_COL] == market)
    ].sort_values(PERIOD_COL).reset_index(drop=True)

    if subset.empty:
        raise ValueError(
            f"No data found for commodity='{commodity}' market='{market}'"
        )

    return subset
