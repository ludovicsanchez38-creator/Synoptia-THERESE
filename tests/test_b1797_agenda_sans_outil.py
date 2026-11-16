"""L'agenda n'est attribué qu'à une lecture effective de l'outil."""

import json
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.models.entities import Calendar, CalendarEvent, Message
from app.services.civil_time import PARIS
from app.services.providers.base import StreamEvent, ToolCall
from sqlmodel import select

from tests.test_r2_3_outil import fournisseur  # noqa: F401

MENTION = "Je n'ai pas consulté ton agenda pour cette réponse : ces rendez-vous ne viennent pas de lui."


def _evenements(reponse):
    return [json.loads(ligne.removeprefix("data: ")) for ligne in reponse.text.splitlines()
            if ligne.startswith("data: ")]


def _texte(reponse, stream):
    assert reponse.status_code == 200
    if not stream:
        return reponse.json()["content"]
    return "".join(e.get("content", "") for e in _evenements(reponse) if e["type"] == "text")


@pytest.mark.asyncio
async def test_agenda_offert_le_texte_et_le_premier_token_arrivent_au_fil_de_l_eau(
    client, db_session, fournisseur, monkeypatch  # noqa: F811
):
    from app.routers import chat

    db_session.add(Calendar(id="agenda-stream", summary="Agenda", provider="local"))
    await db_session.commit()
    progression = []

    class Modele:
        async def stream(self, _system, _messages, tools=None, **_kwargs):
            assert "list_calendar_events" in {outil["function"]["name"] for outil in tools}
            progression.append("premier")
            yield StreamEvent(type="text", content="Bonjour, ")
            progression.append("deuxième")
            yield StreamEvent(type="text", content="je reviens vers toi.")
            progression.append("fin")
            yield StreamEvent(type="done", stop_reason="end_turn")

    metriques = SimpleNamespace(record_first_token=MagicMock(), record_output_tokens=MagicMock())
    moniteur = SimpleNamespace(start_stream=MagicMock(return_value=metriques), finish_stream=MagicMock())
    monkeypatch.setattr(chat, "get_performance_monitor", lambda: moniteur)
    fournisseur[0]._provider = Modele()
    conversation = (await client.post("/api/chat/conversations", json={"title": "Flux"})).json()["id"]
    flux = chat._do_stream_response(
        conversation, "Rédige un mail de relance", db_session, [],
        calendar_id="agenda-stream", include_memory=False,
    )
    evenements = []

    async def prochain_texte():
        async for morceau in flux:
            evenement = json.loads(morceau.removeprefix("data: "))
            evenements.append(evenement)
            assert evenement["type"] not in {"done", "error"}
            if evenement["type"] == "text":
                return evenement["content"]
        pytest.fail("Le flux s'est terminé avant le morceau attendu")

    try:
        assert await prochain_texte() == "Bonjour, "
        assert progression == ["premier"]
        metriques.record_first_token.assert_called_once_with()
        assert await prochain_texte() == "je reviens vers toi."
        assert progression == ["premier", "deuxième"]
        metriques.record_first_token.assert_called_once_with()
        async for morceau in flux:
            evenements.append(json.loads(morceau.removeprefix("data: ")))
        assert progression == ["premier", "deuxième", "fin"]
        assert [e["content"] for e in evenements if e["type"] == "text"] == [
            "Bonjour, ", "je reviens vers toi.",
        ]
        assert evenements[-1]["type"] == "done"
    finally:
        await flux.aclose()


@pytest.mark.asyncio
async def test_annonce_avant_lecture_puis_texte_du_modele(
    client, db_session, fournisseur  # noqa: F811
):
    debut = (datetime.now(PARIS) + timedelta(days=1)).replace(tzinfo=None)
    db_session.add(Calendar(id="agenda-annonce", summary="Agenda", provider="local"))
    db_session.add(CalendarEvent(
        id="rdv-annonce", calendar_id="agenda-annonce", summary="Consultation vérifiée",
        start_datetime=debut, end_datetime=debut + timedelta(hours=1), status="confirmed",
    ))
    await db_session.commit()

    class Modele:
        async def stream(self, _system, _messages, tools=None, **_kwargs):
            assert "list_calendar_events" in {outil["function"]["name"] for outil in tools}
            yield StreamEvent(type="text", content="Je regarde ton agenda.")
            yield StreamEvent(type="tool_call", tool_call=ToolCall(
                id="lecture", name="list_calendar_events", arguments={"days": 7},
            ))
            yield StreamEvent(type="done", stop_reason="tool_calls")

        async def continue_with_tool_results(self, *args, **kwargs):
            assert "Consultation vérifiée" in str(args[4][0].result)
            yield StreamEvent(type="text", content="- Consultation vérifiée")
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    reponse = await client.post("/api/chat/send", json={
        "message": "Que se passe-t-il demain ?", "calendar_id": "agenda-annonce",
        "include_memory": False, "stream": True,
    })
    evenements = _evenements(reponse)
    indice_annonce = next((i for i, e in enumerate(evenements)
                           if e["type"] == "text" and e["content"] == "Je regarde ton agenda."), None)
    indice_resultat = next(i for i, e in enumerate(evenements) if e["type"] == "tool_result")
    assert indice_annonce is not None and indice_annonce < indice_resultat
    texte = _texte(reponse, True)
    assert "Consultation vérifiée" in texte
    assert texte == "Je regarde ton agenda.- Consultation vérifiée"
    messages = (await db_session.execute(select(Message))).scalars().all()
    assert [message.content for message in messages if message.role == "assistant"] == [texte]


@pytest.mark.asyncio
async def test_annulation_en_flux_enregistre_exactement_le_texte_diffuse(
    client, db_session, fournisseur  # noqa: F811
):
    from app.routers import chat

    db_session.add(Calendar(id="agenda-annulation", summary="Agenda", provider="local"))
    await db_session.commit()

    class Modele:
        async def stream(self, _system, _messages, tools=None, **_kwargs):
            assert "list_calendar_events" in {outil["function"]["name"] for outil in tools}
            yield StreamEvent(type="text", content="Premier morceau. ")
            yield StreamEvent(type="text", content="Morceau non diffusé.")
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    conversation = (await client.post("/api/chat/conversations", json={"title": "Arrêt"})).json()["id"]
    flux = chat._do_stream_response(
        conversation, "Rédige un mail de relance", db_session, [],
        calendar_id="agenda-annulation", include_memory=False,
    )
    async for morceau in flux:
        evenement = json.loads(morceau.removeprefix("data: "))
        assert evenement["type"] not in {"done", "error"}
        if evenement["type"] == "text":
            texte_diffuse = evenement["content"]
            break
    await flux.aclose()
    messages = (await db_session.execute(
        select(Message).where(Message.conversation_id == conversation, Message.role == "assistant")
    )).scalars().all()
    assert [message.content for message in messages] == [texte_diffuse]


@pytest.mark.asyncio
async def test_annulation_apres_preambule_enregistre_le_texte_diffuse(
    client, db_session, fournisseur  # noqa: F811
):
    from app.routers import chat

    db_session.add(Calendar(id="agenda-preambule", summary="Agenda", provider="local"))
    await db_session.commit()
    conversation = (await client.post("/api/chat/conversations", json={"title": "Préambule"})).json()["id"]
    flux = chat._do_stream_response(
        conversation, "Rédige un mail de relance", db_session, [],
        preamble="Préambule affiché.", calendar_id="agenda-preambule", include_memory=False,
    )
    async for morceau in flux:
        evenement = json.loads(morceau.removeprefix("data: "))
        assert evenement["type"] not in {"done", "error"}
        if evenement["type"] == "text":
            texte_diffuse = evenement["content"]
            break
    await flux.aclose()
    messages = (await db_session.execute(
        select(Message).where(Message.conversation_id == conversation, Message.role == "assistant")
    )).scalars().all()
    assert [message.content for message in messages] == [texte_diffuse]


@pytest.mark.asyncio
async def test_annulation_apres_mention_enregistre_tout_le_texte_diffuse(
    client, db_session, fournisseur  # noqa: F811
):
    from app.routers import chat

    db_session.add(Calendar(id="agenda-mention", summary="Agenda", provider="local"))
    await db_session.commit()

    class Modele:
        async def stream(self, _system, _messages, tools=None, **_kwargs):
            assert "list_calendar_events" in {outil["function"]["name"] for outil in tools}
            yield StreamEvent(type="text", content="- 14h : Exemple A\n- 15h : Exemple B")
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    conversation = (await client.post("/api/chat/conversations", json={"title": "Mention"})).json()["id"]
    flux = chat._do_stream_response(
        conversation, "Mes rendez-vous de demain ?", db_session, [],
        calendar_id="agenda-mention", include_memory=False,
    )
    textes = []
    async for morceau in flux:
        evenement = json.loads(morceau.removeprefix("data: "))
        assert evenement["type"] not in {"done", "error"}
        if evenement["type"] == "text":
            textes.append(evenement["content"])
            if MENTION in evenement["content"]:
                break
    else:
        pytest.fail("La mention n'a pas été diffusée")
    await flux.aclose()
    messages = (await db_session.execute(
        select(Message).where(Message.conversation_id == conversation, Message.role == "assistant")
    )).scalars().all()
    assert [message.content for message in messages] == ["".join(textes)]


@pytest.mark.asyncio
async def test_annulation_apres_lecture_conserve_exactement_le_texte_diffuse(
    client, db_session, fournisseur  # noqa: F811
):
    from app.routers import chat

    debut = (datetime.now(PARIS) + timedelta(days=1)).replace(tzinfo=None)
    db_session.add(Calendar(id="agenda-partiel", summary="Agenda", provider="local"))
    db_session.add(CalendarEvent(
        id="rdv-partiel", calendar_id="agenda-partiel", summary="Lecture vérifiée",
        start_datetime=debut, end_datetime=debut + timedelta(hours=1), status="confirmed",
    ))
    await db_session.commit()

    class Modele:
        async def stream(self, _system, _messages, tools=None, **_kwargs):
            yield StreamEvent(type="text", content="Je regarde ton agenda.")
            yield StreamEvent(type="tool_call", tool_call=ToolCall(
                id="lecture", name="list_calendar_events", arguments={"days": 7},
            ))
            yield StreamEvent(type="done", stop_reason="tool_calls")

        async def continue_with_tool_results(self, *args, **kwargs):
            yield StreamEvent(type="text", content="Lecture vérifiée : premier morceau.")
            yield StreamEvent(type="text", content="Morceau non diffusé.")
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    conversation = (await client.post("/api/chat/conversations", json={"title": "Lecture"})).json()["id"]
    flux = chat._do_stream_response(
        conversation, "Mon agenda demain ?", db_session, [],
        calendar_id="agenda-partiel", include_memory=False,
    )
    textes = []
    async for morceau in flux:
        evenement = json.loads(morceau.removeprefix("data: "))
        assert evenement["type"] not in {"done", "error"}
        if evenement["type"] == "text":
            textes.append(evenement["content"])
            if "Lecture vérifiée" in evenement["content"]:
                break
    else:
        pytest.fail("Le texte après lecture n'a pas été diffusé")
    await flux.aclose()
    messages = (await db_session.execute(
        select(Message).where(Message.conversation_id == conversation, Message.role == "assistant")
    )).scalars().all()
    assert [message.content for message in messages] == ["".join(textes)]


@pytest.mark.asyncio
@pytest.mark.parametrize("lecture_agenda", [False, True], ids=["sans_lecture", "lecture_en_chaine"])
async def test_continuation_apres_autre_outil_reste_progressive(
    client, db_session, fournisseur, monkeypatch, lecture_agenda  # noqa: F811
):
    from app.routers import chat
    from app.services import workspace_tools

    debut = (datetime.now(PARIS) + timedelta(days=1)).replace(tzinfo=None)
    db_session.add(Calendar(id="agenda-chaine", summary="Agenda", provider="local"))
    db_session.add(CalendarEvent(
        id="rdv-chaine", calendar_id="agenda-chaine", summary="Entretien vérifié",
        start_datetime=debut, end_datetime=debut + timedelta(hours=1), status="confirmed",
    ))
    await db_session.commit()
    disponibles = workspace_tools.outils_workspace_disponibles
    executer = chat.execute_workspace_tool

    async def offrir_lecture_fictive(session, outils):
        resultat = await disponibles(session, outils)
        resultat.append(next(outil for outil in outils if outil["function"]["name"] == "search_emails"))
        return resultat

    async def executer_lecture_fictive(nom, arguments, session, **kwargs):
        if nom == "search_emails":
            return "Message fictif trouvé."
        return await executer(nom, arguments, session, **kwargs)

    monkeypatch.setattr(workspace_tools, "outils_workspace_disponibles", offrir_lecture_fictive)
    monkeypatch.setattr(chat, "execute_workspace_tool", executer_lecture_fictive)
    metriques = SimpleNamespace(record_first_token=MagicMock(), record_output_tokens=MagicMock())
    moniteur = SimpleNamespace(start_stream=MagicMock(return_value=metriques), finish_stream=MagicMock())
    monkeypatch.setattr(chat, "get_performance_monitor", lambda: moniteur)
    progression = []

    class Modele:
        continuations = 0

        async def stream(self, _system, _messages, tools=None, **_kwargs):
            assert {"search_emails", "list_calendar_events"} <= {
                outil["function"]["name"] for outil in tools
            }
            yield StreamEvent(type="tool_call", tool_call=ToolCall(
                id="mail", name="search_emails", arguments={"query": "fictif"},
            ))
            yield StreamEvent(type="done", stop_reason="tool_calls")

        async def continue_with_tool_results(self, *args, **kwargs):
            self.continuations += 1
            if self.continuations == 1:
                progression.append("premier")
                yield StreamEvent(type="text", content="Message trouvé. ")
                progression.append("deuxième")
                yield StreamEvent(type="text", content="Je poursuis.")
                progression.append("fin")
                if lecture_agenda:
                    yield StreamEvent(type="tool_call", tool_call=ToolCall(
                        id="agenda", name="list_calendar_events", arguments={"days": 7},
                    ))
                    yield StreamEvent(type="done", stop_reason="tool_calls")
                else:
                    yield StreamEvent(type="done", stop_reason="end_turn")
            else:
                yield StreamEvent(type="text", content="- 14h : Première entrée\n- 15h : Seconde entrée")
                yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    conversation = (await client.post("/api/chat/conversations", json={"title": "Chaîne"})).json()["id"]
    flux = chat._do_stream_response(
        conversation, "Lis mon agenda de demain", db_session, [],
        calendar_id="agenda-chaine", include_memory=False,
    )
    textes = []
    async for morceau in flux:
        evenement = json.loads(morceau.removeprefix("data: "))
        assert evenement["type"] != "error"
        if evenement["type"] == "text":
            textes.append(evenement["content"])
            if len(textes) == 1:
                assert progression == ["premier"]
                metriques.record_first_token.assert_called_once_with()
            elif len(textes) == 2:
                assert progression == ["premier", "deuxième"]
                metriques.record_first_token.assert_called_once_with()
    assert textes[:2] == ["Message trouvé. ", "Je poursuis."]
    assert progression == ["premier", "deuxième", "fin"]
    texte = "".join(textes)
    assert ("Première entrée" in texte) is lecture_agenda
    assert MENTION not in texte
    messages = (await db_session.execute(
        select(Message).where(Message.conversation_id == conversation, Message.role == "assistant")
    )).scalars().all()
    assert [message.content for message in messages] == [texte]


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["sans_flux", "flux"])
@pytest.mark.parametrize(("demande", "horaires"), [
    ("Quels sont mes rendez-vous de demain ?", ("14h", "15:00")),
    ("Demain, montre-moi mon agenda.", ("14 h 30", "15h")),
    ("Mon planning pour lundi ?", ("9:00", "14 h")),
    ("Qu'est-ce que j'ai de prévu demain ?", ("9h", "15h")),
    ("Suis-je disponible jeudi ?", ("10:00", "14:00")),
])
async def test_qwen_sans_outil_preserve_les_horaires_et_ajoute_la_mention(
    client, db_session, fournisseur, demande, horaires, stream  # noqa: F811
):
    contenu = f"Voici tes rendez-vous :\n- {horaires[0]} : Réunion fictive\n- {horaires[1]} : Entretien fictif"

    class ModeleInventif:
        async def stream(self, *args, **kwargs):
            yield StreamEvent(type="text", content=contenu[:20])
            yield StreamEvent(type="text", content=contenu[20:])
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = ModeleInventif()
    reponse = await client.post("/api/chat/send", json={
        "message": demande, "include_memory": False, "stream": stream,
    })
    assert _texte(reponse, stream) == contenu + "\n\n" + MENTION
    messages = (await db_session.execute(select(Message))).scalars().all()
    assert [message.content for message in messages if message.role == "assistant"] == [
        contenu + "\n\n" + MENTION
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["sans_flux", "flux"])
@pytest.mark.parametrize(("demande", "lecture_avant"), [
    ("Comment brancher mon agenda ?", False),
    ("Rédige-moi le mail de confirmation de mon rendez-vous de jeudi.", False),
    ("Le devis prévoit un rendez-vous de livraison. Peux-tu le reformuler ?", False),
    ("Les données du rendez-vous client sont dans la pièce jointe, résume-les.", False),
    ("Donne-moi un exemple de mail de prise de rendez-vous.", False),
    ("Je suis libre cet après-midi, propose-moi un plan de travail.", False),
    ("Suis-je libre d'utiliser cette photo ?", False),
    ("Ma présentation est libre de droits, rédige la clause.", False),
    ("Affiche le calendrier des formations internes.", False),
    ("Rédige le mail pour demain", True),
    ("Envoie le compte-rendu jeudi", True),
], ids=["brancher", "mail", "devis", "piece_jointe", "exemple", "plan_de_travail",
        "photo", "droits", "formations", "relance_redaction", "relance_envoi"])
async def test_faux_positifs_reponse_intacte_sans_mention(
    client, db_session, fournisseur, demande, lecture_avant, stream  # noqa: F811
):
    contenu = "Réponse du modèle :\n- 14h : Exemple A\n- 15:00 : Exemple B"

    class Modele:
        lecture_a_faire = lecture_avant

        async def stream(self, *args, **kwargs):
            if self.lecture_a_faire:
                self.lecture_a_faire = False
                yield StreamEvent(type="tool_call", tool_call=ToolCall(
                    id="lecture", name="list_calendar_events", arguments={"days": 7},
                ))
                yield StreamEvent(type="done", stop_reason="tool_calls")
            else:
                yield StreamEvent(type="text", content=contenu)
                yield StreamEvent(type="done", stop_reason="end_turn")

        async def continue_with_tool_results(self, *args, **kwargs):
            yield StreamEvent(type="text", content="Lecture terminée.")
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    conversation = None
    if lecture_avant:
        debut = (datetime.now(PARIS) + timedelta(days=1)).replace(tzinfo=None)
        db_session.add(Calendar(id="agenda-precedent", summary="Agenda", provider="local"))
        db_session.add(CalendarEvent(
            id="rdv-precedent", calendar_id="agenda-precedent", summary="Lecture réelle fictive",
            start_datetime=debut, end_datetime=debut + timedelta(hours=1), status="confirmed",
        ))
        await db_session.commit()
        premiere = await client.post("/api/chat/send", json={
            "message": "Quels sont mes rendez-vous de demain ?", "calendar_id": "agenda-precedent",
            "include_memory": False, "stream": True,
        })
        assert _texte(premiere, True) == "Lecture terminée."
        conversation = next(e["conversation_id"] for e in _evenements(premiere) if e.get("conversation_id"))

    reponse = await client.post("/api/chat/send", json={
        "message": demande, "conversation_id": conversation,
        "include_memory": False, "stream": stream,
    })
    assert _texte(reponse, stream) == contenu
    messages = (await db_session.execute(select(Message))).scalars().all()
    assert [message.content for message in messages if message.role == "assistant"][-1] == contenu


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["sans_flux", "flux"])
@pytest.mark.parametrize("contenu", [
    "Je ne peux pas lire ton agenda.",
    "Une seule ligne : 14h et 15:00.",
], ids=["sans_horaire", "une_seule_ligne"])
async def test_sans_deux_lignes_horaires_aucune_mention(
    client, db_session, fournisseur, contenu, stream  # noqa: F811
):
    class Modele:
        async def stream(self, *args, **kwargs):
            yield StreamEvent(type="text", content=contenu)
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    reponse = await client.post("/api/chat/send", json={
        "message": "Mes rendez-vous de demain ?", "include_memory": False, "stream": stream,
    })
    assert _texte(reponse, stream) == contenu
    messages = (await db_session.execute(select(Message))).scalars().all()
    assert [message.content for message in messages if message.role == "assistant"] == [contenu]


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["sans_flux", "flux"])
@pytest.mark.parametrize("demande", [
    "Montre mon agenda.",
    "Explique comment lire mon agenda demain.",
    "Demain, configure mon planning.",
    "Affiche le calendrier des formations demain.",
    "Comment utiliser mon agenda demain ?",
    "Raconte-moi comment fonctionne mon planning lundi.",
    "Crée deux événements dans mon agenda demain.",
    "Ajoute demain 14 h et 16 h à mon planning.",
], ids=["sans_repere_temporel", "explication", "configuration", "calendrier_non_personnel",
        "utilisation", "fonctionnement", "creation", "ajout"])
async def test_sans_lecture_explicite_et_repere_aucune_mention(
    client, fournisseur, demande, stream  # noqa: F811
):
    contenu = "- 14h : Exemple A\n- 15 h 30 : Exemple B"

    class Modele:
        async def stream(self, *args, **kwargs):
            yield StreamEvent(type="text", content=contenu)
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    reponse = await client.post("/api/chat/send", json={
        "message": demande, "include_memory": False, "stream": stream,
    })
    assert _texte(reponse, stream) == contenu


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["sans_flux", "flux"])
@pytest.mark.parametrize("demande", [
    "Mon agenda à 14 h 30 ?",
    "Mon planning le 16 décembre ?",
    "2027-02-10 : mes rendez-vous ?",
], ids=["heure", "date_en_lettres", "date_iso"])
async def test_reperes_temporels_explicites_declenchent_la_mention(
    client, fournisseur, demande, stream  # noqa: F811
):
    contenu = "- 14h : Exemple A\n- 15:00 : Exemple B"

    class Modele:
        async def stream(self, *args, **kwargs):
            yield StreamEvent(type="text", content=contenu)
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    reponse = await client.post("/api/chat/send", json={
        "message": demande, "include_memory": False, "stream": stream,
    })
    assert _texte(reponse, stream) == contenu + "\n\n" + MENTION


@pytest.mark.asyncio
async def test_skill_fichier_explicite_recoit_le_texte_du_modele(client, fournisseur, monkeypatch):  # noqa: F811
    from app.services import skills

    contenu = "# Document\n\nTexte du modèle pour le document."

    class Modele:
        async def stream(self, *args, **kwargs):
            yield StreamEvent(type="text", content=contenu)
            yield StreamEvent(type="done", stop_reason="end_turn")

    registre = SimpleNamespace(
        get=lambda _id: SimpleNamespace(output_type=SimpleNamespace(value="file"),
                                        output_format=SimpleNamespace(value="docx")),
        execute=AsyncMock(return_value=SimpleNamespace(success=True, file_id="fictif",
                          file_name="fictif.docx", file_size=10, download_url="/fictif")),
        output_dir=".",
    )
    monkeypatch.setattr(skills, "get_skills_registry", lambda: registre)
    fournisseur[0]._provider = Modele()
    reponse = await client.post("/api/chat/send", json={
        "message": "Rédige le document de mes rendez-vous de demain.",
        "skill_id": "docx-pro", "include_memory": False, "stream": True,
    })
    assert _texte(reponse, True) == contenu
    registre.execute.assert_awaited_once()
    assert registre.execute.await_args.args[2] == contenu
    assert any(e["type"] == "skill_file" for e in _evenements(reponse))


@pytest.mark.asyncio
async def test_lecture_effective_conserve_le_texte_avant_et_apres_outil(
    client, db_session, fournisseur  # noqa: F811
):
    debut = (datetime.now(PARIS) + timedelta(days=1)).replace(tzinfo=None)
    db_session.add(Calendar(id="agenda-outil", summary="Agenda", provider="local"))
    db_session.add(CalendarEvent(
        id="rdv-outil", calendar_id="agenda-outil", summary="Événement vérifié",
        start_datetime=debut, end_datetime=debut + timedelta(hours=1), status="confirmed",
    ))
    await db_session.commit()

    class Modele:
        async def stream(self, *args, **kwargs):
            yield StreamEvent(type="text", content="Événement inventé avant outil. ")
            yield StreamEvent(type="tool_call", tool_call=ToolCall(
                id="lecture", name="list_calendar_events", arguments={"days": 7},
            ))
            yield StreamEvent(type="done", stop_reason="tool_calls")

        async def continue_with_tool_results(self, *args, **kwargs):
            yield StreamEvent(type="text", content="Événement inventé après outil.")
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    reponse = await client.post("/api/chat/send", json={
        "message": "Que se passe-t-il jeudi ?", "calendar_id": "agenda-outil",
        "include_memory": False, "stream": True,
    })
    texte = _texte(reponse, True)
    assert "Événement inventé avant outil. " in texte
    assert "Événement inventé après outil." in texte
    messages = (await db_session.execute(select(Message))).scalars().all()
    assert [message.content for message in messages if message.role == "assistant"] == [texte]


@pytest.mark.asyncio
async def test_une_question_sur_le_fonctionnement_de_l_agenda_reste_possible(
    client, fournisseur  # noqa: F811
):
    class ModeleExplicatif:
        async def stream(self, *args, **kwargs):
            yield StreamEvent(type="text", content="Ouvre Agenda et lance la synchronisation.")
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = ModeleExplicatif()
    reponse = await client.post("/api/chat/send", json={
        "message": "Comment synchroniser mon agenda ?",
        "include_memory": False, "stream": True,
    })
    evenements = [json.loads(ligne.removeprefix("data: "))
                  for ligne in reponse.text.splitlines() if ligne.startswith("data: ")]
    texte = "".join(e.get("content", "") for e in evenements if e["type"] == "text")
    assert "Ouvre Agenda et lance la synchronisation." in texte


@pytest.mark.asyncio
@pytest.mark.parametrize("avec_skill", [False, True], ids=["conversation", "skill_fichier"])
async def test_lecture_puis_mail_preserve_le_flux_et_le_message_enregistre(
    client, db_session, fournisseur, monkeypatch, avec_skill  # noqa: F811
):
    from app.services import skills

    debut = (datetime.now(PARIS) + timedelta(days=1)).replace(tzinfo=None)
    db_session.add(Calendar(id="agenda-mail", summary="Agenda", provider="local"))
    db_session.add(CalendarEvent(
        id="rdv-mail", calendar_id="agenda-mail", summary="Entretien avec Paul",
        start_datetime=debut, end_datetime=debut + timedelta(hours=1), status="confirmed",
    ))
    await db_session.commit()
    preambule = "Je consulte ton agenda.\n\n"
    mail = "Bonjour Paul,\n\nJe te confirme notre entretien.\n\nÀ bientôt."

    class Modele:
        async def stream(self, _system, _messages, tools=None, **_kwargs):
            assert "list_calendar_events" in {outil["function"]["name"] for outil in tools}
            yield StreamEvent(type="text", content=preambule)
            yield StreamEvent(type="tool_call", tool_call=ToolCall(
                id="lecture-mail", name="list_calendar_events", arguments={"days": 7},
            ))
            yield StreamEvent(type="done", stop_reason="tool_calls")

        async def continue_with_tool_results(self, *args, **kwargs):
            assert "Entretien avec Paul" in str(args[4][0].result)
            yield StreamEvent(type="text", content=mail[:20])
            yield StreamEvent(type="text", content=mail[20:])
            yield StreamEvent(type="done", stop_reason="end_turn")

    registre = SimpleNamespace(
        get=lambda _id: SimpleNamespace(output_type=SimpleNamespace(value="file"),
                                        output_format=SimpleNamespace(value="docx")),
        execute=AsyncMock(return_value=SimpleNamespace(success=True, file_id="fictif",
                          file_name="fictif.docx", file_size=10, download_url="/fictif")),
        output_dir=".",
    )
    monkeypatch.setattr(skills, "get_skills_registry", lambda: registre)
    fournisseur[0]._provider = Modele()
    demande = {
        "message": "Lis mon agenda de demain et rédige un mail à Paul",
        "calendar_id": "agenda-mail", "include_memory": False, "stream": True,
    }
    if avec_skill:
        demande["skill_id"] = "docx-pro"
    reponse = await client.post("/api/chat/send", json=demande)
    texte = _texte(reponse, True)
    assert texte == preambule + mail
    assert MENTION not in texte
    messages = (await db_session.execute(select(Message))).scalars().all()
    assert [message.content for message in messages if message.role == "assistant"] == [texte]
    if avec_skill:
        registre.execute.assert_awaited_once()
        assert registre.execute.await_args.args[2] == preambule + mail


@pytest.mark.asyncio
async def test_apres_lecture_la_presentation_du_second_outil_est_conservee(
    client, db_session, fournisseur, monkeypatch  # noqa: F811
):
    from app.routers import chat
    from app.services import workspace_tools

    db_session.add(Calendar(id="agenda-deux-outils", summary="Agenda", provider="local"))
    await db_session.commit()
    disponibles = workspace_tools.outils_workspace_disponibles
    executer = chat.execute_workspace_tool

    async def offrir_second_outil(session, outils):
        resultat = await disponibles(session, outils)
        resultat.append(next(outil for outil in outils if outil["function"]["name"] == "search_emails"))
        return resultat

    async def executer_second_outil(nom, arguments, session, **kwargs):
        if nom == "search_emails":
            return "Courrier fictif trouvé."
        return await executer(nom, arguments, session, **kwargs)

    monkeypatch.setattr(workspace_tools, "outils_workspace_disponibles", offrir_second_outil)
    monkeypatch.setattr(chat, "execute_workspace_tool", executer_second_outil)

    class Modele:
        continuations = 0

        async def stream(self, _system, _messages, tools=None, **_kwargs):
            yield StreamEvent(type="tool_call", tool_call=ToolCall(
                id="agenda", name="list_calendar_events", arguments={"days": 7},
            ))
            yield StreamEvent(type="done", stop_reason="tool_calls")

        async def continue_with_tool_results(self, *args, **kwargs):
            self.continuations += 1
            if self.continuations == 1:
                yield StreamEvent(type="text", content="Je cherche maintenant le courrier. ")
                yield StreamEvent(type="tool_call", tool_call=ToolCall(
                    id="courrier", name="search_emails", arguments={"query": "fictif"},
                ))
                yield StreamEvent(type="done", stop_reason="tool_calls")
            else:
                yield StreamEvent(type="text", content="Courrier trouvé.")
                yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    reponse = await client.post("/api/chat/send", json={
        "message": "Lis mon agenda de demain et cherche le courrier.",
        "calendar_id": "agenda-deux-outils", "include_memory": False, "stream": True,
    })
    texte = _texte(reponse, True)
    assert texte == "Je cherche maintenant le courrier. Courrier trouvé."
    messages = (await db_session.execute(select(Message))).scalars().all()
    assert [message.content for message in messages if message.role == "assistant"] == [texte]


@pytest.mark.asyncio
async def test_sans_flux_le_tableau_markdown_est_converti_et_enregistre(
    client, db_session, fournisseur  # noqa: F811
):
    tableau = "Récapitulatif :\n| Sujet | Valeur |\n| --- | --- |\n| Exemple | Texte |"
    attendu = "Récapitulatif :\n- Sujet : Exemple | Valeur : Texte"

    class Modele:
        async def stream(self, *args, **kwargs):
            yield StreamEvent(type="text", content=tableau)
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    reponse = await client.post("/api/chat/send", json={
        "message": "Résume les données.", "include_memory": False, "stream": False,
    })
    assert _texte(reponse, False) == attendu
    messages = (await db_session.execute(select(Message))).scalars().all()
    assert [message.content for message in messages if message.role == "assistant"] == [attendu]


@pytest.mark.asyncio
@pytest.mark.parametrize("echec", [False, True], ids=["lecture", "erreur_outil"])
async def test_apres_appel_de_lecture_aucune_mention(
    client, db_session, fournisseur, monkeypatch, echec  # noqa: F811
):
    from app.routers import chat

    db_session.add(Calendar(id="agenda-sans-mention", summary="Agenda", provider="local"))
    await db_session.commit()
    contenu = "- 14h : Premier événement\n- 15h : Second événement"
    executer = chat.execute_workspace_tool

    async def executer_lecture(nom, arguments, session, **kwargs):
        if echec and nom == "list_calendar_events":
            raise RuntimeError("Erreur d'agenda fictive")
        return await executer(nom, arguments, session, **kwargs)

    monkeypatch.setattr(chat, "execute_workspace_tool", executer_lecture)

    class Modele:
        async def stream(self, _system, _messages, tools=None, **_kwargs):
            yield StreamEvent(type="tool_call", tool_call=ToolCall(
                id="lecture", name="list_calendar_events", arguments={"days": 7},
            ))
            yield StreamEvent(type="done", stop_reason="tool_calls")

        async def continue_with_tool_results(self, *args, **kwargs):
            assert args[4] and args[4][0].is_error is echec
            yield StreamEvent(type="text", content=contenu)
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    reponse = await client.post("/api/chat/send", json={
        "message": "Lis mon agenda de demain.", "calendar_id": "agenda-sans-mention",
        "include_memory": False, "stream": True,
    })
    texte = _texte(reponse, True)
    assert texte == contenu
    assert MENTION not in texte
    messages = (await db_session.execute(select(Message))).scalars().all()
    assert [message.content for message in messages if message.role == "assistant"] == [texte]
