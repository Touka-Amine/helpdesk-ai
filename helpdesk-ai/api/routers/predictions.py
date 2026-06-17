"""Prediction routes scaffold."""

from fastapi import APIRouter


router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/health")
def predictions_health() -> dict:
    return {"status": "ok", "module": "predictions"}
