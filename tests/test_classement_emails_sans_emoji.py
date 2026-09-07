"""B-293 (cycle 4) : l'explication du classement d'un e-mail commençait par une
pastille emoji (rouge, orange, verte) construite côté serveur, alors que la
charte du projet proscrit les emoji au profit d'icônes SVG. Le texte garde la
couleur en toutes lettres ; l'écran dessine la pastille."""

from __future__ import annotations

import re
import unicodedata

from app.services.email_classifier import EmailClassifier

EMOJI = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")


def _classer(sujet: str, expediteur: str, labels: list[str] | None = None):
    return EmailClassifier().classify(
        subject=sujet,
        from_email=expediteur,
        snippet="",
        labels=labels or [],
    )


def test_la_raison_ne_commence_par_aucun_emoji():
    for sujet, exp in (
        ("URGENT : facture impayée", "compta@client.fr"),
        ("Newsletter de septembre", "news@promo.example"),
        ("Bonjour", "ami@example.org"),
    ):
        resultat = _classer(sujet, exp)
        assert not EMOJI.search(resultat.reason), resultat.reason
        assert unicodedata.category(resultat.reason[0]).startswith("L"), resultat.reason


def test_la_couleur_reste_en_toutes_lettres():
    haute = _classer("URGENT : relance facture impayée mise en demeure", "compta@client.fr")
    assert haute.reason.startswith(("Rouge", "Orange", "Vert")), haute.reason
