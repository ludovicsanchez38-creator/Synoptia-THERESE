"""B-1624 (régression de B-1431) : sans agenda, la carte de confirmation d'un
rendez-vous ne prévenait plus qu'un agenda serait créé. B-1431 avait réécrit
le message (« Aucun agenda configuré ») mais la destination cherchait encore
l'ancien texte (« Aucun calendrier configure ») : « Destination à vérifier »,
alors que la confirmation crée bien « Mon calendrier ».
"""

import pytest


@pytest.mark.asyncio
async def test_sans_agenda_la_destination_annonce_mon_calendrier(db_session):
    from app.services.workspace_tools import get_calendar_confirmation_destination

    destination = await get_calendar_confirmation_destination(db_session)

    assert destination["will_create_calendar"] is True, destination
    assert destination["calendar_name"] == "Mon calendrier"
