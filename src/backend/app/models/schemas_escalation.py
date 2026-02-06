"""
THÉRÈSE v2 - Schemas Escalation

Request/Response models pour le suivi de tokens, coûts et limites.
"""

from pydantic import BaseModel


class TokenLimitsRequest(BaseModel):
    """Token limits configuration request."""

    max_input_tokens: int = 8000
    max_output_tokens: int = 4000
    daily_input_limit: int = 500000
    daily_output_limit: int = 100000
    monthly_budget_eur: float = 50.0
    warn_at_percentage: int = 80


class CostEstimateRequest(BaseModel):
    """Cost estimation request."""

    model: str
    input_tokens: int
    output_tokens: int


class UncertaintyCheckRequest(BaseModel):
    """Uncertainty check request."""

    response: str
