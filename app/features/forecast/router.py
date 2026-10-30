from __future__ import annotations

import re
from fastapi import APIRouter, HTTPException, Query, status

from app.features.forecast.schemas import ForecastResponse, HealthResponse, SeriesItem
from app.features.forecast.service import forecast_service
from app.shared.exceptions import STANDARD_ERROR_RESPONSES

router = APIRouter()

MONTH_REGEX = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["Forecast"],
)
async def forecast_health():
    return forecast_service.get_health()


@router.get(
    "/series",
    response_model=list[SeriesItem],
    status_code=status.HTTP_200_OK,
    tags=["Forecast"],
)
async def list_forecast_series():
    return forecast_service.list_series()


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    status_code=status.HTTP_200_OK,
    responses=STANDARD_ERROR_RESPONSES,
    tags=["Forecast"],
)
async def get_forecast(
    commodity: str = Query(..., min_length=2, description="Canonical commodity name"),
    market: str = Query(..., min_length=2, description="Market name"),
    month: str = Query(..., description="Target month in YYYY-MM format"),
):
    if not MONTH_REGEX.match(month):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Month must follow YYYY-MM format (e.g. 2017-03)",
        )

    return forecast_service.forecast(commodity=commodity, market=market, month=month)


@router.get("/metrics", tags=["Metrics"])
async def metrics_endpoint():
    from fastapi.responses import Response
    from app.features.forecast.metrics import get_latest_metrics

    content, media_type = get_latest_metrics()
    return Response(content=content, media_type=media_type)
