from fastapi import APIRouter

from app.routes import admin, auth, blog, exercises, forum, nutrition, users, workouts

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(exercises.router, prefix="/exercises", tags=["exercises"])
api_router.include_router(workouts.router, prefix="/workouts", tags=["workouts"])
api_router.include_router(nutrition.router, prefix="/nutrition", tags=["nutrition"])
api_router.include_router(blog.router, prefix="/blog", tags=["blog"])
api_router.include_router(forum.router, prefix="/forum", tags=["forum"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
