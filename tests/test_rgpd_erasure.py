"""US-003 (RGPD-1) : l'anonymisation d'un contact (droit à l'oubli, art. 17)
doit aussi effacer ses emails liés. Ils restaient en base avec le contact_id,
contenu intégral inclus — effacement incomplet."""
from datetime import UTC, datetime

import pytest
from app.models.entities import Contact, EmailAccount, EmailMessage
from sqlmodel import select


@pytest.mark.asyncio
async def test_anonymisation_efface_les_emails_du_contact(client, db_session):
    db_session.add(EmailAccount(id="acc1", email="me@x.fr", provider="gmail"))
    db_session.add(Contact(id="c1", first_name="Jean", last_name="Test", email="jean@x.fr"))
    db_session.add(
        EmailMessage(
            id="m1",
            thread_id="t1",
            account_id="acc1",
            from_email="jean@x.fr",
            to_emails='["me@x.fr"]',
            date=datetime.now(UTC),
            internal_date=datetime.now(UTC),
            labels='["INBOX"]',
            contact_id="c1",
            subject="Confidentiel",
            body_plain="contenu personnel à effacer",
        )
    )
    await db_session.commit()

    resp = await client.post("/api/rgpd/anonymize/c1", json={"reason": "demande client"})
    assert resp.status_code == 200

    remaining = (
        await db_session.execute(
            select(EmailMessage).where(EmailMessage.contact_id == "c1")
        )
    ).scalars().all()
    assert remaining == []


@pytest.mark.asyncio
async def test_purge_vecteur_retente_apres_echec_transitoire(monkeypatch):
    """RGPD-2 : une panne transitoire de Qdrant ne doit pas laisser un vecteur
    fantôme (recherche sémantique). On retente avant d'abandonner."""
    from app.services import rgpd_auto

    calls = {"n": 0}

    class _FlakyQdrant:
        async def async_delete_by_entity(self, _cid):
            calls["n"] += 1
            if calls["n"] < 2:
                raise RuntimeError("Qdrant momentanément indisponible")
            return 1

    monkeypatch.setattr(
        "app.services.qdrant.get_qdrant_service", lambda: _FlakyQdrant()
    )

    purged = await rgpd_auto.purge_contact_vector("c1")
    assert purged == 1
    assert calls["n"] == 2
