"""Le scénario de refus doit rester valable sur une machine à grande mémoire."""

import pytest
from app.services import ollama_budget

from tests.test_r2_3_outil import fournisseur  # noqa: F401
from tests.test_r3_4_ollama import (
    test_refus_a_lecran_meme_sans_fiches as verifier_refus_existant,
)


@pytest.mark.asyncio
@pytest.mark.parametrize("memoire", [True, False])
@pytest.mark.parametrize("stream", [True, False])
async def test_refus_existant_avec_grande_fenetre(
    client, db_session, fournisseur, monkeypatch, memoire, stream  # noqa: F811
):
    monkeypatch.setattr(ollama_budget, "plafond_memoire", lambda: 131072)
    await verifier_refus_existant(client, db_session, fournisseur, monkeypatch, memoire, stream)
