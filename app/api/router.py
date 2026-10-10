"""
app/api/router.py
Central API router — registers all sub-routers.
"""
from fastapi import APIRouter

from app.api.routes import attendance, corrections, analytics

api_router = APIRouter()

api_router.include_router(attendance.router)
api_router.include_router(corrections.router)
api_router.include_router(analytics.router)
