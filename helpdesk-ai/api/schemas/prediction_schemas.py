"""Prediction and health schemas."""

from typing import List, Optional

from pydantic import BaseModel


class PredictionResult(BaseModel):
    categorie: str
    confiance: float
    auto_routed: bool
    low_confidence: bool


class Recommendation(BaseModel):
    rank: int
    score: float
    resolution: str
    knowledge: str
    titre: str
    fallback: bool = False


class FullResponse(BaseModel):
    ticket_titre: str
    prediction: PredictionResult
    recommendations: List[Recommendation]
    message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    rag_loaded: bool
    version: str = "1.0.0"
