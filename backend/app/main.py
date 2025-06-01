from fastapi import FastAPI, Depends, HTTPException, status, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging
import logging.config
import time

from .api.api_v1.api import api_router
from app.db import get_db
from app.api.deps import get_api_key
from .db import init_db, engine
from .config import settings, get_settings

# Create database tables
# models.Base.metadata.create_all(bind=engine)

# Configure logging
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "level": settings.LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": settings.LOG_LEVEL,
            "propagate": True,
        },
    },
})

logger = logging.getLogger(__name__)

# Initialize FastAPI application with docs and redoc always enabled
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for storing and retrieving time series data from IoT devices",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """Initialize database and create tables on startup."""
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

@app.get("/", response_model=Dict[str, str])
async def root() -> Dict[str, str]:
    """Root endpoint that returns a welcome message."""
    return {"message": "Welcome to the IoT Time Series API"}

@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check if the API and database are running. This endpoint is publicly accessible."
)
async def health_check(db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Health check endpoint to verify the API and database are running.
    
    Returns:
        Dict with status and database connection status
    """
    try:
        # Test database connection with proper SQLAlchemy text()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "error": str(e)}
        )

# Add exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
