from __future__ import annotations

import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class HealthResponse(BaseModel):
    status: str = "ok"
    training_cutoff: str
    series_count: int
    data_version: str = "v2"
    model_config = ConfigDict(extra="ignore")


class SeriesItem(BaseModel):
    commodity: str
    market: str
    first_month: str
    last_month: str
    observations: int
    model_config = ConfigDict(extra="ignore")


class ForecastResponse(BaseModel):
    commodity: str
    market: str
    month: str
    champion: str = "naive"
    champion_forecast: Optional[float] = None
    challenger_forecast: Optional[float] = None
    last_month_price_kes_per_kg: Optional[float] = None
    realised_price_kes_per_kg: Optional[float] = None
    model_cutoff: str
    note: Optional[str] = None
    model_config = ConfigDict(extra="ignore")


MONTH_REGEX = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class ForecastQuery(BaseModel):
    commodity: str = Field(..., min_length=2, description="Canonical commodity name")
    market: str = Field(..., min_length=2, description="Wholesale market name")
    month: str = Field(..., description="Month in YYYY-MM format")

    @field_validator("month")
    @classmethod
    def validate_month_format(cls, v: str) -> str:
        if not MONTH_REGEX.match(v):
            raise ValueError("Month must be in YYYY-MM format (e.g. 2017-03)")
        return v
