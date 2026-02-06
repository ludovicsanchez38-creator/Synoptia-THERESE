"""
THERESE v2 - Token Tracker Service

US-ESC-01 to US-ESC-05: Token tracking, cost estimation, and limits.
"""

import logging
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


# ============================================================
# Token Pricing (per 1M tokens, January 2026)
# ============================================================

TOKEN_PRICES = {
    # Anthropic (février 2026)
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "claude-opus-4-6": {"input": 5.00, "output": 25.00},
    # OpenAI (février 2026)
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "o3": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    # Gemini (février 2026)
    "gemini-3-pro-preview": {"input": 1.25, "output": 5.00},
    "gemini-3-flash-preview": {"input": 0.075, "output": 0.30},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
    # Mistral (février 2026)
    "mistral-large-latest": {"input": 2.00, "output": 6.00},
    "codestral-latest": {"input": 0.30, "output": 0.90},
    "mistral-small-latest": {"input": 0.20, "output": 0.60},
    # Grok (février 2026 - tarifs corrigés)
    "grok-3": {"input": 5.00, "output": 15.00},
    "grok-3-fast": {"input": 5.00, "output": 25.00},
    # Ollama (local, no cost)
    "default": {"input": 0.0, "output": 0.0},
}


# ============================================================
# US-ESC-03: Token Limits
# ============================================================


@dataclass
class TokenLimits:
    """Token limit configuration."""

    # Per-message limits
    max_input_tokens: int = 8000
    max_output_tokens: int = 4000

    # Daily limits
    daily_input_limit: int = 500000  # 500K tokens/day
    daily_output_limit: int = 100000  # 100K tokens/day

    # Monthly budget (in EUR)
    monthly_budget_eur: float = 50.0

    # Warnings
    warn_at_percentage: int = 80  # Warn when usage reaches 80%

    def to_dict(self) -> dict:
        return {
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "daily_input_limit": self.daily_input_limit,
            "daily_output_limit": self.daily_output_limit,
            "monthly_budget_eur": self.monthly_budget_eur,
            "warn_at_percentage": self.warn_at_percentage,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TokenLimits":
        return cls(
            max_input_tokens=data.get("max_input_tokens", 8000),
            max_output_tokens=data.get("max_output_tokens", 4000),
            daily_input_limit=data.get("daily_input_limit", 500000),
            daily_output_limit=data.get("daily_output_limit", 100000),
            monthly_budget_eur=data.get("monthly_budget_eur", 50.0),
            warn_at_percentage=data.get("warn_at_percentage", 80),
        )


# ============================================================
# US-ESC-02/04: Token Usage Record
# ============================================================


@dataclass
class TokenUsageRecord:
    """Record of token usage for a single request."""

    timestamp: datetime
    conversation_id: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost_eur: float
    context_truncated: bool = False
    truncated_messages: int = 0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "conversation_id": self.conversation_id,
            "model": self.model,
            "provider": self.provider,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_eur": self.cost_eur,
            "context_truncated": self.context_truncated,
            "truncated_messages": self.truncated_messages,
        }


# ============================================================
# Token Tracker Service
# ============================================================


class TokenTracker:
    """
    Singleton service for tracking token usage and costs.

    Provides:
    - Real-time cost estimation (US-ESC-02)
    - Token limit enforcement (US-ESC-03)
    - Usage history (US-ESC-04)
    - Context truncation alerts (US-ESC-05)
    """

    _instance: "TokenTracker | None" = None

    def __new__(cls) -> "TokenTracker":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Usage history (keep last 1000 records)
        self._usage_history: deque[TokenUsageRecord] = deque(maxlen=1000)

        # Daily counters
        self._today_input: int = 0
        self._today_output: int = 0
        self._today_cost: float = 0.0
        self._today_date: str = datetime.now(UTC).strftime("%Y-%m-%d")

        # Monthly counters
        self._month_input: int = 0
        self._month_output: int = 0
        self._month_cost: float = 0.0
        self._current_month: str = datetime.now(UTC).strftime("%Y-%m")

        # Limits
        self._limits = TokenLimits()

    def set_limits(self, limits: TokenLimits) -> None:
        """Set token limits."""
        self._limits = limits
        logger.info(f"[TOKEN] Limits updated: {limits.to_dict()}")

    def get_limits(self) -> TokenLimits:
        """Get current token limits."""
        return self._limits

    def _reset_daily_if_needed(self) -> None:
        """Reset daily counters if date has changed."""
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        if today != self._today_date:
            self._today_input = 0
            self._today_output = 0
            self._today_cost = 0.0
            self._today_date = today

    def _reset_monthly_if_needed(self) -> None:
        """Reset monthly counters if month has changed."""
        month = datetime.now(UTC).strftime("%Y-%m")
        if month != self._current_month:
            self._month_input = 0
            self._month_output = 0
            self._month_cost = 0.0
            self._current_month = month

    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Estimate cost for a request (US-ESC-02).

        Returns cost in EUR.
        """
        prices = TOKEN_PRICES.get(model, TOKEN_PRICES["default"])
        input_cost = (input_tokens / 1_000_000) * prices["input"]
        output_cost = (output_tokens / 1_000_000) * prices["output"]
        return input_cost + output_cost

    def record_usage(
        self,
        conversation_id: str,
        model: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        context_truncated: bool = False,
        truncated_messages: int = 0,
    ) -> TokenUsageRecord:
        """
        Record token usage for a request (US-ESC-04).
        """
        self._reset_daily_if_needed()
        self._reset_monthly_if_needed()

        cost = self.estimate_cost(model, input_tokens, output_tokens)

        record = TokenUsageRecord(
            timestamp=datetime.now(UTC),
            conversation_id=conversation_id,
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_eur=cost,
            context_truncated=context_truncated,
            truncated_messages=truncated_messages,
        )

        self._usage_history.append(record)

        # Update counters
        self._today_input += input_tokens
        self._today_output += output_tokens
        self._today_cost += cost

        self._month_input += input_tokens
        self._month_output += output_tokens
        self._month_cost += cost

        logger.info(
            f"[TOKEN] Recorded: {input_tokens} in / {output_tokens} out "
            f"({cost:.4f} EUR) - {model}"
        )

        return record

    def check_limits(
        self,
        input_tokens: int,
        output_tokens: int | None = None,
    ) -> dict:
        """
        Check if a request would exceed limits (US-ESC-03).

        Returns dict with status and any warnings/errors.
        """
        self._reset_daily_if_needed()
        self._reset_monthly_if_needed()

        result = {
            "allowed": True,
            "warnings": [],
            "errors": [],
        }

        # Check per-message limits
        if input_tokens > self._limits.max_input_tokens:
            result["errors"].append(
                f"Message trop long: {input_tokens} tokens "
                f"(limite: {self._limits.max_input_tokens})"
            )
            result["allowed"] = False

        # Check daily limits
        projected_daily_input = self._today_input + input_tokens
        daily_input_pct = (projected_daily_input / self._limits.daily_input_limit) * 100

        if daily_input_pct >= 100:
            result["errors"].append(
                f"Limite quotidienne atteinte: {projected_daily_input:,} tokens "
                f"(limite: {self._limits.daily_input_limit:,})"
            )
            result["allowed"] = False
        elif daily_input_pct >= self._limits.warn_at_percentage:
            result["warnings"].append(
                f"Utilisation quotidienne: {daily_input_pct:.0f}% "
                f"({projected_daily_input:,} / {self._limits.daily_input_limit:,} tokens)"
            )

        # Check monthly budget
        if output_tokens:
            estimated_cost = self.estimate_cost("default", input_tokens, output_tokens)
            projected_month_cost = self._month_cost + estimated_cost
            budget_pct = (projected_month_cost / self._limits.monthly_budget_eur) * 100

            if budget_pct >= 100:
                result["errors"].append(
                    f"Budget mensuel atteint: {projected_month_cost:.2f} EUR "
                    f"(budget: {self._limits.monthly_budget_eur:.2f} EUR)"
                )
                result["allowed"] = False
            elif budget_pct >= self._limits.warn_at_percentage:
                result["warnings"].append(
                    f"Budget mensuel: {budget_pct:.0f}% "
                    f"({projected_month_cost:.2f} / {self._limits.monthly_budget_eur:.2f} EUR)"
                )

        return result

    def get_daily_usage(self) -> dict:
        """Get today's usage summary."""
        self._reset_daily_if_needed()

        return {
            "date": self._today_date,
            "input_tokens": self._today_input,
            "output_tokens": self._today_output,
            "total_tokens": self._today_input + self._today_output,
            "cost_eur": self._today_cost,
            "input_limit": self._limits.daily_input_limit,
            "output_limit": self._limits.daily_output_limit,
            "input_usage_pct": (self._today_input / self._limits.daily_input_limit) * 100,
            "output_usage_pct": (self._today_output / self._limits.daily_output_limit) * 100,
        }

    def get_monthly_usage(self) -> dict:
        """Get this month's usage summary."""
        self._reset_monthly_if_needed()

        return {
            "month": self._current_month,
            "input_tokens": self._month_input,
            "output_tokens": self._month_output,
            "total_tokens": self._month_input + self._month_output,
            "cost_eur": self._month_cost,
            "budget_eur": self._limits.monthly_budget_eur,
            "budget_usage_pct": (self._month_cost / self._limits.monthly_budget_eur) * 100,
        }

    def get_usage_history(
        self,
        limit: int = 50,
        conversation_id: str | None = None,
    ) -> list[dict]:
        """
        Get usage history (US-ESC-04).

        Optionally filter by conversation.
        """
        records = list(self._usage_history)

        if conversation_id:
            records = [r for r in records if r.conversation_id == conversation_id]

        # Sort by timestamp descending
        records.sort(key=lambda r: r.timestamp, reverse=True)

        return [r.to_dict() for r in records[:limit]]

    def get_stats(self) -> dict:
        """Get overall token tracking stats."""
        return {
            "daily": self.get_daily_usage(),
            "monthly": self.get_monthly_usage(),
            "limits": self._limits.to_dict(),
            "history_count": len(self._usage_history),
        }


# Singleton accessor
_token_tracker: TokenTracker | None = None


def get_token_tracker() -> TokenTracker:
    """Get the token tracker singleton."""
    global _token_tracker
    if _token_tracker is None:
        _token_tracker = TokenTracker()
    return _token_tracker


# ============================================================
# US-ESC-01: Confidence/Uncertainty Detection
# ============================================================

# Phrases that indicate LLM uncertainty
UNCERTAINTY_PHRASES = [
    "je ne suis pas sur",
    "je ne suis pas certain",
    "il est possible que",
    "je pense que",
    "peut-etre",
    "probablement",
    "il semble que",
    "d'apres ce que je sais",
    "sous reserve",
    "je ne peux pas confirmer",
    "a ma connaissance",
    "i'm not sure",
    "i'm not certain",
    "it's possible that",
    "i think",
    "maybe",
    "probably",
    "it seems",
    "as far as i know",
    "i cannot confirm",
]


def detect_uncertainty(response: str) -> dict:
    """
    Detect if the LLM response indicates uncertainty (US-ESC-01).

    Returns dict with uncertainty indicators.
    """
    lower_response = response.lower()

    # Check for uncertainty phrases
    detected_phrases = []
    for phrase in UNCERTAINTY_PHRASES:
        if phrase in lower_response:
            detected_phrases.append(phrase)

    # Calculate confidence score (inverse of uncertainty)
    # More uncertainty phrases = lower confidence
    base_confidence = 100
    penalty_per_phrase = 15
    confidence_score = max(0, base_confidence - (len(detected_phrases) * penalty_per_phrase))

    # Classify confidence level
    if confidence_score >= 80:
        confidence_level = "high"
    elif confidence_score >= 50:
        confidence_level = "medium"
    else:
        confidence_level = "low"

    return {
        "is_uncertain": len(detected_phrases) > 0,
        "uncertainty_phrases": detected_phrases,
        "confidence_score": confidence_score,
        "confidence_level": confidence_level,
        "should_verify": confidence_level in ["low", "medium"] and len(detected_phrases) > 1,
    }
