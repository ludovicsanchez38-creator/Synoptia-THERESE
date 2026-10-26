"""B-1165 : TVA sur base par taux et ventilation du PDF, historique figé."""

from decimal import ROUND_HALF_UP, Decimal

import pytest
from app.models import database as db
from app.models.entities import Invoice
from app.routers.invoices import _get_invoice_with_lines
from pypdf import PdfReader


async def creer(client, lignes, document_type="facture", tva_applicable=True):
    profil = await client.post("/api/config/profile", json={
        "name": "Atelier fictif", "company": "Ventilation", "address": "Paris", "siret": "99988877900009",
    })
    assert profil.status_code == 200, profil.text
    contact = await client.post("/api/memory/contacts", json={"first_name": "TVA", "last_name": "Plusieurs taux"})
    response = await client.post("/api/invoices/", json={
        "contact_id": contact.json()["id"], "document_type": document_type,
        "tva_applicable": tva_applicable, "lines": lignes,
    })
    assert response.status_code == 200, response.text
    return response.json()


def lignes(nombre, prix, taux):
    return [{"description": f"Prestation {i}", "quantity": 1, "unit_price_ht": prix, "tva_rate": taux}
            for i in range(nombre)]


async def texte_pdf(client, identifiant):
    pdf = await client.get(f"/api/invoices/{identifiant}/pdf")
    assert pdf.status_code == 200, pdf.text
    return " ".join(" ".join(page.extract_text() for page in PdfReader(pdf.json()["pdf_path"]).pages).split())


@pytest.mark.asyncio
@pytest.mark.parametrize("nombre,prix,taux,ht,taxe", [(10, 12.34, 5.5, 123.4, 6.79), (12, 0.99, 20, 11.88, 2.38)])
async def test_tva_arrondie_sur_la_base_du_taux(client, nombre, prix, taux, ht, taxe):
    piece = await creer(client, lignes(nombre, prix, taux))
    relue = (await client.get(f"/api/invoices/{piece['id']}")).json()
    assert (relue["subtotal_ht"], relue["total_tax"]) == (ht, taxe)
    assert round(sum(ligne["total_ttc"] for ligne in relue["lines"]), 2) == relue["total_ttc"]


@pytest.mark.asyncio
async def test_pdf_ventile_les_bases_et_taxes_par_taux(client):
    piece = await creer(client, lignes(1, 123.4, 5.5) + lignes(1, 11.88, 20))
    emission = await client.put(f"/api/invoices/{piece['id']}", json={"status": "sent"})
    assert emission.status_code == 200, emission.text
    assert emission.json()["total_ttc"] == 144.45
    texte = await texte_pdf(client, piece["id"])
    assert "Base HT à 5,5 % 123,40" in texte
    assert "TVA à 5,5 % 6,79" in texte
    assert "Base HT à 20,0 % 11,88" in texte
    assert "TVA à 20,0 % 2,38" in texte
    assert "Total TVA 9,17" in texte
    assert "Total TTC 144,45" in texte


@pytest.mark.asyncio
async def test_piece_emise_historique_ne_change_jamais_de_montants(client):
    piece = await creer(client, lignes(10, 12.34, 5.5) + lignes(12, 0.99, 20))
    # État réellement persisté par l'ancien calcul, sans migration.
    async with db.AsyncSessionLocal() as session:
        historique = await _get_invoice_with_lines(session, piece["id"])
        historique.invoice_number = "FACT-2025-042"
        historique.status = "sent"
        historique.subtotal_ht, historique.total_tax, historique.total_ttc = 135.28, 9.2, 144.48
        for ligne in historique.lines:
            ligne.total_ttc = 13.02 if ligne.tva_rate == 5.5 else 1.19
        await session.commit()
    chemin = f"/api/invoices/{piece['id']}"
    avant = (await client.get(chemin)).json()
    texte = await texte_pdf(client, piece["id"])
    assert "Total TVA 9,20" in texte and "Total TTC 144,48" in texte
    assert "TVA à 5,5 % 6,80" in texte and "TVA à 20,0 % 2,40" in texte
    paiement = await client.patch(chemin + "/mark-paid", json={"payment_date": "2026-07-20"})
    assert paiement.status_code == 200, paiement.text
    apres = (await client.get(chemin)).json()
    for champ in ("subtotal_ht", "total_tax", "total_ttc", "lines"):
        assert apres[champ] == avant[champ]
    async with db.AsyncSessionLocal() as session:
        stockee = await session.get(Invoice, piece["id"])
        assert stockee.total_ttc == 144.48


@pytest.mark.asyncio
@pytest.mark.parametrize("groupes,type_document,applicable,attendu", [
    ([(10, 12.34, 5.5), (12, 0.99, 20)], "facture", True, (135.28, 9.17, 144.45)),
    ([(3, 33.33, 20), (1, 10, 5.5)], "devis", True, (109.99, 20.55, 130.54)),
    ([(7, 0.05, 10), (3, 0.01, 20)], "avoir", True, (0.38, 0.05, 0.43)),
    ([(2, 0.25, 2.1), (1, 10, 0)], "facture", True, (10.5, 0.01, 10.51)),
    ([(3, 1.005, 20), (2, 2.675, 5.5)], "devis", True, (8.39, 0.9, 9.29)),
    ([(5, 19.99, 10), (2, 4.99, 5.5)], "avoir", True, (109.93, 10.55, 120.48)),
    ([(4, 0.33, 5.5), (3, 0.27, 2.1)], "facture", True, (2.13, 0.09, 2.22)),
    ([(2, 100.01, 20), (3, 0.99, 0)], "devis", True, (202.99, 40.0, 242.99)),
    ([(10, 12.34, 5.5), (12, 0.99, 20)], "facture", False, (135.28, 0.0, 135.28)),
    ([(10, 12.34, 5.5)], "avoir", True, (123.4, 6.79, 130.19)),
])
async def test_dix_entrees_apres_correctif(client, groupes, type_document, applicable, attendu):
    demandes = [ligne for nombre, prix, taux in groupes for ligne in lignes(nombre, prix, taux)]
    piece = await creer(client, demandes, type_document, applicable)
    chemin = f"/api/invoices/{piece['id']}"
    # Une modification des lignes d'un brouillon applique la même règle.
    retouche = await client.put(chemin, json={"lines": list(reversed(demandes))})
    assert retouche.status_code == 200, retouche.text
    piece = (await client.get(chemin)).json()
    assert tuple(piece[k] for k in ("subtotal_ht", "total_tax", "total_ttc")) == attendu
    assert sum(Decimal(str(ligne["total_ttc"])) for ligne in piece["lines"]) == Decimal(str(attendu[2]))
    # Vérifier chaque groupe indépendamment, après relecture persistée.
    for _, _, taux in groupes:
        groupe = [ligne for ligne in piece["lines"] if ligne["tva_rate"] == taux]
        base = sum(Decimal(str(ligne["total_ht"])) for ligne in groupe)
        taxe = (base * Decimal(str(taux if applicable else 0)) / 100).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
        assert sum(Decimal(str(ligne["total_ttc"])) for ligne in groupe) == base + taxe
    texte = await texte_pdf(client, piece["id"])
    if applicable and len(groupes) > 1:
        for _, _, taux in groupes:
            assert f"Base HT à {taux:.1f}".replace(".", ",") in texte
            assert f"TVA à {taux:.1f}".replace(".", ",") in texte
    else:
        assert "Base HT à" not in texte


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["convert", "convert-to-invoice"])
async def test_copie_nouvelle_regle_source_historique_intacte(client, operation):
    source = await creer(client, lignes(10, 12.34, 5.5), "devis")
    async with db.AsyncSessionLocal() as session:
        devis = await _get_invoice_with_lines(session, source["id"])
        devis.subtotal_ht, devis.total_tax, devis.total_ttc = 123.4, 6.8, 130.2
        for ligne in devis.lines:
            ligne.total_ttc = 13.02
        await session.commit()
    conversion = await client.post(f"/api/invoices/{source['id']}/{operation}", json={"target_type": "facture"})
    assert conversion.status_code == 200, conversion.text
    copie = (await client.get(f"/api/invoices/{conversion.json()['id']}")).json()
    assert (copie["total_tax"], copie["total_ttc"]) == (6.79, 130.19)
    original = (await client.get(f"/api/invoices/{source['id']}")).json()
    assert (original["total_tax"], original["total_ttc"]) == (6.8, 130.2)
    assert all(ligne["total_ttc"] == 13.02 for ligne in original["lines"])
