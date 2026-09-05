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
                    "name": "Camille Exemple",
                    "company": "Exemple SARL",
                    "address": "12 rue de l'Exemple 04100 Manosque",
                    "siret": "12345678900010",
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
        assert get_cached_profile().siret == "12345678900010"


class TestFallbackSessionDansLesStatuts:
    """B-387 / B-411 (05/09/2026) : ces deux verrous cherchaient la chaîne
    « get_user_profile(session) » dans le source. Un appel commenté ou placé
    sous `if False:` les laissait verts. Ils exercent désormais les routes,
    cache vidé, comme le fait tests/test_lot7_mecaniques.py."""

    @pytest.mark.asyncio
    async def test_dashboard_setup_status_a_la_lecture_de_secours(self, client):
        from app.models import database as db_module
        from app.services.user_profile import UserProfile, set_cached_profile, set_user_profile

        async with db_module.AsyncSessionLocal() as session:
            await set_user_profile(
                session, UserProfile(name="Marie", company="Atelier", address="Manosque", siret="12345678900011")
            )
        set_cached_profile(None)
        reponse = await client.get("/api/dashboard/setup-status")
        assert reponse.status_code == 200, reponse.text
        assert reponse.json()["billing_complete"] is True

    @pytest.mark.asyncio
    async def test_billing_profile_status_a_la_lecture_de_secours(self, client):
        from app.models import database as db_module
        from app.services.user_profile import UserProfile, set_cached_profile, set_user_profile

        async with db_module.AsyncSessionLocal() as session:
            await set_user_profile(
                session, UserProfile(name="Marie", company="Atelier", address="Manosque", siret="12345678900011")
            )
        set_cached_profile(None)
        reponse = await client.get("/api/invoices/billing/profile-status")
        assert reponse.status_code == 200, reponse.text
        assert reponse.json()["is_complete"] is True
