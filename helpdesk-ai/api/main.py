"""FastAPI application."""

from fastapi import FastAPI

from .schemas import PredictRequest, PredictResponse
from src.models.predict import predict

app = FastAPI()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def run_predict(payload: PredictRequest) -> PredictResponse:
    result = predict(payload.text)
    return PredictResponse(**result)
