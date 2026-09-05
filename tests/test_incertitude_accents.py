"""B-496 (05/09/2026) : le vocabulaire d'incertitude était écrit sans accents
et comparé par simple `in` sur la réponse en minuscules : « je ne suis pas
sûr » ne rencontrait jamais « je ne suis pas sur ». Une réponse en français
correct passait pour une certitude absolue (score 100, niveau « high »).
"""

from __future__ import annotations

from app.services.token_tracker import detect_uncertainty


def test_une_reponse_en_francais_accentue_est_reconnue_incertaine():
    verdict = detect_uncertainty("Je ne suis pas sûr, peut-être demain, d'après ce que je sais.")

    assert verdict["is_uncertain"] is True
    assert len(verdict["uncertainty_phrases"]) >= 3, verdict
    assert verdict["confidence_level"] != "high"


def test_la_forme_sans_accent_reste_reconnue():
    verdict = detect_uncertainty("je ne suis pas sur, peut-etre demain.")

    assert verdict["is_uncertain"] is True
    assert len(verdict["uncertainty_phrases"]) == 2, verdict


def test_une_reponse_assuree_reste_assuree():
    verdict = detect_uncertainty("Le devis DEV-2026-020 a été créé le 5 septembre.")

    assert verdict["is_uncertain"] is False
    assert verdict["confidence_score"] == 100
