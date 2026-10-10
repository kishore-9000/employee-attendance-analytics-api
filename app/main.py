"""
app/main.py
FastAPI application factory with startup/shutdown lifecycle hooks.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

from app.api.router import api_router
from app.core.config import settings
from app.core.database import connect_db, disconnect_db
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Handle startup and shutdown events."""
    logger.info("Starting Employee Attendance & Analytics API [env=%s]", settings.app_env)
    connect_db()
    yield
    disconnect_db()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title="Employee Attendance & Analytics API",
    description=(
        "REST API for recording employee attendance (punch-in / punch-out), "
        "applying manual corrections with a full audit trail, and querying "
        "analytics via MongoDB aggregation pipelines.\n\n"
        "**Assignment**: HROne Software Engineer Trainee Technical Assignment."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ──────────────────────────────────────────────
# Register routes
# ──────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


# ──────────────────────────────────────────────
# Global exception handlers
# ──────────────────────────────────────────────

@app.exception_handler(PyMongoError)
async def pymongo_exception_handler(request: Request, exc: PyMongoError) -> JSONResponse:
    logger.error("MongoDB error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database error. Please try again later."},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred."},
    )


# ──────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────

@app.get("/health", tags=["Health"], summary="Application health check")
def health_check() -> dict:
    """Returns application status. Does not ping MongoDB."""
    return {"status": "ok", "version": "1.0.0"}
