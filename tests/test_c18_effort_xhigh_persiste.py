"""xhigh est accepté à l'enregistrement et doit survivre au redémarrage.

La lecture de llm_effort ne gardait que low, medium, high et max.
Un nouveau service, qui relit les préférences, perdait le réglage.
"""

from __future__ import annotations

import pytest


async def _poser(db_session, **valeurs: str) -> None:
    from app.models.entities import Preference

    for cle, valeur in valeurs.items():
        db_session.add(Preference(key=cle, value=valeur, category="llm"))
    await db_session.commit()


class TestEffortXhighPersiste:
    @pytest.mark.asyncio
    async def test_un_redemarrage_simule_relit_xhigh(self, client, db_session, monkeypatch):
        from app.services import llm as module

        await _poser(
            db_session,
            llm_provider="openai",
            llm_model="gpt-6.1-sol",
            llm_effort="xhigh",
        )
        monkeypatch.setattr(
            module, "_get_api_key_from_db", lambda nom: "cle-test" if nom == "openai" else None,
        )
        monkeypatch.setattr(module, "_cle_depuis_environnement", lambda nom: None)
        module.invalidate_llm_service()
        service = module.LLMService()
        assert service.config.model == "gpt-6.1-sol"
        assert service.config.effort == "xhigh"
