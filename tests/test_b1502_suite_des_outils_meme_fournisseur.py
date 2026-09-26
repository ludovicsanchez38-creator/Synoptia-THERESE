"""B-1502 : la suite d'un tour d'outils repartait chez le fournisseur
principal, même quand le disjoncteur avait basculé le premier appel.

`stream_response_with_tools` résout la configuration effective localement
(B-488) ; `continue_with_tool_results` repartait de `self.config`. Les appels
d'outils émis par le fournisseur de repli étaient rejoués chez le principal,
justement en panne, et dans un autre format (signatures Gemini, reasoning).
"""


import pytest


class _Fournisseur:
    def __init__(self, nom, appels):
        self.nom, self.appels = nom, appels

    async def stream(self, system_prompt, messages, tools=None, **kwargs):
        from app.services.providers.base import StreamEvent, ToolCall

        self.appels.append((self.nom, "flux"))
        yield StreamEvent(type="tool_call", tool_call=ToolCall(id="t1", name="web_search", arguments={"query": "q"}))
        yield StreamEvent(type="done", stop_reason="tool_use")

    async def continue_with_tool_results(self, *args, **kwargs):
        from app.services.providers.base import StreamEvent

        self.appels.append((self.nom, "suite"))
        yield StreamEvent(type="text", content="Réponse.")
        yield StreamEvent(type="done", stop_reason="end_turn")


@pytest.mark.asyncio
async def test_la_suite_part_chez_le_fournisseur_qui_a_servi_le_tour(monkeypatch):
    from app.services.context import ContextWindow
    from app.services.llm import LLMConfig, LLMProvider, LLMService
    from app.services.providers.base import ToolCall, ToolResult

    principal = LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-test", api_key="k")
    repli = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-test", api_key="k")
    service = LLMService(principal)
    appels: list = []
    service._provider = _Fournisseur("principal", appels)

    async def rien():
        return None

    async def fournisseur_pour(config):
        return _Fournisseur("repli" if config is repli else "principal", appels)

    monkeypatch.setattr(service, "_ensure_provider", rien)
    monkeypatch.setattr(service, "_provider_pour", fournisseur_pour)
    monkeypatch.setattr(service, "_resolve_with_circuit_breaker", lambda: repli)

    contexte = ContextWindow(messages=[], system_prompt="Tu es THÉRÈSE.")
    _ = [e async for e in service.stream_response_with_tools(contexte, [])]
    appel = ToolCall(id="t1", name="web_search", arguments={"query": "q"})
    resultat = ToolResult(tool_call_id="t1", result="ok", is_error=False)
    # Le disjoncteur s'est refermé entre-temps : la suite ne doit pas changer
    # de fournisseur au milieu du tour pour autant.
    monkeypatch.setattr(service, "_resolve_with_circuit_breaker", lambda: principal)
    _ = [e async for e in service.continue_with_tool_results(contexte, "", [appel], [resultat], [])]

    assert appels == [("repli", "flux"), ("repli", "suite")]
