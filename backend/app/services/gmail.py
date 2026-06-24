import base64
import logging
from email.mime.text import MIMEText

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


async def refresh_access_token(refresh_token: str) -> str | None:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
    if resp.status_code != 200:
        logger.warning("Google token refresh failed: %s", resp.text)
        return None
    return resp.json().get("access_token")


def _encode_message(*, from_email: str, to_email: str, subject: str, body: str) -> str:
    msg = MIMEText(body, "plain", "utf-8")
    msg["To"] = to_email
    msg["From"] = from_email
    msg["Subject"] = subject
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


async def send_gmail_as_user(
    *,
    refresh_token: str,
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
) -> bool:
    access_token = await refresh_access_token(refresh_token)
    if not access_token:
        return False

    raw = _encode_message(
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        body=body,
    )

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            GMAIL_SEND_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            json={"raw": raw},
        )

    if resp.status_code != 200:
        logger.warning("Gmail send failed: %s", resp.text)
        return False
    return True
