"""Pydantic schemas for the API."""

from pydantic import BaseModel


class PredictRequest(BaseModel):
    text: str


class PredictResponse(BaseModel):
    label: str
    input: str
