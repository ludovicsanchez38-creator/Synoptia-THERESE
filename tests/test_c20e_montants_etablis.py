"""Contre-relecture Claude : une copie ou une relecture conserve les centimes."""

import re
from decimal import ROUND_HALF_UP, Decimal

import pytest
from app.models import database as db
from app.routers.invoices import _get_invoice_with_lines
from pypdf import PdfReader


def lignes(nombre, prix, taux, description="Repas"):
    return [{"description": description, "quantity": 1, "unit_price_ht": prix, "tva_rate": taux}
            for _ in range(nombre)]


async def creer(client, demandes, type_document="facture"):
    profil = await client.post("/api/config/profile", json={
        "name": "Atelier fictif", "company": "Ventilation", "address": "Paris",
        "siret": "99988877900009",
    })
    assert profil.status_code == 200, profil.text
    contact = await client.post("/api/memory/contacts", json={"first_name": "Client", "last_name": "Centimes"})
    response = await client.post("/api/invoices/", json={
        "contact_id": contact.json()["id"], "document_type": type_document, "lines": demandes,
    })
    assert response.status_code == 200, response.text
    return response.json()


def montants(piece):
    return tuple(piece[k] for k in ("subtotal_ht", "total_tax", "total_ttc"))


async def etablir_ancien_calcul(identifiant, statut):
    # Reconstituer les valeurs déjà enregistrées avant 9a774e20, indépendamment
    # du moteur courant : centime commercial sur chaque ligne puis somme.
    async with db.AsyncSessionLocal() as session:
        piece = await _get_invoice_with_lines(session, identifiant)
        piece.status = statut
        ht, ttc = Decimal(0), Decimal(0)
        for ligne in piece.lines:
            base = Decimal(str(ligne.total_ht))
            total = (base * (1 + Decimal(str(ligne.tva_rate)) / 100)).quantize(
                Decimal(".01"), rounding=ROUND_HALF_UP,
            )
            ligne.total_ttc = float(total)
            ht += base
            ttc += total
        piece.subtotal_ht, piece.total_tax, piece.total_ttc = float(ht), float(ttc - ht), float(ttc)
        if statut == "sent" and piece.document_type == "facture":
            piece.invoice_number = "FACT-2025-042"
        await session.commit()


async def relire(client, identifiant):
    response = await client.get(f"/api/invoices/{identifiant}")
    assert response.status_code == 200, response.text
    return response.json()


async def texte_pdf(client, identifiant):
    response = await client.get(f"/api/invoices/{identifiant}/pdf")
    assert response.status_code == 200, response.text
    return " ".join(" ".join(page.extract_text() for page in PdfReader(response.json()["pdf_path"]).pages).split())


@pytest.mark.asyncio
async def test_avoir_convert_solde_exactement_la_facture_historique(client):
    source = await creer(client, lignes(10, 12.34, 5.5) + lignes(12, 0.99, 20, "Boisson"))
    await etablir_ancien_calcul(source["id"], "sent")
    avant = await relire(client, source["id"])
    assert montants(avant) == (135.28, 9.2, 144.48)
    response = await client.post(f"/api/invoices/{source['id']}/convert", json={"target_type": "avoir"})
    assert response.status_code == 200, response.text
    avoir = response.json()
    assert montants(avoir) == montants(avant)
    assert avoir["converted_from_id"] == source["id"]
    emission = await client.put(f"/api/invoices/{avoir['id']}", json={"status": "sent"})
    assert emission.status_code == 200, emission.text
    assert montants(await relire(client, avoir["id"])) == montants(avant)
    assert await relire(client, source["id"]) == avant
    texte = await texte_pdf(client, avoir["id"])
    assert "TVA à 5,5 % 6,80" in texte and "TVA à 20,0 % 2,40" in texte
    assert "144,48" in texte


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["convert", "convert-to-invoice"])
async def test_devis_accepte_converti_au_montant_accepte(client, operation):
    source = await creer(client, lignes(10, 12.34, 5.5), "devis")
    await etablir_ancien_calcul(source["id"], "accepted")
    avant = await relire(client, source["id"])
    assert montants(avant) == (123.4, 6.8, 130.2)
    response = await client.post(f"/api/invoices/{source['id']}/{operation}", json={"target_type": "facture"})
    assert response.status_code == 200, response.text
    assert montants(await relire(client, response.json()["id"])) == montants(avant)
    assert montants(await relire(client, source["id"])) == montants(avant)
    assert "Total TTC 130,20" in await texte_pdf(client, response.json()["id"])


@pytest.mark.asyncio
@pytest.mark.parametrize("type_document,statut", [("facture", "draft"), ("devis", "accepted")])
async def test_enregistrer_notes_et_lignes_inchangees_garde_les_montants(client, type_document, statut):
    demandes = lignes(10, 12.34, 5.5) + lignes(12, 0.99, 20, "Boisson")
    source = await creer(client, demandes, type_document)
    await etablir_ancien_calcul(source["id"], statut)
    avant = await relire(client, source["id"])
    response = await client.put(f"/api/invoices/{source['id']}", json={"notes": "Note changée", "lines": demandes})
    assert response.status_code == 200, response.text
    assert montants(response.json()) == montants(avant)
    assert montants(await relire(client, source["id"])) == montants(avant)


@pytest.mark.asyncio
async def test_pdf_lignes_identiques_et_ventilation_des_montants_stockes(client):
    piece = await creer(client, lignes(10, 12.34, 5.5) + lignes(12, 0.99, 20, "Boisson"))
    texte = await texte_pdf(client, piece["id"])
    # Contrôler les cellules du vrai PDF, pas seulement son bloc de totaux.
    repas = re.findall(r"Repas 1 12,34 € 5,5% 12,34 € ([\d,]+) €", texte)
    boissons = re.findall(r"Boisson 1 0,99 € 20,0% 0,99 € ([\d,]+) €", texte)
    assert repas == ["13,02"] * 10, texte
    assert boissons == ["1,19"] * 12, texte
    assert "TVA à 5,5 % 6,80" in texte and "TVA à 20,0 % 2,40" in texte
    assert "Total TTC 144,48" in texte


@pytest.mark.asyncio
@pytest.mark.parametrize("groupes,type_document,statut,operation,attendu", [
    ([(3, 7.77, 5.5)], "facture", "sent", "convert", (23.31, 1.29, 24.6)),
    ([(9, 0.07, 20)], "devis", "accepted", "convert-to-invoice", (0.63, 0.09, 0.72)),
    ([(4, 0.15, 10)], "devis", "draft", "convert", (0.6, 0.08, 0.68)),
    ([(6, 2.35, 2.1)], "facture", "sent", "convert", (14.1, 0.3, 14.4)),
    ([(2, 49.99, 20)], "devis", "accepted", "convert", (99.98, 20.0, 119.98)),
    ([(5, 3.33, 5.5)], "devis", "draft", "convert-to-invoice", (16.65, 0.9, 17.55)),
    ([(8, 0.26, 10)], "facture", "sent", "convert", (2.08, 0.24, 2.32)),
    ([(7, 0.23, 2.1)], "devis", "accepted", "convert-to-invoice", (1.61, 0.0, 1.61)),
    ([(3, 17.11, 0)], "devis", "draft", "convert", (51.33, 0.0, 51.33)),
    ([(4, 6.66, 5.5), (3, 0.29, 20)], "facture", "sent", "convert", (27.51, 1.66, 29.17)),
])
async def test_dix_entrees_apres_revert(client, groupes, type_document, statut, operation, attendu):
    demandes = [ligne for n, prix, taux in groupes for ligne in lignes(n, prix, taux)]
    source = await creer(client, demandes, type_document)
    assert montants(source) == attendu
    await etablir_ancien_calcul(source["id"], statut)
    avant = await relire(client, source["id"])
    assert montants(avant) == attendu
    if type_document == "devis":
        sauvegarde = await client.put(f"/api/invoices/{source['id']}", json={"notes": "Relecture", "lines": demandes})
        assert sauvegarde.status_code == 200, sauvegarde.text
        assert montants(await relire(client, source["id"])) == attendu
    response = await client.post(f"/api/invoices/{source['id']}/{operation}", json={
        "target_type": "avoir" if type_document == "facture" else "facture",
    })
    assert response.status_code == 200, response.text
    copie = await relire(client, response.json()["id"])
    assert montants(copie) == attendu
    assert montants(await relire(client, source["id"])) == attendu
    assert sum(Decimal(str(ligne["total_ttc"])) for ligne in copie["lines"]) == Decimal(str(attendu[2]))
    for _, prix, taux in groupes:
        identiques = [ligne["total_ttc"] for ligne in copie["lines"]
                      if ligne["unit_price_ht"] == prix and ligne["tva_rate"] == taux]
        assert len(set(identiques)) == 1
    texte = await texte_pdf(client, copie["id"])
    assert f"{attendu[2]:.2f}".replace(".", ",") in texte
    if len(groupes) > 1:
        assert "TVA à 5,5 % 1,48" in texte and "TVA à 20,0 % 0,18" in texte
