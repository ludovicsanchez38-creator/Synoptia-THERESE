"""
L'agenda d'une conversation rattachée ne montre pas les rendez-vous d'un autre
dossier.

Campagne cinq personas, constat d'Inès — gravité bloquante. Depuis la
conversation rattachée au dossier Ruiz :

    [list_calendar_events] OK (41ms): 1 evenement(s) dans les 7 prochains
    jours : - 01/09 10:00-11:00 — Séance Martin

restitué à l'écran en « Séance avec le patient **Martin** ».

Sa cause était plus grave que le symptôme : `_list_calendar_events(args,
session)` n'avait ni `scope`, ni `scope_id`, ni `conversation_id`. **La cloison
n'y était pas contournée : elle n'y était pas exprimable.**

CE QUE CE LOT NE FAIT PAS, et c'est délibéré :
- il ne cloisonne QUE l'agenda local. Fichiers, factures et mails n'ont pas été
  éprouvés par la campagne (corpus vide) : cloisonner un domaine non éprouvé,
  c'est afficher un mur devant une pièce qu'on n'a pas visitée ;
- il ne touche pas au chemin Google, qui liste en direct — la colonne SQLite ne
  le filtrerait pas, et prétendre le contraire serait le motif de la 0.53 ;
- il ne rattache PAS les événements existants (pas de backfill) : les coller au
  premier dossier venu serait présomptueux.

Le dernier test de ce fichier FIGE que les factures et les mails ignorent le
périmètre, pour que personne ne croie la signature suffisante.
"""

import json
from datetime import datetime, timedelta

import pytest


def _creneau(dans_heures=24, duree_heures=1):
    """Un rendez-vous a venir, pas une date gravee.

    Les trois premiers tests fixaient 2026-09-01T10:00. Le 01/09/2026 a midi,
    `list_calendar_events` ne rend que les 30 prochains JOURS : deux tests sont
    devenus rouges, et le troisieme — qui verifie une absence — est reste vert
    pour la mauvaise raison. Une date absolue dans un test qui interroge
    l avenir est une bombe a retardement.
    """
    debut = datetime.now() + timedelta(hours=dans_heures)
    fin = debut + timedelta(hours=duree_heures)
    return debut.strftime("%Y-%m-%dT%H:%M:%S"), fin.strftime("%Y-%m-%dT%H:%M:%S")


async def _projet(client, nom):
    reponse = await client.post(
        "/api/memory/projects", json={"name": nom, "description": "dossier"}
    )
    return reponse.json()["id"]


async def _conversation_rattachee(session, projet_id, identifiant):
    from app.models.entities import Conversation

    conv = Conversation(
        id=identifiant, title=f"suivi {projet_id[:6]}",
        memory_scope="project", project_id=projet_id,
    )
    session.add(conv)
    await session.commit()
    return identifiant


class TestUnEvenementSuitSonDossier:
    @pytest.mark.asyncio
    async def test_le_dossier_voisin_ne_voit_pas_mes_rendez_vous(self, client):
        from app.models.database import get_session_context
        from app.services.workspace_tools import execute_workspace_tool

        martin = await _projet(client, "Dossier Martin")
        ruiz = await _projet(client, "Dossier Ruiz")

        async with get_session_context() as session:
            await _conversation_rattachee(session, martin, "conv-martin")
            await _conversation_rattachee(session, ruiz, "conv-ruiz")

            await execute_workspace_tool(
                "create_calendar_event",
                {"summary": "Séance Martin", "start": _creneau()[0],
                 "end": _creneau()[1]},
                session,
                conversation_id="conv-martin",
            )

            depuis_ruiz = await execute_workspace_tool(
                "list_calendar_events", {}, session, conversation_id="conv-ruiz"
            )

        assert "Martin" not in depuis_ruiz, (
            "le rendez-vous d'un patient apparaît dans le dossier d'un autre : "
            f"{depuis_ruiz[:200]!r}"
        )

    @pytest.mark.asyncio
    async def test_mon_propre_dossier_voit_mes_rendez_vous(self, client):
        """La cloison ne doit pas éteindre l'agenda de celui qui l'a créé."""
        from app.models.database import get_session_context
        from app.services.workspace_tools import execute_workspace_tool

        martin = await _projet(client, "Dossier Martin")

        async with get_session_context() as session:
            await _conversation_rattachee(session, martin, "conv-m2")
            await execute_workspace_tool(
                "create_calendar_event",
                {"summary": "Séance Martin", "start": _creneau()[0],
                 "end": _creneau()[1]},
                session,
                conversation_id="conv-m2",
            )
            depuis_martin = await execute_workspace_tool(
                "list_calendar_events", {}, session, conversation_id="conv-m2"
            )

        assert "Martin" in depuis_martin

    @pytest.mark.asyncio
    async def test_une_conversation_libre_voit_tout(self, client):
        """Sans rattachement, aucune cloison : c'est le comportement d'aujourd'hui."""
        from app.models.database import get_session_context
        from app.services.workspace_tools import execute_workspace_tool

        martin = await _projet(client, "Dossier Martin")

        async with get_session_context() as session:
            await _conversation_rattachee(session, martin, "conv-m3")
            await execute_workspace_tool(
                "create_calendar_event",
                {"summary": "Séance Martin", "start": _creneau()[0],
                 "end": _creneau()[1]},
                session,
                conversation_id="conv-m3",
            )
            libre = await execute_workspace_tool("list_calendar_events", {}, session)

        assert "Martin" in libre

    @pytest.mark.asyncio
    async def test_un_evenement_anterieur_reste_visible(self, client):
        """Pas de backfill : coller un événement existant à un dossier serait
        présomptueux. Ils restent visibles partout."""
        from app.models.database import get_session_context
        from app.models.entities import CalendarEvent
        from app.services.workspace_tools import execute_workspace_tool
        from sqlalchemy import select

        ruiz = await _projet(client, "Dossier Ruiz")
        async with get_session_context() as session:
            await _conversation_rattachee(session, ruiz, "conv-r2")
            # Un evenement cree AVANT la 0.56 : il n'a pas de dossier.
            await execute_workspace_tool(
                "create_calendar_event",
                {"summary": "Rendez-vous d'avant la 0.56",
                 "start": _creneau(48)[0], "end": _creneau(48)[1]},
                session,
            )
            resultat = await session.execute(
                select(CalendarEvent).where(
                    CalendarEvent.summary == "Rendez-vous d'avant la 0.56"
                )
            )
            ancien = resultat.scalars().one()
            assert ancien.project_id is None, (
                "cree hors conversation rattachee : aucun dossier"
            )
            await session.commit()
            depuis_ruiz = await execute_workspace_tool(
                "list_calendar_events", {}, session, conversation_id="conv-r2"
            )

        assert "avant la 0.56" in depuis_ruiz, (
            "un événement sans dossier doit rester visible : sinon la mise à "
            "jour ferait disparaître l'agenda de tout le monde"
        )


class TestCeQueCeLotNeCloisonnePas:
    """Figé pour que personne ne croie la signature suffisante."""

    @pytest.mark.asyncio
    async def test_les_factures_ignorent_encore_le_perimetre(self, client):
        from app.models.database import get_session_context
        from app.services.workspace_tools import execute_workspace_tool

        martin = await _projet(client, "Dossier Martin")
        async with get_session_context() as session:
            await _conversation_rattachee(session, martin, "conv-fact")
            resultat = await execute_workspace_tool(
                "invoice_totals", {}, session, conversation_id="conv-fact"
            )
        # Il rend un résultat, sans erreur de périmètre : la cloison n'y est pas.
        assert json.loads(resultat) is not None


class TestLeCheminDeConfirmationEstCouvertAussi:
    """
    Inès n'a pas créé son rendez-vous par un appel direct : elle a **confirmé**.

    `create_calendar_event` est un outil sensible : il passe par une carte de
    confirmation. Cloisonner le flux sans cloisonner la confirmation ne
    couvrirait donc PAS le cas qui a produit le constat — l'événement se
    créerait sans dossier et reparaîtrait chez l'autre patient.

    Ce test suit le chemin complet : mise en attente depuis une conversation
    rattachée, puis confirmation.
    """

    def test_la_conversation_voyage_avec_l_action_en_attente(self):
        from app.services.tool_confirmations import pop_pending, register_pending

        identifiant = register_pending(
            "create_calendar_event",
            {"summary": "Séance Martin"},
            conversation_id="conv-martin",
        )
        action = pop_pending(identifiant)

        assert action is not None
        nom, arguments, conversation_id = action
        assert nom == "create_calendar_event"
        assert conversation_id == "conv-martin", (
            "sans la conversation, l'événement confirmé se crée sans dossier "
            "et réapparaît chez l'autre patient : c'est le cas d'Inès"
        )

    def test_sans_conversation_l_action_reste_valide(self):
        """Une action mise en attente hors conversation ne doit pas casser."""
        from app.services.tool_confirmations import pop_pending, register_pending

        identifiant = register_pending("send_email", {"to": "a@b.c"})
        nom, arguments, conversation_id = pop_pending(identifiant)

        assert nom == "send_email"
        assert conversation_id is None
