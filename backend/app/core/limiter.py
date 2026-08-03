"""
Rate limiter instance using slowapi.

Key Generator Policy:
- Uses authenticated user_id as rate-limit key when valid Bearer token is present.
- Falls back to client IP address for unauthenticated requests (e.g. login/register).
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core import security


def get_user_or_ip_key(request: Request) -> str:
    """
    Extracts authenticated user_id / email from Authorization Bearer token header if valid,
    otherwise returns client IP address.
    """
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = security.decode_nextauth_token(token)
            user_id = payload.get("sub") or payload.get("email")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=get_user_or_ip_key)
