from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.error_handling import register_exception_handlers
from app.core.limiter import limiter
from app.core.metrics import ProductMetrics, RequestMetricTags, classify_request
from app.core.security import decode_token
from app.core.security import hash_password
from app.data.seed_content import ensure_seed_content
from app.data.seed_templates import ensure_seed_templates
from app.models.user import User
from app.repositories.user import UserRepository
from app.routes import api_router

logger = logging.getLogger("app")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
metrics = ProductMetrics()


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


async def _ensure_templates() -> None:
    async with SessionLocal() as db:
        try:
            created, updated = await ensure_seed_templates(db)
            logger.info("workout templates ensured: created=%d updated=%d", created, updated)
        except Exception:
            logger.exception("failed to ensure workout templates")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        await _ensure_admin()
    except IntegrityError:
        logger.info("admin already exists (race on first boot)")
    except Exception:
        logger.exception("failed to ensure admin user")
    await _ensure_templates()
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
register_exception_handlers(app)

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
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    started = time.perf_counter()
    user_id: int | None = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        try:
            payload = decode_token(token, expected_type="access")
            sub = payload.get("sub")
            if sub is not None:
                user_id = int(sub)
        except Exception:
            user_id = None
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    plan_id = request.path_params.get("plan_id")
    error_code = None
    if getattr(response, "media_type", "") == "application/json":
        try:
            payload = response.body.decode("utf-8")
            if payload and '"error_code"' in payload:
                import json

                parsed = json.loads(payload)
                if isinstance(parsed, dict):
                    error_code = parsed.get("error_code")
        except Exception:
            error_code = None
    tags = RequestMetricTags(method=request.method, path=request.url.path, status_code=response.status_code)
    metric_type = classify_request(tags)
    if metric_type == "generation":
        metrics.record_generation(response.status_code < 400)
    elif metric_type == "finalize":
        metrics.record_finalize(response.status_code < 400)
    elif metric_type == "set_log":
        metrics.record_set_log_latency(duration_ms)
    logger.info(
        "request_completed request_id=%s user_id=%s plan_id=%s endpoint=%s duration_ms=%.2f status_code=%s error_code=%s",
        request_id,
        user_id,
        plan_id,
        request.url.path,
        duration_ms,
        response.status_code,
        error_code,
    )
    if metric_type is not None:
        logger.info("product_metrics type=%s snapshot=%s", metric_type, metrics.snapshot())
    response.headers["X-Request-ID"] = request_id
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
