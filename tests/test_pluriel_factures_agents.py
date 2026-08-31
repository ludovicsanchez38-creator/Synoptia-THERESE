"""Finding 8 (revue 30/08) : les agents d'action étiquetaient toute facture en euros.

`number` et `client_name` n'existent pas sur Invoice : une facture USD
sortait « ? | ? | 1000 EUR ».
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.models.entities import Contact, Invoice


@pytest.mark.asyncio
async def test_contexte_agents_porte_la_devise_et_le_client(db_session, monkeypatch):
    contact = Contact(first_name="Maya", last_name="Chen", company="Acme US")
    db_session.add(contact)
    await db_session.flush()
    db_session.add(
        Invoice(
            invoice_number="FACT-2026-009",
            contact_id=contact.id,
            document_type="facture",
            currency="USD",
            due_date=datetime.now(UTC) + timedelta(days=30),
            status="sent",
            total_ttc=1000.0,
        )
    )
    await db_session.commit()

    class _Session:
        async def __aenter__(self):
            return db_session

        async def __aexit__(self, *_a):
            return False

    monkeypatch.setattr(
        "app.models.database.get_session_context", lambda: _Session()
    )

    from app.services.action_agents import _gather_local_context

    contexte = await _gather_local_context(["invoices"])
    assert "FACT-2026-009" in contexte
    assert "USD" in contexte
    assert "EUR" not in contexte.split("FACT-2026-009")[1].split("\n")[0]
    assert "Maya Chen" in contexte or "Acme US" in contexte
    assert "?" not in contexte.split("FACT-2026-009")[1].split("\n")[0]
