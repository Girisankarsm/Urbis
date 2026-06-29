from fastapi import Response

from app.config import settings
from app.services.session import COOKIE_NAME, SESSION_DAYS


def attach_session_cookie(response: Response, session_token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite=settings.effective_cookie_samesite,
        secure=settings.effective_cookie_secure,
        max_age=SESSION_DAYS * 24 * 3600,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        COOKIE_NAME,
        samesite=settings.effective_cookie_samesite,
        secure=settings.effective_cookie_secure,
        path="/",
    )
