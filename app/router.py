from fastapi import APIRouter
from app.features.sample.router import router as sample_router
from app.features.websocket.router import router as websocket_router
from app.features.forecast.router import router as forecast_router

api_router = APIRouter()
api_router.include_router(sample_router, prefix="/samples", tags=["Samples"])
api_router.include_router(websocket_router, prefix="/ws", tags=["WebSockets"])
api_router.include_router(forecast_router, prefix="", tags=["Forecast"])
