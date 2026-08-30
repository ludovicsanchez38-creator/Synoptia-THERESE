"""
Un fichier produit par l'outil `generate_document` doit arriver à l'écran.

Campagne cinq personas : Léa est le SEUL abandon sur un défaut de
l'application, tous les autres ont abandonné sur le temps du modèle local.
Elle a demandé « fais-moi le fichier Excel de la semaine ». Le fichier a été
produit - un vrai `.xlsx`, avec ses trois créneaux. Rien ne s'est affiché pour
le récupérer.

Sa preuve : le flux contient
`[generate_document] OK (104ms): Document XLSX généré : …xlsx` et **aucun
chunk `skill_file`**. La conversation relue rend `extra_data: null`. Elle a
ouvert Excel et refait le travail à la main.

Contre-épreuve décisive qu'elle a menée : la même demande avec
`skill_id: "xlsx-pro"` fait bien arriver la carte. **La mécanique de carte
marche ; c'est le chemin OUTIL qui ne branche rien.**

Le test qui existait (`test_chat_skill_file_stream.py`) appelle
`record_generated_file` puis `drain_generated_files` dans le même contexte
isolé : il est vert et ne voit rien. Celui-ci passe par le VRAI flux, avec un
modèle qui appelle l'outil.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from app.models.entities import Conversation
from app.services.providers.base import StreamEvent


class _Provider:
    value = "anthropic"


class _Config:
    provider = _Provider()
    model = "fake-model"


class _ToolCall:
    """Un appel d'outil, tel que le fournisseur le rend."""

    def __init__(self, name, arguments):
        self.id = "call-1"
        self.name = name
        self.arguments = arguments


class _LLMQuiAppelleLOutil:
    """Le modèle demande un document, puis conclut - comme chez Léa."""

    config = _Config()

    def prepare_context(self, messages, memory_context=None):
        from app.services.context import ContextWindow

        return ContextWindow(messages=[], system_prompt="")

    def __init__(self):
        self.tours = 0

    async def stream_response_with_tools(self, context, tools=None):
        self.tours += 1
        if self.tours == 1:
            yield StreamEvent(
                type="tool_call",
                tool_call=_ToolCall(
                    "generate_document",
                    {"format": "xlsx", "content": "Planning de la semaine"},
                ),
            )
            yield StreamEvent(type="done", stop_reason="tool_calls")
        else:
            yield StreamEvent(type="text", content="Voilà ton planning.")
            yield StreamEvent(type="done", stop_reason="end_turn")

    async def continue_with_tool_results(self, *a, **k):
        """Le second tour, après l'exécution de l'outil — chemin NOMINAL."""
        yield StreamEvent(type="text", content="Voilà ton planning.")
        yield StreamEvent(type="done", stop_reason="end_turn")


async def _evenements(db_session, llm, conv_id: str = "conv-outil-fichier"):
    from app.routers.chat import _do_stream_response

    conv = Conversation(id=conv_id, title="planning")
    db_session.add(conv)
    await db_session.commit()

    with patch("app.routers.chat.get_llm_service", return_value=llm), \
         patch("app.routers.chat._get_memory_context", AsyncMock(return_value="")):
        brut = ""
        async for morceau in _do_stream_response(
            conv.id, "fais-moi le fichier Excel de la semaine", db_session
        ):
            brut += morceau

    evenements = []
    for bloc in brut.split("\n\n"):
        bloc = bloc.strip()
        if bloc.startswith("data: "):
            evenements.append(json.loads(bloc[len("data: "):]))
    return evenements


async def _confirmer_generation(db_session, evenements, faux_outil):
    """Passe 4 : generate_document attend une carte. Le fichier n'est
    plus écrit pendant le flux ; il l'est à la confirmation."""
    from app.routers.chat import ConfirmToolRequest, confirm_tool

    confirms = [e for e in evenements if e.get("type") == "confirmation_required"]
    assert confirms, (
        "generate_document s'est exécuté sans carte : "
        f"{sorted({e.get('type') for e in evenements})}"
    )
    cid = confirms[0]["confirmation"]["confirmation_id"]
    with patch("app.routers.chat.execute_workspace_tool", faux_outil):
        return await confirm_tool(
            ConfirmToolRequest(confirmation_id=cid, approved=True),
            session=db_session,
        )


class TestLaCarteArriveQuandLOutilAEcrit:
    @pytest.mark.asyncio
    async def test_un_fichier_produit_par_l_outil_emet_une_carte(
        self, db_session
    ):
        from app.services import workspace_tools

        async def _faux_outil(nom, arguments, session, contexte=None, conversation_id=None):
            if nom == "generate_document":
                workspace_tools.record_generated_file({
                    "skill_id": None, "file_id": "f-1",
                    "file_name": "planning-semaine.xlsx",
                    "file_size": 4096, "download_url": "/api/skills/files/f-1",
                    "format": "xlsx", "local_dir": "/tmp",
                })
                return "Document XLSX généré : planning-semaine.xlsx."
            return "ok"

        with patch("app.routers.chat.execute_workspace_tool", _faux_outil), \
             patch("app.routers.chat.WORKSPACE_TOOL_NAMES", {"generate_document"}):
            evenements = await _evenements(
                db_session, _LLMQuiAppelleLOutil(), conv_id="conv-outil-fichier-1"
            )

        assert not [e for e in evenements if e.get("type") == "error"], (
            "le chemin doit être NOMINAL : une erreur testerait autre chose"
        )
        data = await _confirmer_generation(db_session, evenements, _faux_outil)
        fichiers = data.get("skill_files") or []
        assert fichiers, (
            "l'utilisateur a confirmé, le fichier est écrit, et aucune "
            f"carte de téléchargement n'est renvoyée : {data}"
        )
        assert fichiers[0]["file_name"] == "planning-semaine.xlsx"

    @pytest.mark.asyncio
    async def test_la_carte_de_confirmation_arrive_avant_done(self, db_session):
        """Le client arrête la lecture sur `done` : la demande de
        confirmation doit arriver AVANT, sinon elle n'atteint jamais l'écran."""
        from app.services import workspace_tools

        async def _faux_outil(nom, arguments, session, contexte=None, conversation_id=None):
            workspace_tools.record_generated_file({
                "file_id": "f-2", "file_name": "planning.xlsx", "format": "xlsx",
            })
            return "Document XLSX généré."

        with patch("app.routers.chat.execute_workspace_tool", _faux_outil), \
             patch("app.routers.chat.WORKSPACE_TOOL_NAMES", {"generate_document"}):
            evenements = await _evenements(
                db_session, _LLMQuiAppelleLOutil(), conv_id="conv-outil-fichier-2"
            )

        types = [e.get("type") for e in evenements]
        assert "confirmation_required" in types
        assert types.index("confirmation_required") < types.index("done"), (
            f"carte émise après `done`, donc jamais lue : {types}"
        )


class _LLMQuiAppelleAuSecondTour:
    """Le modèle bavarde, PUIS demande le document — la récursion d'outils.

    Chemin non couvert par le test nominal : `_execute_tools_and_continue`
    s'appelle elle-même (`chat.py:3144`) quand le second tour porte encore un
    appel d'outil. Le drain, lui, vit dans la fonction du dessus.
    """

    config = _Config()

    def prepare_context(self, messages, memory_context=None):
        from app.services.context import ContextWindow

        return ContextWindow(messages=[], system_prompt="")

    def __init__(self):
        self.tours = 0

    async def stream_response_with_tools(self, context, tools=None):
        self.tours += 1
        yield StreamEvent(
            type="tool_call",
            tool_call=_ToolCall("list_calendar_events", {}),
        )
        yield StreamEvent(type="done", stop_reason="tool_calls")

    async def continue_with_tool_results(self, *a, **k):
        self.tours += 1
        if self.tours == 2:
            # Second tour : le modèle demande MAINTENANT le document.
            yield StreamEvent(
                type="tool_call",
                tool_call=_ToolCall("generate_document", {"format": "xlsx"}),
            )
            yield StreamEvent(type="done", stop_reason="tool_calls")
        else:
            yield StreamEvent(type="text", content="Voilà ton planning.")
            yield StreamEvent(type="done", stop_reason="end_turn")


class TestLaCarteArriveAussiDansLaRecursion:
    @pytest.mark.asyncio
    async def test_un_fichier_ecrit_au_second_tour_emet_une_carte(
        self, db_session
    ):
        from app.services import workspace_tools

        async def _faux_outil(nom, arguments, session, contexte=None, conversation_id=None):
            if nom == "generate_document":
                workspace_tools.record_generated_file({
                    "file_id": "f-3", "file_name": "planning-recursion.xlsx",
                    "format": "xlsx",
                })
                return "Document XLSX généré : planning-recursion.xlsx."
            return "Aucun événement."

        with patch("app.routers.chat.execute_workspace_tool", _faux_outil), \
             patch(
                 "app.routers.chat.WORKSPACE_TOOL_NAMES",
                 {"generate_document", "list_calendar_events"},
             ):
            evenements = await _evenements(
                db_session, _LLMQuiAppelleAuSecondTour(), conv_id="conv-outil-fichier-3"
            )

        types = [e.get("type") for e in evenements]
        assert "confirmation_required" in types, (
            f"fichier demandé au second tour, aucune carte : {types}"
        )
        data = await _confirmer_generation(db_session, evenements, _faux_outil)
        fichiers = data.get("skill_files") or []
        assert fichiers and fichiers[0]["file_name"] == "planning-recursion.xlsx"


class TestLeRetourDOutilNePrometPasUneCarteQuiNexistePas:
    """
    La moitié du défaut de Léa que je peux prouver.

    Le retour de `generate_document` ORDONNE au modèle : « L'utilisateur peut
    l'enregistrer via la carte affichée sous ce message - ne fournis aucun
    lien. » Quand la carte n'est pas émise, un modèle parfait obéit et ment :
    il annonce une carte, et Léa cherche un bouton qui n'existe pas.

    Elle n'a pas douté de l'application. Elle a cherché.

    La promesse ne doit donc être faite QUE si l'enregistrement a réellement
    eu lieu. Sinon : l'identifiant, et aucune promesse.

    NOTE D'HONNÊTETÉ : le symptôme de Léa (fichier écrit, aucun `skill_file`
    dans le flux) n'est PAS reproduit. Trois chemins testés - nominal,
    récursion, et le vrai serveur - émettent la carte. Ollama était épuisé au
    moment de la vérification en conditions réelles. Ce test ferme la moitié
    prouvable ; l'autre reste ouverte et nommée.
    """

    def test_le_collecteur_dit_s_il_a_collecte(self):
        from app.services.workspace_tools import (
            drain_generated_files,
            record_generated_file,
            start_generated_files_collection,
        )

        start_generated_files_collection()
        assert record_generated_file({"file_id": "a"}) is True
        drain_generated_files()
        assert record_generated_file({"file_id": "b"}) is False, (
            "hors collecte, l'enregistrement est un no-op : l'outil doit le "
            "savoir pour ne pas promettre une carte"
        )

    def test_sans_collecte_le_retour_ne_promet_aucune_carte(self):
        from app.services.workspace_tools import _texte_de_retour_document

        texte = _texte_de_retour_document("planning.xlsx", "xlsx", collecte=False)
        # Viser la PROMESSE, pas le mot : le texte de repli dit justement
        # « n'annonce aucune carte », et contient donc le mot.
        assert "via la carte affich" not in texte.lower(), (
            f"promesse d'une carte qui ne sera pas affichée : {texte!r}"
        )
        assert "aucune carte" in texte.lower()
        assert "planning.xlsx" in texte

    def test_avec_collecte_le_retour_annonce_la_carte(self):
        from app.services.workspace_tools import _texte_de_retour_document

        texte = _texte_de_retour_document("planning.xlsx", "xlsx", collecte=True)
        assert "carte" in texte.lower()
        assert "ne fournis aucun lien" in texte.lower()


class TestLeCablageEntreLeCollecteurEtLeTexte:
    """
    Le sabotage a montré que le CÂBLAGE n'était pas couvert.

    Les deux moitiés étaient testées séparément - le collecteur rend un
    booléen, le texte le respecte - et retirer le fil entre les deux ne
    cassait rien. C'est le motif de la session : tester l'aide plutôt que le
    parcours.

    Ce test appelle le VRAI outil, deux fois : sous collecte, et hors
    collecte. Les deux textes doivent différer.
    """

    @staticmethod
    def _registry_qui_reussit():
        class _Resp:
            success = True
            error = None
            file_id = "f-x"
            file_name = "planning.xlsx"
            file_size = 1024
            download_url = "/api/skills/files/f-x"

        class _Registry:
            output_dir = "/tmp"

            async def execute(self, *a, **k):
                return _Resp()

        return _Registry()

    @pytest.mark.asyncio
    async def test_le_texte_suit_l_etat_reel_de_la_collecte(self, db_session):
        from app.services import workspace_tools
        from app.services.workspace_tools import (
            drain_generated_files,
            execute_workspace_tool,
            start_generated_files_collection,
        )

        with patch(
            "app.services.skills.get_skills_registry",
            return_value=self._registry_qui_reussit(),
        ):
            start_generated_files_collection()
            sous_collecte = await execute_workspace_tool(
                "generate_document",
                {"format": "xlsx", "content": "x"},
                db_session,
            )
            fichiers = drain_generated_files()

            # Hors collecte : le seau est vidé, plus rien ne sera affiché.
            hors_collecte = await execute_workspace_tool(
                "generate_document",
                {"format": "xlsx", "content": "x"},
                db_session,
            )

        assert fichiers, "le premier appel devait être collecté"
        assert "via la carte affich" in sous_collecte.lower(), sous_collecte
        assert "via la carte affich" not in hors_collecte.lower(), (
            "hors collecte, l'outil promet encore une carte : le fil entre le "
            f"collecteur et le texte est coupé. Retour : {hors_collecte!r}"
        )
        assert workspace_tools.record_generated_file({"x": 1}) is False
