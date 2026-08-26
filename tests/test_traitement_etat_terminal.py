"""L'état terminal se commite AVANT de rendre la tâche non annulable.

Contrôle post-release des 0.48.x. `terminer()` retirait l'adaptateur du
registre, puis écrivait l'état terminal. Si l'écriture échoue — SQLite est
mono-écrivain et `busy_timeout` vaut 5 s, l'app y a déjà des transactions
longues —, la ligne reste `running` alors que plus personne ne peut
l'annuler : `can_cancel` est faux, et une demande d'arrêt la laisse
définitivement en `cancel_requested`.

Le helper `_terminer_sans_masquer` du Board absorbe l'exception pour ne
pas perdre le message métier, ce qui rendait la tâche fantôme silencieuse.
"""

import pytest
from app.models.processing import EtatTache


class AdaptateurEspion:
    async def annuler(self) -> bool:
        return True


async def _traitement(**kw):
    from app.services import traitements

    return await traitements.creer_traitement(
        type=kw.pop("type", "essai"), label=kw.pop("label", "Un essai"), **kw
    )


class TestUneEcritureQuiEchoueNeLaissePasDeFantome:
    @pytest.mark.asyncio
    async def test_l_etat_terminal_est_ecrit_avant_le_retrait_du_registre(
        self, client, monkeypatch
    ):
        """Si le retrait précède l'écriture, une panne d'écriture est fatale."""
        from app.services import traitements

        handle = await _traitement()
        await handle.demarrer()
        await handle.lier_adaptateur(AdaptateurEspion())

        ordre: list[str] = []
        vrai_retirer = traitements.task_registry.retirer

        def espion_retirer(task_id: str):
            ordre.append("retrait")
            return vrai_retirer(task_id)

        monkeypatch.setattr(traitements.task_registry, "retirer", espion_retirer)

        vrai_ecrire = traitements.TraitementHandle._ecrire_etat_terminal

        async def espion_ecrire(self, *a, **k):
            ordre.append("ecriture")
            return await vrai_ecrire(self, *a, **k)

        monkeypatch.setattr(
            traitements.TraitementHandle, "_ecrire_etat_terminal", espion_ecrire
        )

        await handle.terminer(EtatTache.DONE)

        assert ordre == ["ecriture", "retrait"], (
            f"ordre observé {ordre} : une écriture qui échoue laisserait "
            "une tâche active et inannulable"
        )

    @pytest.mark.asyncio
    async def test_une_ecriture_en_echec_laisse_la_tache_annulable(
        self, client, monkeypatch
    ):
        """Le filet : si l'écriture échoue, l'adaptateur RESTE joignable."""
        from app.services import traitements

        handle = await _traitement()
        await handle.demarrer()
        await handle.lier_adaptateur(AdaptateurEspion())

        async def ecriture_en_panne(self, *a, **k):
            raise RuntimeError("database is locked")

        monkeypatch.setattr(
            traitements.TraitementHandle, "_ecrire_etat_terminal", ecriture_en_panne
        )

        with pytest.raises(RuntimeError):
            await handle.terminer(EtatTache.DONE)

        assert traitements.task_registry.est_vivante(handle.id), (
            "l'adaptateur a été retiré : la tâche est devenue inannulable"
        )
        ligne = await traitements.lire(handle.id)
        assert ligne.state == EtatTache.RUNNING
