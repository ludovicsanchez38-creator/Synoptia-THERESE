"""B-200 (P-010, décision de Ludo) : sur la version installée, les clés présentes
dans l'environnement de la machine ne sont plus lues à l'insu de l'utilisateur.
Le repli reste en développement, ou sur demande explicite."""

from __future__ import annotations

import pytest


@pytest.fixture
def cle_openai_dans_l_environnement(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-inconnue-de-l-utilisatrice")
    monkeypatch.delenv("THERESE_LIRE_CLES_ENV", raising=False)


def test_en_developpement_le_repli_reste(monkeypatch, cle_openai_dans_l_environnement):
    from app.config import settings
    from app.services.llm import _cle_depuis_environnement

    monkeypatch.setattr(settings, "therese_env", "development")
    assert _cle_depuis_environnement("openai") == "sk-env-inconnue-de-l-utilisatrice"


def test_sur_la_version_installee_la_cle_d_environnement_est_ignoree(monkeypatch, cle_openai_dans_l_environnement):
    from app.config import settings
    from app.services.llm import _cle_depuis_environnement

    monkeypatch.setattr(settings, "therese_env", "production")
    assert _cle_depuis_environnement("openai") is None


def test_l_utilisateur_peut_retablir_le_repli_explicitement(monkeypatch, cle_openai_dans_l_environnement):
    from app.config import settings
    from app.services.llm import _cle_depuis_environnement

    monkeypatch.setattr(settings, "therese_env", "production")
    monkeypatch.setenv("THERESE_LIRE_CLES_ENV", "1")
    assert _cle_depuis_environnement("openai") == "sk-env-inconnue-de-l-utilisatrice"
