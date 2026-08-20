import asyncio
from typing import Annotated, Any

from app.auth.models import (
    AuthenticatedUser,
    UserRole,
)
from app.config import get_settings
from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from google.auth.transport import requests
from google.oauth2 import id_token

bearer_scheme = HTTPBearer(
    auto_error=False
)


def _operator_emails() -> set[str]:
    settings = get_settings()

    return {
        email.strip().lower()
        for email
        in settings.operator_emails.split(",")
        if email.strip()
    }


def _verify_token_sync(
    token: str,
) -> dict[str, Any]:
    settings = get_settings()

    if not settings.google_oauth_client_id:
        raise ValueError(
            "GOOGLE_OAUTH_CLIENT_ID "
            "is not configured."
        )

    result = id_token.verify_oauth2_token( # type: ignore[no-untyped-call]
        token,
        requests.Request(),
        settings.google_oauth_client_id,
    )

    return dict(result)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> AuthenticatedUser:
    settings = get_settings()

    # Local/demo reads work without Google OAuth when unset.
    if (
        credentials is None
        and not settings.google_oauth_client_id
    ):
        return AuthenticatedUser(
            subject="local-dev",
            email="dev@localhost",
            role=UserRole.VIEWER,
        )

    if credentials is None:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Authentication required.",
        )

    try:
        claims = await asyncio.to_thread(
            _verify_token_sync,
            credentials.credentials,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Invalid Google ID token.",
        ) from exc

    subject = claims.get("sub")
    email = claims.get("email")

    if (
        not isinstance(subject, str)
        or not subject
        or not isinstance(email, str)
        or not email
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Google token is missing "
                "required identity claims."
            ),
        )

    role = (
        UserRole.OPERATOR
        if email.lower()
        in _operator_emails()
        else UserRole.VIEWER
    )

    return AuthenticatedUser(
        subject=subject,
        email=email,
        role=role,
    )


async def require_operator(
    user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
) -> AuthenticatedUser:
    if user.role is not UserRole.OPERATOR:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail="Operator role required.",
        )

    return user