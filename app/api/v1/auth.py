"""Authentication endpoints."""

from datetime import timedelta

from litestar import Controller, post
from pydantic import BaseModel

from app.settings import settings


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"


class AuthController(Controller):
    """Authentication controller."""

    path = "/auth"

    @post("/login")
    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate user and return JWT token."""
        # TODO: Implement actual authentication
        return TokenResponse(access_token="dummy-token")
