"""B-345 (05/09/2026) : une pièce en franchise de TVA (art. 293 B du CGI) doit
porter les mêmes montants partout.

Constat X01-01 de la campagne de robustesse du cycle 3 : une facture créée
avec `tva_applicable=false` et une ligne à 20 % valait 120 EUR en base, dans
la liste et dans l'encours, pendant que le PDF remis au client imprimait
« Total TTC 100,00 € ». `_montants_de_ligne` appliquait le taux de la ligne
sans regarder l'exonération, attribut de la PIÈCE que seul le PDF consultait.
Le PDF est la pièce juridique : ce sont la base et l'encours qui mentaient.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from httpx import AsyncClient


async def _contact(client: AsyncClient) -> str:
    reponse = await client.post(
        "/api/memory/contacts",
        json={"first_name": "Franchise", "last_name": "Test", "email": "franchise@test.fr"},
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["id"]


@pytest.mark.asyncio
async def test_une_facture_en_franchise_de_tva_ne_porte_aucune_taxe(client: AsyncClient):
    contact_id = await _contact(client)
    reponse = await client.post(
        "/api/invoices/",
        json={
            "contact_id": contact_id,
            "document_type": "facture",
            "tva_applicable": False,
            "lines": [
                {"description": "Conseil", "quantity": 1.0, "unit_price_ht": 100.0, "tva_rate": 20.0}
            ],
        },
    )
    assert reponse.status_code == 200, reponse.text[:300]
    piece = reponse.json()

    assert piece["subtotal_ht"] == 100.0
    assert piece["total_tax"] == 0.0, "une pièce en franchise ne collecte aucune TVA"
    assert piece["total_ttc"] == 100.0, (
        "le TTC stocké doit être celui du PDF (100,00 €), pas 120"
    )
    assert piece["lines"][0]["total_ttc"] == 100.0

    # Le montant relu par la liste est le même que celui de la création
    liste = await client.get("/api/invoices/")
    assert liste.status_code == 200
    relue = next(p for p in liste.json() if p["id"] == piece["id"])
    assert relue["total_ttc"] == 100.0


@pytest.mark.asyncio
async def test_la_mise_a_jour_des_lignes_respecte_aussi_la_franchise(client: AsyncClient):
    contact_id = await _contact(client)
    creation = await client.post(
        "/api/invoices/",
        json={
            "contact_id": contact_id,
            "document_type": "facture",
            "tva_applicable": False,
            "lines": [
                {"description": "Conseil", "quantity": 1.0, "unit_price_ht": 100.0, "tva_rate": 20.0}
            ],
        },
    )
    assert creation.status_code == 200, creation.text[:300]
    piece_id = creation.json()["id"]

    maj = await client.put(
        f"/api/invoices/{piece_id}",
        json={
            "lines": [
                {"description": "Conseil", "quantity": 2.0, "unit_price_ht": 100.0, "tva_rate": 20.0}
            ]
        },
    )
    assert maj.status_code == 200, maj.text[:300]
    assert maj.json()["total_tax"] == 0.0
    assert maj.json()["total_ttc"] == 200.0


def _base_avec_pieces(db_path: Path) -> None:
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "CREATE TABLE invoices (id TEXT PRIMARY KEY, invoice_number TEXT, "
            "tva_applicable INTEGER NOT NULL DEFAULT 1, subtotal_ht REAL, total_tax REAL, "
            "total_ttc REAL)"
        )
        conn.execute(
            "CREATE TABLE invoice_lines (id TEXT PRIMARY KEY, invoice_id TEXT, "
            "total_ht REAL, total_ttc REAL)"
        )
        # Pièce en franchise stockée avec une TVA fantôme (le défaut)
        conn.execute("INSERT INTO invoices VALUES ('f1', 'FACT-2026-021', 0, 100.0, 20.0, 120.0)")
        conn.execute("INSERT INTO invoice_lines VALUES ('l1', 'f1', 100.0, 120.0)")
        # Pièce assujettie : ne doit PAS être touchée
        conn.execute("INSERT INTO invoices VALUES ('f2', 'FACT-2026-022', 1, 100.0, 20.0, 120.0)")
        conn.execute("INSERT INTO invoice_lines VALUES ('l2', 'f2', 100.0, 120.0)")
        conn.commit()


def test_les_pieces_deja_stockees_en_franchise_sont_reparees_une_fois(tmp_path: Path):
    """Corriger la source ne répare pas l'historique : les factures déjà
    émises en franchise gardent 120 en base tant qu'on n'y touche pas, et
    l'encours continue de mentir. Réparation idempotente au démarrage."""
    from app.models.database import reparer_totaux_tva_non_applicable

    db_path = tmp_path / "therese.db"
    _base_avec_pieces(db_path)

    with closing(sqlite3.connect(db_path)) as conn:
        reparees = reparer_totaux_tva_non_applicable(conn)
        assert reparees == 1

        assert conn.execute(
            "SELECT subtotal_ht, total_tax, total_ttc FROM invoices WHERE id='f1'"
        ).fetchone() == (100.0, 0.0, 100.0)
        assert conn.execute("SELECT total_ttc FROM invoice_lines WHERE id='l1'").fetchone() == (100.0,)
        # La pièce assujettie est intacte
        assert conn.execute(
            "SELECT total_tax, total_ttc FROM invoices WHERE id='f2'"
        ).fetchone() == (20.0, 120.0)
        assert conn.execute("SELECT total_ttc FROM invoice_lines WHERE id='l2'").fetchone() == (120.0,)

        # Idempotent : un second passage ne touche plus rien
        assert reparer_totaux_tva_non_applicable(conn) == 0


def test_la_reparation_tolere_une_base_sans_table_factures(tmp_path: Path):
    from app.models.database import reparer_totaux_tva_non_applicable

    db_path = tmp_path / "vide.db"
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("CREATE TABLE contacts (id TEXT PRIMARY KEY)")
        conn.commit()
        assert reparer_totaux_tva_non_applicable(conn) == 0
