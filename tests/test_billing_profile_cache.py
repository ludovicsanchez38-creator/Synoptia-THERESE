"""Recette Ludo 16/07/2026 : profil chiffré = carte facturation mensongère.

Le préchargement au démarrage n'a pas le droit de déchiffrer
(allow_decrypt=False, trousseau), donc le cache profil restait vide et
billing_complete répondait False alors que le profil en base était complet.
Correctifs : cache auto-réparé à toute lecture réussie + lecture de secours
en session dans les statuts dashboard et facturation.
"""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services.user_profile import (
    get_cached_profile,
    get_user_profile,
    set_cached_profile,
)

BACKEND = Path(__file__).parent.parent / "src" / "backend" / "app"


@pytest.fixture(autouse=True)
def _cache_vierge():
    set_cached_profile(None)
    yield
    set_cached_profile(None)


class TestCacheAutoRepare:
    async def test_lecture_reussie_repare_le_cache(self):
        """Une lecture en session doit repeupler le cache process."""
        pref = SimpleNamespace(
            value=json.dumps(
                {
                    "name": "Ludovic Sanchez",
                    "company": "Synoptïa",
                    "address": "294 Montée des Genêts 04100 Manosque",
                    "siret": "99160678100011",
                }
            )
        )
        result = SimpleNamespace(scalar_one_or_none=lambda: pref)
        session = SimpleNamespace(execute=AsyncMock(return_value=result))

        assert get_cached_profile() is None
        profile = await get_user_profile(session)

        assert profile is not None
        assert profile.is_billing_complete()
        assert get_cached_profile() is not None
        assert get_cached_profile().siret == "99160678100011"


class TestFallbackSessionDansLesStatuts:
    def test_dashboard_setup_status_a_la_lecture_de_secours(self):
        code = (BACKEND / "routers" / "dashboard.py").read_text(encoding="utf-8")
        assert "get_user_profile(session)" in code, (
            "setup-status doit lire le profil en session quand le cache est vide"
        )

    def test_billing_profile_status_a_la_lecture_de_secours(self):
        code = (BACKEND / "routers" / "invoices.py").read_text(encoding="utf-8")
        assert "get_user_profile(session)" in code, (
            "billing/profile-status doit lire le profil en session quand le cache est vide"
        )
