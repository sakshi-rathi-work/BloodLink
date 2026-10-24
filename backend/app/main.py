import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.router import api_router
from app.core.config import settings
from app.core.errors import AppException, app_exception_handler
from app.db.session import SessionLocal
from app.jobs.scheduler import start_scheduler, stop_scheduler
from app.services.inventory import expire_overdue_units

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown routines."""
    # Run startup expiry sweep
    try:
        with SessionLocal() as db:
            count = expire_overdue_units(db)
            if count > 0:
                logger.info("Startup expiry sweep marked %d units as expired.", count)
    except Exception as exc:
        logger.warning("Startup expiry sweep skipped or failed: %s", exc)

    # Start background scheduler
    try:
        start_scheduler()
    except Exception as exc:
        logger.warning("Could not start background scheduler: %s", exc)

    yield

    # Shutdown background scheduler
    try:
        stop_scheduler()
    except Exception as exc:
        logger.warning("Error stopping background scheduler: %s", exc)


app = FastAPI(
    title="BloodLink API",
    description="Blood Bank Management & Availability Prediction System API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Ensure HTTP exceptions adhere to the {detail: {code, message}} envelope."""
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    code = "HTTP_ERROR"
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        code = "NOT_AUTHENTICATED"
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        code = "FORBIDDEN"
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        code = "NOT_FOUND"

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": {"code": code, "message": str(exc.detail)}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Ensure any unhandled server errors return standard JSON envelope with CORS headers."""
    logger.exception("Unhandled server exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected server error occurred."}},
    )


# Mount API routers under /api
app.include_router(api_router)
