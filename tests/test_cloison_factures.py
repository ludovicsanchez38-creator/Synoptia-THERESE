"""B-539 (cycle 4) : `execute_workspace_tool` calculait le dossier de la
conversation puis ne le transmettait qu'à l'agenda. Depuis une conversation
rattachée au dossier Martin, une question de trésorerie faisait ressortir les
factures de Ruiz. Les outils de facturation reçoivent désormais le dossier :
seules les pièces du client du dossier sont visibles."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest


async def _deux_clients_factures(db_session):
    from app.models.entities import Contact, Conversation, Invoice, Project

    martin = Contact(first_name="Paul", last_name="Martin", email="martin@exemple.fr")
    ruiz = Contact(first_name="Ana", last_name="Ruiz", email="ruiz@exemple.fr")
    db_session.add_all([martin, ruiz])
    await db_session.flush()
    dossier_martin = Project(name="Dossier Martin", contact_id=martin.id)
    dossier_sans_client = Project(name="Dossier interne")
    db_session.add_all([dossier_martin, dossier_sans_client])
    await db_session.flush()
    maintenant = datetime.now(UTC)
    commun = dict(document_type="facture", status="sent", issue_date=maintenant,
                  due_date=maintenant + timedelta(days=30), subtotal_ht=0, total_tax=0)
    db_session.add_all([
        Invoice(invoice_number="FACT-2026-501", contact_id=martin.id, client_name="Paul Martin", total_ttc=1218.0, **commun),
        Invoice(invoice_number="FACT-2026-502", contact_id=ruiz.id, client_name="Ana Ruiz", total_ttc=4620.0, **commun),
        Conversation(id="conv-martin", title="suivi Martin", memory_scope="project", project_id=dossier_martin.id),
        Conversation(id="conv-interne", title="interne", memory_scope="project", project_id=dossier_sans_client.id),
        Conversation(id="conv-libre", title="libre", memory_scope="global"),
    ])
    await db_session.commit()


@pytest.mark.asyncio
async def test_l_encours_d_une_conversation_rattachee_ne_compte_que_son_client(client, db_session):
    from app.services.workspace_tools import execute_workspace_tool

    await _deux_clients_factures(db_session)
    resultat = await execute_workspace_tool("invoice_totals", {}, db_session, conversation_id="conv-martin")
    texte = json.dumps(json.loads(resultat))
    assert "1218" in texte, resultat
    assert "4620" not in texte, "la facture de Ruiz sort dans le dossier Martin"


@pytest.mark.asyncio
async def test_la_recherche_de_factures_reste_dans_le_dossier(client, db_session):
    from app.services.workspace_tools import execute_workspace_tool

    await _deux_clients_factures(db_session)
    chez_martin = await execute_workspace_tool("search_invoices", {"query": "Ruiz"}, db_session, conversation_id="conv-martin")
    assert "FACT-2026-502" not in chez_martin, chez_martin
    assert "Aucune facture" in chez_martin
    la_sienne = await execute_workspace_tool("search_invoices", {"query": "FACT-2026-501"}, db_session, conversation_id="conv-martin")
    assert "FACT-2026-501" in la_sienne


@pytest.mark.asyncio
async def test_sans_rattachement_tout_reste_visible(client, db_session):
    from app.services.workspace_tools import execute_workspace_tool

    await _deux_clients_factures(db_session)
    texte = json.dumps(json.loads(await execute_workspace_tool("invoice_totals", {}, db_session, conversation_id="conv-libre")))
    assert "1218" in texte and "4620" in texte


@pytest.mark.asyncio
async def test_un_dossier_sans_client_ferme_la_cloison(client, db_session):
    from app.services.workspace_tools import execute_workspace_tool

    await _deux_clients_factures(db_session)
    resultat = await execute_workspace_tool("invoice_totals", {}, db_session, conversation_id="conv-interne")
    assert "aucun client" in resultat.lower(), resultat
    assert "4620" not in resultat and "1218" not in resultat
    recherche = await execute_workspace_tool("search_invoices", {"query": "FACT"}, db_session, conversation_id="conv-interne")
    assert "FACT-2026" not in recherche
