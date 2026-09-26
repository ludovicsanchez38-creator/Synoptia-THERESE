"""P-148 : ce que rassemble un projet, en une lecture.

La fenêtre d'un projet ne montrait ni ses conversations, ni ses documents,
ni ses tâches : la promesse de l'état vide (« rassembler les contacts,
documents et tâches d'une même affaire ») n'était tenue nulle part. La route
`GET /api/memory/projects/{id}/ensemble` rend chaque famille, bornée, avec son
total, sur les MÊMES clauses que la suppression du projet : le compte que la
confirmation annoncera est le compte que la suppression exécutera.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from tests.peuplement_projet import garnir_un_projet, poser_du_bruit


async def _garnir_avec_du_bruit(contact_id: str | None = None):
    from app.models import database as db_module
    from app.models.entities import Contact

    async with db_module.AsyncSessionLocal() as session:
        if contact_id:
            session.add(Contact(id=contact_id, first_name="Camille", last_name="Roux", company="Roux SARL"))
        garni = await garnir_un_projet(session, "projet-cible", contact_id=contact_id)
        await poser_du_bruit(session)
        await session.commit()
    return garni


class TestLaRoute:
    @pytest.mark.asyncio
    async def test_un_projet_inconnu_rend_404(self, client):
        reponse = await client.get("/api/memory/projects/projet-fantome/ensemble")
        assert reponse.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize("limite", [0, 201])
    async def test_la_limite_est_bornee(self, client, limite):
        await _garnir_avec_du_bruit()
        reponse = await client.get(f"/api/memory/projects/projet-cible/ensemble?limite={limite}")
        assert reponse.status_code == 422

    @pytest.mark.asyncio
    async def test_chaque_total_ne_compte_que_ce_projet(self, client):
        garni = await _garnir_avec_du_bruit()

        reponse = await client.get("/api/memory/projects/projet-cible/ensemble")

        assert reponse.status_code == 200, reponse.text
        ensemble = reponse.json()
        assert ensemble["indisponibles"] == []
        assert ensemble["conversations"]["total"] == 1
        assert [c["id"] for c in ensemble["conversations"]["elements"]] == [garni.conversation_id]
        assert ensemble["conversations"]["elements"][0]["titre"] == "Devis cuisine"
        assert ensemble["documents"]["total"] == 1
        assert ensemble["documents"]["elements"][0] == {
            "id": garni.document_id, "titre": "Plan de formation", "statut": "en_cours",
            "mise_a_jour": ensemble["documents"]["elements"][0]["mise_a_jour"],
        }
        assert ensemble["taches"]["total"] == 2
        assert ensemble["taches"]["ouvertes"] == 2
        assert ensemble["taches"]["en_retard"] == 0
        assert sorted(t["id"] for t in ensemble["taches"]["elements"]) == sorted(garni.taches)
        assert ensemble["contacts"]["total"] == 1
        assert ensemble["contacts"]["ranges"] == 1
        assert ensemble["contacts"]["elements"] == [
            {"id": garni.contact_range_id, "first_name": "Julien", "last_name": "Garnier", "company": None, "associe": False},
        ]
        assert ensemble["livrables"] == {"total": 1}
        # Le fichier du peuplement est indexé depuis le disque, hors du dépôt.
        assert ensemble["fichiers"] == {"total": 1, "deposes": 0, "indexes_sur_place": 1}
        assert ensemble["dossier_synchronise"] == {"rattache": False}
        assert ensemble["rendez_vous"] == {"total": 1}
        assert ensemble["sous_dossiers"] == {"total": 1}
        assert ensemble["planning"] == {"total": 2}

    @pytest.mark.asyncio
    async def test_un_horodatage_du_serveur_porte_son_fuseau(self, client):
        """B-216 : sans fuseau, l'écran lirait l'heure UTC comme la sienne."""
        await _garnir_avec_du_bruit()
        ensemble = (await client.get("/api/memory/projects/projet-cible/ensemble")).json()
        assert ensemble["conversations"]["elements"][0]["mise_a_jour"].endswith("+00:00")

    @pytest.mark.asyncio
    async def test_la_limite_borne_les_elements_pas_les_totaux(self, client):
        from app.models import database as db_module
        from app.models.entities import Conversation

        await _garnir_avec_du_bruit()
        async with db_module.AsyncSessionLocal() as session:
            for i in range(7):
                session.add(Conversation(id=f"conv-en-plus-{i}", title=f"Échange {i}", project_id="projet-cible"))
            await session.commit()

        par_defaut = (await client.get("/api/memory/projects/projet-cible/ensemble")).json()
        tout = (await client.get("/api/memory/projects/projet-cible/ensemble?limite=200")).json()

        assert par_defaut["conversations"]["total"] == 8
        assert len(par_defaut["conversations"]["elements"]) == 5
        assert len(tout["conversations"]["elements"]) == 8

    @pytest.mark.asyncio
    async def test_une_conversation_ouverte_a_toute_la_memoire_est_listee(self, client):
        """La cloison documentaire n'est pas en jeu : aucun modèle ne lit cette route."""
        from app.models import database as db_module
        from app.models.entities import Conversation

        await _garnir_avec_du_bruit()
        async with db_module.AsyncSessionLocal() as session:
            session.add(Conversation(id="conv-toute-memoire", title="Bilan", project_id="projet-cible", memory_scope="all"))
            await session.commit()

        ensemble = (await client.get("/api/memory/projects/projet-cible/ensemble")).json()

        assert "conv-toute-memoire" in [c["id"] for c in ensemble["conversations"]["elements"]]

    @pytest.mark.asyncio
    async def test_une_famille_en_panne_se_nomme_et_les_autres_restent(self, client, monkeypatch):
        from app.services import projet_ensemble

        async def en_panne(*_args, **_kwargs):
            raise RuntimeError("table verrouillée")

        await _garnir_avec_du_bruit()
        monkeypatch.setattr(projet_ensemble, "_lire_documents", en_panne)

        reponse = await client.get("/api/memory/projects/projet-cible/ensemble")

        assert reponse.status_code == 200, reponse.text
        ensemble = reponse.json()
        assert ensemble["indisponibles"] == ["documents"]
        # Une panne n'est pas un vide : la famille n'annonce aucun total.
        assert ensemble["documents"] is None
        assert ensemble["conversations"]["total"] == 1
        assert ensemble["taches"]["total"] == 2


class TestLesFichiersDuProjet:
    @pytest.mark.asyncio
    async def test_deposes_et_indexes_sur_place_se_distinguent(self, client, tmp_path, monkeypatch):
        """Revue P-148, constat 3 : la suppression efface le dépôt de THÉRÈSE,
        pas les fichiers indexés depuis le dossier synchronisé, qui restent sur
        le disque (`_purger_le_depot_du_dossier`). La confirmation doit pouvoir
        le dire, et annoncer le détachement du dossier synchronisé."""
        from pathlib import Path

        from app.config import settings
        from app.models import database as db_module
        from app.models.entities import FileMetadata
        from app.models.entities_sync import ProjectSyncRoot

        monkeypatch.setattr(settings, "data_dir", tmp_path / "donnees")
        await _garnir_avec_du_bruit()
        depot = (Path(settings.data_dir) / "projects" / "projet-cible" / "files").resolve()
        dossier = (tmp_path / "Mes documents" / "Cuisine").resolve()
        async with db_module.AsyncSessionLocal() as session:
            session.add(FileMetadata(
                id="fichier-depose", path=str(depot / "plan.pdf"), name="plan.pdf",
                extension=".pdf", size=1, scope="project", scope_id="projet-cible",
            ))
            session.add(FileMetadata(
                id="fichier-synchronise", path=str(dossier / "devis.docx"), name="devis.docx",
                extension=".docx", size=1, scope="project", scope_id="projet-cible",
            ))
            session.add(ProjectSyncRoot(project_id="projet-cible", racine=str(dossier), volume_id=1))
            await session.commit()

        ensemble = (await client.get("/api/memory/projects/projet-cible/ensemble")).json()

        # Le peuplement pose déjà un fichier indexé hors du dépôt.
        assert ensemble["fichiers"] == {"total": 3, "deposes": 1, "indexes_sur_place": 2}
        assert ensemble["dossier_synchronise"] == {"rattache": True}
        rapport = (await client.delete("/api/memory/projects/projet-cible")).json()["cascade_deleted"]
        assert rapport["files"] == ensemble["fichiers"]["total"]

    @pytest.mark.asyncio
    async def test_un_dossier_synchronise_delie_n_est_plus_annonce(self, client):
        from app.models import database as db_module
        from app.models.entities_sync import ProjectSyncRoot

        await _garnir_avec_du_bruit()
        async with db_module.AsyncSessionLocal() as session:
            session.add(ProjectSyncRoot(project_id="projet-cible", racine="/ancien", volume_id=1, detachee=True))
            await session.commit()

        ensemble = (await client.get("/api/memory/projects/projet-cible/ensemble")).json()

        assert ensemble["dossier_synchronise"] == {"rattache": False}


class TestLeContactAssocie:
    @pytest.mark.asyncio
    async def test_le_contact_associe_passe_en_tete(self, client):
        garni = await _garnir_avec_du_bruit(contact_id="contact-camille")

        contacts = (await client.get("/api/memory/projects/projet-cible/ensemble")).json()["contacts"]

        assert contacts["total"] == 2
        assert contacts["elements"] == [
            {"id": "contact-camille", "first_name": "Camille", "last_name": "Roux", "company": "Roux SARL", "associe": True},
            {"id": garni.contact_range_id, "first_name": "Julien", "last_name": "Garnier", "company": None, "associe": False},
        ]

    @pytest.mark.asyncio
    async def test_un_contact_associe_et_range_dans_le_projet_n_apparait_qu_une_fois(self, client):
        """Constat 18 de la revue : dédoublonner par identifiant."""
        from app.models import database as db_module
        from app.models.entities import Project

        garni = await _garnir_avec_du_bruit()
        async with db_module.AsyncSessionLocal() as session:
            projet = await session.get(Project, "projet-cible")
            assert projet is not None
            projet.contact_id = garni.contact_range_id
            session.add(projet)
            await session.commit()

        contacts = (await client.get("/api/memory/projects/projet-cible/ensemble")).json()["contacts"]

        assert contacts["total"] == 1
        assert contacts["elements"] == [
            {"id": garni.contact_range_id, "first_name": "Julien", "last_name": "Garnier", "company": None, "associe": True},
        ]
        # La suppression le rendra au général : il reste compté parmi les rangés.
        assert contacts["ranges"] == 1


class TestLOrdre:
    @pytest.mark.asyncio
    async def test_conversations_et_documents_du_plus_recent_au_plus_ancien(self, db_session):
        from app.models.entities import Conversation, Document, Project
        from app.services.projet_ensemble import lire_l_ensemble

        base = datetime(2026, 9, 1, 10, 0)
        projet = Project(id="projet-ordre", name="Ordre")
        db_session.add(projet)
        for i, jours in enumerate((3, 1, 2)):
            db_session.add(Conversation(id=f"c{i}", title=f"C{i}", project_id=projet.id, updated_at=base + timedelta(days=jours)))
            db_session.add(Document(id=f"d{i}", title=f"D{i}", project_id=projet.id, updated_at=base + timedelta(days=jours)))
        await db_session.commit()

        ensemble = await lire_l_ensemble(db_session, projet)

        assert [c["id"] for c in ensemble["conversations"]["elements"]] == ["c0", "c2", "c1"]
        assert [d["id"] for d in ensemble["documents"]["elements"]] == ["d0", "d2", "d1"]

    @pytest.mark.asyncio
    async def test_taches_ouvertes_d_abord_puis_par_echeance_sans_echeance_en_dernier(self, db_session):
        from app.models.entities import Project, Task
        from app.services.projet_ensemble import lire_l_ensemble

        projet = Project(id="projet-taches", name="Tâches")
        db_session.add(projet)
        jour = datetime(2026, 9, 20, 12, 0)
        for tache in (
            Task(id="faite-hier", title="Faite", status="done", due_date=jour - timedelta(days=1), project_id=projet.id),
            Task(id="a-faire-j5", title="J+5", status="todo", due_date=jour + timedelta(days=5), project_id=projet.id),
            Task(id="en-cours-j2", title="J+2", status="in_progress", due_date=jour + timedelta(days=2), project_id=projet.id),
            Task(id="a-faire-sans-date", title="Sans date", status="todo", project_id=projet.id),
            Task(id="annulee-sans-date", title="Annulée", status="cancelled", project_id=projet.id),
        ):
            db_session.add(tache)
        await db_session.commit()

        ensemble = await lire_l_ensemble(db_session, projet, maintenant=datetime(2026, 9, 20, 8, 0, tzinfo=UTC))

        assert [t["id"] for t in ensemble["taches"]["elements"]] == [
            "en-cours-j2", "a-faire-j5", "a-faire-sans-date", "faite-hier", "annulee-sans-date",
        ]
        assert ensemble["taches"]["total"] == 5
        assert ensemble["taches"]["ouvertes"] == 3


class TestLeRetard:
    @pytest.mark.asyncio
    async def test_en_retard_bascule_a_minuit_de_paris_pas_a_minuit_utc(self, db_session):
        from app.models.entities import Project, Task
        from app.services.projet_ensemble import lire_l_ensemble

        projet = Project(id="projet-retard", name="Retard")
        db_session.add(projet)
        # Échéance du 26/09 (jour civil, comme l'écrit le formulaire).
        db_session.add(Task(id="due-le-26", title="Due le 26", status="todo", due_date=datetime(2026, 9, 26, 12, 0), project_id=projet.id))
        db_session.add(Task(id="faite-due-le-20", title="Faite", status="done", due_date=datetime(2026, 9, 20, 12, 0), project_id=projet.id))
        await db_session.commit()

        # 23 h 30 à Paris le 26 : pas encore en retard.
        veille = await lire_l_ensemble(db_session, projet, maintenant=datetime(2026, 9, 26, 21, 30, tzinfo=UTC))
        # 0 h 30 à Paris le 27, encore le 26 en UTC : en retard.
        lendemain = await lire_l_ensemble(db_session, projet, maintenant=datetime(2026, 9, 26, 22, 30, tzinfo=UTC))

        assert veille["taches"]["en_retard"] == 0
        assert lendemain["taches"]["en_retard"] == 1


class TestUneSeuleDefinition:
    @pytest.mark.asyncio
    async def test_les_totaux_annonces_sont_ceux_que_la_suppression_execute(self, client):
        """Le compte annoncé par la confirmation est le compte exécuté, famille par famille."""
        from app.models import database as db_module
        from app.models.entities import Contact, Conversation, FileMetadata, Task

        await _garnir_avec_du_bruit(contact_id="contact-camille")
        async with db_module.AsyncSessionLocal() as session:
            # Du relief : des familles à plusieurs éléments, et du bruit voisin.
            session.add(Conversation(id="conv-2", title="Suite", project_id="projet-cible"))
            session.add(Task(id="tache-c", title="Relancer", project_id="projet-cible"))
            session.add(Contact(id="contact-2", first_name="Inès", scope="project", scope_id="projet-cible"))
            session.add(Contact(id="contact-voisin-2", first_name="Paul", scope="project", scope_id="projet-voisin"))
            session.add(FileMetadata(
                id="fichier-contact", path="/p148/contact/cv.md", name="cv.md", extension=".md",
                size=1, scope="contact", scope_id="contact-camille",
            ))
            await session.commit()

        ensemble = (await client.get("/api/memory/projects/projet-cible/ensemble")).json()
        rapport = (await client.delete("/api/memory/projects/projet-cible")).json()["cascade_deleted"]

        annonce = {
            "files": ensemble["fichiers"]["total"],
            "conversations_detachees": ensemble["conversations"]["total"],
            "documents_detaches": ensemble["documents"]["total"],
            "evenements_detaches": ensemble["rendez_vous"]["total"],
            "contacts_rendus_au_general": ensemble["contacts"]["ranges"],
            "sous_dossiers_rendus_au_general": ensemble["sous_dossiers"]["total"],
            "taches_supprimees": ensemble["taches"]["total"],
            "livrables_supprimes": ensemble["livrables"]["total"],
        }
        assert annonce == rapport
        assert rapport["conversations_detachees"] == 2
        assert rapport["contacts_rendus_au_general"] == 2

    def test_la_suppression_lit_les_clauses_du_service(self):
        """Une seconde définition dans le routeur finirait par répondre un autre chiffre."""
        import inspect

        from app.routers import memory

        from tests.aide_lecture_source import code_sans_commentaires

        code = code_sans_commentaires(inspect.getsource(memory._nettoyer_et_supprimer_projet))
        for clause in (
            "clause_fichiers", "clause_conversations", "clause_documents", "clause_rendez_vous",
            "clause_contacts_ranges", "clause_sous_dossiers", "clause_taches", "clause_livrables",
        ):
            assert clause in code, clause
        assert "project_id ==" not in code
        assert "scope_id ==" not in code
