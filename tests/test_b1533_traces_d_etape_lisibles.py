"""B-1533 (revue du diff P-132b, constat 3) : la fiche lue par le modèle
remontait les changements d'étape en identifiants, « Stage: proposition ->
lost », alors qu'elle promet l'étape en toutes lettres. Un modèle lit
« signature » comme « en attente de signature ».
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_un_changement_d_etape_se_lit_en_mots_de_l_ecran(client: AsyncClient):
    fiche = (await client.post("/api/memory/contacts", json={"first_name": "Karim", "last_name": "Benali"})).json()
    for etape in ("proposition", "lost"):
        reponse = await client.patch(f"/api/crm/contacts/{fiche['id']}/stage", json={"stage": etape})
        assert reponse.status_code == 200, reponse.text

    lue = await client.get(f"/api/memory/contacts/{fiche['id']}/fiche")
    assert lue.status_code == 200, lue.text
    changements = [t for t in lue.json()["traces"] if t["origine"] == "activite (stage_change)"]

    assert sorted(t["titre"] for t in changements) == [
        "Étape : Contact → Proposition", "Étape : Proposition → Perdu",
    ]
    texte = " ".join(f"{t['titre']} {t['texte']}" for t in changements)
    for brut in ("Stage", "stage", "lost", "proposition ->"):
        assert brut not in texte, brut
