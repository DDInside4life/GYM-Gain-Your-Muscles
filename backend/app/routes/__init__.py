from fastapi import APIRouter

from app.routes import (
    admin,
    ai,
    auth,
    blog,
    exercises,
    food_entries,
    forum,
    intelligent_training,
    meals,
    nutrition,
    questionnaires,
    templates,
    users,
    workouts,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(exercises.router, prefix="/exercises", tags=["exercises"])
api_router.include_router(workouts.router, prefix="/workouts", tags=["workouts"])
api_router.include_router(questionnaires.router, prefix="/workouts/questionnaires", tags=["questionnaires"])
api_router.include_router(nutrition.router, prefix="/nutrition", tags=["nutrition"])
api_router.include_router(meals.router, prefix="/meals", tags=["meals"])
api_router.include_router(food_entries.router, prefix="/food-entries", tags=["food-entries"])
api_router.include_router(blog.router, prefix="/blog", tags=["blog"])
api_router.include_router(forum.router, prefix="/forum", tags=["forum"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(intelligent_training.router, tags=["training"])
