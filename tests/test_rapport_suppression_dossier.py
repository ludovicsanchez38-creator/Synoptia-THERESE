"""Le rapport de suppression d'un dossier nomme tout ce qu'il a détruit.

RB2-009 (B-179). `DELETE /api/memory/projects/{id}` rend un `cascade_deleted`
qui énumère les fichiers supprimés et les trois catégories détachées
(conversations, documents, événements). Or `Project.tasks` et
`Project.deliverables` portent `cascade_delete=True` : les tâches et les
livrables du dossier DISPARAISSENT aussi, sans figurer nulle part dans le
rapport. L'utilisateur lit une liste qui se veut exhaustive et perd des tâches
qu'elle ne mentionne pas.
"""

import pytest


class TestLeRapportNommeLesDestructions:
    @pytest.mark.asyncio
    async def test_les_taches_et_livrables_supprimes_sont_annonces(self, client):
        dossier = await client.post(
            "/api/memory/projects", json={"name": "Chantier RB2"}
        )
        assert dossier.status_code in (200, 201), dossier.text[:200]
        dossier_id = dossier.json()["id"]

        tache = await client.post(
            "/api/tasks/", json={"title": "Tache du chantier", "project_id": dossier_id}
        )
        assert tache.status_code in (200, 201), tache.text[:200]
        tache_id = tache.json()["id"]

        livrable = await client.post(
            "/api/crm/deliverables",
            json={"project_id": dossier_id, "title": "Livrable du chantier"},
        )
        assert livrable.status_code in (200, 201), livrable.text[:200]

        suppression = await client.delete(f"/api/memory/projects/{dossier_id}")
        assert suppression.status_code == 200, suppression.text[:300]
        rapport = suppression.json()["cascade_deleted"]

        # La tâche a bien disparu : c'est ce que le rapport doit dire.
        relecture = await client.get(f"/api/tasks/{tache_id}")
        assert relecture.status_code == 404, (
            "la tâche survit : la prémisse du bug a changé, revoir le test"
        )

        assert rapport.get("taches_supprimees") == 1, (
            "le rapport de suppression ne compte pas les tâches détruites : "
            f"{rapport}"
        )
        assert rapport.get("livrables_supprimes") == 1, (
            "le rapport de suppression ne compte pas les livrables détruits : "
            f"{rapport}"
        )

    @pytest.mark.asyncio
    async def test_un_dossier_sans_tache_annonce_zero(self, client):
        """Le rapport reste une liste complète, pas une liste des non-vides."""
        dossier = await client.post(
            "/api/memory/projects", json={"name": "Chantier vide RB2"}
        )
        dossier_id = dossier.json()["id"]

        rapport = (
            await client.delete(f"/api/memory/projects/{dossier_id}")
        ).json()["cascade_deleted"]

        assert rapport.get("taches_supprimees") == 0, rapport
        assert rapport.get("livrables_supprimes") == 0, rapport
