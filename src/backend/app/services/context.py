"""
THÉRÈSE v2 - Context Window Module

Manages conversation context within token limits.
Sprint 2 - PERF-2.1: Extracted from monolithic llm.py
"""

from dataclasses import dataclass
from typing import Any

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

    _MARQUE_TRONCATURE = "\n[... contenu tronqué pour tenir dans la fenêtre du modèle]"

    def trim_to_fit(self) -> "ContextWindow":
        """Trim oldest messages to fit within max_tokens."""
        while self.total_tokens() > self.max_tokens and len(self.messages) > 1:
            # Always keep the system prompt and last user message
            # Remove oldest non-system messages
            self.messages.pop(0)
        # Revue 0.48 (F2, durci p2/F3) : quand il ne reste qu'UN message et
        # qu'il déborde encore (le Board met question + contexte + résultats
        # web dans un seul message), tronquer son CONTENU au budget - en
        # préservant le DÉBUT ET LA FIN (une question placée après un long
        # collage survit), la marque au point de coupe. Budget déjà épuisé
        # par le prompt système : ne PAS vider la demande - un refus propre
        # de l'API vaut mieux qu'une question disparue en silence.
        if self.messages and self.total_tokens() > self.max_tokens:
            dernier = self.messages[-1]
            hors_dernier = self.total_tokens() - self.estimate_tokens(dernier.content)
            budget_tokens = self.max_tokens - hors_dernier - self.estimate_tokens(
                self._MARQUE_TRONCATURE
            )
            budget_chars = budget_tokens * 4
            if budget_chars > 0:
                tete = budget_chars // 2
                queue = budget_chars - tete
                dernier.content = (
                    dernier.content[:tete]
                    + self._MARQUE_TRONCATURE
                    + dernier.content[-queue:]
                )
        return self

    @staticmethod
    def _a_du_fond(m: Message) -> bool:
        """Un message porte du fond s'il a du texte OU une image.

        31/08 : le filtre ne regardait que le texte. Déposer une capture sans
        rien écrire, le geste le plus naturel qui soit, faisait disparaître le
        message entier avant d'atteindre le modèle.
        """
        return bool((m.content and m.content.strip()) or m.images)

    def to_anthropic_format(self) -> tuple[str | None, list[dict]]:
        """Convert to Anthropic API format."""
        # Filter out empty messages (Anthropic rejects empty content)
        messages: list[dict[str, Any]] = []
        for m in self.messages:
            if not self._a_du_fond(m):
                continue
            if not m.images:
                messages.append({"role": m.role, "content": m.content})
                continue
            blocs: list[dict[str, Any]] = []
            if m.content and m.content.strip():
                blocs.append({"type": "text", "text": m.content})
            blocs.extend(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image.media_type,
                        "data": image.donnees_base64,
                    },
                }
                for image in m.images
            )
            messages.append({"role": m.role, "content": blocs})
        return self.system_prompt, messages

    def to_mistral_format(self) -> list[dict]:
        """Convert to Mistral API format."""
        messages: list[dict[str, Any]] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        # Filter out empty messages
        for m in self.messages:
            if not self._a_du_fond(m):
                continue
            if not m.images:
                messages.append({"role": m.role, "content": m.content})
                continue
            blocs: list[dict[str, Any]] = []
            if m.content and m.content.strip():
                blocs.append({"type": "text", "text": m.content})
            blocs.extend(
                {"type": "image_url", "image_url": {"url": image.uri_donnees()}}
                for image in m.images
            )
            messages.append({"role": m.role, "content": blocs})
        return messages

    def to_openai_format(self) -> list[dict]:
        """Convert to OpenAI API format (same as Mistral)."""
        return self.to_mistral_format()

    def to_gemini_format(self) -> tuple[str | None, list[dict]]:
        """Convert to Google Gemini API format."""
        # Gemini uses "contents" with "parts" and separate systemInstruction
        # Filter out empty messages (Gemini rejects empty parts)
        contents: list[dict[str, Any]] = []
        for msg in self.messages:
            if not self._a_du_fond(msg):
                continue
            role = "user" if msg.role == "user" else "model"
            parts: list[dict[str, Any]] = []
            if msg.content and msg.content.strip():
                parts.append({"text": msg.content})
            parts.extend(
                {
                    "inline_data": {
                        "mime_type": image.media_type,
                        "data": image.donnees_base64,
                    }
                }
                for image in msg.images
            )
            contents.append({"role": role, "parts": parts})
        return self.system_prompt, contents
