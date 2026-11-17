"""Garde les preuves de l'intégration et éprouve le test de confidentialité."""

from pathlib import Path

import pytest


def test_les_preuves_integrees_sont_livrees():
    racine = Path(__file__).resolve().parents[1]
    attendus = [
        "tests/test_c20_windows_zombies.py", "tests/test_c20_relance_sidecar.py",
        "tests/test_b1806_banc_ollama.py", "tests/test_b1807_recette_deb.py",
        "tests/test_b1851_preuve_frontiere.py", "tests/test_b1852_preuve_attribution.py",
        "tests/test_b2029_couverture.py", "tests/test_b2033_charges.py",
        "tests/bancs_sans_reseau.py",
        "src/frontend/src/App.lienEvitement.b1915.test.tsx",
        "src/frontend/src/components/SplashScreen.relanceDemarrage.b1912.test.tsx",
        "src/frontend/src/components/board/BoardPanel.interactionsHistorique.b1913.test.tsx",
        "src/frontend/src/components/board/BoardPanel.visibiliteSuppression.b1914.test.tsx",
        "src/frontend/src/components/calendar/CalendarPanel.reconnexion.chargement.test.tsx",
        "src/frontend/src/components/chat/MessageBubble.b1970.test.tsx",
        "src/frontend/src/lib/chatPersistence.fin.test.ts",
        "src/frontend/src/test/b1854-garde-parcours.test.ts",
    ]
    absents = [p for p in attendus if not (racine / p).is_file()]
    assert not absents, f"Preuves intégrées absentes : {absents}"


@pytest.mark.asyncio
@pytest.mark.parametrize("defaut", ["aucune_erreur", "champ_annexe"])
async def test_la_preuve_fournisseur_refuse_un_flux_invalide(monkeypatch, defaut):
    from app.services.providers.base import StreamEvent
    from app.services.providers.openrouter import OpenRouterProvider

    from tests.test_frontiere_erreurs import TestRevueSosoPasse2

    async def flux_invalide(*_args, **_kwargs):
        if defaut == "aucune_erreur":
            yield StreamEvent(type="done")
        else:
            # Le témoin synthétique est celui injecté par le test historique.
            yield StreamEvent(type="error", content="Erreur publique", tool_call={
                "detail": ["/Users/ludo/.therese/cle-sk-123 trace-interne"],
            })

    monkeypatch.setattr(OpenRouterProvider, "stream", flux_invalide)
    with pytest.raises(AssertionError):
        await TestRevueSosoPasse2().test_p7_f2_openrouter_et_ollama_ne_relaient_pas_le_detail(monkeypatch)
