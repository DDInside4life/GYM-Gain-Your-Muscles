from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import Forbidden, Unauthorized
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user import UserRepository

_required_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=True)
_optional_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def _user_from_token(db: AsyncSession, token: str | None) -> User | None:
    if not token:
        return None
    try:
        payload = decode_token(token, expected_type="access")
    except ValueError:
        return None
    sub = payload.get("sub")
    if not sub:
        return None
    user = await UserRepository(db).get(int(sub))
    if user is None or not user.is_active:
        return None
    return user


async def get_current_user(
    db: DbSession,
    token: Annotated[str, Depends(_required_scheme)],
) -> User:
    user = await _user_from_token(db, token)
    if user is None:
        raise Unauthorized("Invalid or expired token")
    return user


async def get_optional_user(
    db: DbSession,
    token: Annotated[str | None, Depends(_optional_scheme)],
) -> User | None:
    return await _user_from_token(db, token)


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


async def get_current_admin(user: CurrentUser) -> User:
    if not user.is_admin:
        raise Forbidden("Admin only")
    return user


CurrentAdmin = Annotated[User, Depends(get_current_admin)]
