"""
Tests pour le systeme d'agents actionnables (action_agents).
"""

import asyncio
import json

import pytest

from app.services.action_agents import (
    ActionAgentDef,
    ActionAgentStep,
    ActionRunner,
    StepStatus,
    TaskStatus,
    get_agent_definitions,
    reload_agent_definitions,
)


class TestActionAgentDefinitions:
    """Tests de chargement des definitions d'agents."""

    def test_load_definitions(self):
        """Les definitions sont chargees correctement depuis le JSON."""
        reload_agent_definitions()
        defs = get_agent_definitions()
        assert len(defs) >= 5, f"Attendu au moins 5 agents, obtenu {len(defs)}"

    def test_rapport_hebdo_exists(self):
        """L'agent rapport-hebdo est bien defini."""
        defs = get_agent_definitions()
        assert "rapport-hebdo" in defs
        agent = defs["rapport-hebdo"]
        assert agent.name == "Rapport hebdomadaire"
        assert len(agent.steps) >= 4

    def test_relance_clients_exists(self):
        """L'agent relance-clients est bien defini."""
        defs = get_agent_definitions()
        assert "relance-clients" in defs
        agent = defs["relance-clients"]
        assert len(agent.steps) >= 2
        assert "crm" in agent.tools

    def test_prep_rdv_has_params(self):
        """L'agent prep-rdv a des parametres requis."""
        defs = get_agent_definitions()
        assert "prep-rdv" in defs
        agent = defs["prep-rdv"]
        assert len(agent.params) >= 1
        param = agent.params[0]
        assert param.id == "contact_name"
        assert param.required is True

    def test_veille_concurrent_has_params(self):
        """L'agent veille-concurrent a des parametres requis."""
        defs = get_agent_definitions()
        assert "veille-concurrent" in defs
        agent = defs["veille-concurrent"]
        assert len(agent.params) >= 1
        assert agent.params[0].id == "competitor_name"

    def test_audit_tresorerie_exists(self):
        """L'agent audit-tresorerie est bien defini."""
        defs = get_agent_definitions()
        assert "audit-tresorerie" in defs
        agent = defs["audit-tresorerie"]
        assert "invoices" in agent.tools

    def test_all_agents_have_steps(self):
        """Tous les agents ont au moins une etape."""
        defs = get_agent_definitions()
        for agent_id, agent in defs.items():
            assert len(agent.steps) > 0, f"Agent {agent_id} n'a aucune etape"

    def test_all_agents_have_description(self):
        """Tous les agents ont une description."""
        defs = get_agent_definitions()
        for agent_id, agent in defs.items():
            assert agent.description, f"Agent {agent_id} n'a pas de description"

    def test_all_agents_have_icon(self):
        """Tous les agents ont une icone."""
        defs = get_agent_definitions()
        for agent_id, agent in defs.items():
            assert agent.icon, f"Agent {agent_id} n'a pas d'icone"

    def test_all_agents_have_category(self):
        """Tous les agents ont une categorie."""
        defs = get_agent_definitions()
        for agent_id, agent in defs.items():
            assert agent.category, f"Agent {agent_id} n'a pas de categorie"

    def test_step_prompts_not_empty(self):
        """Aucune etape n'a un prompt vide."""
        defs = get_agent_definitions()
        for agent_id, agent in defs.items():
            for step in agent.steps:
                assert step.prompt.strip(), (
                    f"Agent {agent_id}, etape {step.id} a un prompt vide"
                )

    def test_onboarding_client_has_select_param(self):
        """L'agent onboarding-client a un parametre de type select."""
        defs = get_agent_definitions()
        assert "onboarding-client" in defs
        agent = defs["onboarding-client"]
        select_params = [p for p in agent.params if p.type == "select"]
        assert len(select_params) >= 1
        assert len(select_params[0].options) >= 3


class TestActionRunner:
    """Tests du runner d'actions (sans LLM reel)."""

    def test_unknown_agent_raises(self):
        """Un agent_id inconnu leve une ValueError."""
        with pytest.raises(ValueError, match="Agent inconnu"):
            asyncio.get_event_loop().run_until_complete(
                ActionRunner.run("agent-inexistant")
            )

    def test_missing_required_param_raises(self):
        """Un parametre requis manquant leve une ValueError."""
        with pytest.raises(ValueError, match="Parametre requis manquant"):
            asyncio.get_event_loop().run_until_complete(
                ActionRunner.run("prep-rdv", params={})
            )

    def test_cancel_nonexistent_task(self):
        """Annuler une tache inexistante retourne False."""
        assert ActionRunner.cancel_task("tache-inexistante") is False

    def test_task_state_serialization(self):
        """La serialisation to_dict fonctionne."""
        from app.services.action_agents import TaskState, StepResult

        task = TaskState(
            task_id="test-123",
            agent_id="rapport-hebdo",
            agent_name="Rapport hebdomadaire",
            steps=[
                StepResult(step_id="s1", label="Etape 1"),
                StepResult(
                    step_id="s2",
                    label="Etape 2",
                    status=StepStatus.COMPLETED,
                    content="Resultat",
                ),
            ],
        )
        d = task.to_dict()
        assert d["task_id"] == "test-123"
        assert d["agent_id"] == "rapport-hebdo"
        assert len(d["steps"]) == 2
        assert d["steps"][0]["status"] == "pending"
        assert d["steps"][1]["status"] == "completed"
        assert d["progress"] == 0.5  # 1/2 completed

    def test_progress_calculation(self):
        """Le calcul de progression est correct."""
        from app.services.action_agents import TaskState, StepResult

        task = TaskState(
            task_id="test-456",
            agent_id="test",
            agent_name="Test",
            steps=[
                StepResult(step_id="s1", label="1", status=StepStatus.COMPLETED),
                StepResult(step_id="s2", label="2", status=StepStatus.COMPLETED),
                StepResult(step_id="s3", label="3", status=StepStatus.RUNNING),
                StepResult(step_id="s4", label="4", status=StepStatus.PENDING),
            ],
        )
        assert task._progress() == 0.5  # 2/4

    def test_progress_zero_when_no_steps(self):
        """La progression est 0 quand il n'y a pas d'etapes."""
        from app.services.action_agents import TaskState

        task = TaskState(
            task_id="test-789",
            agent_id="test",
            agent_name="Test",
            steps=[],
        )
        assert task._progress() == 0.0


class TestIntentDetector:
    """Tests de la detection d'action agents dans les messages."""

    def test_detect_action_agent(self):
        """Detecte un action agent dans {{action: rapport-hebdo}}."""
        from app.services.skills.intent_detector import (
            resolve_action_agent_from_message,
        )

        agent_id, clean = resolve_action_agent_from_message(
            "{{action: rapport-hebdo}}"
        )
        assert agent_id == "rapport-hebdo"
        assert clean == ""

    def test_detect_action_agent_with_text(self):
        """Detecte un action agent avec du texte autour."""
        from app.services.skills.intent_detector import (
            resolve_action_agent_from_message,
        )

        agent_id, clean = resolve_action_agent_from_message(
            "Lance le {{action: relance-clients}} stp"
        )
        assert agent_id == "relance-clients"
        assert "Lance le" in clean
        assert "stp" in clean

    def test_no_detection_for_skills(self):
        """Ne detecte pas un skill comme action agent."""
        from app.services.skills.intent_detector import (
            resolve_action_agent_from_message,
        )

        agent_id, _ = resolve_action_agent_from_message(
            "{{action: email-pro}}"
        )
        assert agent_id is None

    def test_no_detection_without_braces(self):
        """Pas de detection sans la syntaxe {{action: ...}}."""
        from app.services.skills.intent_detector import (
            resolve_action_agent_from_message,
        )

        agent_id, clean = resolve_action_agent_from_message(
            "fais un rapport hebdo"
        )
        assert agent_id is None
        assert clean == "fais un rapport hebdo"


class TestActionsRouter:
    """Tests du router API /api/actions."""

    @pytest.fixture
    def client(self):
        """Client de test FastAPI."""
        import os

        os.environ["THERESE_SKIP_SERVICES"] = "1"

        from fastapi.testclient import TestClient

        from app.main import app

        return TestClient(app)

    def test_list_actions(self, client):
        """GET /api/actions retourne la liste des agents."""
        response = client.get("/api/actions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5
        # Verifier la structure
        agent = data[0]
        assert "id" in agent
        assert "name" in agent
        assert "description" in agent
        assert "steps_count" in agent
        assert "params" in agent

    def test_get_action(self, client):
        """GET /api/actions/{id} retourne les details d'un agent."""
        response = client.get("/api/actions/rapport-hebdo")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "rapport-hebdo"
        assert data["steps_count"] >= 4

    def test_get_unknown_action(self, client):
        """GET /api/actions/{id} retourne 404 pour un agent inconnu."""
        response = client.get("/api/actions/agent-fantome")
        assert response.status_code == 404

    def test_run_action_missing_param(self, client):
        """POST /api/actions/{id}/run retourne 400 si parametre manquant."""
        response = client.post(
            "/api/actions/prep-rdv/run",
            json={"params": {}},
        )
        assert response.status_code == 400
        body = response.json()
        # Le message peut etre dans "detail" ou "message" selon le error handler
        error_text = body.get("detail", body.get("message", ""))
        assert "Parametre requis manquant" in error_text

    def test_get_unknown_task(self, client):
        """GET /api/actions/tasks/{id} retourne 404 pour une tache inconnue."""
        response = client.get("/api/actions/tasks/tache-fantome")
        assert response.status_code == 404

    def test_cancel_unknown_task(self, client):
        """DELETE /api/actions/tasks/{id} retourne 404 pour une tache inconnue."""
        response = client.delete("/api/actions/tasks/tache-fantome")
        assert response.status_code == 404
