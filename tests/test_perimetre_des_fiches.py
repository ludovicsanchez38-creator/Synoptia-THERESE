"""C2 — le périmètre d'une fiche doit pouvoir être choisi, et changé.

Campagne dix personas, finding F5 de l'avocat : dans le dossier Rousset,
THÉRÈSE lui ressort la lettre de licenciement d'un autre client et le
traitement anxiolytique de sa cliente.

Le mécanisme est assumé par le code — « Les contacts GÉNÉRAUX restent visibles
partout » — mais il n'existe AUCUN moyen de sortir une fiche du général :

  * `ContactCreate` porte un champ `scope`, que l'écran n'envoie jamais ;
  * `ContactUpdate` n'en a pas du tout : une fiche créée globale le reste ;
  * `ProjectCreate` n'en a pas non plus, alors que c'est l'entité PROJET qui a
    trahi l'avocat (« Présente dans le projet Valette ») — le fichier, lui,
    était bien cloisonné.

Le code promet pourtant de pouvoir « promouvoir » un contact
(`memory_tools.py:228`). Ce contrôle n'a jamais eu d'appelant.

C2 vient AVANT le mode cabinet (C3) : sans lui, activer un cloisonnement strict
viderait le dossier Rousset de Mme Rousset elle-même, dont la fiche est
globale.
"""
import pytest
from app.models.schemas import ContactUpdate, ProjectCreate, ProjectUpdate


class TestLeSchemaPermetDeChoisirLePerimetre:
    def test_un_projet_peut_naitre_dans_un_perimetre(self):
        """`POST /projects` posait une ligne globale, sans recours."""
        champs = ProjectCreate.model_fields
        assert "scope" in champs, (
            "l'entité projet est celle qui a trahi l'avocat : elle doit pouvoir "
            "être créée dans un périmètre"
        )
        assert "scope_id" in champs

    def test_le_defaut_d_un_projet_reste_global(self):
        """Ne pas changer le comportement en silence."""
        projet = ProjectCreate(name="Dossier")
        assert projet.scope == "global"

    def test_une_fiche_contact_peut_etre_rattachee_apres_coup(self):
        """La « promotion » que le code promet depuis 0.43, enfin possible."""
        champs = ContactUpdate.model_fields
        assert "scope" in champs, (
            "sans cela, une fiche créée globale le reste pour toujours"
        )
        assert "scope_id" in champs

    def test_un_projet_peut_etre_rattache_apres_coup(self):
        assert "scope" in ProjectUpdate.model_fields
        assert "scope_id" in ProjectUpdate.model_fields

    def test_le_perimetre_n_est_pas_impose(self):
        """Une mise à jour qui ne parle pas de périmètre ne doit pas le changer."""
        maj = ContactUpdate(first_name="Jean")
        assert maj.scope is None
        assert maj.scope_id is None


class TestLaRouteHonoreLePerimetre:
    """Un champ de schéma qu'aucune route n'écrit est un contrôle mort."""

    def test_la_creation_de_projet_ecrit_le_perimetre(self):
        import inspect

        from app.routers import memory

        source = inspect.getsource(memory.create_project)
        assert "scope=" in source, (
            "POST /projects doit poser le périmètre demandé, sinon le champ de "
            "schéma ne sert à rien"
        )

    @pytest.mark.parametrize("nom", ["update_contact", "update_project"])
    def test_les_mises_a_jour_acceptent_le_perimetre(self, nom):
        import inspect

        from app.routers import memory

        source = inspect.getsource(getattr(memory, nom))
        # `exclude_unset` garantit qu'un champ non fourni ne remet pas le
        # périmètre à zéro.
        assert "exclude_unset" in source or "scope" in source, (
            f"{nom} doit pouvoir changer le périmètre sans l'écraser par défaut"
        )


class TestLApiRendCeQuElleEcrit:
    """Écrire un périmètre que l'API ne relit pas, c'est la leçon de
    `ContactCreate.scope` rejouée : un champ mort.

    Relevé par la relecture : « tu écris un périmètre que l'API ne relit pas.
    C'est ContactCreate.scope recommencé. La leçon que tu cites, tu viens de
    la rejouer. »
    """

    @pytest.mark.asyncio
    async def test_un_projet_cree_dans_un_dossier_est_relu_dans_ce_dossier(self, client):
        """Aller-retour HTTP réel, pas un grep de schéma.

        Le premier jet vérifiait `ProjectResponse.model_fields`. Il était vert
        alors que les QUATRE constructeurs de la réponse ne passaient pas les
        champs : Pydantic rendait le défaut « global » quoi qu'il y ait en base.

        C'est la faute que ce test existe pour empêcher, commise dans le
        commentaire même qui la dénonce — « un champ que l'écriture honore et
        que la lecture écrase ». On écrit, on relit, on compare.
        """
        creation = await client.post(
            "/api/memory/projects",
            json={"name": "Valette c/ SARL", "scope": "project", "scope_id": "dossier-valette"},
        )
        assert creation.status_code in (200, 201), creation.text
        cree = creation.json()
        assert cree["scope"] == "project", "la création doit RENDRE le périmètre posé"
        assert cree["scope_id"] == "dossier-valette"

        relecture = await client.get(f"/api/memory/projects/{cree['id']}")
        assert relecture.status_code == 200
        relu = relecture.json()
        assert relu["scope"] == "project", (
            "la lecture écrasait le périmètre par le défaut du schéma"
        )
        assert relu["scope_id"] == "dossier-valette"

    @pytest.mark.asyncio
    async def test_la_liste_des_projets_rend_aussi_le_perimetre(self, client):
        await client.post(
            "/api/memory/projects",
            json={"name": "Rousset c/ SAS", "scope": "project", "scope_id": "dossier-rousset"},
        )
        liste = await client.get("/api/memory/projects")
        assert liste.status_code == 200
        projets = liste.json()
        cible = [p for p in projets if p["name"] == "Rousset c/ SAS"]
        assert cible, "projet introuvable dans la liste"
        assert cible[0]["scope"] == "project"

    @pytest.mark.asyncio
    async def test_rattacher_un_projet_apres_coup_est_relu(self, client):
        """Le quatrième constructeur, que la preuve par sabotage a trouvé nu.

        Les trois autres (liste, création, lecture) étaient couverts ; celui de
        la mise à jour ne l'était pas. Un test par constructeur, sinon le
        sabotage le dit.
        """
        creation = await client.post("/api/memory/projects", json={"name": "Dossier neutre"})
        projet = creation.json()
        assert projet["scope"] == "global", "défaut inchangé"

        maj = await client.patch(
            f"/api/memory/projects/{projet['id']}",
            json={"scope": "project", "scope_id": "dossier-valette"},
        )
        assert maj.status_code == 200, maj.text
        assert maj.json()["scope"] == "project", (
            "la réponse de mise à jour doit rendre le périmètre, pas le défaut"
        )
        assert maj.json()["scope_id"] == "dossier-valette"

    def test_la_fiche_contact_renvoyee_porte_son_perimetre(self):
        """Les contacts, eux, câblaient déjà les deux (`_contact_to_response`)."""
        from app.models.schemas import ContactResponse

        champs = ContactResponse.model_fields
        assert "scope" in champs and "scope_id" in champs
