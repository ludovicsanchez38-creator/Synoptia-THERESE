"""B-1164 (cycle 13) : un participant de rendez-vous suit la règle d'adresse.

B-1150 (0.75) refuse « : » et les formes à plusieurs adresses dans les fiches
contact. Les participants d'un rendez-vous avaient leur propre expression,
qui acceptait « g:a@b.fr », « Nom<a@b.fr> » ou « a@b.fr,c.fr », et la
modification d'un rendez-vous ne vérifiait rien : CalDAV écrit ensuite
`mailto:{participant}` tel quel.
"""

import pytest
from app.models.schemas import CreateEventRequest, UpdateEventRequest
from pydantic import ValidationError

FENETRE = {"summary": "Réunion", "start_datetime": "2026-10-01T10:00:00", "end_datetime": "2026-10-01T11:00:00"}
INVALIDES = ["g:a@b.fr", "Nom<a@b.fr>", "a@b.fr,c.fr", "a@b.fr c@d.fr"]


@pytest.mark.parametrize("participant", INVALIDES)
def test_la_creation_refuse_un_participant_invalide(participant):
    with pytest.raises(ValidationError):
        CreateEventRequest(**FENETRE, attendees=[participant])


@pytest.mark.parametrize("participant", INVALIDES)
def test_la_modification_refuse_un_participant_invalide(participant):
    with pytest.raises(ValidationError):
        UpdateEventRequest(attendees=[participant])


def test_une_adresse_valide_passe_et_est_nettoyee():
    creation = CreateEventRequest(**FENETRE, attendees=["  lea@exemple.fr "])
    modification = UpdateEventRequest(attendees=["lea@exemple.fr"])
    assert creation.attendees == ["lea@exemple.fr"]
    assert modification.attendees == ["lea@exemple.fr"]
