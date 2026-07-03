# api/middleware/auth_middleware.py
"""Rate limiting et sécurité — dépendances FastAPI (pas middleware HTTP)."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request

# ── Rate limiting login ────────────────────────────────────────────────────────
_login_attempts: dict[str, list[datetime]] = defaultdict(list)
_RATE_WINDOW_S = 60
_RATE_MAX      = 10


async def check_login_rate_limit(request: Request) -> None:
    """
    Dépendance FastAPI — limite le nombre de tentatives de connexion par IP.
    10 tentatives max sur 60 secondes.
    Lever HTTPException 429 si dépassé.
    """
    ip = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=_RATE_WINDOW_S)

    _login_attempts[ip] = [t for t in _login_attempts[ip] if t > window_start]
    if len(_login_attempts[ip]) >= _RATE_MAX:
        raise HTTPException(
            status_code=429,
            detail=f"Trop de tentatives ({_RATE_MAX}/{_RATE_WINDOW_S}s). Réessayez dans 1 minute.",
        )
    _login_attempts[ip].append(now)
