# api/middleware/auth_middleware.py
"""Rate limiting et sécurité — dépendances FastAPI (pas middleware HTTP)."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request

def _compter(
    registre: dict[str, list[datetime]],
    request: Request,
    fenetre_s: int,
    maximum: int,
    message: str,
) -> None:
    """Compte les appels d'une IP sur une fenêtre glissante et lève 429 au-delà."""
    ip = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=fenetre_s)

    registre[ip] = [t for t in registre[ip] if t > window_start]
    if len(registre[ip]) >= maximum:
        raise HTTPException(status_code=429, detail=message)
    registre[ip].append(now)


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
    _compter(
        _login_attempts, request, _RATE_WINDOW_S, _RATE_MAX,
        f"Trop de tentatives ({_RATE_MAX}/{_RATE_WINDOW_S}s). Réessayez dans 1 minute.",
    )


# ── Rate limiting mot de passe oublié ──────────────────────────────────────────
# Plafond nettement plus bas que celui du login : chaque appel réussi déclenche
# l'envoi d'un courriel vers une adresse que l'appelant choisit. Sans plafond,
# l'endpoint devient un moyen d'inonder la boîte d'un collaborateur.
_reset_requests: dict[str, list[datetime]] = defaultdict(list)
_RESET_WINDOW_S = 900
_RESET_MAX      = 5


async def check_password_reset_rate_limit(request: Request) -> None:
    """Dépendance FastAPI — 5 demandes de réinitialisation par IP sur 15 minutes."""
    _compter(
        _reset_requests, request, _RESET_WINDOW_S, _RESET_MAX,
        "Trop de demandes de réinitialisation. Réessayez dans quinze minutes.",
    )
