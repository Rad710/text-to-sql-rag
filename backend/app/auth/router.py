"""Auth endpoints (decisions 0009, 0013): register/login issue an access + refresh pair; refresh
rotates them (reuse-detected); logout revokes; `/me` is the current-user probe."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.deps import get_current_user
from app.store.engine import get_session
from app.store.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

Session = Annotated[AsyncSession, Depends(get_session)]


class RegisterRequest(BaseModel):
    # Validated at the edge so bad data never reaches the store: a well-formed email, a non-empty
    # name, and a long-enough password (rejected as 422 before the endpoint runs).
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    name: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, session: Session) -> TokenResponse:
    try:
        user = await service.register(
            session, email=req.email, name=req.name, password=req.password
        )
    except service.EmailTakenError:
        raise HTTPException(status.HTTP_409_CONFLICT, "email already registered") from None
    access, refresh = await service.issue_tokens(session, user.id)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, session: Session) -> TokenResponse:
    user = await service.authenticate(session, email=req.email, password=req.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    access, refresh = await service.issue_tokens(session, user.id)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, session: Session) -> TokenResponse:
    try:
        access, new_refresh = await service.rotate_tokens(session, req.refresh_token)
    except service.ReuseDetectedError:
        # A rotated-away token was replayed; the family is now revoked. Force a fresh login.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "refresh token reuse detected") from None
    except service.InvalidRefreshTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid refresh token") from None
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(req: RefreshRequest, session: Session) -> Response:
    await service.revoke(session, req.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, name=user.name)
