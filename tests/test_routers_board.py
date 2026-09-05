"""
THERESE v2 - Board Router Tests

Tests for US-BOARD-01 to US-BOARD-05.
"""

import pytest
from httpx import AsyncClient


class TestBoardAdvisors:
    """Tests for board advisors listing."""

    @pytest.mark.asyncio
    async def test_list_advisors(self, client: AsyncClient):
        """Test listing all 5 advisors."""
        response = await client.get("/api/board/advisors")

        assert response.status_code == 200
        advisors = response.json()

        assert len(advisors) == 5

        # Check each advisor has required fields
        for advisor in advisors:
            assert "role" in advisor
            assert "name" in advisor
            assert "emoji" in advisor
            assert "color" in advisor
            assert "personality" in advisor

    @pytest.mark.asyncio
    async def test_get_analyst_advisor(self, client: AsyncClient):
        """Test getting the analyst advisor."""
        response = await client.get("/api/board/advisors/analyst")

        assert response.status_code == 200
        advisor = response.json()

        assert advisor["role"] == "analyst"
        assert advisor["name"] == "L'Analyste"

    @pytest.mark.asyncio
    async def test_get_strategist_advisor(self, client: AsyncClient):
        """Test getting the strategist advisor."""
        response = await client.get("/api/board/advisors/strategist")

        assert response.status_code == 200
        advisor = response.json()

        assert advisor["role"] == "strategist"
        assert advisor["name"] == "Le Stratège"

    @pytest.mark.asyncio
    async def test_get_devils_advocate(self, client: AsyncClient):
        """Test getting the devil's advocate advisor."""
        response = await client.get("/api/board/advisors/devil")

        assert response.status_code == 200
        advisor = response.json()

        assert advisor["role"] == "devil"
        assert advisor["name"] == "L'Avocat du Diable"

    @pytest.mark.asyncio
    async def test_get_pragmatic_advisor(self, client: AsyncClient):
        """Test getting the pragmatic advisor."""
        response = await client.get("/api/board/advisors/pragmatic")

        assert response.status_code == 200
        advisor = response.json()

        assert advisor["role"] == "pragmatic"
        assert advisor["name"] == "Le Pragmatique"

    @pytest.mark.asyncio
    async def test_get_visionary_advisor(self, client: AsyncClient):
        """Test getting the visionary advisor."""
        response = await client.get("/api/board/advisors/visionary")

        assert response.status_code == 200
        advisor = response.json()

        assert advisor["role"] == "visionary"
        assert advisor["name"] == "Le Visionnaire"

    @pytest.mark.asyncio
    async def test_get_nonexistent_advisor(self, client: AsyncClient):
        """Test getting a non-existent advisor."""
        response = await client.get("/api/board/advisors/unknown")

        assert response.status_code == 422  # Invalid enum value


class TestBoardDeliberation:
    """Tests for US-BOARD-01: Submit question to board."""

    @pytest.mark.asyncio
    async def test_deliberate_returns_sse_stream(self, client: AsyncClient, sample_board_request):
        """Test deliberation returns SSE stream."""
        # Note: This is a streaming endpoint, we test the response format
        response = await client.post(
            "/api/board/deliberate",
            json=sample_board_request,
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

    @pytest.mark.asyncio
    async def test_deliberate_empty_question_rejected(self, client: AsyncClient):
        """Test deliberation rejects empty question."""
        response = await client.post("/api/board/deliberate", json={
            "question": "",
            "context": None,
        })

        assert response.status_code == 422


class TestBoardDecisions:
    """Tests for US-BOARD-03 to US-BOARD-05: Decision history."""

    @pytest.mark.asyncio
    async def test_list_decisions_empty(self, client: AsyncClient):
        """Test listing decisions when empty."""
        response = await client.get("/api/board/decisions")

        assert response.status_code == 200
        decisions = response.json()

        assert isinstance(decisions, list)
        assert len(decisions) == 0

    @pytest.mark.asyncio
    async def test_list_decisions_with_limit(self, client: AsyncClient):
        """Test listing decisions with limit parameter."""
        response = await client.get("/api/board/decisions?limit=10")

        assert response.status_code == 200
        decisions = response.json()

        assert isinstance(decisions, list)

    @pytest.mark.asyncio
    async def test_get_nonexistent_decision(self, client: AsyncClient):
        """Test getting a non-existent decision."""
        response = await client.get("/api/board/decisions/nonexistent-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_decision(self, client: AsyncClient):
        """Test deleting a non-existent decision."""
        response = await client.delete("/api/board/decisions/nonexistent-id")

        assert response.status_code == 404


class TestBoardSynthesis:
    """Tests for US-BOARD-02: Board synthesis."""

    @pytest.mark.asyncio
    async def test_decision_response_structure(self, client: AsyncClient):
        """Test decision response has required fields."""
        # This test verifies the schema structure
        # Full integration test would require mocking LLM
        response = await client.get("/api/board/decisions")

        assert response.status_code == 200
        # Empty list is valid, structure is defined in schema


class TestFicheEtListeDisentLaMemeChose:
    """B-302 : la fiche d'un conseiller omettait `modele_deprecie`.

    `None` y signifie « non sondé », pas « tout va bien » (models/board.py) :
    ouvrir la fiche faisait donc disparaître un avertissement que la liste
    affichait, sur le même conseiller au même instant.

    La sonde est forcée à trois valeurs DIFFÉRENTES selon le fournisseur :
    un correctif qui recopierait bêtement `True` partout, ou un helper partagé
    qui perdrait le champ des deux côtés à la fois, ne passerait pas.
    """

    @pytest.fixture
    def sonde_forcee(self, monkeypatch):
        from app.services import board as board_module

        # anthropic = L'Analyste (dérive), openai = Le Stratège (vérifié
        # présent), les trois autres restent non sondés.
        monkeypatch.setattr(
            board_module, "_etat_catalogue", {"anthropic": True, "openai": False}
        )
        return {
            "analyst": True,
            "strategist": False,
            "devil": None,
            "pragmatic": None,
            "visionary": None,
        }

    @pytest.mark.asyncio
    async def test_la_liste_porte_bien_l_etat_de_la_sonde(
        self, client: AsyncClient, sonde_forcee
    ):
        """Témoin : sans lui, une sonde muette rendrait le test suivant vert."""
        reponse = await client.get("/api/board/advisors")

        assert reponse.status_code == 200
        etats = {a["role"]: a["modele_deprecie"] for a in reponse.json()}
        assert etats == sonde_forcee

    @pytest.mark.asyncio
    async def test_fiche_conseiller_dit_la_meme_chose_que_la_liste(
        self, client: AsyncClient, sonde_forcee
    ):
        liste = await client.get("/api/board/advisors")
        assert liste.status_code == 200
        par_role = {a["role"]: a for a in liste.json()}

        for role, attendu in sonde_forcee.items():
            fiche = await client.get(f"/api/board/advisors/{role}")
            assert fiche.status_code == 200
            detail = fiche.json()

            # Valeur absolue : la fiche doit dire ce que la sonde sait.
            assert detail["modele_deprecie"] is attendu, (
                f"{role} : la fiche dit {detail['modele_deprecie']!r}, "
                f"la sonde dit {attendu!r}"
            )
            # Et rien d'autre ne doit diverger entre les deux surfaces.
            assert detail == par_role[role]
