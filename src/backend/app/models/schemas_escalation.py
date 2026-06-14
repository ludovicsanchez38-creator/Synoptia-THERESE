"""
THÉRÈSE v2 - Schemas Escalation

Request/Response models pour le suivi de tokens, coûts et limites.
"""

from pydantic import BaseModel, Field


class TokenLimitsRequest(BaseModel):
    """Token limits configuration request."""

    # Validation gt=0 : une limite a 0 provoquait une division par zero -> 500 (rapport Syn 14/06)
    max_input_tokens: int = Field(default=8000, gt=0)
    max_output_tokens: int = Field(default=4000, gt=0)
    daily_input_limit: int = Field(default=500000, gt=0)
    daily_output_limit: int = Field(default=100000, gt=0)
    monthly_budget_eur: float = Field(default=50.0, gt=0)
    warn_at_percentage: int = Field(default=80, ge=1, le=100)


class CostEstimateRequest(BaseModel):
    """Cost estimation request."""

    model: str
    input_tokens: int
    output_tokens: int


class UncertaintyCheckRequest(BaseModel):
    """Uncertainty check request."""

    response: str
