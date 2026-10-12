"""Envelopes específicos da API."""

from pydantic import BaseModel

from app.models import League


class HealthResponse(BaseModel):
    status: str
    version: str
    ligas: list[League]
