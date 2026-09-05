"""B-334 et B-352 (05/09/2026) : deux routeurs jamais rattachés à la
frontière d'erreurs de la 0.48.

La génération du PDF de facture (invoices.py) et dix sites du routeur
agenda (calendar.py) recopiaient `str(e)` dans le `detail` HTTP, et
`http_exception_handler` (main.py) renvoie ce détail tel quel à l'écran :
une exception ReportLab avec ses adresses mémoire, un chemin de poste, un
fragment de clé, tout atteignait l'utilisateur. RULES-DESIGN.md:393-396 :
à la limite de l'écran, seuls les messages localisés passent.
"""

from __future__ import annotations

import inspect

import pytest


def test_les_routeurs_facturation_et_agenda_ne_recopient_plus_str_e():
    from app.routers import calendar as calendar_router
    from app.routers import invoices as invoices_router

    for module in (calendar_router, invoices_router):
        source = inspect.getsource(module)
        assert "detail=str(e)" not in source, module.__name__
        assert "{str(e)}" not in source, module.__name__
        assert "message_pour_ecran" in source, f"{module.__name__} n'est pas rattaché à la frontière"


async def _profil_complet(client) -> None:
    reponse = await client.post(
        "/api/config/profile",
        json={
            "name": "Marie Exemple",
            "company": "Atelier Exemple",
            "address": "1 rue des Lices, 04100 Manosque",
            "siret": "12345678900011",
        },
    )
    assert reponse.status_code == 200, reponse.text


@pytest.mark.asyncio
async def test_une_panne_du_generateur_pdf_ne_fuit_pas_a_l_ecran(client, monkeypatch):
    from app.routers import invoices as module

    await _profil_complet(client)
    contact = await client.post(
        "/api/memory/contacts",
        json={"first_name": "Paul", "last_name": "Durand", "email": "paul@durand.test"},
    )
    assert contact.status_code == 200, contact.text
    piece = await client.post(
        "/api/invoices/",
        json={
            "contact_id": contact.json()["id"],
            "document_type": "facture",
            "lines": [{"description": "Conseil", "quantity": 1, "unit_price_ht": 100, "tva_rate": 20}],
        },
    )
    assert piece.status_code == 200, piece.text

    def generateur_qui_crash(self, **kwargs):
        raise RuntimeError("Reportlab <Frame at 0x1049f3d10> /Users/ludo/secret sk-abc")

    monkeypatch.setattr(module.InvoicePDFGenerator, "generate_invoice_pdf", generateur_qui_crash)

    reponse = await client.get(f"/api/invoices/{piece.json()['id']}/pdf")

    assert reponse.status_code == 500
    corps = reponse.text
    for brut in ("0x1049f3d10", "/Users/ludo", "sk-abc", "RuntimeError"):
        assert brut not in corps, f"le détail technique « {brut} » atteint l'écran : {corps[:200]}"
    assert "PDF" in corps or "facture" in corps.lower(), corps[:200]
