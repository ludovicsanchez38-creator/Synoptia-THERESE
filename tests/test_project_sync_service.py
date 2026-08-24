"""Orchestration de project.sync : racine, plan, apply, reprise (0.45).

Les contrats viennent du design V2.1 challengé deux fois :
- racine exclusive, jamais imbriquée, generation incrémentée au changement ;
- plan fail-closed, seuls les derniers plans s'appliquent, les précédents
  deviennent caducs ;
- apply at-least-once : `a_faire` ET `echec` se rejouent, une opération n'est
  `fait` qu'après le succès COMPLET, une dérive depuis le plan est `obsolete`
  (jamais indexée), l'état de référence naît des opérations réussies ;
- un apply à la fois par projet, et pas de nouveau plan pendant un apply.
"""

import hashlib
from pathlib import Path
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def qdrant_factice(monkeypatch):
    from app.services import indexation

    faux = AsyncMock()
    monkeypatch.setattr(indexation, "get_qdrant_service", lambda: faux)
    monkeypatch.setattr(indexation, "extract_text", lambda _p: "texte extrait")
    return faux


@pytest.fixture
def racine(tmp_path: Path) -> Path:
    d = tmp_path / "dossier-sync"
    d.mkdir()
    (d / "un.txt").write_text("premier", encoding="utf-8")
    (d / "deux.txt").write_text("second", encoding="utf-8")
    return d


async def _creer_projet(client) -> str:
    resp = await client.post("/api/memory/projects", json={"name": "Chantier"})
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["id"]


class TestLaRacineEstExclusive:
    @pytest.mark.asyncio
    async def test_rattachement_nominal(self, client, racine):
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        root = await svc.definir_racine(projet, str(racine))

        assert root.racine == str(racine.resolve())
        assert root.generation == 1
        assert root.volume_id == racine.stat().st_dev

    @pytest.mark.asyncio
    async def test_deux_projets_ne_partagent_pas_une_racine(self, client, racine):
        from app.services import project_sync_service as svc

        p1 = await _creer_projet(client)
        p2 = await _creer_projet(client)
        await svc.definir_racine(p1, str(racine))

        with pytest.raises(svc.ErreurRacine):
            await svc.definir_racine(p2, str(racine))

    @pytest.mark.asyncio
    async def test_une_racine_imbriquee_est_refusee(self, client, racine):
        from app.services import project_sync_service as svc

        p1 = await _creer_projet(client)
        p2 = await _creer_projet(client)
        await svc.definir_racine(p1, str(racine))
        sous = racine / "sous-dossier"
        sous.mkdir()

        with pytest.raises(svc.ErreurRacine):
            await svc.definir_racine(p2, str(sous))

    @pytest.mark.asyncio
    async def test_changer_de_racine_incremente_la_generation(
        self, client, racine, tmp_path, qdrant_factice
    ):
        from app.models.entities_sync import EtatPlan
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        plan = await svc.preparer_plan(projet)

        autre = tmp_path / "autre-dossier"
        autre.mkdir()
        root = await svc.definir_racine(projet, str(autre))

        assert root.generation == 2
        plan_relu = await svc.lire_plan(plan.id)
        assert plan_relu.etat == EtatPlan.CADUC, (
            "un plan de la génération précédente ne doit plus être applicable"
        )


class TestLePlan:
    @pytest.mark.asyncio
    async def test_premier_plan_indexe_tout(self, client, racine, qdrant_factice):
        from app.models.entities_sync import TypeOperation
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))

        plan = await svc.preparer_plan(projet)

        assert plan.nb_indexer == 2
        assert plan.nb_retirer == 0
        ops = await svc.lire_operations(plan.id)
        assert {o.type for o in ops} == {TypeOperation.INDEXER}
        assert all(o.empreinte_prevue for o in ops)

    @pytest.mark.asyncio
    async def test_un_nouveau_plan_rend_le_precedent_caduc(
        self, client, racine, qdrant_factice
    ):
        from app.models.entities_sync import EtatPlan
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        premier = await svc.preparer_plan(projet)
        second = await svc.preparer_plan(projet)

        assert (await svc.lire_plan(premier.id)).etat == EtatPlan.CADUC
        assert (await svc.lire_plan(second.id)).etat == EtatPlan.PROPOSE

    @pytest.mark.asyncio
    async def test_racine_debranchee_zero_plan(self, client, racine, qdrant_factice):
        import shutil

        from app.services import project_sync_service as svc
        from app.services.project_sync import ErreurDeScan

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        shutil.rmtree(racine)

        with pytest.raises(ErreurDeScan):
            await svc.preparer_plan(projet)

        assert (await svc.etat_sync(projet))["dernier_plan"] is None, (
            "un scan en échec ne doit produire AUCUN plan - surtout pas un "
            "plan de retrait massif"
        )


class TestLApply:
    @pytest.mark.asyncio
    async def test_apply_indexe_et_etablit_le_referentiel(
        self, client, racine, qdrant_factice
    ):
        from app.models.entities_sync import EtatOperation, EtatPlan
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        plan = await svc.preparer_plan(projet)

        await svc.appliquer_plan(projet, plan.id)

        assert (await svc.lire_plan(plan.id)).etat == EtatPlan.APPLIQUE
        ops = await svc.lire_operations(plan.id)
        assert all(o.etat == EtatOperation.FAIT for o in ops)
        referentiel = await svc.lire_referentiel(projet)
        assert len(referentiel) == 2
        attendu = hashlib.sha256(b"premier").hexdigest()
        assert referentiel[str((racine / "un.txt").resolve())][1] == attendu

    @pytest.mark.asyncio
    async def test_second_plan_sans_changement_zero_operation(
        self, client, racine, qdrant_factice
    ):
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        plan = await svc.preparer_plan(projet)
        await svc.appliquer_plan(projet, plan.id)

        second = await svc.preparer_plan(projet)

        assert second.nb_indexer == 0
        assert second.nb_reindexer == 0
        assert second.nb_retirer == 0
        assert second.nb_inchanges == 2

    @pytest.mark.asyncio
    async def test_un_fichier_disparu_est_retire_apres_apply(
        self, client, racine, qdrant_factice
    ):
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        plan = await svc.preparer_plan(projet)
        await svc.appliquer_plan(projet, plan.id)

        (racine / "deux.txt").unlink()
        second = await svc.preparer_plan(projet)
        assert second.nb_retirer == 1
        await svc.appliquer_plan(projet, second.id)

        referentiel = await svc.lire_referentiel(projet)
        assert len(referentiel) == 1

    @pytest.mark.asyncio
    async def test_un_fichier_modifie_entre_plan_et_apply_devient_obsolete(
        self, client, racine, qdrant_factice
    ):
        """On n'indexe JAMAIS une version différente de celle approuvée."""
        from app.models.entities_sync import EtatOperation
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        plan = await svc.preparer_plan(projet)

        (racine / "un.txt").write_text("modifié après le plan", encoding="utf-8")
        await svc.appliquer_plan(projet, plan.id)

        ops = await svc.lire_operations(plan.id)
        etats = {Path(o.chemin).name: o.etat for o in ops}
        assert etats["un.txt"] == EtatOperation.OBSOLETE
        assert etats["deux.txt"] == EtatOperation.FAIT
        from app.models.entities_sync import EtatPlan

        assert (await svc.lire_plan(plan.id)).etat == EtatPlan.APPLIQUE_PARTIEL, (
            "un plan avec une opération obsolète n'est PAS appliqué : le "
            "disque et l'index ne disent pas la même chose"
        )
        referentiel = await svc.lire_referentiel(projet)
        assert str((racine / "un.txt").resolve()) not in referentiel

    @pytest.mark.asyncio
    async def test_un_echec_est_reessayable_dans_le_meme_plan(
        self, client, racine, qdrant_factice, monkeypatch
    ):
        from app.models.entities_sync import EtatOperation
        from app.services import indexation
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        plan = await svc.preparer_plan(projet)

        vraie = indexation.extract_text

        def extraction_en_panne(_p):
            raise RuntimeError("disque fatigué")

        monkeypatch.setattr(indexation, "extract_text", extraction_en_panne)
        await svc.appliquer_plan(projet, plan.id)

        ops = await svc.lire_operations(plan.id)
        assert all(o.etat == EtatOperation.ECHEC for o in ops)
        assert all(o.attempt_count == 1 for o in ops)

        monkeypatch.setattr(indexation, "extract_text", vraie)
        await svc.appliquer_plan(projet, plan.id)

        ops = await svc.lire_operations(plan.id)
        assert all(o.etat == EtatOperation.FAIT for o in ops)
        assert all(o.attempt_count == 2 for o in ops)

    @pytest.mark.asyncio
    async def test_pas_de_plan_pendant_un_apply(self, client, racine, qdrant_factice):
        import asyncio

        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        plan = await svc.preparer_plan(projet)

        async with svc._verrou_du_projet(projet):
            with pytest.raises(svc.OperationRefusee):
                await asyncio.wait_for(svc.preparer_plan(projet), timeout=1)
            with pytest.raises(svc.OperationRefusee):
                await asyncio.wait_for(
                    svc.appliquer_plan(projet, plan.id), timeout=1
                )


class TestLaReprise:
    @pytest.mark.asyncio
    async def test_un_apply_orphelin_est_repris_au_demarrage(
        self, client, racine, qdrant_factice
    ):
        """Un plan reste `en_cours` après un crash : le récupérateur crée un
        nouveau run et termine le travail - `interrupted` seul ne suffit pas."""
        from app.models.entities_sync import EtatOperation, EtatPlan
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        plan = await svc.preparer_plan(projet)

        # simuler le crash : le plan est marqué en_cours, rien n'est exécuté
        await svc._marquer_plan(plan.id, EtatPlan.EN_COURS)

        repris = await svc.reprendre_applies_orphelins()

        assert repris == 1
        assert (await svc.lire_plan(plan.id)).etat == EtatPlan.APPLIQUE
        ops = await svc.lire_operations(plan.id)
        assert all(o.etat == EtatOperation.FAIT for o in ops)


class TestLesBloquantsDeLaRevue:
    """Reproductions de la revue du jalon (NO-GO), transformées en tests."""

    @pytest.mark.asyncio
    async def test_b1_changer_de_racine_attend_la_fin_de_l_apply(
        self, client, racine, tmp_path, qdrant_factice
    ):
        """B1 : la racine ne change pas PENDANT un apply - même verrou projet.
        Sans lui, l'apply finissant réécrivait `applique` sur un plan caduc et
        recréait des entrées de génération 1 vers l'ancienne racine."""
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        autre = tmp_path / "autre"
        autre.mkdir()

        async with svc._verrou_du_projet(projet):
            with pytest.raises(svc.OperationRefusee):
                await svc.definir_racine(projet, str(autre))
            with pytest.raises(svc.OperationRefusee):
                await svc.retirer_racine(projet)

    @pytest.mark.asyncio
    async def test_b1_un_plan_caduc_ne_redevient_jamais_applique(
        self, client, racine, qdrant_factice
    ):
        from app.models.entities_sync import EtatPlan
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        plan = await svc.preparer_plan(projet)

        await svc._marquer_plan(plan.id, EtatPlan.CADUC)
        # même si un finaliseur tardif tente d'écrire l'état final :
        await svc._finaliser_plan(plan.id, EtatPlan.APPLIQUE)

        assert (await svc.lire_plan(plan.id)).etat == EtatPlan.CADUC

    @pytest.mark.asyncio
    async def test_b1_la_generation_ne_repart_jamais_a_1(
        self, client, racine, tmp_path, qdrant_factice
    ):
        """Retirer puis rattacher NE remet PAS la génération à 1 : un ancien
        plan partiel de génération 1 redeviendrait compatible."""
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        await svc.retirer_racine(projet)
        autre = tmp_path / "encore"
        autre.mkdir()
        root = await svc.definir_racine(projet, str(autre))

        assert root.generation >= 2

    @pytest.mark.asyncio
    async def test_b2_un_fichier_revenu_n_est_jamais_retire(
        self, client, racine, qdrant_factice
    ):
        """B2 : le retrait revalide le DISQUE - un fichier revenu entre le
        plan et l'apply devient obsolete, jamais retiré."""
        from app.models.entities_sync import EtatOperation
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        premier = await svc.preparer_plan(projet)
        await svc.appliquer_plan(projet, premier.id)

        cible = racine / "deux.txt"
        contenu = cible.read_bytes()
        cible.unlink()
        plan = await svc.preparer_plan(projet)
        assert plan.nb_retirer == 1
        cible.write_bytes(contenu)  # le fichier REVIENT avant l'apply

        await svc.appliquer_plan(projet, plan.id)

        ops = await svc.lire_operations(plan.id)
        retirer = next(o for o in ops if o.type == "retirer")
        assert retirer.etat == EtatOperation.OBSOLETE
        referentiel = await svc.lire_referentiel(projet)
        assert str(cible.resolve()) in referentiel, (
            "le fichier est là ET indexé : le retirer aurait vidé son index"
        )

    @pytest.mark.asyncio
    async def test_b2_un_fichier_instable_n_est_pas_declare_disparu(
        self, client, racine, qdrant_factice, monkeypatch
    ):
        """Un fichier exclu du scan pour instabilité ne doit pas devenir une
        opération de retrait au plan suivant."""
        from app.services import project_sync
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        premier = await svc.preparer_plan(projet)
        await svc.appliquer_plan(projet, premier.id)

        cible = (racine / "un.txt").resolve()
        vrai_hash = project_sync._hacher

        def hash_derangeant(chemin):
            r = vrai_hash(chemin)
            if chemin == cible:
                cible.write_text("bouge encore", encoding="utf-8")
            return r

        monkeypatch.setattr(project_sync, "_hacher", hash_derangeant)
        plan = await svc.preparer_plan(projet)

        assert plan.nb_retirer == 0, (
            "instable = on ne touche à rien, surtout pas un retrait"
        )

    @pytest.mark.asyncio
    async def test_b5_un_chemin_recree_n_est_pas_la_meme_entite(
        self, client, racine, qdrant_factice
    ):
        """B5 : la réindexation vérifie l'IDENTITÉ prévue (file_id), pas
        seulement l'empreinte - un fichier supprimé puis recréé est une autre
        entité."""
        import hashlib

        from app.services import indexation

        fichier = racine / "un.txt"
        await indexation.index_payload(str(fichier.resolve()))
        empreinte = hashlib.sha256(fichier.read_bytes()).hexdigest()

        with pytest.raises(indexation.ContenuModifieDepuisLePlan):
            await indexation.index_payload(
                str(fichier.resolve()),
                sha256_attendu=empreinte,
                file_id_attendu="une-entite-disparue",
            )

    @pytest.mark.asyncio
    async def test_b5_le_retrait_manuel_nettoie_l_entree_sync(
        self, client, racine, qdrant_factice
    ):
        """Supprimer un fichier depuis l'explorateur (delete_file) doit aussi
        retirer son entrée de référence - sinon le plan suivant annonce
        « inchangé » un fichier qui n'est plus indexé."""
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        plan = await svc.preparer_plan(projet)
        await svc.appliquer_plan(projet, plan.id)

        referentiel = await svc.lire_referentiel(projet)
        chemin, (file_id, _sha) = next(iter(referentiel.items()))

        resp = await client.delete(f"/api/files/{file_id}")
        assert resp.status_code == 200, resp.text

        referentiel = await svc.lire_referentiel(projet)
        assert chemin not in referentiel

        second = await svc.preparer_plan(projet)
        assert second.nb_indexer == 1, (
            "le fichier n'est plus indexé : le plan doit proposer de le "
            "réindexer, pas le déclarer inchangé"
        )


class TestLeRunEstUnTraitementHonnete:
    """0.46, phase 2 : project.sync est le banc d'essai du patron
    TraitementHandle. Finding 5 du challenge : pas de try/finally autour du
    run - une exception hors boucle laissait la ligne `running` fantôme."""

    @pytest.mark.asyncio
    async def test_une_exception_hors_boucle_termine_failed(
        self, client, racine, qdrant_factice, monkeypatch
    ):
        from app.models.database import get_session_context
        from app.models.processing import EtatTache, ProcessingTask
        from app.services import project_sync_service as svc
        from sqlmodel import select

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        plan = await svc.preparer_plan(projet)

        def explose(*a, **k):
            raise RuntimeError("hors boucle")

        monkeypatch.setattr(svc, "lire_operations", explose)

        with pytest.raises(RuntimeError):
            await svc.appliquer_plan(projet, plan.id)

        async with get_session_context() as session:
            resultat = await session.execute(
                select(ProcessingTask).where(
                    ProcessingTask.type == "project_sync",
                    ProcessingTask.entity_id == plan.id,
                )
            )
            run = resultat.scalars().first()
        assert run is not None
        assert run.state == EtatTache.FAILED, (
            "une exception hors boucle laissait le run `running` jusqu'au "
            "prochain redémarrage"
        )

    @pytest.mark.asyncio
    async def test_un_apply_s_arrete_depuis_le_panneau(
        self, client, racine, qdrant_factice
    ):
        """L'annulation par /api/processing-tasks coupe l'apply ENTRE deux
        opérations : ce qui est fait reste fait, le reste attend, le run est
        `cancelled` par le producteur."""
        from app.models.entities_sync import EtatOperation, EtatPlan
        from app.models.processing import EtatTache
        from app.services import indexation, traitements
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        plan = await svc.preparer_plan(projet)
        assert plan.nb_indexer == 2

        # poser l'annulation APRÈS la première opération, par le vrai service
        vraie = indexation.index_payload
        run_id: list[str] = []

        async def index_puis_annule(*a, **k):
            reponse = await vraie(*a, **k)
            if not run_id:
                run = await svc.lire_run(plan.id)
                run_id.append(run.id)
                await traitements.demander_arret(run.id)
            return reponse

        import unittest.mock as mock

        with mock.patch.object(indexation, "index_payload", index_puis_annule):
            await svc.appliquer_plan(projet, plan.id)

        ops = await svc.lire_operations(plan.id)
        etats = sorted(o.etat for o in ops)
        assert etats == [EtatOperation.A_FAIRE, EtatOperation.FAIT], etats

        run = await svc.lire_run(plan.id)
        assert run.state == EtatTache.CANCELLED, (
            "le producteur pose cancelled après son arrêt réel"
        )
        assert (await svc.lire_plan(plan.id)).etat == EtatPlan.APPLIQUE_PARTIEL

    @pytest.mark.asyncio
    async def test_une_panne_de_finalisation_ne_laisse_pas_running(
        self, client, racine, qdrant_factice, monkeypatch
    ):
        """Revue jalon (F3) : _finaliser_plan vivait HORS du try - sa panne
        laissait le run running fantôme."""
        from app.models.processing import EtatTache
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        plan = await svc.preparer_plan(projet)

        async def finalisation_en_panne(*a, **k):
            raise RuntimeError("finalisation en panne")

        monkeypatch.setattr(svc, "_finaliser_plan", finalisation_en_panne)

        with pytest.raises(RuntimeError):
            await svc.appliquer_plan(projet, plan.id)

        run = await svc.lire_run(plan.id)
        assert run.state == EtatTache.FAILED

    @pytest.mark.asyncio
    async def test_le_shutdown_est_un_arret_pas_une_panne(
        self, client, racine, qdrant_factice, monkeypatch
    ):
        """Une CancelledError (shutdown) termine cancelled - jamais failed
        avec une erreur inventée."""
        import asyncio

        from app.models.processing import EtatTache
        from app.services import indexation
        from app.services import project_sync_service as svc

        projet = await _creer_projet(client)
        await svc.definir_racine(projet, str(racine))
        plan = await svc.preparer_plan(projet)

        async def index_annule(*a, **k):
            raise asyncio.CancelledError()

        monkeypatch.setattr(indexation, "index_payload", index_annule)

        # CancelledError DANS une operation est absorbee par la boucle
        # (echec d'operation) SAUF si elle traverse : ici on la fait traverser
        # en la levant hors operation, via lire_operations au 2e appel
        vraie = svc.lire_operations
        appels = {"n": 0}

        async def lire_puis_annule(plan_id):
            appels["n"] += 1
            if appels["n"] >= 2:
                raise asyncio.CancelledError()
            return await vraie(plan_id)

        monkeypatch.setattr(svc, "lire_operations", lire_puis_annule)

        with pytest.raises(asyncio.CancelledError):
            await svc.appliquer_plan(projet, plan.id)

        run = await svc.lire_run(plan.id)
        assert run.state == EtatTache.CANCELLED
        assert "hors boucle" not in (run.error or "")
