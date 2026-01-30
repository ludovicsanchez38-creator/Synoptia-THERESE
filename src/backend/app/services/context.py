"""
THÉRÈSE v2 - Context Window Module

Manages conversation context within token limits.
Sprint 2 - PERF-2.1: Extracted from monolithic llm.py
"""

from dataclasses import dataclass

from app.services.providers.base import Message


@dataclass
class ContextWindow:
    """Manages conversation context within token limits."""

    messages: list[Message]
    system_prompt: str | None = None
    max_tokens: int = 100000  # Reserve some space for response

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars = 1 token for most languages)."""
        return len(text) // 4

    def total_tokens(self) -> int:
        """Estimate total tokens in the context."""
        total = 0
        if self.system_prompt:
            total += self.estimate_tokens(self.system_prompt)
        for msg in self.messages:
            total += self.estimate_tokens(msg.content) + 4  # role overhead
        return total

    def trim_to_fit(self) -> "ContextWindow":
        """Trim oldest messages to fit within max_tokens."""
        while self.total_tokens() > self.max_tokens and len(self.messages) > 1:
            # Always keep the system prompt and last user message
            # Remove oldest non-system messages
            self.messages.pop(0)
        return self

    def to_anthropic_format(self) -> tuple[str | None, list[dict]]:
        """Convert to Anthropic API format."""
        # Filter out empty messages (Anthropic rejects empty content)
        messages = [
            {"role": m.role, "content": m.content}
            for m in self.messages
            if m.content and m.content.strip()
        ]
        return self.system_prompt, messages

    def to_mistral_format(self) -> list[dict]:
        """Convert to Mistral API format."""
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        # Filter out empty messages
        messages.extend([
            {"role": m.role, "content": m.content}
            for m in self.messages
            if m.content and m.content.strip()
        ])
        return messages

    def to_openai_format(self) -> list[dict]:
        """Convert to OpenAI API format (same as Mistral)."""
        return self.to_mistral_format()

    def to_gemini_format(self) -> tuple[str | None, list[dict]]:
        """Convert to Google Gemini API format."""
        # Gemini uses "contents" with "parts" and separate systemInstruction
        contents = []
        for msg in self.messages:
            role = "user" if msg.role == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
        return self.system_prompt, contents
