"""B-572 (05/09/2026) : « Relance clients » ne voyait pas les vraies créances.

Le contexte `invoices` des actions prenait les quinze factures les plus
récemment CRÉÉES, sans filtre de statut ni d'échéance. Dès que quinze
documents (brouillons compris) suivaient une facture en retard, celle-ci
sortait de la fenêtre et le modèle ne pouvait ni la relancer ni la citer.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.services.action_agents import _gather_local_context


async def _seme_des_factures() -> None:
    from app.models import database as db_module
    from app.models.entities import Contact, Invoice

    async with db_module.AsyncSessionLocal() as session:
        claire = Contact(first_name="Claire", last_name="Roux")
        session.add(claire)
        await session.flush()
        maintenant = datetime.now(UTC)
        session.add(
            Invoice(
                invoice_number="FACT-2026-002",
                contact_id=claire.id,
                issue_date=maintenant - timedelta(days=40),
                due_date=maintenant - timedelta(days=10),
                status="overdue",
                total_ttc=1440.0,
                created_at=maintenant - timedelta(days=40),
            )
        )
        for i in range(16):
            session.add(
                Invoice(
                    invoice_number=f"DEV-2026-{100 + i}",
                    contact_id=claire.id,
                    document_type="devis",
                    issue_date=maintenant,
                    due_date=maintenant + timedelta(days=30),
                    status="draft",
                    total_ttc=10.0,
                    created_at=maintenant - timedelta(minutes=16 - i),
                )
            )
        await session.commit()


@pytest.mark.asyncio
async def test_une_facture_en_retard_ancienne_reste_visible(client):
    await _seme_des_factures()

    contexte = await _gather_local_context(["invoices"])

    assert "## Factures" in contexte, contexte
    assert "FACT-2026-002" in contexte, contexte
    assert "Claire Roux" in contexte
