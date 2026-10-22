from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.router import api_router
from app.utils.exceptions import BaseAppException, create_success_response

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Central API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Exception Handlers
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
