"""B-1187 : synchro tableur des contacts (route servie POST /api/crm/sync/import,
même upsert que POST /api/crm/sync) : une ligne réduite à son ID vide la fiche
existante et remet étape et score par défaut.

Attendus écrits :
- B-1163 (bugs.json, memory.py:861) : « Une fiche garde toujours un nom ou
  une entreprise » ;
- arbitrage du 24/09 (docs/plans/2026-09-24-arbitrages-par-delegation.md:20-26) :
  « le tableur fait foi pour ce qu'il dit, pas pour ce qu'il tait : une
  cellule vide ou une valeur inconnue ne remplace pas la valeur enregistrée »
  (la parenthèse cite projets, tâches, livrables ; les contacts n'y sont pas) ;
- en face, crm_utils.py:292-295 revendique le miroir pour le courriel seul
  (« Une cellule vide garde son sens de miroir », B-1107).
"""

from __future__ import annotations

import pytest

FICHE = {
    "first_name": "Alice",
    "last_name": "Martin",
    "company": "Boulangerie Martin",
    "email": "alice.martin@example.fr",
    "phone": "+33 6 12 34 56 78",
    "stage": "signature",
    "source": "salon",
}


async def _fiche_pleine(client) -> dict:
    cree = await client.post("/api/memory/contacts", json=FICHE)
    assert cree.status_code == 200, cree.text
    cid = cree.json()["id"]
    maj = await client.patch(f"/api/memory/contacts/{cid}", json={"score": 80})
    assert maj.status_code == 200, maj.text
    fiche = (await client.get(f"/api/memory/contacts/{cid}")).json()
    assert fiche["stage"] == "signature" and fiche["score"] == 80, fiche
    return fiche


def _vue(fiche: dict) -> dict:
    return {k: fiche.get(k) for k in
            ("first_name", "last_name", "company", "email", "phone", "source", "stage", "score")}


@pytest.mark.asyncio
async def test_une_ligne_reduite_a_son_id_ne_vide_pas_l_identite(client):
    avant = await _fiche_pleine(client)

    resp = await client.post("/api/crm/sync/import", json={"clients": [{"ID": avant["id"]}]})
    assert resp.status_code == 200, resp.text
    apres = (await client.get(f"/api/memory/contacts/{avant['id']}")).json()

    identite = [apres.get(k) for k in ("first_name", "last_name", "company", "email")]
    assert any(identite), (
        f"ligne {{'ID': ...}} seule : avant={_vue(avant)} ; après={_vue(apres)}"
    )


@pytest.mark.asyncio
async def test_une_ligne_reduite_a_son_id_ne_remet_pas_etape_et_score_par_defaut(client):
    avant = await _fiche_pleine(client)

    resp = await client.post("/api/crm/sync/import", json={"clients": [{"ID": avant["id"]}]})
    assert resp.status_code == 200, resp.text
    apres = (await client.get(f"/api/memory/contacts/{avant['id']}")).json()

    assert (apres["stage"], apres["score"]) == ("signature", 80), (
        f"étape {avant['stage']!r} -> {apres['stage']!r}, score {avant['score']} -> {apres['score']}"
    )


@pytest.mark.asyncio
async def test_temoin_une_ligne_complete_met_bien_la_fiche_a_jour(client):
    avant = await _fiche_pleine(client)

    ligne = {"ID": avant["id"], "Nom": "Alice Martin", "Entreprise": "Boulangerie Martin & Fils",
             "Email": "alice.martin@example.fr", "Tel": "+33 6 12 34 56 78",
             "Source": "salon", "Stage": "delivery", "Score": "90"}
    resp = await client.post("/api/crm/sync/import", json={"clients": [ligne]})
    assert resp.status_code == 200, resp.text
    apres = (await client.get(f"/api/memory/contacts/{avant['id']}")).json()

    assert apres["company"] == "Boulangerie Martin & Fils"
    assert (apres["stage"], apres["score"]) == ("delivery", 90)


@pytest.mark.asyncio
async def test_mesure_une_etape_hors_pipeline_venue_du_tableur(client):
    """Mesure annexe (B-167, schemas.py:237-249) : l'étape du tableur n'est pas
    confrontée aux sept étapes du pipeline."""
    avant = await _fiche_pleine(client)
    ligne = {"ID": avant["id"], "Nom": "Alice Martin", "Stage": "Gelé"}
    resp = await client.post("/api/crm/sync/import", json={"clients": [ligne]})
    assert resp.status_code == 200, resp.text
    apres = (await client.get(f"/api/memory/contacts/{avant['id']}")).json()
    assert apres["stage"] in {
        "contact", "discovery", "proposition", "signature", "delivery", "active", "archive"
    }, f"étape stockée après synchro : {apres['stage']!r}"


@pytest.mark.asyncio
@pytest.mark.parametrize("cellule", ["élevé", "1e999", "-40", "250"])
async def test_un_score_illisible_ou_hors_bornes_ne_remplace_pas_le_score(client, cellule):
    """B-1213 : suite de B-1187. Une cellule Score illisible remplaçait le
    score enregistré par 50, et un score hors de 0 à 100 était recopié tel
    quel (jumeau de B-1165)."""
    cid = (await _fiche_pleine(client))["id"]
    resp = await client.post("/api/crm/sync/import", json={"clients": [{"ID": cid, "Score": cellule}]})
    assert resp.status_code == 200, resp.text
    apres = (await client.get(f"/api/memory/contacts/{cid}")).json()
    assert apres["score"] == 80, (cellule, apres["score"])
