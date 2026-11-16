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
