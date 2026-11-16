"""La réserve d'agenda suit les dates, les heures et la demande du tour."""

import pytest
from app.models.entities import Message
from app.services.providers.base import StreamEvent
from sqlmodel import select

from tests.test_b1797_agenda_sans_outil import MENTION, _texte
from tests.test_r2_3_outil import fournisseur  # noqa: F401

HORAIRES = "- 09h : Réunion fictive\n- 14h : Entretien fictif"


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["sans_flux", "flux"])
@pytest.mark.parametrize(("contenu", "converti", "mention_attendue"), [
    (
        "- 09:00 Réunion client\n- 14:00 Entretien",
        "- 09:00 Réunion client\n- 14:00 Entretien",
        True,
    ),
    (
        "- 09h Réunion client\n- 14h Entretien",
        "- 09h Réunion client\n- 14h Entretien",
        True,
    ),
    (
        "- **09:00** Réunion client\n- **14:00** Entretien",
        "- **09:00** Réunion client\n- **14:00** Entretien",
        True,
    ),
    (
        "| Heure | Rendez-vous |\n| --- | --- |\n"
        "| 09:00 | Réunion client |\n| 14:00 | Entretien |",
        "- Heure : 09:00 | Rendez-vous : Réunion client\n"
        "- Heure : 14:00 | Rendez-vous : Entretien",
        True,
    ),
    (
        "| Rendez-vous | Horaire |\n| --- | --- |\n"
        "| Réunion client | 9h |\n| Entretien | 14h |",
        "- Rendez-vous : Réunion client | Horaire : 9h\n"
        "- Rendez-vous : Entretien | Horaire : 14h",
        True,
    ),
    (
        "- 3h30 de préparation\n- 2h15 de trajet",
        "- 3h30 de préparation\n- 2h15 de trajet",
        False,
    ),
    (
        "| Durée | Activité |\n| --- | --- |\n"
        "| 3h | Préparation |\n| 2h | Trajet |",
        "- Durée : 3h | Activité : Préparation\n"
        "- Durée : 2h | Activité : Trajet",
        False,
    ),
], ids=["heures_sans_separateur", "heures_h_sans_separateur", "heures_en_gras",
        "tableau_heure_en_premier", "tableau_heure_en_second", "durees_avec_minutes",
        "tableau_de_durees"])
async def test_horaires_et_tableaux_sans_separateur_conservent_la_reserve(
    client, db_session, fournisseur, contenu, converti, mention_attendue, stream  # noqa: F811
):
    class Modele:
        async def stream(self, *args, **kwargs):
            yield StreamEvent(type="text", content=contenu)
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    reponse = await client.post("/api/chat/send", json={
        "message": "Lis mon agenda de demain", "include_memory": False, "stream": stream,
    })
    attendu = (contenu if stream else converti) + ("\n\n" + MENTION if mention_attendue else "")
    assert _texte(reponse, stream) == attendu
    messages = (await db_session.execute(select(Message))).scalars().all()
    assert [message.content for message in messages if message.role == "assistant"] == [attendu]


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["sans_flux", "flux"])
@pytest.mark.parametrize(("demande", "mention_attendue"), [
    ("Explique comment je consulte mon agenda demain", False),
    ("Rédige un résumé de la liste de mes rendez-vous de demain", False),
    ("Rédige une liste de mes rendez-vous demain", False),
    ("Rédige une longue liste de mes rendez-vous de demain", False),
    ("Explique comment, demain, je consulte mon agenda et rédige un mail", False),
    ("Explique comment j'ai consulté mon agenda lundi", False),
    ("Explique comment Marie consulte mon agenda demain", False),
    ("Explique comment, demain, Marie consulte mon agenda", False),
    ("Explique comment je consulte mon agenda demain, puis lis mon agenda demain", True),
    ("Rédige une liste, puis consulte mon agenda demain", True),
    ("Rédige un mail, puis liste mes rendez-vous de demain", True),
    ("Rédige une note puis liste mes rendez-vous de demain", True),
    ("Consulte mon agenda demain et explique comment je consulte mon agenda", True),
    ("D'abord consulte mon agenda demain et rédige un mail", True),
    ("Pour demain lis mon agenda puis rédige un mail", True),
    ("Après avoir consulté mon agenda demain, rédige un mail", True),
    ("Rédige un mail après avoir consulté mon agenda demain", True),
    ("S'il te plaît consulte mon agenda demain et rédige un mail", True),
], ids=["explication_je", "liste_nominale", "liste_a_rediger", "liste_avec_adjectif",
        "explication_et_redaction", "explication_passee", "explication_tiers",
        "explication_tiers_avec_incise", "explication_puis_lecture", "redaction_puis_lecture",
        "redaction_puis_liste", "redaction_note_puis_liste", "lecture_puis_explication",
        "lecture_d_abord", "lecture_apres_repere", "lecture_prealable", "lecture_avant_redaction",
        "lecture_politesse"])
async def test_explication_ou_redaction_seule_ne_demande_pas_la_lecture(
    client, db_session, fournisseur, demande, mention_attendue, stream  # noqa: F811
):
    class Modele:
        async def stream(self, *args, **kwargs):
            yield StreamEvent(type="text", content=HORAIRES)
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    reponse = await client.post("/api/chat/send", json={
        "message": demande, "include_memory": False, "stream": stream,
    })
    attendu = HORAIRES + ("\n\n" + MENTION if mention_attendue else "")
    assert _texte(reponse, stream) == attendu
    messages = (await db_session.execute(select(Message))).scalars().all()
    assert [message.content for message in messages if message.role == "assistant"] == [attendu]


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["sans_flux", "flux"])
@pytest.mark.parametrize(("demande", "contenu", "mention_attendue"), [
    ("Mon agenda, point 1.2", HORAIRES, False),
    ("Mon agenda, point 2.10", HORAIRES, False),
    ("Mon agenda au 32/13/2026 ?", HORAIRES, False),
    ("Mon agenda au 2026-02-31 ?", HORAIRES, False),
    ("Lis mon agenda de demain", "- 3h de préparation\n- 2h de trajet", False),
    ("Lis mon agenda de demain", "- 3h\n- 2h", False),
    ("Lis mon agenda de demain et rédige un mail", HORAIRES, True),
    ("Rédige un mail, puis consulte mon planning de lundi", HORAIRES, True),
    ("Peux-tu lire mon agenda demain et rédiger un mail ?", HORAIRES, True),
    ("Explique comment lire mon agenda demain et rédige un mail", HORAIRES, False),
    ("Rédige un mail pour mon agenda de demain", HORAIRES, False),
    ("Mon agenda du 01/12/2026 ?", HORAIRES, True),
    ("Mon agenda du 01.12.2026 ?", HORAIRES, True),
    ("Mon agenda du 2026-12-01 ?", HORAIRES, True),
    ("Lis mon agenda de demain", "- Départ à 3h\n- Retour à 2h", True),
    ("Lis mon agenda de demain", "- À 14h, trajet de 3h\n- À 16h, séance de 2h", True),
], ids=[
    "point_decimal", "point_decimal_deux_chiffres", "date_invalide", "date_iso_invalide",
    "durees", "durees_seules", "lecture_puis_redaction", "redaction_puis_lecture",
    "lire_puis_rediger", "explication_et_redaction", "redaction_seule",
    "date_barres", "date_points", "date_iso", "heures_a",
    "horaires_et_durees",
])
async def test_la_mention_suit_les_reperes_reels_et_la_lecture_demandee(
    client, db_session, fournisseur, demande, contenu, mention_attendue, stream  # noqa: F811
):
    class Modele:
        async def stream(self, *args, **kwargs):
            yield StreamEvent(type="text", content=contenu)
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    reponse = await client.post("/api/chat/send", json={
        "message": demande, "include_memory": False, "stream": stream,
    })
    attendu = contenu + ("\n\n" + MENTION if mention_attendue else "")
    assert _texte(reponse, stream) == attendu
    messages = (await db_session.execute(select(Message))).scalars().all()
    assert [message.content for message in messages if message.role == "assistant"] == [attendu]
