"""B-1156 : un modèle Ollama Cloud ne passe jamais pour local (moteur).

B-1146 (0.75) n'avait corrigé que les libellés. Reproduit au cycle 13 :
`detect_default_ollama_model` choisissait « kimi-k2.6:cloud », et le Board
en mode souverain démarrait ses conseillers sur un modèle Cloud, dont les
requêtes partent chez ollama.com. Règle : le choix par défaut ignore les
modèles Cloud ; en mode souverain, le modèle Cloud du chat est remplacé par
le premier modèle local installé, et un modèle Cloud demandé explicitement
pour un conseiller ou pour la synthèse est refusé avec un message.
"""

from types import SimpleNamespace

import pytest


def test_detect_default_ollama_model_ne_choisit_pas_un_modele_cloud(monkeypatch):
    import httpx
    from app.services.llm import detect_default_ollama_model

    class Rep:
        status_code = 200

        def json(self):
            return {"models": [{"name": "kimi-k2.6:cloud"}, {"name": "qwen3:8b"}]}

    monkeypatch.setattr(httpx, "get", lambda *a, **k: Rep())
    choisi = detect_default_ollama_model(base_url="http://ollama.test")
    assert choisi == "qwen3:8b", (
        f"detect_default_ollama_model a choisi {choisi!r} (modèle Ollama Cloud)"
    )


@pytest.mark.asyncio
async def test_le_board_souverain_refuse_un_modele_cloud(monkeypatch):
    from app.models.board import AdvisorRole, BoardMode, BoardRequest
    from app.services import board as board_module
    from app.services.board import BoardService
    from app.services.error_handler import ErreurPourEcran
    from app.services.llm import LLMProvider

    class FakeLLM:
        def __init__(self, model):
            self.config = SimpleNamespace(provider=LLMProvider.OLLAMA, model=model)

        def prepare_context(self, messages, system_prompt=None):
            return messages, system_prompt

        async def stream_response(self, context, usage_sink=None, raise_on_error=False):
            yield "Avis mesuré."

    modeles_utilises: list[str] = []

    def faux_helper(provider_name, model_override=None, **kwargs):
        modeles_utilises.append(model_override)
        return FakeLLM(model_override or "defaut")

    # Le modèle choisi par l'utilisateur dans le chat est un modèle Ollama Cloud.
    import app.services.llm as module_llm

    monkeypatch.setattr(board_module, "get_llm_service", lambda: FakeLLM("kimi-k2.6:cloud"))
    monkeypatch.setattr(module_llm, "detect_default_ollama_model", lambda *a, **k: "qwen3:8b")
    monkeypatch.setattr(board_module, "get_llm_service_for_provider", faux_helper)
    monkeypatch.setattr(board_module, "_get_user_context", lambda: "")
    monkeypatch.setattr(BoardService, "_track_usage", lambda *a, **k: None)

    service = BoardService()
    request = BoardRequest(
        question="Faut-il lancer ce pilote maintenant ?",
        mode=BoardMode.SOVEREIGN,
        advisors=[AdvisorRole.ANALYST],
    )
    demarre_sur = None
    refuse = False
    try:
        async for chunk in service.deliberate(request):
            if chunk.type == "advisor_start":
                demarre_sur = chunk.provider
                break
    except ErreurPourEcran:
        refuse = True
    assert not refuse
    assert demarre_sur == "ollama:qwen3:8b", (
        f"mode souverain : conseiller démarré sur {demarre_sur!r} "
        f"(modèles demandés {modeles_utilises!r})"
    )


@pytest.mark.asyncio
async def test_le_board_souverain_refuse_un_modele_cloud_par_role(monkeypatch):
    from app.models.board import AdvisorRole, BoardMode, BoardRequest
    from app.services import board as board_module
    from app.services.board import BoardService
    from app.services.error_handler import ErreurPourEcran
    from app.services.llm import LLMProvider

    class FakeLLM:
        def __init__(self, model):
            self.config = SimpleNamespace(provider=LLMProvider.OLLAMA, model=model)

        def prepare_context(self, messages, system_prompt=None):
            return messages, system_prompt

        async def stream_response(self, context, usage_sink=None, raise_on_error=False):
            yield "Avis mesuré."

    monkeypatch.setattr(board_module, "get_llm_service", lambda: FakeLLM("qwen3:8b"))
    monkeypatch.setattr(
        board_module, "get_llm_service_for_provider",
        lambda provider_name, model_override=None, **k: FakeLLM(model_override or "qwen3:8b"),
    )
    monkeypatch.setattr(board_module, "_get_user_context", lambda: "")
    monkeypatch.setattr(BoardService, "_track_usage", lambda *a, **k: None)

    service = BoardService()
    request = BoardRequest(
        question="Faut-il lancer ce pilote maintenant ?",
        mode=BoardMode.SOVEREIGN,
        advisors=[AdvisorRole.ANALYST],
        ollama_models={"analyst": "gpt-oss:120b-cloud"},
    )
    demarre_sur = None
    with pytest.raises(ErreurPourEcran, match="Ollama Cloud"):
        async for chunk in service.deliberate(request):
            if chunk.type == "advisor_start":
                demarre_sur = chunk.provider
                break
    assert demarre_sur is None


@pytest.mark.asyncio
async def test_le_board_souverain_refuse_une_synthese_cloud_avant_tout_conseiller(monkeypatch):
    from app.models.board import AdvisorRole, BoardMode, BoardRequest
    from app.services import board as board_module
    from app.services.board import BoardService
    from app.services.error_handler import ErreurPourEcran
    from app.services.llm import LLMProvider

    class FakeLLM:
        def __init__(self, model):
            self.config = SimpleNamespace(provider=LLMProvider.OLLAMA, model=model)

        def prepare_context(self, messages, system_prompt=None):
            return messages, system_prompt

        async def stream_response(self, context, usage_sink=None, raise_on_error=False):
            yield "Avis mesuré."

    monkeypatch.setattr(board_module, "get_llm_service", lambda: FakeLLM("qwen3:8b"))
    monkeypatch.setattr(
        board_module, "get_llm_service_for_provider",
        lambda provider_name, model_override=None, **k: FakeLLM(model_override or "qwen3:8b"),
    )
    monkeypatch.setattr(board_module, "_get_user_context", lambda: "")
    monkeypatch.setattr(BoardService, "_track_usage", lambda *a, **k: None)

    service = BoardService()
    request = BoardRequest(
        question="Faut-il lancer ce pilote maintenant ?",
        mode=BoardMode.SOVEREIGN,
        advisors=[AdvisorRole.ANALYST],
        ollama_models={"synthesis": "gpt-oss:120b-cloud"},
    )
    demarre_sur = None
    with pytest.raises(ErreurPourEcran, match="Ollama Cloud"):
        async for chunk in service.deliberate(request):
            if chunk.type == "advisor_start":
                demarre_sur = chunk.provider
                break
    assert demarre_sur is None
