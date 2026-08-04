"""
API v1 Router aggregation.
"""

from fastapi import APIRouter

from app.api.v1 import auth, health, learning, resume, skill

router = APIRouter()

router.include_router(health.router)
router.include_router(auth.router)
router.include_router(resume.router)
router.include_router(skill.router)
router.include_router(learning.router)

