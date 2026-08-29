"""US-002 : la boucle d'outils n'exécute jamais send_email sans confirmation.

Test d'intégration de _execute_tools_and_continue : un appel send_email du LLM
doit être mis en attente (événement confirmation_required) et NE PAS déclencher
execute_workspace_tool.
"""
import json
from unittest.mock import MagicMock

import app.routers.chat as chat_mod
import pytest
from app.routers.chat import _execute_tools_and_continue
from app.services import tool_confirmations
from app.services.llm import ToolCall


class _Event:
    def __init__(self, type, content="", tool_call=None, stop_reason="end_turn"):
        self.type = type
        self.content = content
        self.tool_call = tool_call
        self.stop_reason = stop_reason
        self.assistant_content_brut = None  # contrat StreamEvent 0.48


class _FakeLLM:
    async def continue_with_tool_results(
        self, context, assistant_content, tool_calls, tool_results, tools
    , prior_turns=None, assistant_content_brut=None):
        self.received_tool_results = tool_results
        yield _Event("done", stop_reason="end_turn")


def _parse_chunks(raw_chunks):
    out = []
    for c in raw_chunks:
        body = c[len("data: ") :].strip() if c.startswith("data: ") else c.strip()
        try:
            out.append(json.loads(body))
        except json.JSONDecodeError:
            pass
    return out


@pytest.mark.asyncio
async def test_send_email_demande_confirmation_sans_envoyer(monkeypatch):
    executed = {"workspace": False}

    async def _spy_execute(*args, **kwargs):
        executed["workspace"] = True
        return "ENVOYÉ"

    monkeypatch.setattr(chat_mod, "execute_workspace_tool", _spy_execute)

    llm = _FakeLLM()
    tc = ToolCall(
        id="t1",
        name="send_email",
        arguments={"to": "x@y.fr", "subject": "Sujet", "body": "Corps"},
    )

    raw = [
        chunk
        async for chunk in _execute_tools_and_continue(
            llm, None, None, "", [tc], [], "conv1", 3, session=MagicMock()
        )
    ]
    chunks = _parse_chunks(raw)

    # 1. send_email n'a PAS été exécuté automatiquement.
    assert executed["workspace"] is False

    # 2. Un événement de demande de confirmation a été émis avec les détails.
    confirms = [c for c in chunks if c.get("type") == "confirmation_required"]
    assert len(confirms) == 1
    payload = confirms[0]["confirmation"]
    assert payload["tool_name"] == "send_email"
    assert payload["arguments"]["to"] == "x@y.fr"

    # 3. L'action est réellement en attente et consommable une fois.
    cid = payload["confirmation_id"]
    assert tool_confirmations.pop_pending(cid) == (
        "send_email",
        {"to": "x@y.fr", "subject": "Sujet", "body": "Corps"},
        # 0.56 : la conversation voyage avec l'action (cloison agenda).
        "conv1",
    )

    # 4. Le LLM a reçu un résultat marquant l'action comme non exécutée.
    assert any(not tr.is_error for tr in llm.received_tool_results)


class _FakeLLMReemetSendEmail:
    """Modèle faible qui re-émet send_email dans la continuation (spirale BUG-121)."""

    def __init__(self):
        self.continuations = 0

    async def continue_with_tool_results(
        self, context, assistant_content, tool_calls, tool_results, tools, prior_turns=None,
        assistant_content_brut=None,
    ):
        self.continuations += 1
        # Le modèle re-tente un envoi avec des arguments hallucinés différents
        # (comme dans le log réel : body puis content, objet différent).
        yield _Event(
            "tool_call",
            tool_call=ToolCall(
                id=f"retry{self.continuations}",
                name="send_email",
                arguments={"to": "x@y.fr", "subject": "Autre objet", "content": "Corps"},
            ),
        )
        yield _Event("done", stop_reason="tool_calls")


@pytest.mark.asyncio
async def test_send_email_reemis_ne_cree_quune_seule_carte(monkeypatch):
    """BUG-121 : même si le modèle re-émet send_email en boucle, une seule carte
    de confirmation est produite et aucun envoi n'a lieu (invariant US-002)."""
    executed = {"workspace": False}

    async def _spy_execute(*args, **kwargs):
        executed["workspace"] = True
        return "ENVOYÉ"

    monkeypatch.setattr(chat_mod, "execute_workspace_tool", _spy_execute)

    llm = _FakeLLMReemetSendEmail()
    tc = ToolCall(
        id="t1",
        name="send_email",
        arguments={"to": "x@y.fr", "subject": "Merci", "body": "Corps"},
    )

    raw = [
        chunk
        async for chunk in _execute_tools_and_continue(
            llm, None, None, "", [tc], [], "conv1", 5, session=MagicMock()
        )
    ]
    chunks = _parse_chunks(raw)

    # Une seule carte, malgré la ré-émission par le modèle.
    confirms = [c for c in chunks if c.get("type") == "confirmation_required"]
    assert len(confirms) == 1
    # Aucun envoi automatique.
    assert executed["workspace"] is False
    # La chaîne d'outils n'a PAS été relancée après la mise en attente
    # (une seule continuation, pas de récursion qui empilerait des cartes).
    assert llm.continuations == 1


@pytest.mark.asyncio
async def test_send_email_mcp_namespace_non_execute_sans_confirmation(monkeypatch):
    """BUG-121 : un send_email exposé via MCP ('{server_id}__send_email') doit
    être mis en attente, jamais dispatché directement au service MCP."""

    class _SpyMCP:
        def __init__(self):
            self.called = False

        async def execute_tool_call(self, name, arguments):
            self.called = True
            raise AssertionError("send_email MCP exécuté sans confirmation !")

    mcp = _SpyMCP()
    llm = _FakeLLM()
    tc = ToolCall(
        id="t1",
        name="therese__send_email",
        arguments={"to": "x@y.fr", "subject": "S", "body": "B"},
    )

    raw = [
        chunk
        async for chunk in _execute_tools_and_continue(
            llm, mcp, None, "", [tc], [], "conv1", 3, session=MagicMock()
        )
    ]
    chunks = _parse_chunks(raw)

    assert mcp.called is False
    confirms = [c for c in chunks if c.get("type") == "confirmation_required"]
    assert len(confirms) == 1
    cid = confirms[0]["confirmation"]["confirmation_id"]
    # L'action mise en attente conserve le nom MCP préfixé (routage à la confirmation).
    assert tool_confirmations.pop_pending(cid) == (
        "therese__send_email",
        {"to": "x@y.fr", "subject": "S", "body": "B"},
        # 0.56 : la conversation voyage avec l'action (cloison agenda).
        "conv1",
    )


# ---------------------------------------------------------------------------
# D1 (Dr_logic, 27/08) : « demande d'envoi d'un email, j'ai une double
# confirmation ? »
#
# Le garde BUG-121 (`sensitive_pending`) ne bloque QUE la récursion. Dans le
# tour courant, `for tc in allowed_calls` émet une carte par appel : un modèle
# qui répète send_email dans un même tour empile des cartes pour un seul envoi.
# Deux envois RÉELLEMENT différents doivent, eux, garder deux cartes — une
# confirmation d'envoi est une garantie, jamais un confort.
# ---------------------------------------------------------------------------


def _cartes(chunks):
    return [c for c in chunks if c.get("type") == "confirmation_required"]


@pytest.mark.asyncio
async def test_deux_send_email_identiques_dans_un_tour_une_seule_carte(monkeypatch):
    async def _jamais(*args, **kwargs):  # pragma: no cover - ne doit pas être appelé
        raise AssertionError("send_email exécuté sans confirmation")

    monkeypatch.setattr(chat_mod, "execute_workspace_tool", _jamais)

    args = {"to": "x@y.fr", "subject": "Sujet", "body": "Corps"}
    appels = [
        ToolCall(id="t1", name="send_email", arguments=dict(args)),
        ToolCall(id="t2", name="send_email", arguments=dict(args)),
    ]

    raw = [
        chunk
        async for chunk in _execute_tools_and_continue(
            _FakeLLM(), None, None, "", appels, [], "conv1", 3, session=MagicMock()
        )
    ]
    assert len(_cartes(_parse_chunks(raw))) == 1


@pytest.mark.asyncio
async def test_variantes_du_meme_envoi_ne_font_quune_carte(monkeypatch):
    """BUG-121 a observé des arguments hallucinés (`body` vs `content`).

    La casse du destinataire, les espaces et l'alias du corps ne font pas deux
    envois : c'est le même e-mail réémis.
    """
    async def _jamais(*args, **kwargs):  # pragma: no cover
        raise AssertionError("send_email exécuté sans confirmation")

    monkeypatch.setattr(chat_mod, "execute_workspace_tool", _jamais)

    appels = [
        ToolCall(
            id="t1",
            name="send_email",
            arguments={"to": "X@Y.fr ", "subject": "Sujet ", "body": "Corps"},
        ),
        ToolCall(
            id="t2",
            name="send_email",
            arguments={"to": "x@y.fr", "subject": "Sujet", "content": "Corps"},
        ),
    ]

    raw = [
        chunk
        async for chunk in _execute_tools_and_continue(
            _FakeLLM(), None, None, "", appels, [], "conv1", 3, session=MagicMock()
        )
    ]
    assert len(_cartes(_parse_chunks(raw))) == 1


@pytest.mark.asyncio
async def test_deux_destinataires_differents_gardent_deux_cartes(monkeypatch):
    """Le fail-safe : jamais fusionner deux envois distincts en une seule carte."""
    async def _jamais(*args, **kwargs):  # pragma: no cover
        raise AssertionError("send_email exécuté sans confirmation")

    monkeypatch.setattr(chat_mod, "execute_workspace_tool", _jamais)

    appels = [
        ToolCall(
            id="t1",
            name="send_email",
            arguments={"to": "alice@y.fr", "subject": "Sujet", "body": "Corps"},
        ),
        ToolCall(
            id="t2",
            name="send_email",
            arguments={"to": "bob@y.fr", "subject": "Sujet", "body": "Corps"},
        ),
    ]

    raw = [
        chunk
        async for chunk in _execute_tools_and_continue(
            _FakeLLM(), None, None, "", appels, [], "conv1", 3, session=MagicMock()
        )
    ]
    cartes = _cartes(_parse_chunks(raw))
    assert len(cartes) == 2
    assert {c["confirmation"]["arguments"]["to"] for c in cartes} == {
        "alice@y.fr",
        "bob@y.fr",
    }


@pytest.mark.asyncio
async def test_destinataire_absent_emet_quand_meme_la_carte(monkeypatch):
    """Fail-open : une empreinte incalculable ne doit jamais avaler une carte."""
    async def _jamais(*args, **kwargs):  # pragma: no cover
        raise AssertionError("send_email exécuté sans confirmation")

    monkeypatch.setattr(chat_mod, "execute_workspace_tool", _jamais)

    appels = [
        ToolCall(id="t1", name="send_email", arguments={"subject": "A"}),
        ToolCall(id="t2", name="send_email", arguments={"subject": "B"}),
    ]

    raw = [
        chunk
        async for chunk in _execute_tools_and_continue(
            _FakeLLM(), None, None, "", appels, [], "conv1", 3, session=MagicMock()
        )
    ]
    assert len(_cartes(_parse_chunks(raw))) == 2


@pytest.mark.asyncio
async def test_meme_envoi_par_loutil_natif_et_par_mcp_une_seule_carte(monkeypatch):
    """Le même envoi proposé deux fois sous deux noms reste un seul envoi.

    Quand un serveur MCP expose lui aussi un send_email, le modèle voit deux
    outils d'envoi et peut appeler les deux dans le tour. L'empreinte raisonne
    sur le nom de base, pas sur le nom préfixé.
    """
    async def _jamais(*args, **kwargs):  # pragma: no cover
        raise AssertionError("send_email exécuté sans confirmation")

    monkeypatch.setattr(chat_mod, "execute_workspace_tool", _jamais)

    args = {"to": "x@y.fr", "subject": "Sujet", "body": "Corps"}
    appels = [
        ToolCall(id="t1", name="send_email", arguments=dict(args)),
        ToolCall(id="t2", name="courrier__send_email", arguments=dict(args)),
    ]

    raw = [
        chunk
        async for chunk in _execute_tools_and_continue(
            _FakeLLM(), None, None, "", appels, [], "conv1", 3, session=MagicMock()
        )
    ]
    assert len(_cartes(_parse_chunks(raw))) == 1


@pytest.mark.asyncio
async def test_le_corps_est_conserve_quel_que_soit_lordre_des_alias(monkeypatch):
    """Relevé par la relecture adversariale : la dédup pouvait vider l'e-mail.

    L'empreinte tient `content` et `body` pour un même corps, mais la carte
    conserve les arguments du PREMIER appel — et l'envoi ne lit que `body`.
    Ordre `content` puis `body` : une seule carte, corps vide à l'écran, et un
    e-mail vide expédié après confirmation. Le corps doit survivre à l'alias.
    """
    async def _jamais(*args, **kwargs):  # pragma: no cover
        raise AssertionError("send_email exécuté sans confirmation")

    monkeypatch.setattr(chat_mod, "execute_workspace_tool", _jamais)

    appels = [
        ToolCall(
            id="t1",
            name="send_email",
            arguments={"to": "x@y.fr", "subject": "Sujet", "content": "Le corps"},
        ),
        ToolCall(
            id="t2",
            name="send_email",
            arguments={"to": "x@y.fr", "subject": "Sujet", "body": "Le corps"},
        ),
    ]

    raw = [
        chunk
        async for chunk in _execute_tools_and_continue(
            _FakeLLM(), None, None, "", appels, [], "conv1", 3, session=MagicMock()
        )
    ]
    cartes = _cartes(_parse_chunks(raw))
    assert len(cartes) == 1
    assert cartes[0]["confirmation"]["arguments"]["body"] == "Le corps"


@pytest.mark.asyncio
async def test_un_corps_sous_alias_seul_nest_pas_perdu(monkeypatch):
    """Même seul, `content` doit atteindre l'envoi, qui ne lit que `body`."""
    async def _jamais(*args, **kwargs):  # pragma: no cover
        raise AssertionError("send_email exécuté sans confirmation")

    monkeypatch.setattr(chat_mod, "execute_workspace_tool", _jamais)

    appels = [
        ToolCall(
            id="t1",
            name="send_email",
            arguments={"to": "x@y.fr", "subject": "Sujet", "content": "Le corps"},
        ),
    ]

    raw = [
        chunk
        async for chunk in _execute_tools_and_continue(
            _FakeLLM(), None, None, "", appels, [], "conv1", 3, session=MagicMock()
        )
    ]
    cartes = _cartes(_parse_chunks(raw))
    assert len(cartes) == 1
    assert cartes[0]["confirmation"]["arguments"]["body"] == "Le corps"
