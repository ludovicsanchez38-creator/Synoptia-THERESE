"""P-057 (Ludo, 09/09/2026, accepté pour la 0.70.0) : le modèle OpenAI gpt-6-astra
entre dans THÉRÈSE, et D184 (secondes lectures c6) : chaque modèle du catalogue a un
tarif, sinon le budget affiche un coût menti à 0,00.

Sources relevées le 10/09/2026 : developers.openai.com/api/docs/pricing (gpt-6-astra
10 $ / 50 $ par million, standard), developers.openai.com/api/docs/models/gpt-6-astra
(contexte 1 050 000, sortie 128 000, reasoning.effort low/medium/high/xhigh/max),
platform.claude.com/docs/en/about-claude/pricing, ai.google.dev/gemini-api/docs/pricing,
docs.mistral.ai/inference/pricing, docs.x.ai/docs/models.
"""

from __future__ import annotations

import json
import pathlib

import pytest

RACINE = pathlib.Path(__file__).resolve().parent.parent


def test_gpt_6_astra_est_au_catalogue_openai_avec_sa_fiche():
    from app.services.modeles_catalogue import CATALOGUE, resoudre_effort

    openai = CATALOGUE["openai"]
    assert "gpt-6-astra" in openai.modeles
    assert openai.modeles[1] == "gpt-6-astra", "même convention qu'Anthropic : le recommandé d'abord, la puissance maximale juste après"
    for effort in ("low", "medium", "high", "xhigh", "max"):
        assert resoudre_effort("gpt-6-astra", effort, "openai") == effort, effort
    assert resoudre_effort("gpt-6-astra", "none", "openai") is None, "« none » n'est pas documenté pour gpt-6-astra : rien n'est envoyé"


def test_gpt_6_astra_suit_la_famille_raisonnante_cote_backend_et_temoins():
    from app.services.providers.openai import _uses_max_completion_tokens

    assert _uses_max_completion_tokens("gpt-6-astra") is True
    temoins = json.loads((RACINE / "src/frontend/src/lib/effortOpenAI.temoins.json").read_text(encoding="utf-8"))
    assert temoins["temoins"].get("gpt-6-astra") is True
    assert "gpt-6-astra" in temoins["effort_transmis_sans_outils"]


def test_gpt_6_astra_a_son_tarif():
    from app.services.token_tracker import TOKEN_PRICES

    assert TOKEN_PRICES["gpt-6-astra"] == {"input": 10.00, "output": 50.00}


def test_chaque_modele_du_catalogue_a_un_tarif():
    from app.services.modeles_catalogue import CATALOGUE
    from app.services.token_tracker import TOKEN_PRICES

    manquants = [
        f"{nom}/{modele}"
        for nom, fiche in CATALOGUE.items()
        if nom in ("anthropic", "openai", "gemini", "mistral", "grok")
        for modele in fiche.modeles
        if modele not in TOKEN_PRICES
    ]
    assert not manquants, f"modèles du catalogue sans tarif (coût affiché 0,00) : {manquants}"


@pytest.mark.parametrize(
    "modele, attendu",
    [
        ("claude-fable-5", {"input": 10.00, "output": 50.00}),
        ("claude-sonnet-5", {"input": 2.00, "output": 10.00}),
        ("claude-opus-4-7", {"input": 5.00, "output": 25.00}),
        ("claude-opus-4-6", {"input": 5.00, "output": 25.00}),
        ("gemini-3.6-flash", {"input": 0.75, "output": 3.75}),
        ("gemini-3.5-flash-lite", {"input": 0.30, "output": 2.50}),
        ("mistral-medium-latest", {"input": 1.50, "output": 7.50}),
        ("grok-4.5", {"input": 2.00, "output": 6.00}),
    ],
)
def test_les_tarifs_releves_le_10_09_sont_ceux_du_compteur(modele, attendu):
    from app.services.token_tracker import TOKEN_PRICES

    assert TOKEN_PRICES.get(modele) == attendu, f"{modele} : {TOKEN_PRICES.get(modele)}"


def test_la_fenetre_de_contexte_suit_le_modele_pas_seulement_le_fournisseur():
    """Revue Grok 0.70.0 (P2) : la fiche gpt-6-astra annonçait 1 050 000 jetons en
    commentaire, mais `prepare_context` coupait à la fenêtre du fournisseur
    (200 000) ; un long document sur Astra était tronqué bien avant sa capacité."""
    from app.services.modeles_catalogue import fenetre_de_contexte

    assert fenetre_de_contexte("openai", "gpt-6-astra") == 1_050_000
    assert fenetre_de_contexte("openai", "gpt-5.6-sol") == 200_000
    assert fenetre_de_contexte("anthropic", "claude-inconnu") == 200_000
