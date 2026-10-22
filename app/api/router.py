from fastapi import APIRouter
from app.api.routes import sample

api_router = APIRouter()
api_router.include_router(sample.router, prefix="/samples", tags=["Samples"])
