"""B-799 (cycle 9) : `tm.snippet or tm.body_plain[:200]` levait TypeError quand
snippet était vide et body_plain None ; l'exception avalée faisait perdre en
silence tout le contexte du fil."""
from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from app.routers.email import ligne_de_contexte_du_fil


def _message(**champs):
    base = dict(
        date=datetime(2026, 9, 15, 10, 0, tzinfo=UTC), from_name="Camille", from_email="camille@example.fr",
        subject="Contrat", snippet=None, body_plain=None,
    )
    base.update(champs)
    return SimpleNamespace(**base)


def test_sans_extrait_ni_corps_texte_le_fil_garde_sa_ligne() -> None:
    lignes = ligne_de_contexte_du_fil(_message())
    assert lignes[0] == "[2026-09-15 10:00] De: Camille"
    assert lignes[1] == "Sujet: Contrat"
    assert lignes[2] == ""


def test_le_corps_texte_est_tronque_a_200_caracteres() -> None:
    lignes = ligne_de_contexte_du_fil(_message(body_plain="x" * 500))
    assert lignes[2] == "x" * 200


def test_l_extrait_prime_sur_le_corps() -> None:
    assert ligne_de_contexte_du_fil(_message(snippet="résumé", body_plain="corps"))[2] == "résumé"


def test_sans_date_la_ligne_reste_lisible() -> None:
    """B-820 (cycle 9) : `tm.date.strftime` sans garde sur une date absente."""
    lignes = ligne_de_contexte_du_fil(_message(date=None))
    assert lignes[0] == "[date inconnue] De: Camille"
