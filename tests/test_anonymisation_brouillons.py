"""B-169 (P-003, décision de Ludo) : après une anonymisation, le nom reste sur les
pièces déjà émises (pièce comptable), mais disparaît des brouillons jamais
envoyés."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select


@pytest.mark.asyncio
async def test_le_nom_reste_sur_la_facture_emise_et_disparait_du_brouillon(client, db_session):
    from app.models.entities import Contact, Invoice

    contact = Contact(first_name="Claire", last_name="Roux", email="claire@exemple.fr")
    db_session.add(contact)
    await db_session.flush()
    maintenant = datetime.now(UTC)
    commun = dict(contact_id=contact.id, document_type="facture", client_name="Claire Roux", client_email="claire@exemple.fr",
                  issue_date=maintenant, due_date=maintenant + timedelta(days=30), subtotal_ht=100.0, total_tax=20.0, total_ttc=120.0)
    emise = Invoice(invoice_number="FACT-2026-900", status="sent", **commun)
    brouillon = Invoice(invoice_number="DEV-2026-900", status="draft", **{**commun, "document_type": "devis"})
    db_session.add_all([emise, brouillon])
    await db_session.commit()

    reponse = await client.post(f"/api/rgpd/anonymize/{contact.id}", json={"reason": "demande du client"})
    assert reponse.status_code == 200, reponse.text

    db_session.expire_all()
    emise_relue = (await db_session.execute(select(Invoice).where(Invoice.invoice_number == "FACT-2026-900"))).scalar_one()
    brouillon_relu = (await db_session.execute(select(Invoice).where(Invoice.invoice_number == "DEV-2026-900"))).scalar_one()
    assert emise_relue.client_name == "Claire Roux", "la pièce émise doit garder son nom (pièce comptable)"
    assert brouillon_relu.client_name == "[ANONYMISÉ]", "le brouillon jamais envoyé garde le nom"
    assert brouillon_relu.client_email is None
