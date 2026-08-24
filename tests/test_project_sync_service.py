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
