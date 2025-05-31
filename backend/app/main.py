from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging
import time

from .api.api_v1.api import api_router
from .db import get_db, init_db, engine
from .config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for storing and retrieving time series data from IoT devices",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    debug=settings.DEBUG
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: Session = Depends(get_db)) -> Dict[str, str]:
    """Health check endpoint to verify the API and database are running."""
    try:
        # Test database connection
        db.execute("SELECT 1")
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
