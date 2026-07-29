"""Health response schema — used by /api/v1/health."""
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    message: str
