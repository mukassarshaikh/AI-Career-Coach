"""
API v1 Router aggregation.
"""

from fastapi import APIRouter

from app.api.v1 import auth, career, dashboard, health, learning, resume, skill, user

router = APIRouter()

router.include_router(health.router)
router.include_router(auth.router)
router.include_router(user.router)
router.include_router(resume.router)
router.include_router(skill.router)
router.include_router(learning.router)
router.include_router(dashboard.router)
router.include_router(career.router)

