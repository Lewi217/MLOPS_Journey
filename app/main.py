import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.core.config import settings
from app.core.redis import get_redis_pool, close_redis_pool
from app.shared.exceptions import BaseAppException, create_success_response
from app.features.websocket.manager import manager
from app.router import api_router

logger = logging.getLogger(__name__)

WS_PUBSUB_CHANNEL = "ws:broadcast"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initialising Redis connection pool…")
    pool = get_redis_pool()
    redis_client = Redis(connection_pool=pool)

    pubsub_task = asyncio.create_task(
        manager.start_pubsub_listener(redis_client, WS_PUBSUB_CHANNEL)
    )
    logger.info("Redis Pub/Sub bridge task started.")

    yield

    logger.info("Shutting down — cancelling Pub/Sub task and closing Redis pool…")
    pubsub_task.cancel()
    try:
        await pubsub_task
    except asyncio.CancelledError:
        pass
    await close_redis_pool()
    logger.info("Shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response_dict(),
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    fields = {}
    for err in exc.errors():
        field_path = ".".join(str(loc) for loc in err.get("loc", []) if loc != "body")
        fields[field_path or "body"] = err.get("msg", "Invalid value")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "success": False,
            "data": None,
            "meta": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "fields": fields,
            },
        },
    )


@app.get("/health", tags=["Health"])
def health():
    return create_success_response(
        message="Service is healthy",
        data={"status": "ok", "project": settings.PROJECT_NAME},
    )
