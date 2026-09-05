"""B-482 et B-486 (05/09/2026), décision de Ludo : on AVERTIT pour un modèle
hors grille tarifaire, et les plafonds de jetons sont enfin APPLIQUÉS avant
l'appel au modèle.

Avant : `check_limits` comptait un modèle inconnu à 0 USD (donc jamais
plafonné), ignorait les deux contrôles de sortie, et n'avait AUCUN point
d'application : seul `/api/escalation/check-limits` l'appelait, que le
frontend n'appelle jamais. Les plafonds affichés avec leur pourcentage
n'avaient jamais bloqué une requête.
"""

from __future__ import annotations

import pytest
from app.services.token_tracker import TokenLimits, TokenTracker, get_token_tracker


def _tracker_isole() -> TokenTracker:
    tracker = object.__new__(TokenTracker)
    tracker._initialized = False
    tracker.__init__()
    return tracker


class TestCheckLimits:
    def test_un_modele_hors_grille_est_signale_sans_bloquer(self):
        tracker = _tracker_isole()
        verdict = tracker.check_limits(1000, 1000, model="modele-hors-grille-xyz")
        assert verdict["allowed"] is True
        assert any("hors grille" in w for w in verdict["warnings"]), verdict

    def test_un_modele_local_n_est_pas_signale(self):
        tracker = _tracker_isole()
        verdict = tracker.check_limits(1000, 1000, model="gemma4-tia:latest", local=True)
        assert verdict["warnings"] == []

    def test_la_limite_quotidienne_de_sortie_bloque(self):
        tracker = _tracker_isole()
        tracker.set_limits(TokenLimits(daily_output_limit=10))
        tracker._today_output = 10_000
        verdict = tracker.check_limits(input_tokens=1, output_tokens=1_000_000, model="claude-sonnet-4-6")
        assert verdict["allowed"] is False
        assert any("sortie" in e.lower() for e in verdict["errors"]), verdict

    def test_une_sortie_au_dela_du_plafond_par_message_avertit(self):
        tracker = _tracker_isole()
        tracker.set_limits(TokenLimits(max_output_tokens=10))
        verdict = tracker.check_limits(input_tokens=1, output_tokens=1000, model="claude-sonnet-4-6")
        assert verdict["allowed"] is True
        assert any("sortie" in w.lower() for w in verdict["warnings"]), verdict


@pytest.fixture
def budget_epuise():
    tracker = get_token_tracker()
    limites_avant = tracker.get_limits()
    cout_avant = tracker._month_cost
    tracker.set_limits(TokenLimits(monthly_budget_eur=0.01))
    tracker._month_cost = 5.0
    yield
    tracker.set_limits(limites_avant)
    tracker._month_cost = cout_avant


class TestLePlafondEstAppliqueDansLeChat:
    @pytest.mark.asyncio
    async def test_non_stream_refuse_avant_d_appeler_le_modele(self, client, budget_epuise):
        reponse = await client.post("/api/chat/send", json={"message": "Bonjour", "stream": False})
        assert reponse.status_code == 200, reponse.text[:200]
        contenu = reponse.json()["content"]
        assert contenu.startswith("Désolée"), contenu
        assert "Budget mensuel atteint" in contenu, contenu

    @pytest.mark.asyncio
    async def test_stream_refuse_avant_d_appeler_le_modele(self, client, budget_epuise):
        reponse = await client.post("/api/chat/send", json={"message": "Bonjour", "stream": True})
        assert reponse.status_code == 200
        assert '"type": "error"' in reponse.text
        assert "Budget mensuel atteint" in reponse.text

    @pytest.mark.asyncio
    async def test_un_avertissement_arrive_a_l_ecran(self, client):
        tracker = get_token_tracker()
        limites_avant = tracker.get_limits()
        cout_avant = tracker._month_cost
        tracker.set_limits(TokenLimits(monthly_budget_eur=1.0, warn_at_percentage=1))
        tracker._month_cost = 0.5
        try:
            flux = await client.post("/api/chat/send", json={"message": "Bonjour", "stream": True})
            assert '"type": "warning"' in flux.text, flux.text[:300]
            reponse = await client.post("/api/chat/send", json={"message": "Bonjour", "stream": False})
            assert reponse.json().get("warnings"), reponse.text[:300]
        finally:
            tracker.set_limits(limites_avant)
            tracker._month_cost = cout_avant
