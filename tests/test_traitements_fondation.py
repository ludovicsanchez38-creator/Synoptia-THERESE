"""Fondation du chantier 0.46 - TraitementHandle, annulation, routes, rétention.

Contrats du design V2.1, challengé deux fois :
- l'état terminal appartient au PRODUCTEUR : l'endpoint cancel ne pose
  jamais `cancelled` sur une running, jamais `interrupted` ;
- une `queued` s'annule par CAS direct (sinon bloquée en cancel_requested
  pour toujours), et son démarrage ultérieur est refusé ;
- `lier_adaptateur()` REJOUE une demande arrivée avant l'enrôlement ;
- `can_cancel` devient faux dès la demande posée ;
- un producteur qui finit pendant un cancel_requested termine `done` ;
- visibilité : les chat/deep-research < 2 s sont masqués CÔTÉ SERVEUR,
  échecs et annulations toujours visibles.
"""

import pytest
from app.models.processing import EtatTache


class AdaptateurEspion:
    def __init__(self, coupe: bool = True) -> None:
        self.demandes = 0
        self.coupe = coupe

    async def annuler(self) -> bool:
        self.demandes += 1
        return self.coupe


async def _traitement(client, **kw):
    from app.services import traitements

    return await traitements.creer_traitement(
        type=kw.pop("type", "essai"), label=kw.pop("label", "Un essai"), **kw
    )


class TestLeCycleDeVie:
    @pytest.mark.asyncio
    async def test_nominal(self, client):
        from app.services import traitements

        handle = await _traitement(client)
        assert (await traitements.lire(handle.id)).state == EtatTache.QUEUED

        await handle.demarrer()
        assert (await traitements.lire(handle.id)).state == EtatTache.RUNNING

        await handle.progresser(step="découpage", progress=0.5)
        ligne = await traitements.lire(handle.id)
        assert (ligne.step, ligne.progress) == ("découpage", 0.5)

        await handle.terminer(EtatTache.DONE)
        ligne = await traitements.lire(handle.id)
        assert ligne.state == EtatTache.DONE
        assert ligne.finished_at is not None

    @pytest.mark.asyncio
    async def test_une_queued_annulee_ne_demarre_jamais(self, client):
        from app.services import traitements

        handle = await _traitement(client)
        resultat = await traitements.demander_arret(handle.id)

        assert resultat.state == EtatTache.CANCELLED, (
            "une queued sans producteur resterait cancel_requested pour "
            "toujours : le CAS la passe cancelled directement"
        )
        with pytest.raises(traitements.AnnuleAvantDemarrage):
            await handle.demarrer()

    @pytest.mark.asyncio
    async def test_une_running_sans_adaptateur_reste_au_producteur(self, client):
        from app.services import traitements

        handle = await _traitement(client)
        await handle.demarrer()

        resultat = await traitements.demander_arret(handle.id)

        assert resultat.state == EtatTache.CANCEL_REQUESTED
        assert resultat.resultat == "unavailable", (
            "l'absence d'adaptateur ne prouve pas la mort du processus : "
            "jamais interrupted ici"
        )

        # le producteur finit son travail : done, jamais ecrase par cancelled
        await handle.terminer(EtatTache.DONE)
        assert (await traitements.lire(handle.id)).state == EtatTache.DONE

    @pytest.mark.asyncio
    async def test_l_adaptateur_recoit_meme_une_demande_anterieure(self, client):
        """La fenetre entre creation et enrolement est fermee : lier_adaptateur
        REJOUE une demande arrivee avant lui."""
        from app.services import traitements

        handle = await _traitement(client)
        await handle.demarrer()
        await traitements.demander_arret(handle.id)

        espion = AdaptateurEspion()
        await handle.lier_adaptateur(espion)

        assert espion.demandes == 1

    @pytest.mark.asyncio
    async def test_l_endpoint_ne_pose_jamais_cancelled_sur_une_running(self, client):
        from app.services import traitements

        handle = await _traitement(client)
        await handle.demarrer()
        espion = AdaptateurEspion(coupe=True)
        await handle.lier_adaptateur(espion)

        resultat = await traitements.demander_arret(handle.id)

        assert resultat.resultat == "stopped"
        assert resultat.state == EtatTache.CANCEL_REQUESTED, (
            "meme un arret confirme laisse l'etat terminal au producteur"
        )
        await handle.terminer(EtatTache.CANCELLED)
        assert (await traitements.lire(handle.id)).state == EtatTache.CANCELLED

    @pytest.mark.asyncio
    async def test_can_cancel_devient_faux_des_la_demande(self, client):
        from app.services import traitements

        handle = await _traitement(client)
        await handle.demarrer()
        await handle.lier_adaptateur(AdaptateurEspion())
        assert (await traitements.dto(handle.id))["can_cancel"] is True

        await traitements.demander_arret(handle.id)

        assert (await traitements.dto(handle.id))["can_cancel"] is False


class TestLesRoutes:
    @pytest.mark.asyncio
    async def test_liste_et_annulation(self, client):

        handle = await _traitement(client, type="atelier", label="Mission X")
        await handle.demarrer()
        await handle.lier_adaptateur(AdaptateurEspion())

        resp = await client.get("/api/processing-tasks?actives=true")
        assert resp.status_code == 200
        lignes = resp.json()["traitements"]
        assert any(t["id"] == handle.id and t["can_cancel"] for t in lignes)

        resp = await client.post(f"/api/processing-tasks/{handle.id}/cancel")
        assert resp.status_code == 200
        assert resp.json()["state"] == EtatTache.CANCEL_REQUESTED

        await handle.terminer(EtatTache.CANCELLED)
        resp = await client.post(f"/api/processing-tasks/{handle.id}/cancel")
        assert resp.status_code == 409, "une terminale ne s'annule pas"

        resp = await client.post("/api/processing-tasks/inconnue/cancel")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_le_seuil_de_visibilite_est_cote_serveur(self, client):
        """chat/deep-research < 2 s masqués ; échecs TOUJOURS visibles ;
        les autres types jamais masqués."""
        from datetime import UTC, datetime, timedelta

        from app.models.database import get_session_context
        from app.models.processing import ProcessingTask
        from app.services import task_registry

        async with get_session_context() as session:
            il_y_a_1s = datetime.now(UTC) - timedelta(seconds=1)
            il_y_a_60s = datetime.now(UTC) - timedelta(seconds=60)
            session.add(ProcessingTask(
                type="chat", label="jeune active", state="running",
                run_instance_id=task_registry.instance_courante(),
                created_at=il_y_a_1s,
            ))
            session.add(ProcessingTask(
                type="chat", label="vieille active", state="running",
                run_instance_id=task_registry.instance_courante(),
                created_at=il_y_a_60s,
            ))
            session.add(ProcessingTask(
                type="chat", label="succes eclair", state="done",
                run_instance_id=task_registry.instance_courante(),
                created_at=il_y_a_60s,
                finished_at=il_y_a_60s + timedelta(seconds=1),
            ))
            session.add(ProcessingTask(
                type="chat", label="echec eclair", state="failed",
                run_instance_id=task_registry.instance_courante(),
                created_at=il_y_a_60s,
                finished_at=il_y_a_60s + timedelta(seconds=1),
            ))
            session.add(ProcessingTask(
                type="project_sync", label="sync jeune", state="running",
                run_instance_id=task_registry.instance_courante(),
                created_at=il_y_a_1s,
            ))
            await session.commit()

        resp = await client.get("/api/processing-tasks")
        labels = {t["label"] for t in resp.json()["traitements"]}

        assert "jeune active" not in labels
        assert "succes eclair" not in labels
        assert {"vieille active", "echec eclair", "sync jeune"} <= labels


class TestLaRetention:
    @pytest.mark.asyncio
    async def test_les_terminees_anciennes_sont_purgees(self, client):
        from datetime import UTC, datetime, timedelta

        from app.models.database import get_session_context
        from app.models.processing import ProcessingTask
        from app.services import traitements

        async with get_session_context() as session:
            vieux = datetime.now(UTC) - timedelta(days=45)
            session.add(ProcessingTask(
                type="chat", label="antique done", state="done",
                run_instance_id="ancienne", created_at=vieux, finished_at=vieux,
            ))
            session.add(ProcessingTask(
                type="chat", label="antique running", state="running",
                run_instance_id="ancienne", created_at=vieux,
            ))
            await session.commit()

        purgees = await traitements.purger_les_terminees(retention_jours=30)

        assert purgees == 1
        resp = await client.get("/api/processing-tasks?limit=200")
        labels = {t["label"] for t in resp.json()["traitements"]}
        assert "antique done" not in labels
        assert "antique running" in labels, (
            "une active n'est JAMAIS purgee, meme antique - elle finira "
            "interrupted au recuperateur, pas a la corbeille"
        )


class TestLesTransitionsSontDesCAS:
    """Revue jalon (F1-F2) : SELECT puis commit n'est pas un CAS - deux
    sessions concurrentes cassaient les garanties. Les transitions passent
    par UPDATE conditionnel, verifie par rowcount."""

    @pytest.mark.asyncio
    async def test_demarrer_perd_contre_une_annulation(self, client):
        """L'annulation commite cancelled entre le SELECT et le commit de
        demarrer : l'etat final ne doit JAMAIS etre running."""
        from app.models.database import get_session_context
        from app.models.processing import ProcessingTask
        from app.services import traitements
        from sqlmodel import select as sel

        handle = await _traitement(client)
        # une autre session pose cancelled directement (la course simulee)
        async with get_session_context() as session:
            r = await session.execute(
                sel(ProcessingTask).where(ProcessingTask.id == handle.id)
            )
            ligne = r.scalar_one()
            ligne.state = EtatTache.CANCELLED
            await session.commit()

        with pytest.raises(traitements.AnnuleAvantDemarrage):
            await handle.demarrer()
        assert (await traitements.lire(handle.id)).state == EtatTache.CANCELLED

    @pytest.mark.asyncio
    async def test_l_arret_ne_regresse_jamais_un_terminal(self, client):
        """Le producteur termine done pendant que la demande d'arret est en
        vol : done ne doit JAMAIS regresser en cancel_requested."""
        from app.models.database import get_session_context
        from app.models.processing import ProcessingTask
        from app.services import traitements
        from sqlmodel import select as sel

        handle = await _traitement(client)
        await handle.demarrer()
        # le producteur termine juste avant l'UPDATE de la demande
        async with get_session_context() as session:
            r = await session.execute(
                sel(ProcessingTask).where(ProcessingTask.id == handle.id)
            )
            ligne = r.scalar_one()
            ligne.state = EtatTache.DONE
            await session.commit()

        resultat = await traitements.demander_arret(handle.id)

        assert (await traitements.lire(handle.id)).state == EtatTache.DONE
        assert resultat.state == EtatTache.DONE

    @pytest.mark.asyncio
    async def test_le_rejeu_survit_a_la_perte_du_set_volatile(self, client):
        """F2 : la demande durable cancel_requested est la verite - meme si
        le set memoire a ete perdu (redemarrage partiel, course), l'enrolement
        transmet."""
        from app.services import traitements

        handle = await _traitement(client)
        await handle.demarrer()
        await traitements.demander_arret(handle.id)
        traitements._demandes_en_attente.discard(handle.id)  # le set est perdu

        espion = AdaptateurEspion()
        await handle.lier_adaptateur(espion)

        assert espion.demandes == 1, (
            "l'etat durable cancel_requested doit suffire au rejeu"
        )

    @pytest.mark.asyncio
    async def test_une_queued_est_annulable_depuis_le_panneau(self, client):
        """Une queued s'annule par l'API : can_cancel doit le dire."""
        from app.services import traitements

        handle = await _traitement(client)

        assert (await traitements.dto(handle.id))["can_cancel"] is True
