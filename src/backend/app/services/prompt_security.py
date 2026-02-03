"""
THÉRÈSE v2 - Prompt Security Service

Protects against prompt injection attacks.
Sprint 2 - PERF-2.11: Input validation and sanitization.

Detection patterns based on OWASP LLM Top 10 (2025).
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ThreatLevel(str, Enum):
    """Threat severity levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityCheck:
    """Result of a security check."""
    is_safe: bool
    threat_level: ThreatLevel
    threat_type: Optional[str] = None
    details: Optional[str] = None
    sanitized_input: Optional[str] = None


# Patterns indicating potential prompt injection
INJECTION_PATTERNS = [
    # Direct instruction override attempts
    (r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)", ThreatLevel.HIGH, "instruction_override"),
    (r"disregard\s+(all\s+)?(previous|prior|above)", ThreatLevel.HIGH, "instruction_override"),
    (r"forget\s+(everything|all|what)\s+(you|i)\s+(said|told|wrote)", ThreatLevel.MEDIUM, "instruction_override"),

    # Role manipulation
    (r"you\s+are\s+now\s+(a|an|the)\s+\w+", ThreatLevel.MEDIUM, "role_manipulation"),
    (r"pretend\s+(to\s+be|you\s+are)", ThreatLevel.MEDIUM, "role_manipulation"),
    (r"act\s+as\s+(if|a|an|the)", ThreatLevel.LOW, "role_manipulation"),
    (r"from\s+now\s+on\s+(you|i)\s+(are|am|will)", ThreatLevel.MEDIUM, "role_manipulation"),

    # System prompt extraction
    (r"(show|display|print|reveal|tell)\s+(me\s+)?(your|the)\s+(system\s+)?(prompt|instructions?)", ThreatLevel.HIGH, "prompt_extraction"),
    (r"what\s+(are|is)\s+(your|the)\s+(system\s+)?(prompt|instructions?)", ThreatLevel.MEDIUM, "prompt_extraction"),
    (r"repeat\s+(your|the)\s+(initial|first|original)\s+(prompt|instructions?)", ThreatLevel.HIGH, "prompt_extraction"),

    # Delimiter injection
    (r"<\|?(system|user|assistant)\|?>", ThreatLevel.HIGH, "delimiter_injection"),
    (r"\[INST\]|\[/INST\]", ThreatLevel.HIGH, "delimiter_injection"),
    (r"###\s*(system|instruction|human|assistant)", ThreatLevel.MEDIUM, "delimiter_injection"),

    # Jailbreak attempts
    (r"(DAN|do\s+anything\s+now)\s+mode", ThreatLevel.CRITICAL, "jailbreak"),
    (r"(evil|dark|unfiltered)\s+mode", ThreatLevel.HIGH, "jailbreak"),
    (r"bypass\s+(safety|filter|restriction)", ThreatLevel.CRITICAL, "jailbreak"),
    (r"without\s+(any\s+)?(ethical|moral|safety)\s+(guidelines?|restrictions?)", ThreatLevel.HIGH, "jailbreak"),

    # Code injection via prompts
    (r"execute\s+(this\s+)?(code|command|script)", ThreatLevel.MEDIUM, "code_injection"),
    (r"run\s+(the\s+following|this)\s+(code|command)", ThreatLevel.MEDIUM, "code_injection"),

    # Data exfiltration
    (r"(send|post|upload|transmit)\s+(to|data|information)\s+(http|url|webhook)", ThreatLevel.HIGH, "data_exfiltration"),
    (r"curl\s+|wget\s+|fetch\s*\(", ThreatLevel.MEDIUM, "data_exfiltration"),

    # French injection patterns (SEC-016)
    # App targets French solopreneurs - must detect FR prompt injection

    # Instruction override (FR)
    (r"ignore[sz]?\s+(les?\s+)?instructions?\s+(pr[eé]c[eé]dentes?|ant[eé]rieures?|ci-dessus)", ThreatLevel.HIGH, "instruction_override"),
    (r"oublie[sz]?\s+(tes|les|toutes\s+les)\s+(r[eè]gles?|instructions?|consignes?)", ThreatLevel.HIGH, "instruction_override"),
    (r"ne\s+(tiens?|tenez)\s+(pas|plus)\s+compte\s+de", ThreatLevel.HIGH, "instruction_override"),

    # Role manipulation (FR)
    (r"tu\s+es\s+(maintenant|d[eé]sormais|dor[eé]navant)\s+", ThreatLevel.MEDIUM, "role_manipulation"),
    (r"fais\s+(semblant|comme\s+si)\s+(d[' ]?[eê]tre|tu\s+[eé]tais)", ThreatLevel.MEDIUM, "role_manipulation"),
    (r"comporte[- ]?toi\s+comme\s+(un|une|si)", ThreatLevel.MEDIUM, "role_manipulation"),
    (r"adopte\s+(le\s+)?r[oô]le\s+d", ThreatLevel.MEDIUM, "role_manipulation"),

    # Prompt extraction (FR)
    (r"(montre|affiche|r[eé]v[eè]le|donne)[- ]?moi\s+(ton|le|ta)\s+(prompt|instruction|consigne)", ThreatLevel.HIGH, "prompt_extraction"),
    (r"(quel|quelles?)\s+(est|sont)\s+(ton|ta|tes)\s+(prompt|instruction|consigne)", ThreatLevel.MEDIUM, "prompt_extraction"),
    (r"r[eé]p[eè]te\s+(ton|ta|tes|le)\s+(prompt|instruction|consigne)\s+(initial|original|syst[eè]me)", ThreatLevel.HIGH, "prompt_extraction"),

    # Jailbreak (FR)
    (r"mode\s+sans\s+(restriction|filtre|limite|censure)", ThreatLevel.HIGH, "jailbreak"),
    (r"contourne[sz]?\s+(les?\s+)?(restrictions?|filtres?|s[eé]curit[eé]s?|protections?)", ThreatLevel.CRITICAL, "jailbreak"),
    (r"d[eé]sactive[sz]?\s+(les?\s+)?(filtres?|restrictions?|protections?|s[eé]curit[eé]s?)", ThreatLevel.CRITICAL, "jailbreak"),
    (r"r[eé]ponds?\s+sans\s+(censure|filtre|restriction|limite)", ThreatLevel.HIGH, "jailbreak"),

    # Data exfiltration (FR)
    (r"(envoie|transmets?|transf[eè]re)[sz]?\s+(les?\s+)?(donn[eé]es?|informations?|fichiers?)\s+[aà]", ThreatLevel.HIGH, "data_exfiltration"),
    (r"(copie|exporte)[sz]?\s+(les?\s+)?(donn[eé]es?|base|contacts?)\s+(vers|sur|[aà])", ThreatLevel.MEDIUM, "data_exfiltration"),
]

# Characters to sanitize (potential encoding attacks)
DANGEROUS_CHARS = {
    "\u200b": "",  # Zero-width space
    "\u200c": "",  # Zero-width non-joiner
    "\u200d": "",  # Zero-width joiner
    "\ufeff": "",  # BOM
    "\u2028": " ",  # Line separator
    "\u2029": " ",  # Paragraph separator
}


class PromptSecurityService:
    """Service for prompt security checks."""

    def __init__(self, strict_mode: bool = True):
        """
        Initialize security service.

        Args:
            strict_mode: If True, block medium threats too (default: True for business apps)
        """
        self.strict_mode = strict_mode
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), level, threat_type)
            for pattern, level, threat_type in INJECTION_PATTERNS
        ]

    def check_input(self, text: str) -> SecurityCheck:
        """
        Check user input for potential prompt injection.

        Args:
            text: User input to check

        Returns:
            SecurityCheck with results
        """
        if not text:
            return SecurityCheck(is_safe=True, threat_level=ThreatLevel.NONE)

        # Sanitize invisible characters
        sanitized = self._sanitize_text(text)

        # Check for injection patterns
        highest_threat = ThreatLevel.NONE
        detected_type = None
        detected_details = None

        for pattern, level, threat_type in self._compiled_patterns:
            if pattern.search(sanitized):
                if self._threat_priority(level) > self._threat_priority(highest_threat):
                    highest_threat = level
                    detected_type = threat_type
                    detected_details = f"Pattern matched: {pattern.pattern[:50]}..."

        # Determine if safe
        if highest_threat == ThreatLevel.CRITICAL:
            is_safe = False
        elif highest_threat == ThreatLevel.HIGH:
            is_safe = False
        elif highest_threat == ThreatLevel.MEDIUM:
            is_safe = not self.strict_mode
        else:
            is_safe = True

        if not is_safe:
            logger.warning(
                f"Prompt injection detected: level={highest_threat.value}, "
                f"type={detected_type}"
            )

        return SecurityCheck(
            is_safe=is_safe,
            threat_level=highest_threat,
            threat_type=detected_type,
            details=detected_details,
            sanitized_input=sanitized if sanitized != text else None,
        )

    def sanitize_for_context(self, text: str, source: str = "user") -> str:
        """
        Sanitize text for inclusion in LLM context.

        Adds clear delimiters to prevent confusion.

        Args:
            text: Text to sanitize
            source: Source label (user, file, memory, etc.)

        Returns:
            Sanitized text with delimiters
        """
        sanitized = self._sanitize_text(text)

        # Escape any existing delimiters
        sanitized = sanitized.replace("---", "- - -")
        sanitized = sanitized.replace("###", "# # #")

        # Add clear source delimiter
        return f"[Source: {source}]\n{sanitized}\n[End {source}]"

    def _sanitize_text(self, text: str) -> str:
        """Remove dangerous characters from text."""
        result = text
        for char, replacement in DANGEROUS_CHARS.items():
            result = result.replace(char, replacement)
        return result

    def _threat_priority(self, level: ThreatLevel) -> int:
        """Get numeric priority for threat level."""
        priorities = {
            ThreatLevel.NONE: 0,
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.HIGH: 3,
            ThreatLevel.CRITICAL: 4,
        }
        return priorities.get(level, 0)


# Global instance
_security_service: PromptSecurityService | None = None


def get_prompt_security() -> PromptSecurityService:
    """Get global prompt security service (strict mode for business data)."""
    global _security_service
    if _security_service is None:
        _security_service = PromptSecurityService(strict_mode=True)
    return _security_service


def check_prompt_safety(text: str) -> SecurityCheck:
    """
    Convenience function to check prompt safety.

    Args:
        text: User input to check

    Returns:
        SecurityCheck with results
    """
    return get_prompt_security().check_input(text)
