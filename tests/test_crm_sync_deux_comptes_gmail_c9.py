"""B-838 (cycle 9) : `scalar_one_or_none()` hors try sur les comptes Gmail :
deux comptes Gmail avec identifiants faisaient lever MultipleResultsFound au
rafraîchissement du jeton CRM."""
from __future__ import annotations

import pytest
from app.models.entities import EmailAccount, Preference
from app.services import crm_sync


@pytest.mark.asyncio
async def test_deux_comptes_gmail_ne_font_pas_planter_le_rafraichissement(db_session, monkeypatch):
    monkeypatch.setattr(crm_sync, "decrypt_value", lambda v: v, raising=False)
    import app.services.encryption as chiffrement
    monkeypatch.setattr(chiffrement, "decrypt_value", lambda v: v)
    db_session.add(Preference(key=crm_sync.CRM_SHEETS_TOKEN_KEY, value="jeton-actuel"))
    db_session.add(Preference(key=crm_sync.CRM_SHEETS_REFRESH_TOKEN_KEY, value="jeton-de-rafraichissement"))
    for i in (1, 2):
        db_session.add(EmailAccount(email=f"g{i}@example.invalid", provider="gmail", client_id="id", client_secret="secret"))
    await db_session.commit()

    class FauxOAuth:
        async def refresh_access_token(self, *a, **k):
            raise RuntimeError("pas de réseau dans ce test")

    # Relecture U1 (c9) : crm_sync importe get_oauth_service dans le corps de la
    # fonction ; la doublure vit donc sur app.services.oauth, sinon elle est inerte.
    import app.services.oauth as oauth
    monkeypatch.setattr(oauth, "get_oauth_service", lambda: FauxOAuth())

    # Avant la correction : MultipleResultsFound levée avant même d'atteindre le refresh.
    jeton = await crm_sync.ensure_valid_crm_token(db_session)
    assert jeton == "jeton-actuel"
