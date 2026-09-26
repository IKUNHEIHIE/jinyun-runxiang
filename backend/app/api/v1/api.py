from fastapi import APIRouter
from app.api import (
    auth, home, course, ai_workshop, community,
    teacher, activity, mall, device, admin, festival, screen, heritage
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(home.router)
api_router.include_router(course.router)
api_router.include_router(course.learning_router)
api_router.include_router(ai_workshop.router)
api_router.include_router(community.router)
api_router.include_router(teacher.router)
api_router.include_router(activity.router)
api_router.include_router(mall.router)
api_router.include_router(device.router)
api_router.include_router(admin.router)
api_router.include_router(festival.router)
api_router.include_router(screen.router)
api_router.include_router(heritage.router)

