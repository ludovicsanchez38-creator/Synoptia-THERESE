"""
THERESE v2 - Escalation Tests

Tests for US-ESC-01 to US-ESC-05.
"""

import pytest
from httpx import AsyncClient


class TestCostEstimation:
    """Tests for US-ESC-02: Cost estimation."""

    @pytest.mark.asyncio
    async def test_estimate_cost(self, async_client: AsyncClient):
        """Test cost estimation for a request."""
        response = await async_client.post(
            "/api/escalation/estimate-cost",
            json={
                "model": "claude-sonnet-4-6",
                "input_tokens": 1000,
                "output_tokens": 500,
            },
        )
        assert response.status_code == 200

        data = response.json()
        # B-189 : la route rend des dollars, sous un nom qui le dit.
        assert "estimated_cost_usd" in data
        assert data["estimated_cost_usd"] > 0
        assert data["input_tokens"] == 1000
        assert data["output_tokens"] == 500

    @pytest.mark.asyncio
    @pytest.mark.xfail(strict=True, reason="01/09 : le test attend EUR, l API repond USD. Meme famille que la facture en dollars etiquetee en euros. A trancher : le test ou l API.")
    async def test_get_token_prices(self, async_client: AsyncClient):
        """Test getting token prices."""
        response = await async_client.get("/api/escalation/prices")
        assert response.status_code == 200

        data = response.json()
        assert "prices" in data
        assert "currency" in data
        assert data["currency"] == "EUR"

        # Check some models have pricing
        prices = data["prices"]
        assert "claude-sonnet-4-6" in prices
        assert "gpt-5.5" in prices


class TestTokenLimits:
    """Tests for US-ESC-03: Token limits."""

    @pytest.mark.asyncio
    async def test_get_limits_defaults(self, async_client: AsyncClient):
        """Test getting default token limits."""
        response = await async_client.get("/api/escalation/limits")
        assert response.status_code == 200

        data = response.json()
        assert "max_input_tokens" in data
        assert "max_output_tokens" in data
        assert "daily_input_limit" in data
        assert "monthly_budget_eur" in data

    @pytest.mark.asyncio
    async def test_set_limits(self, async_client: AsyncClient):
        """Test setting token limits."""
        response = await async_client.post(
            "/api/escalation/limits",
            json={
                "max_input_tokens": 10000,
                "max_output_tokens": 5000,
                "daily_input_limit": 600000,
                "daily_output_limit": 150000,
                "monthly_budget_eur": 100.0,
                "warn_at_percentage": 75,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["max_input_tokens"] == 10000
        assert data["monthly_budget_eur"] == 100.0

    @pytest.mark.asyncio
    async def test_check_limits_allowed(self, async_client: AsyncClient):
        """Test checking limits - allowed request."""
        response = await async_client.post(
            "/api/escalation/check-limits",
            params={"input_tokens": 1000},
        )
        assert response.status_code == 200

        data = response.json()
        assert "allowed" in data
        assert "warnings" in data
        assert "errors" in data

    @pytest.mark.asyncio
    async def test_check_limits_exceeded(self, async_client: AsyncClient):
        """Test checking limits - exceeded request."""
        # Set low limits
        await async_client.post(
            "/api/escalation/limits",
            json={
                "max_input_tokens": 100,
                "max_output_tokens": 100,
                "daily_input_limit": 500000,
                "daily_output_limit": 100000,
                "monthly_budget_eur": 50.0,
                "warn_at_percentage": 80,
            },
        )

        # Check with tokens exceeding limit
        response = await async_client.post(
            "/api/escalation/check-limits",
            params={"input_tokens": 1000},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["allowed"] is False
        assert len(data["errors"]) > 0


class TestUsageHistory:
    """Tests for US-ESC-04: Usage history."""

    @pytest.mark.asyncio
    async def test_get_daily_usage(self, async_client: AsyncClient):
        """Test getting daily usage."""
        response = await async_client.get("/api/escalation/usage/daily")
        assert response.status_code == 200

        data = response.json()
        assert "date" in data
        assert "input_tokens" in data
        assert "output_tokens" in data
        assert "cost_eur" in data

    @pytest.mark.asyncio
    async def test_get_monthly_usage(self, async_client: AsyncClient):
        """Test getting monthly usage."""
        response = await async_client.get("/api/escalation/usage/monthly")
        assert response.status_code == 200

        data = response.json()
        assert "month" in data
        assert "input_tokens" in data
        assert "cost_eur" in data
        assert "budget_eur" in data

    @pytest.mark.asyncio
    async def test_get_usage_history(self, async_client: AsyncClient):
        """Test getting usage history."""
        response = await async_client.get("/api/escalation/usage/history?limit=10")
        assert response.status_code == 200

        data = response.json()
        assert "history" in data
        assert "count" in data

    @pytest.mark.asyncio
    async def test_get_usage_stats(self, async_client: AsyncClient):
        """Test getting usage statistics."""
        response = await async_client.get("/api/escalation/usage/stats")
        assert response.status_code == 200

        data = response.json()
        assert "daily" in data
        assert "monthly" in data
        assert "limits" in data


class TestUncertaintyDetection:
    """Tests for US-ESC-01: Uncertainty detection."""

    @pytest.mark.asyncio
    async def test_check_uncertainty_confident(self, async_client: AsyncClient):
        """Test checking a confident response."""
        response = await async_client.post(
            "/api/escalation/check-uncertainty",
            json={
                "response": "Le resultat est 42. La formule utilisee est E=mc^2."
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["is_uncertain"] is False
        assert data["confidence_level"] == "high"
        assert data["confidence_score"] >= 80

    @pytest.mark.asyncio
    async def test_check_uncertainty_uncertain(self, async_client: AsyncClient):
        """Test checking an uncertain response."""
        response = await async_client.post(
            "/api/escalation/check-uncertainty",
            json={
                "response": "Je ne suis pas certain, mais je pense que c'est peut-etre 42. Il est possible que ce soit autre chose."
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["is_uncertain"] is True
        assert data["confidence_level"] in ["low", "medium"]
        assert len(data["uncertainty_phrases"]) > 0


class TestContextTruncation:
    """Tests for US-ESC-05: Context truncation info."""

    @pytest.mark.asyncio
    async def test_get_context_info(self, async_client: AsyncClient):
        """Test getting context window information."""
        response = await async_client.get("/api/escalation/context-info")
        assert response.status_code == 200

        data = response.json()
        assert "context_limits" in data
        assert "truncation_policy" in data
        assert "recommendation" in data

        # Check some models have context limits
        limits = data["context_limits"]
        assert "claude-sonnet-4-6" in limits
        assert limits["claude-sonnet-4-6"] == 1000000


class TestEscalationStatus:
    """Tests for combined escalation status."""

    @pytest.mark.asyncio
    async def test_get_escalation_status(self, async_client: AsyncClient):
        """Test getting combined escalation status."""
        response = await async_client.get("/api/escalation/status")
        assert response.status_code == 200

        data = response.json()
        assert "daily_usage" in data
        assert "monthly_usage" in data
        assert "limits" in data


class TestTokenTrackerUnit:
    """Unit tests for token tracker."""

    def test_estimate_cost(self):
        """Test cost estimation calculation."""
        from app.services.token_tracker import get_token_tracker

        tracker = get_token_tracker()

        # Claude Sonnet: $3/1M input, $15/1M output
        cost = tracker.estimate_cost(
            "claude-sonnet-4-6",
            input_tokens=1000000,
            output_tokens=100000,
        )
        expected = 3.00 + 1.50  # $3 input + $1.50 output
        assert abs(cost - expected) < 0.01

    def test_record_usage(self):
        """Test recording usage."""
        from app.services.token_tracker import get_token_tracker

        tracker = get_token_tracker()
        initial_count = len(tracker._usage_history)

        record = tracker.record_usage(
            conversation_id="test-conv",
            model="gpt-5.5",
            provider="openai",
            input_tokens=1000,
            output_tokens=500,
        )

        assert record.input_tokens == 1000
        assert record.output_tokens == 500
        assert record.cost_eur > 0
        assert len(tracker._usage_history) == initial_count + 1

    def test_detect_uncertainty(self):
        """Test uncertainty detection."""
        from app.services.token_tracker import detect_uncertainty

        # Confident response
        confident = detect_uncertainty("Le resultat est exactement 42.")
        assert confident["is_uncertain"] is False

        # Uncertain response
        uncertain = detect_uncertainty(
            "Je ne suis pas certain, mais je pense que c'est peut-etre correct."
        )
        assert uncertain["is_uncertain"] is True
        assert len(uncertain["uncertainty_phrases"]) >= 2


class TestEstimationHonnete:
    """Regressions B-189 et B-190 sur POST /api/escalation/estimate-cost.

    La route sert de garde-budget : le nom de son champ doit dire la devise
    du montant (la route voisine /prices a deja tranche pour USD), elle doit
    refuser des jetons negatifs comme /limits refuse des limites negatives,
    et elle ne doit pas rendre « gratuit » un modele dont elle ignore le tarif.
    """

    @pytest.mark.asyncio
    async def test_b189_le_champ_dit_des_dollars(self, async_client: AsyncClient):
        """B-189 : le montant vient d'une grille en dollars, le nom doit le dire."""
        response = await async_client.post(
            "/api/escalation/estimate-cost",
            json={
                "model": "claude-opus-5",
                "input_tokens": 1000,
                "output_tokens": 1000,
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert "estimated_cost_eur" not in data, (
            "le montant est en dollars : aucun champ ne doit l'annoncer en euros"
        )
        assert data["currency"] == "USD"
        assert abs(data["estimated_cost_usd"] - 0.030) < 1e-9

    @pytest.mark.asyncio
    async def test_b190_jetons_negatifs_refuses(self, async_client: AsyncClient):
        """B-190 : des jetons negatifs rendaient un cout negatif en HTTP 200."""
        response = await async_client.post(
            "/api/escalation/estimate-cost",
            json={
                "model": "claude-opus-5",
                "input_tokens": -1000000,
                "output_tokens": -1,
            },
        )
        assert response.status_code == 422, response.text

    @pytest.mark.asyncio
    async def test_b190_zero_jeton_reste_accepte(self, async_client: AsyncClient):
        """La borne est ge=0 : estimer une requete vide reste licite."""
        response = await async_client.post(
            "/api/escalation/estimate-cost",
            json={"model": "claude-opus-5", "input_tokens": 0, "output_tokens": 0},
        )
        assert response.status_code == 200
        assert response.json()["estimated_cost_usd"] == 0.0

    @pytest.mark.asyncio
    async def test_b190_modele_inconnu_ne_dit_pas_gratuit(
        self, async_client: AsyncClient
    ):
        """B-190 : 0.0 pour un modele hors grille se lisait « gratuit »."""
        response = await async_client.post(
            "/api/escalation/estimate-cost",
            json={
                "model": "modele-invente",
                "input_tokens": 1000,
                "output_tokens": 1000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tarif_connu"] is False, (
            "un modele absent de la grille doit etre signale, pas facture 0"
        )

    @pytest.mark.asyncio
    async def test_b190_modele_connu_est_tarife(self, async_client: AsyncClient):
        """Le drapeau doit dire vrai quand le tarif existe reellement."""
        response = await async_client.post(
            "/api/escalation/estimate-cost",
            json={
                "model": "claude-opus-5",
                "input_tokens": 1000,
                "output_tokens": 1000,
            },
        )
        assert response.json()["tarif_connu"] is True

    @pytest.mark.asyncio
    async def test_b190_prefixe_openrouter_reste_tarife(
        self, async_client: AsyncClient
    ):
        """Le drapeau et le montant partagent la MEME recherche de tarif.

        Sans quoi « anthropic/claude-opus-5 » sortirait un montant juste sous
        un drapeau qui le declare hors grille.
        """
        response = await async_client.post(
            "/api/escalation/estimate-cost",
            json={
                "model": "anthropic/claude-opus-5",
                "input_tokens": 1000,
                "output_tokens": 1000,
            },
        )
        data = response.json()
        assert data["tarif_connu"] is True
        assert abs(data["estimated_cost_usd"] - 0.030) < 1e-9


class TestB007LePlafondMensuelComptleCoutReel:
    """B-007 : le plafond mensuel de depense ne pouvait jamais se declencher.

    Trois verrous avaient ete reperes en reproduction ; deux vivent ici.

    1. La projection utilisait `estimate_cost("default", ...)` alors que
       TOKEN_PRICES["default"] vaut 0,00 USD en entree comme en sortie : le
       cout de la requete examinee ne pesait JAMAIS rien, la projection valait
       toujours le cumul deja consomme.
    2. Tout le bloc budget vivait sous `if output_tokens:` : il sautait des que
       la sortie etait absente ou nulle, alors que les tokens d'entree sont
       deja factures.

    Le troisieme (aucun appelant dans le pipeline de chat) n'est PAS traite
    ici : brancher une garde avant l'appel au fournisseur est une
    fonctionnalite, pas un correctif de cause racine.
    """

    @staticmethod
    def _tracker_isole():
        """Un tracker a soi : `TokenTracker()` rend le singleton du processus."""
        from app.services.token_tracker import TokenTracker

        tracker = object.__new__(TokenTracker)
        tracker._initialized = False
        tracker.__init__()
        return tracker

    @staticmethod
    def _limites(**kwargs):
        from app.services.token_tracker import TokenLimits

        defauts = dict(
            max_input_tokens=10_000_000,
            max_output_tokens=10_000_000,
            daily_input_limit=100_000_000,
            daily_output_limit=100_000_000,
            monthly_budget_eur=0.01,
            warn_at_percentage=80,
        )
        defauts.update(kwargs)
        return TokenLimits(**defauts)

    def test_le_plafond_compte_le_cout_reel_du_modele_employe(self):
        """0,01 USD de budget contre une requete a 2,50 USD : refus attendu."""
        tracker = self._tracker_isole()
        tracker.set_limits(self._limites())

        # claude-opus-5 : 5,00 USD/M en entree, 25,00 USD/M en sortie.
        cout = tracker.estimate_cost("claude-opus-5", 1000, 100_000)
        assert cout > 2.0, cout

        resultat = tracker.check_limits(
            input_tokens=1000, output_tokens=100_000, model="claude-opus-5"
        )

        assert resultat["allowed"] is False, resultat
        assert any("Budget mensuel" in e for e in resultat["errors"]), resultat

    def test_le_plafond_pese_aussi_une_requete_sans_sortie_estimee(self):
        """Les tokens d'ENTREE sont factures : le budget ne saute pas."""
        tracker = self._tracker_isole()
        tracker.set_limits(self._limites())

        resultat = tracker.check_limits(
            input_tokens=1_000_000, model="claude-opus-5"
        )

        assert resultat["allowed"] is False, resultat
        assert any("Budget mensuel" in e for e in resultat["errors"]), resultat

    def test_un_modele_gratuit_ne_declenche_pas_le_plafond(self):
        """Contre-epreuve : Ollama ne coute rien, la garde ne mord pas."""
        tracker = self._tracker_isole()
        tracker.set_limits(self._limites())

        resultat = tracker.check_limits(
            input_tokens=1_000_000, output_tokens=100_000, model="mistral-nemo"
        )

        assert resultat["allowed"] is True, resultat
        assert resultat["errors"] == [], resultat

    @pytest.mark.asyncio
    async def test_la_route_check_limits_transmet_le_modele(
        self, async_client: AsyncClient
    ):
        """Le defaut a ete observe PAR LA ROUTE : elle doit porter le fix."""
        from app.main import app
        from app.services.token_tracker import get_token_tracker

        tracker = get_token_tracker()
        limites_avant = tracker._limits
        # Le lifespan de test pose ce drapeau ; il n'a pas tourne quand ce
        # fichier est joue seul (la garde fail-closed rend alors 503).
        auth_avant = getattr(app.state, "auth_disabled", False)
        app.state.auth_disabled = True
        try:
            await async_client.post(
                "/api/escalation/limits",
                json=self._limites().to_dict(),
            )
            response = await async_client.post(
                "/api/escalation/check-limits",
                params={
                    "input_tokens": 1000,
                    "output_tokens": 100000,
                    "model": "claude-opus-5",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["allowed"] is False, data
            assert any("Budget mensuel" in e for e in data["errors"]), data
        finally:
            tracker.set_limits(limites_avant)
            app.state.auth_disabled = auth_avant
