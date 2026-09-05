"""B-394 (05/09/2026) : le brouillon de réponse e-mail était signé « Ludo /
Synoptïa » chez une utilisatrice qui s'appelle Marie.

Le générateur ne lisait que le cache de processus (`get_cached_profile`).
Or le préchargement au démarrage ne déchiffre pas le profil (pas de prompt
trousseau bloquant) : sur un poste au profil chiffré, le cache reste vide
jusqu'à la première sauvegarde, et le brouillon partait au nom d'un autre.
C'est le trou fermé en juillet sur le statut de facturation, resté ouvert ici.
"""

from __future__ import annotations

import pytest

from app.services.email_response_generator import EmailResponseGenerator
from app.services.user_profile import (
    UserProfile,
    get_cached_profile,
    set_cached_profile,
    set_user_profile,
)


class _LLMTemoin:
    def __init__(self) -> None:
        self.system_prompt: str | None = None

    async def generate_content(self, prompt: str, system_prompt: str) -> str:
        self.system_prompt = system_prompt
        return "Bonjour, bien reçu.\n\nCordialement,\nMarie Exemple"


@pytest.mark.asyncio
async def test_le_brouillon_lit_le_profil_en_base_quand_le_cache_est_vide(client, monkeypatch):
    from app.models import database as db_module
    from app.services import email_response_generator as module

    async with db_module.AsyncSessionLocal() as session:
        await set_user_profile(
            session, UserProfile(name="Marie Exemple", company="Atelier Exemple", role="Décoratrice")
        )
    set_cached_profile(None)
    assert get_cached_profile() is None

    temoin = _LLMTemoin()
    monkeypatch.setattr(module, "get_llm_service", lambda: temoin)

    async with db_module.AsyncSessionLocal() as session:
        await EmailResponseGenerator.generate_response(
            subject="Devis",
            from_name="Paul Durand",
            from_email="paul@example.test",
            body="Pouvez-vous me renvoyer le devis ?",
            session=session,
        )

    assert temoin.system_prompt is not None
    assert "Marie Exemple" in temoin.system_prompt, temoin.system_prompt[:200]
    assert "Atelier Exemple" in temoin.system_prompt
    assert "Ludo" not in temoin.system_prompt, "le brouillon part encore au nom d'un autre"
