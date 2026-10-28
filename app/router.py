from fastapi import APIRouter
from app.features.sample.router import router as sample_router
from app.features.websocket.router import router as websocket_router

api_router = APIRouter()
api_router.include_router(sample_router, prefix="/samples", tags=["Samples"])
api_router.include_router(websocket_router, prefix="/ws", tags=["WebSockets"])
