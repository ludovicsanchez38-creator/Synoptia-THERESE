"""Une recherche vide ne doit pas devenir une réponse inventée."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.models.entities import Conversation, FileMetadata, Message
from app.routers import chat
from app.services import memory_tools
from app.services.context import ContextWindow
from app.services.providers.base import LLMConfig, LLMProvider, StreamEvent, ToolCall
from sqlalchemy import select


class ModeleInventeur:
    config = None

    def __init__(self):
        self.continuations = 0

    def prepare_context(self, messages):
        return ContextWindow(messages=messages)

    async def continue_with_tool_results(self, *args, **kwargs):
        self.continuations += 1
        yield StreamEvent(type="text", content="Le fichier décrit un comité imaginaire.")
        yield StreamEvent(type="done", stop_reason="end_turn")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("nom", "resultat"),
    [
        ("search_files", '{"found": false, "total": 0, "documents": []}'),
        ("search_emails", "Aucun email trouve pour la recherche 'comité'."),
        ("search_invoices", "Aucune facture ni devis local ne correspond à « comité »."),
    ],
)
async def test_recherche_vide_ne_devient_pas_un_contenu_invente(monkeypatch, nom, resultat):
    modele = ModeleInventeur()
    monkeypatch.setattr(chat, "_perimetre_de_conversation", AsyncMock(return_value=("global", None)))
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=resultat))
    monkeypatch.setattr(chat, "execute_workspace_tool", AsyncMock(return_value=resultat))
    appel = ToolCall(id="recherche", name=nom, arguments={"query": "comité"})
    outils = [{"type": "function", "function": {"name": nom}}]

    evenements = [json.loads(bloc.removeprefix("data: ")) async for bloc in
                  chat._execute_tools_and_continue(
                      modele, None, ContextWindow(messages=[]), "", [appel], outils,
                      "c-test", 3, session=object(),
                  )]
    texte = " ".join(e.get("content", "") for e in evenements if e["type"] == "text")

    assert "aucun" in texte.lower() or "rien trouvé" in texte.lower()
    assert "comité imaginaire" not in texte
    assert modele.continuations == 0


@pytest.mark.asyncio
async def test_recherche_web_confirmee_vide_ne_devient_pas_un_contenu_invente(monkeypatch):
    modele = ModeleInventeur()
    monkeypatch.setattr(chat, "get_llm_service", lambda: modele)
    monkeypatch.setattr(chat, "filtrer_historique", lambda messages, config: (messages, None))
    monkeypatch.setattr(chat, "_attribution", lambda service: ("local", "fictif"))
    monkeypatch.setattr(chat, "get_token_tracker", lambda: MagicMock())

    reponse = await chat._repondre_apres_recherche(
        {"query": "comité", "_provenance_documents": "sans_document"},
        "Aucun résultat trouvé pour: comité", None, object(),
    )

    assert "aucun" in reponse.lower() or "rien trouvé" in reponse.lower()
    assert "comité imaginaire" not in reponse
    assert modele.continuations == 0


@pytest.mark.asyncio
async def test_resultat_non_vide_continue_normalement(monkeypatch):
    modele = ModeleInventeur()
    monkeypatch.setattr(chat, "_perimetre_de_conversation", AsyncMock(return_value=("global", None)))
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=(
        '{"found": true, "total": 1, "documents": [{"nom": "contexte.md"}]}'
    )))
    appel = ToolCall(id="recherche", name="search_files", arguments={"query": "contexte"})
    outils = [{"type": "function", "function": {"name": "search_files"}}]
    evenements = [json.loads(bloc.removeprefix("data: ")) async for bloc in
                  chat._execute_tools_and_continue(
                      modele, None, ContextWindow(messages=[]), "", [appel], outils,
                      "c-test", 3, session=object(),
                  )]
    assert modele.continuations == 1
    assert any(e["type"] == "text" and "comité imaginaire" in e["content"] for e in evenements)


@pytest.mark.asyncio
async def test_document_trouve_n_annonce_pas_de_hors_perimetre(monkeypatch):
    class ModeleQuiCiteLeNom(ModeleInventeur):
        async def continue_with_tool_results(self, *args, **kwargs):
            self.continuations += 1
            yield StreamEvent(type="text", content="Le catalogue contient rapport.txt.")
            yield StreamEvent(type="done", stop_reason="end_turn")

    modele = ModeleQuiCiteLeNom()
    monkeypatch.setattr(chat, "_perimetre_de_conversation", AsyncMock(return_value=("global", None)))
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=json.dumps({
        "found": True, "total": 1, "documents": [{"nom": "rapport.txt"}], "hors_perimetre": 1,
    })))
    appel = ToolCall(id="fichiers", name="search_files", arguments={"query": "rapport"})
    outils = [{"type": "function", "function": {"name": appel.name}}]

    evenements = [json.loads(bloc.removeprefix("data: ")) async for bloc in
                  chat._execute_tools_and_continue(
                      modele, None, ContextWindow(messages=[]), "", [appel], outils,
                      "c-test", 3, session=object(),
                  )]

    assert not any(e.get("limite_recherche") for e in evenements)
    assert modele.continuations == 1


@pytest.mark.asyncio
async def test_limite_de_contenu_booleenne_reste_lisible_sans_relancer_le_modele(monkeypatch):
    modele = ModeleInventeur()
    monkeypatch.setattr(chat, "_perimetre_de_conversation", AsyncMock(return_value=("global", None)))
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=json.dumps({
        "found": False, "total": 0, "documents": [], "contenu_non_consulte": True,
    })))
    appel = ToolCall(id="fichiers", name="search_files", arguments={"query": "rapport"})
    outils = [{"type": "function", "function": {"name": appel.name}}]

    evenements = [json.loads(bloc.removeprefix("data: ")) async for bloc in
                  chat._execute_tools_and_continue(
                      modele, None, ContextWindow(messages=[]), "", [appel], outils,
                      "c-test", 3, session=object(),
                  )]
    texte = " ".join(e.get("content", "") for e in evenements if e["type"] == "text")

    assert "contenu" in texte.lower() and "consulté" in texte.lower()
    assert "comité imaginaire" not in texte
    assert modele.continuations == 0


@pytest.mark.asyncio
async def test_recherche_vide_et_emails_trouves_repondent_avec_les_deux_resultats(monkeypatch):
    class ModeleQuiLitLesResultats(ModeleInventeur):
        async def continue_with_tool_results(self, contexte, contenu, appels, resultats, outils, **kwargs):
            self.continuations += 1
            self.resultats = resultats
            emails = next(r.result for r in resultats if r.tool_call_id == "emails")
            yield StreamEvent(type="text", content=emails)
            yield StreamEvent(type="done", stop_reason="end_turn")

    modele = ModeleQuiLitLesResultats()
    fichiers_vides = '{"found": false, "total": 0, "documents": []}'
    emails_trouves = "Deux e-mails : Rapport Alpha et Rapport Bravo."
    monkeypatch.setattr(chat, "_perimetre_de_conversation", AsyncMock(return_value=("global", None)))
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=fichiers_vides))
    monkeypatch.setattr(chat, "execute_workspace_tool", AsyncMock(return_value=emails_trouves))
    appels = [
        ToolCall(id="fichiers", name="search_files", arguments={"query": "rapport"}),
        ToolCall(id="emails", name="search_emails", arguments={"query": "rapport"}),
    ]
    outils = [{"type": "function", "function": {"name": appel.name}} for appel in appels]

    evenements = [json.loads(bloc.removeprefix("data: ")) async for bloc in
                  chat._execute_tools_and_continue(
                      modele, None, ContextWindow(messages=[]), "", appels, outils,
                      "c-test", 3, session=object(),
                  )]
    texte = " ".join(e.get("content", "") for e in evenements if e["type"] == "text")

    assert "Rapport Alpha" in texte and "Rapport Bravo" in texte
    assert modele.continuations == 1
    assert [(r.tool_call_id, r.result) for r in modele.resultats] == [
        ("fichiers", fichiers_vides), ("emails", emails_trouves),
    ]


@pytest.mark.asyncio
async def test_deux_recherches_vides_ne_relancent_pas_le_modele(monkeypatch):
    modele = ModeleInventeur()
    monkeypatch.setattr(chat, "_perimetre_de_conversation", AsyncMock(return_value=("global", None)))
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=(
        '{"found": false, "total": 0, "documents": []}'
    )))
    monkeypatch.setattr(chat, "execute_workspace_tool", AsyncMock(return_value=(
        "Aucun email trouve pour la recherche 'rapport'."
    )))
    appels = [
        ToolCall(id="fichiers", name="search_files", arguments={"query": "rapport"}),
        ToolCall(id="emails", name="search_emails", arguments={"query": "rapport"}),
    ]
    outils = [{"type": "function", "function": {"name": appel.name}} for appel in appels]

    evenements = [json.loads(bloc.removeprefix("data: ")) async for bloc in
                  chat._execute_tools_and_continue(
                      modele, None, ContextWindow(messages=[]), "", appels, outils,
                      "c-test", 3, session=object(),
                  )]
    texte = " ".join(e.get("content", "") for e in evenements if e["type"] == "text")

    assert "aucun fichier" in texte.lower() and "aucun e-mail" in texte.lower()
    assert modele.continuations == 0


async def _rechercher_dans_la_bulle(monkeypatch, db_session, config):
    modele = ModeleInventeur()
    monkeypatch.setattr(chat, "_perimetre_de_conversation", AsyncMock(return_value=("global", None)))
    appel = ToolCall(id="recherche", name="search_files", arguments={"query": "irrigation"})
    outils = [{"type": "function", "function": {"name": "search_files"}}]
    contexte = ContextWindow(messages=[], config_effective=config)
    evenements = [json.loads(bloc.removeprefix("data: ")) async for bloc in
                  chat._execute_tools_and_continue(
                      modele, None, contexte, "", [appel], outils,
                      "c-test", 3, session=db_session,
                  )]
    texte = " ".join(e.get("content", "") for e in evenements if e["type"] == "text")
    return texte, modele, evenements


@pytest.mark.asyncio
async def test_fichiers_hors_perimetre_annonces_avec_le_selecteur(monkeypatch, db_session):
    db_session.add(FileMetadata(
        path="/client/dossier.txt", name="dossier.txt", extension=".txt", size=10,
        chunk_count=1, scope="project", scope_id="projet-fictif",
    ))
    await db_session.commit()
    index = MagicMock(async_fichiers_contenant=AsyncMock(return_value={}))
    monkeypatch.setattr(memory_tools, "get_qdrant_service", lambda: index)

    texte, modele, evenements = await _rechercher_dans_la_bulle(
        monkeypatch, db_session, LLMConfig(LLMProvider.OLLAMA, "local-fictif")
    )

    assert "hors périmètre" in texte.lower()
    assert "sélecteur" in texte.lower() and "dossier" in texte.lower()
    assert "aucun fichier" not in texte.lower()
    assert "comité imaginaire" not in texte
    assert any(e.get("limite_recherche") for e in evenements)
    assert modele.continuations == 0


@pytest.mark.asyncio
async def test_sans_accord_documents_la_bulle_dit_que_le_contenu_n_est_pas_consulte(
    monkeypatch, db_session
):
    db_session.add(FileMetadata(
        path="/general/dossier.txt", name="dossier.txt", extension=".txt", size=10,
        chunk_count=1, scope="global",
    ))
    await db_session.commit()
    index = MagicMock(async_fichiers_contenant=AsyncMock())
    monkeypatch.setattr(memory_tools, "get_qdrant_service", lambda: index)
    monkeypatch.setattr("app.services.consentements.accord_valide", lambda *args: False)

    texte, modele, evenements = await _rechercher_dans_la_bulle(
        monkeypatch, db_session, LLMConfig(LLMProvider.ANTHROPIC, "service-fictif")
    )

    assert "contenu" in texte.lower() and "pas été consulté" in texte.lower()
    assert "accord" in texte.lower()
    assert "aucun fichier" not in texte.lower()
    assert "comité imaginaire" not in texte
    assert any(e.get("limite_recherche") for e in evenements)
    assert modele.continuations == 0
    index.async_fichiers_contenant.assert_not_awaited()


@pytest.mark.asyncio
async def test_index_en_panne_la_bulle_n_affirme_pas_une_recherche_vide(monkeypatch, db_session):
    db_session.add(FileMetadata(
        path="/general/dossier.txt", name="dossier.txt", extension=".txt", size=10,
        chunk_count=1, scope="global",
    ))
    await db_session.commit()
    index = MagicMock(async_fichiers_contenant=AsyncMock(side_effect=RuntimeError("panne fictive")))
    monkeypatch.setattr(memory_tools, "get_qdrant_service", lambda: index)

    texte, modele, evenements = await _rechercher_dans_la_bulle(
        monkeypatch, db_session, LLMConfig(LLMProvider.OLLAMA, "local-fictif")
    )

    assert "contenu" in texte.lower() and "pas pu être consulté" in texte.lower()
    assert "index" in texte.lower()
    assert "aucun fichier" not in texte.lower() and "comité imaginaire" not in texte
    assert any(e.get("limite_recherche") for e in evenements)
    assert modele.continuations == 0


@pytest.mark.asyncio
async def test_limite_sans_resultat_utile_meme_si_un_autre_outil_echoue(monkeypatch):
    modele = ModeleInventeur()
    monkeypatch.setattr(chat, "_perimetre_de_conversation", AsyncMock(return_value=("global", None)))
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=json.dumps({
        "found": False, "total": 0, "documents": [], "hors_perimetre": 1,
    })))
    monkeypatch.setattr(chat, "execute_workspace_tool", AsyncMock(side_effect=RuntimeError("panne fictive")))
    appels = [
        ToolCall(id="fichiers", name="search_files", arguments={"query": "rapport"}),
        ToolCall(id="emails", name="search_emails", arguments={"query": "rapport"}),
    ]
    outils = [{"type": "function", "function": {"name": appel.name}} for appel in appels]

    evenements = [json.loads(bloc.removeprefix("data: ")) async for bloc in
                  chat._execute_tools_and_continue(
                      modele, None, ContextWindow(messages=[]), "", appels, outils,
                      "c-test", 3, session=object(),
                  )]
    texte = " ".join(e.get("content", "") for e in evenements if e["type"] == "text")

    assert "hors périmètre" in texte.lower()
    assert "comité imaginaire" not in texte
    assert any(e.get("limite_recherche") for e in evenements)
    assert modele.continuations == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("deux_tours", [False, True], ids=["meme-tour", "deux-tours"])
async def test_repli_garde_les_emails_avant_une_recherche_vide(monkeypatch, db_session, deux_tours):
    from app.services import memory_card_context, workspace_tools

    class ModeleSilencieux:
        config = LLMConfig(LLMProvider.OLLAMA, "local-fictif")

        def __init__(self):
            self.continuations = 0

        def prepare_context(self, messages, memory_context=None):
            return ContextWindow(messages=messages, system_prompt="")

        async def stream_response_with_tools(self, contexte, tools=None):
            yield StreamEvent(type="tool_call", tool_call=ToolCall(
                id="emails", name="search_emails", arguments={"query": "rapport"},
            ))
            if not deux_tours:
                yield StreamEvent(type="tool_call", tool_call=ToolCall(
                    id="fichiers", name="search_files", arguments={"query": "rapport"},
                ))
            yield StreamEvent(type="done", stop_reason="tool_calls")

        async def continue_with_tool_results(self, *args, **kwargs):
            self.continuations += 1
            if deux_tours and self.continuations == 1:
                yield StreamEvent(type="tool_call", tool_call=ToolCall(
                    id="fichiers", name="search_files", arguments={"query": "rapport"},
                ))
                yield StreamEvent(type="done", stop_reason="tool_calls")
            else:
                yield StreamEvent(type="done", stop_reason="end_turn")

    modele = ModeleSilencieux()
    conversation = Conversation(id=f"c-repli-vide-{deux_tours}", title="Test fictif")
    db_session.add(conversation)
    await db_session.commit()
    monkeypatch.setattr(chat, "get_llm_service", lambda: modele)
    monkeypatch.setattr(chat, "get_mcp_service", lambda: MagicMock(get_tools_for_llm=lambda: []))
    monkeypatch.setattr(chat, "_get_memory_context", AsyncMock(return_value=""))
    monkeypatch.setattr(chat, "_perimetre_de_conversation", AsyncMock(return_value=("global", None)))
    monkeypatch.setattr(chat, "execute_workspace_tool", AsyncMock(return_value="Rapport Alpha et Rapport Bravo"))
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=json.dumps({
        "found": False, "total": 0, "documents": [],
    })))
    monkeypatch.setattr(workspace_tools, "outils_workspace_disponibles", AsyncMock(side_effect=lambda _, outils: outils))
    monkeypatch.setattr(memory_card_context, "alleger_outils_locaux", lambda _, __, outils: outils)

    evenements = [json.loads(bloc.removeprefix("data: ")) async for bloc in
                  chat._do_stream_response(
                      conversation.id, "Cherche les rapports", db_session, include_memory=False,
                  )]
    texte = "".join(e.get("content", "") for e in evenements if e["type"] == "text")
    enregistre = (await db_session.execute(
        select(Message).where(Message.conversation_id == conversation.id, Message.role == "assistant")
    )).scalar_one().content

    assert "Rapport Alpha" in texte and "Rapport Bravo" in texte
    assert "Rapport Alpha" in enregistre and "Rapport Bravo" in enregistre
    assert "aucun fichier" not in texte.lower() and "aucun fichier" not in enregistre.lower()


@pytest.mark.asyncio
async def test_avertissement_partiel_ne_masque_pas_le_repli_des_emails(monkeypatch, db_session):
    from app.services import memory_card_context, workspace_tools

    class ModeleSilencieux:
        config = LLMConfig(LLMProvider.OLLAMA, "local-fictif")

        def prepare_context(self, messages, memory_context=None):
            return ContextWindow(messages=messages, system_prompt="")

        async def stream_response_with_tools(self, contexte, tools=None):
            yield StreamEvent(type="tool_call", tool_call=ToolCall(
                id="emails", name="search_emails", arguments={"query": "rapport"},
            ))
            yield StreamEvent(type="tool_call", tool_call=ToolCall(
                id="fichiers", name="search_files", arguments={"query": "rapport"},
            ))
            yield StreamEvent(type="done", stop_reason="tool_calls")

        async def continue_with_tool_results(self, *args, **kwargs):
            yield StreamEvent(type="done", stop_reason="end_turn")

    conversation = Conversation(id="c-repli-partiel", title="Test fictif")
    db_session.add(conversation)
    await db_session.commit()
    monkeypatch.setattr(chat, "get_llm_service", lambda: ModeleSilencieux())
    monkeypatch.setattr(chat, "get_mcp_service", lambda: MagicMock(get_tools_for_llm=lambda: []))
    monkeypatch.setattr(chat, "_get_memory_context", AsyncMock(return_value=""))
    monkeypatch.setattr(chat, "_perimetre_de_conversation", AsyncMock(return_value=("global", None)))
    monkeypatch.setattr(chat, "execute_workspace_tool", AsyncMock(return_value="Rapport Alpha et Rapport Bravo"))
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=json.dumps({
        "found": False, "total": 0, "documents": [], "hors_perimetre": 1,
    })))
    monkeypatch.setattr(workspace_tools, "outils_workspace_disponibles", AsyncMock(side_effect=lambda _, outils: outils))
    monkeypatch.setattr(memory_card_context, "alleger_outils_locaux", lambda _, __, outils: outils)

    evenements = [json.loads(bloc.removeprefix("data: ")) async for bloc in
                  chat._do_stream_response(
                      conversation.id, "Cherche les rapports", db_session, include_memory=False,
                  )]
    texte = " ".join(e.get("content", "") for e in evenements if e["type"] == "text")

    assert "hors périmètre" in texte.lower()
    assert "Rapport Alpha" in texte and "Rapport Bravo" in texte
