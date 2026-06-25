import base64
import json
import logging
from email.mime.text import MIMEText

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

GMAIL_API_ENABLE_HINT = (
    "Gmail API is not enabled for your Google Cloud project. "
    "Open Google Cloud Console → APIs & Services → Library → Gmail API → Enable, "
    "wait 1–2 minutes, then try sending again."
)


def _friendly_google_error(resp_text: str, *, context: str) -> str:
    try:
        data = json.loads(resp_text)
        err = data.get("error", {})
        message = err.get("message", "")
        if "Gmail API has not been used" in message or "gmail.googleapis.com" in message:
            return GMAIL_API_ENABLE_HINT
        if "invalid_grant" in message.lower():
            return "Gmail authorization expired. Open Profile → Connect Gmail and sign in again."
        if message:
            return f"{context}: {message}"
    except (json.JSONDecodeError, AttributeError, TypeError):
        pass
    return f"{context}. Open Profile → Connect Gmail or enable Gmail API in Google Cloud Console."


async def refresh_access_token(refresh_token: str) -> tuple[str | None, str]:
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
        return None, _friendly_google_error(resp.text, context="Google sign-in expired")
    return resp.json().get("access_token"), ""


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
) -> tuple[bool, str]:
    access_token, token_error = await refresh_access_token(refresh_token)
    if not access_token:
        return False, token_error

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
        return False, _friendly_google_error(resp.text, context="Gmail send failed")
    return True, ""
