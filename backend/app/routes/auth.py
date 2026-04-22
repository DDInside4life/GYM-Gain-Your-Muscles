from typing import Annotated

from fastapi import APIRouter, Body, Request, status

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession
from app.core.limiter import limiter
from app.schemas.auth import LoginInput, RefreshInput, RegisterInput, TokenPair
from app.schemas.user import UserRead
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_login)
async def register(
    request: Request,
    db: DbSession,
    payload: Annotated[RegisterInput, Body()],
) -> UserRead:
    user = await AuthService(db).register(payload)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenPair)
@limiter.limit(settings.rate_limit_login)
async def login(
    request: Request,
    db: DbSession,
    payload: Annotated[LoginInput, Body()],
) -> TokenPair:
    service = AuthService(db)
    user = await service.authenticate(payload)
    return service.issue_tokens(user)


@router.post("/refresh", response_model=TokenPair)
@limiter.limit(settings.rate_limit_login)
async def refresh(
    request: Request,
    db: DbSession,
    payload: Annotated[RefreshInput, Body()],
) -> TokenPair:
    return await AuthService(db).refresh(payload.refresh_token)


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
