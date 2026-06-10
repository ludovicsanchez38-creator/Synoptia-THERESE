"""US-002 : confirmation humaine avant les outils sensibles (ex. send_email).

Le LLM ne doit pas pouvoir déclencher seul un envoi de mail : l'action est
mise en attente et n'est exécutée qu'après validation explicite de l'utilisateur.
"""
from app.services.tool_confirmations import (
    pop_pending,
    register_pending,
    requires_confirmation,
)


def test_send_email_requiert_une_confirmation():
    assert requires_confirmation("send_email") is True


def test_outils_en_lecture_seule_ne_requierent_pas_de_confirmation():
    assert requires_confirmation("read_emails") is False
    assert requires_confirmation("generate_document") is False
    assert requires_confirmation("search_emails") is False


def test_register_puis_pop_rend_l_action_une_seule_fois():
    cid = register_pending("send_email", {"to": "x@y.fr", "subject": "S", "body": "B"})
    assert isinstance(cid, str) and cid

    action = pop_pending(cid)
    assert action == ("send_email", {"to": "x@y.fr", "subject": "S", "body": "B"})

    # Consommée : un second pop ne rejoue pas l'action (anti-double envoi).
    assert pop_pending(cid) is None


def test_pop_d_un_id_inconnu_retourne_none():
    assert pop_pending("inconnu-xyz") is None
