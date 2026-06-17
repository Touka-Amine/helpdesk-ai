"""Admin routes scaffold."""

from fastapi import APIRouter


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health")
def admin_health() -> dict:
    return {"status": "ok", "module": "admin"}
