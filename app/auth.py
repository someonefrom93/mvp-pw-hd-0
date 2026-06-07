"""Admin authentication: password check, signed cookie session, auth dependency."""

from __future__ import annotations

import os
import secrets

from fastapi import Request
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner

# Plain text for MVP. Replace with bcrypt + user table for production.
ADMIN_PASSWORD = "wero123"

SECRET_KEY = os.environ.get("WERO_SECRET_KEY", "wero-dev-secret-change-me-in-production")

_signer = TimestampSigner(SECRET_KEY)


def check_password(submitted: str) -> bool:
    """Constant-time password comparison to prevent timing attacks."""
    return secrets.compare_digest(submitted, ADMIN_PASSWORD)


def create_session_token() -> str:
    """Create a signed session token valid for 7 days."""
    return _signer.sign(b"admin").decode()


def verify_session_token(token: str) -> bool:
    """Return True if the token is valid and not expired."""
    if not token:
        return False
    try:
        _signer.unsign(token, max_age=7 * 24 * 60 * 60)
        return True
    except (BadSignature, SignatureExpired):
        return False


def get_current_admin(request: Request):
    """FastAPI dependency. Returns 'admin' if authenticated, or RedirectResponse to /admin/login."""
    token = request.cookies.get("wero_admin")
    if not token or not verify_session_token(token):
        return RedirectResponse(url="/admin/login", status_code=303)
    return "admin"