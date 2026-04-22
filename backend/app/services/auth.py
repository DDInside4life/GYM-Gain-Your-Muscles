from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict, Unauthorized
from app.core.security import (
    create_access_token, create_refresh_token, decode_token,
    hash_password, verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginInput, RegisterInput, TokenPair


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)

    async def register(self, payload: RegisterInput) -> User:
        email = payload.email.lower()
        if await self.users.get_by_email(email):
            raise Conflict("Email already registered")
        user = await self.users.create(
            email=email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
        )
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate(self, payload: LoginInput) -> User:
        user = await self.users.get_by_email(payload.email.lower())
        if not user or not verify_password(payload.password, user.hashed_password):
            raise Unauthorized("Invalid credentials")
        if not user.is_active:
            raise Unauthorized("Inactive user")
        return user

    @staticmethod
    def issue_tokens(user: User) -> TokenPair:
        return TokenPair(
            access_token=create_access_token(str(user.id), {"admin": user.is_admin}),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except ValueError as exc:
            raise Unauthorized(str(exc)) from exc
        user = await self.users.get(int(payload["sub"]))
        if not user or not user.is_active:
            raise Unauthorized("User not found")
        return self.issue_tokens(user)
