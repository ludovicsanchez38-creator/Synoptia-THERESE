"""
THERESE v2 - Escalation Router

API endpoints for token tracking, cost estimation, and limits.
US-ESC-01 to US-ESC-05.
"""

import json
import logging

from app.models.database import get_session
from app.models.entities import Preference
from app.models.schemas_escalation import (
    CostEstimateRequest,
    TokenLimitsRequest,
    UncertaintyCheckRequest,
)
from app.services.token_tracker import (
    TokenLimits,
    detect_uncertainty,
    get_token_tracker,
)
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# US-ESC-02: Cost Estimation
# ============================================================


@router.post("/estimate-cost")
async def estimate_cost(request: CostEstimateRequest):
    """
    Estimate cost for a request.

    Returns estimated cost in EUR.
    """
    tracker = get_token_tracker()
    cost = tracker.estimate_cost(
        request.model,
        request.input_tokens,
        request.output_tokens,
    )

    return {
        "model": request.model,
        "input_tokens": request.input_tokens,
        "output_tokens": request.output_tokens,
        "estimated_cost_eur": cost,
    }


@router.get("/prices")
async def get_token_prices():
    """Get current token pricing information."""
    from app.services.token_tracker import TOKEN_PRICES

    # Format prices for display
    formatted = {}
    for model, prices in TOKEN_PRICES.items():
        if model == "default":
            continue
        formatted[model] = {
            "input_per_1m": prices["input"],
            "output_per_1m": prices["output"],
            "input_per_1k": prices["input"] / 1000,
            "output_per_1k": prices["output"] / 1000,
        }

    return {"prices": formatted, "currency": "EUR"}


# ============================================================
# US-ESC-03: Token Limits
# ============================================================


@router.get("/limits")
async def get_token_limits(
    session: AsyncSession = Depends(get_session),
):
    """Get current token limits configuration."""
    # Try to load from database
    result = await session.execute(
        select(Preference).where(Preference.key == "token_limits")
    )
    pref = result.scalar_one_or_none()

    if pref:
        try:
            data = json.loads(pref.value)
            limits = TokenLimits.from_dict(data)
            # Update tracker with saved limits
            tracker = get_token_tracker()
            tracker.set_limits(limits)
            return limits.to_dict()
        except (json.JSONDecodeError, TypeError):
            pass

    # Return default limits
    return TokenLimits().to_dict()


@router.post("/limits")
async def set_token_limits(
    request: TokenLimitsRequest,
    session: AsyncSession = Depends(get_session),
):
    """Set token limits configuration."""
    limits = TokenLimits(
        max_input_tokens=request.max_input_tokens,
        max_output_tokens=request.max_output_tokens,
        daily_input_limit=request.daily_input_limit,
        daily_output_limit=request.daily_output_limit,
        monthly_budget_eur=request.monthly_budget_eur,
        warn_at_percentage=request.warn_at_percentage,
    )

    # Save to database
    result = await session.execute(
        select(Preference).where(Preference.key == "token_limits")
    )
    pref = result.scalar_one_or_none()

    value = json.dumps(limits.to_dict())

    if pref:
        pref.value = value
    else:
        pref = Preference(
            key="token_limits",
            value=value,
            category="llm",
        )
        session.add(pref)

    await session.commit()

    # Update tracker
    tracker = get_token_tracker()
    tracker.set_limits(limits)

    return limits.to_dict()


@router.post("/check-limits")
async def check_limits(
    input_tokens: int = Query(..., description="Number of input tokens"),
    output_tokens: int | None = Query(None, description="Estimated output tokens"),
):
    """
    Check if a request would exceed limits.

    Returns allowed status and any warnings/errors.
    """
    tracker = get_token_tracker()
    result = tracker.check_limits(input_tokens, output_tokens)
    return result


# ============================================================
# US-ESC-04: Usage History
# ============================================================


@router.get("/usage/daily")
async def get_daily_usage():
    """Get today's token usage summary."""
    tracker = get_token_tracker()
    return tracker.get_daily_usage()


@router.get("/usage/monthly")
async def get_monthly_usage():
    """Get this month's token usage summary."""
    tracker = get_token_tracker()
    return tracker.get_monthly_usage()


@router.get("/usage/history")
async def get_usage_history(
    limit: int = Query(50, ge=1, le=500),
    conversation_id: str | None = None,
):
    """
    Get token usage history.

    Optionally filter by conversation.
    """
    tracker = get_token_tracker()
    history = tracker.get_usage_history(limit, conversation_id)
    return {
        "history": history,
        "count": len(history),
    }


@router.get("/usage/stats")
async def get_usage_stats():
    """Get overall usage statistics."""
    tracker = get_token_tracker()
    return tracker.get_stats()


# ============================================================
# US-ESC-01: Uncertainty Detection
# ============================================================


@router.post("/check-uncertainty")
async def check_uncertainty(request: UncertaintyCheckRequest):
    """
    Check if a response indicates uncertainty.

    Returns confidence level and detected uncertainty phrases.
    """
    result = detect_uncertainty(request.response)
    return result


# ============================================================
# US-ESC-05: Context Truncation Info
# ============================================================


@router.get("/context-info")
async def get_context_info():
    """
    Get information about context window limits.

    Returns model context limits and truncation policies.
    """
    context_limits = {
        # Anthropic
        "claude-sonnet-4-5-20250929": 200000,
        "claude-haiku-4-5-20251001": 200000,
        "claude-opus-4-6": 200000,
        # OpenAI
        "gpt-4o": 128000,
        "gpt-4-turbo": 128000,
        "o3": 128000,
        "o4-mini": 128000,
        # Gemini
        "gemini-3-pro-preview": 1000000,
        "gemini-3-flash-preview": 1000000,
        "gemini-2.5-pro": 1000000,
        "gemini-2.5-flash": 1000000,
        # Mistral
        "mistral-large-latest": 128000,
        "codestral-latest": 32000,
        "mistral-small-latest": 32000,
        # Grok
        "grok-3": 131072,
        "grok-3-fast": 131072,
    }

    truncation_policy = {
        "strategy": "oldest_first",
        "description": "Les messages les plus anciens sont supprimes en premier",
        "keep_system_prompt": True,
        "keep_last_n_messages": 4,
        "warning_threshold_pct": 90,
    }

    return {
        "context_limits": context_limits,
        "truncation_policy": truncation_policy,
        "recommendation": "Pour les conversations longues, creez une nouvelle conversation ou utilisez un modele avec un contexte plus large (Gemini).",
    }


# ============================================================
# Combined Status
# ============================================================


@router.get("/status")
async def get_escalation_status(
    session: AsyncSession = Depends(get_session),
):
    """Get combined escalation and limits status."""
    tracker = get_token_tracker()

    return {
        "daily_usage": tracker.get_daily_usage(),
        "monthly_usage": tracker.get_monthly_usage(),
        "limits": tracker.get_limits().to_dict(),
        "recent_history_count": len(tracker._usage_history),
    }
