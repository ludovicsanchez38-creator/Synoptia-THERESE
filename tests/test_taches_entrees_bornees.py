"""B-185 et B-186 (RB2-015, RB2-016) — POST /api/tasks/ accepte n'importe quoi.

`CreateTaskRequest` ne déclare ni `Literal` ni validateur, et `create_task`
recopie `project_id` / `contact_id` dans l'entité sans vérifier qu'ils
désignent quelque chose. Deux conséquences mesurées :

- une tâche au statut hors domaine n'apparaît dans aucune colonne du tableau
  (todo, in_progress, done) et disparaît sans message, alors que la route des
  projets borne déjà son statut par un `Literal` ;
- une tâche accrochée à `projet-fantome` ne remonte dans aucun filtre par
  projet réel et ne sera jamais nettoyée à la suppression d'un projet, là où
  `POST /api/files/upload` rend 404 « Projet non trouvé » avant d'écrire.
"""

import pytest
from httpx import AsyncClient


class TestB185DomaineDesTaches:
    @pytest.mark.asyncio
    async def test_statuts_et_priorites_du_domaine_acceptes(self, client: AsyncClient) -> None:
        """Contrôle de l'instrument : les quatre valeurs déclarées passent."""
        for statut in ("todo", "in_progress", "done", "cancelled"):
            reponse = await client.post(
                "/api/tasks/", json={"title": f"Tache {statut}", "status": statut}
            )
            assert reponse.status_code == 200, reponse.text
            assert reponse.json()["status"] == statut

        for priorite in ("low", "medium", "high", "urgent"):
            reponse = await client.post(
                "/api/tasks/", json={"title": f"Tache {priorite}", "priority": priorite}
            )
            assert reponse.status_code == 200, reponse.text
            assert reponse.json()["priority"] == priorite

    @pytest.mark.asyncio
    async def test_statut_hors_domaine_refuse(self, client: AsyncClient) -> None:
        reponse = await client.post(
            "/api/tasks/", json={"title": "T1", "status": "nimportequoi"}
        )

        assert reponse.status_code == 422, (
            f"statut hors domaine accepte : {reponse.status_code} -> {reponse.text[:200]}"
        )
        assert "status" in reponse.text

    @pytest.mark.asyncio
    async def test_priorite_hors_domaine_refusee(self, client: AsyncClient) -> None:
        reponse = await client.post("/api/tasks/", json={"title": "T1", "priority": "ultra"})

        assert reponse.status_code == 422, (
            f"priorite hors domaine acceptee : {reponse.status_code} -> {reponse.text[:200]}"
        )
        assert "priority" in reponse.text

    @pytest.mark.asyncio
    async def test_titre_vide_refuse(self, client: AsyncClient) -> None:
        """Une tâche sans intitulé est une ligne vide dans le tableau."""
        for titre in ("", "   "):
            reponse = await client.post("/api/tasks/", json={"title": titre})
            assert reponse.status_code == 422, (
                f"titre {titre!r} accepte : {reponse.status_code} -> {reponse.text[:200]}"
            )

    @pytest.mark.asyncio
    async def test_mise_a_jour_hors_domaine_refusee(self, client: AsyncClient) -> None:
        """Le même trou est ouvert sur PUT : le borner à la création seule
        laisserait la porte de service grande ouverte."""
        creee = await client.post("/api/tasks/", json={"title": "A corriger"})
        assert creee.status_code == 200, creee.text
        tache_id = creee.json()["id"]

        reponse = await client.put(
            f"/api/tasks/{tache_id}", json={"status": "nimportequoi"}
        )
        assert reponse.status_code == 422, (
            f"PUT statut hors domaine : {reponse.status_code} -> {reponse.text[:200]}"
        )

        reponse = await client.put(f"/api/tasks/{tache_id}", json={"priority": "ultra"})
        assert reponse.status_code == 422, (
            f"PUT priorite hors domaine : {reponse.status_code} -> {reponse.text[:200]}"
        )

        relue = await client.get(f"/api/tasks/{tache_id}")
        assert relue.json()["status"] == "todo"
        assert relue.json()["priority"] == "medium"


class TestB186RattachementsExistants:
    @pytest.mark.asyncio
    async def test_projet_et_contact_reels_acceptes(self, client: AsyncClient) -> None:
        """Contrôle de l'instrument : un rattachement valide reste écrit."""
        projet = await client.post("/api/memory/projects", json={"name": "Refonte du site"})
        assert projet.status_code in (200, 201), projet.text
        contact = await client.post(
            "/api/memory/contacts", json={"first_name": "Joyce", "last_name": "Poussin"}
        )
        assert contact.status_code in (200, 201), contact.text

        reponse = await client.post(
            "/api/tasks/",
            json={
                "title": "Relancer Joyce",
                "project_id": projet.json()["id"],
                "contact_id": contact.json()["id"],
            },
        )
        assert reponse.status_code == 200, reponse.text
        assert reponse.json()["project_id"] == projet.json()["id"]
        assert reponse.json()["contact_id"] == contact.json()["id"]

    @pytest.mark.asyncio
    async def test_projet_inconnu_refuse(self, client: AsyncClient) -> None:
        reponse = await client.post(
            "/api/tasks/", json={"title": "T2", "project_id": "projet-fantome"}
        )

        assert reponse.status_code == 404, (
            f"projet fantome accepte : {reponse.status_code} -> {reponse.text[:200]}"
        )
        assert "Projet non trouvé" in reponse.text

        liste = await client.get("/api/tasks/?limit=50")
        assert liste.json() == [], "la tache fantome a quand meme ete ecrite"

    @pytest.mark.asyncio
    async def test_contact_inconnu_refuse(self, client: AsyncClient) -> None:
        reponse = await client.post(
            "/api/tasks/", json={"title": "T3", "contact_id": "contact-fantome"}
        )

        assert reponse.status_code == 404, (
            f"contact fantome accepte : {reponse.status_code} -> {reponse.text[:200]}"
        )
        assert "Contact non trouvé" in reponse.text

        liste = await client.get("/api/tasks/?limit=50")
        assert liste.json() == []

    @pytest.mark.asyncio
    async def test_mise_a_jour_vers_un_projet_inconnu_refusee(self, client: AsyncClient) -> None:
        creee = await client.post("/api/tasks/", json={"title": "A rattacher"})
        tache_id = creee.json()["id"]

        reponse = await client.put(
            f"/api/tasks/{tache_id}", json={"project_id": "projet-fantome"}
        )

        assert reponse.status_code == 404, (
            f"PUT projet fantome : {reponse.status_code} -> {reponse.text[:200]}"
        )
        relue = await client.get(f"/api/tasks/{tache_id}")
        assert relue.json()["project_id"] is None


class TestB032LeContactDUneTacheNEstPasJete:
    """Le champ était accepté, validé, puis jeté sans un mot.

    `UpdateTaskRequest` déclare `contact_id`, la requête rend 200 et
    `updated_at` avance — la mise à jour a bien tourné —, mais `update_task`
    ne recopie que `project_id` et `tags` : la réponse ET la relecture
    rendent l'ANCIEN contact. Un contrôle déclaré qu'aucune ligne n'écrit est
    un contrôle mort ; l'utilisateur croit avoir rattaché sa tâche.
    """

    @staticmethod
    async def _contact(client: AsyncClient, prenom: str) -> str:
        reponse = await client.post(
            "/api/memory/contacts", json={"first_name": prenom, "last_name": "Tache"}
        )
        assert reponse.status_code == 200, reponse.text
        return reponse.json()["id"]

    @pytest.mark.asyncio
    async def test_la_mise_a_jour_rattache_bien_le_contact(
        self, client: AsyncClient
    ) -> None:
        contact_a = await self._contact(client, "Amandine")
        contact_b = await self._contact(client, "Bertrand")

        creee = await client.post(
            "/api/tasks/", json={"title": "Rappeler", "contact_id": contact_a}
        )
        assert creee.status_code == 200, creee.text
        tache_id = creee.json()["id"]

        modifiee = await client.put(
            f"/api/tasks/{tache_id}", json={"contact_id": contact_b}
        )
        assert modifiee.status_code == 200, modifiee.text
        assert modifiee.json()["contact_id"] == contact_b, (
            "la réponse rend encore l'ancien contact : le champ a été accepté puis jeté"
        )

        relue = await client.get(f"/api/tasks/{tache_id}")
        assert relue.status_code == 200, relue.text
        assert relue.json()["contact_id"] == contact_b, (
            "la relecture rend l'ancien contact : rien n'a été écrit en base"
        )

    @pytest.mark.asyncio
    async def test_un_contact_inconnu_est_refuse_a_la_mise_a_jour(
        self, client: AsyncClient
    ) -> None:
        """Même devoir qu'à la création (B-186) : on n'accroche pas au vide."""
        creee = await client.post("/api/tasks/", json={"title": "Rappeler"})
        tache_id = creee.json()["id"]

        refus = await client.put(
            f"/api/tasks/{tache_id}", json={"contact_id": "contact-fantome"}
        )

        assert refus.status_code == 404, (
            f"contact inconnu accepté : {refus.status_code} -> {refus.text[:200]}"
        )
        relue = await client.get(f"/api/tasks/{tache_id}")
        assert relue.json()["contact_id"] is None

    @pytest.mark.asyncio
    async def test_aucun_champ_declare_n_est_muet(self, client: AsyncClient) -> None:
        """Garde qui balaie le schéma, pour que le trou ne se rouvre pas ailleurs.

        Chaque champ de `UpdateTaskRequest` reçoit une valeur ; on exige
        qu'elle atterrisse sur l'entité relue. Un champ ajouté au schéma sans
        ligne d'écriture dans le routeur fait rougir ce test.
        """
        from app.models.schemas import UpdateTaskRequest

        projet = await client.post("/api/memory/projects", json={"name": "Dossier tache"})
        assert projet.status_code == 200, projet.text
        contact = await self._contact(client, "Cyprien")

        envoye = {
            "title": "Titre modifié",
            "description": "Description modifiée",
            "status": "in_progress",
            "priority": "urgent",
            "due_date": "2026-12-24T10:00:00",
            "project_id": projet.json()["id"],
            "tags": ["alpha", "beta"],
            "contact_id": contact,
        }
        assert set(envoye) == set(UpdateTaskRequest.model_fields), (
            "un champ du schéma n'est pas couvert par cette garde : "
            f"{set(UpdateTaskRequest.model_fields) ^ set(envoye)}"
        )

        creee = await client.post("/api/tasks/", json={"title": "Avant"})
        tache_id = creee.json()["id"]

        modifiee = await client.put(f"/api/tasks/{tache_id}", json=envoye)
        assert modifiee.status_code == 200, modifiee.text

        relue = (await client.get(f"/api/tasks/{tache_id}")).json()
        for champ, valeur in envoye.items():
            obtenu = relue[champ]
            if champ == "due_date":
                assert obtenu is not None and obtenu.startswith("2026-12-24"), (
                    f"{champ} : envoyé {valeur!r}, relu {obtenu!r}"
                )
            else:
                assert obtenu == valeur, (
                    f"{champ} : envoyé {valeur!r}, relu {obtenu!r} — champ déclaré, "
                    "accepté, puis jeté"
                )
