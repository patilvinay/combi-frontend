from fastapi import APIRouter
from app.api.endpoints import measurements

api_router = APIRouter()
api_router.include_router(measurements.router, prefix="/measurements", tags=["measurements"])
