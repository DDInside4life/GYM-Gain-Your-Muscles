from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.limiter import limiter
from app.core.security import hash_password
from app.data.seed_content import ensure_seed_content
from app.models.user import User
from app.repositories.user import UserRepository
from app.routes import api_router

logger = logging.getLogger("app")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


async def _ensure_admin() -> None:
    async with SessionLocal() as db:
        repo = UserRepository(db)
        existing = await repo.get_by_email(settings.admin_email)
        if existing:
            if not existing.is_admin:
                existing.is_admin = True
                await db.commit()
            await ensure_seed_content(db, existing.id)
            return
        await repo.add(User(
            email=settings.admin_email,
            hashed_password=hash_password(settings.admin_password),
            full_name="Admin",
            is_active=True,
            is_admin=True,
        ))
        await db.commit()
        created = await repo.get_by_email(settings.admin_email)
        if created is not None:
            await ensure_seed_content(db, created.id)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        await _ensure_admin()
    except IntegrityError:
        logger.info("admin already exists (race on first boot)")
    except Exception:
        logger.exception("failed to ensure admin user")
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url=None if settings.is_prod else f"{settings.api_prefix}/docs",
    redoc_url=None,
    openapi_url=None if settings.is_prod else f"{settings.api_prefix}/openapi.json",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    logger.info("request %s %s", request.method, request.url.path)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if settings.is_prod:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


app.include_router(api_router, prefix=settings.api_prefix)


@app.get(f"{settings.api_prefix}/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "env": settings.environment}


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    logger.exception("unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
