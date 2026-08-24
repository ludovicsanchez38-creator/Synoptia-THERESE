"""Deux sauvegardes de profil rapprochées ne doivent pas se marcher dessus.

Le scénario est celui du testeur, mot pour mot : « j'ai refait Continuer et
c'est passé ». Deux appels rapprochés, donc deux indexations concurrentes sur la
même entité — et chacune commence par supprimer l'ancienne. Entre le `delete` de
la seconde et son `add`, le profil n'existe plus dans l'index : « qui suis-je ? »
reste sans réponse, sans que rien ne le signale.

Le dernier écrivain doit gagner, et il ne doit jamais y avoir de trou.
"""
import asyncio

import pytest


async def _attendre_les_indexations() -> None:
    """Attend les tâches de fond plutôt qu'un délai fixe.

    Un `sleep` arbitraire laisse fuiter des tâches d'un test au suivant, qui
    tiennent alors le verrou partagé et font échouer un test parfaitement sain.
    """
    from app.services.user_profile import _INDEXATIONS_EN_COURS

    for _ in range(50):
        if not _INDEXATIONS_EN_COURS:
            return
        await asyncio.sleep(0.02)


class TestDeuxSauvegardesRapprocheesNeSeMarchentPasDessus:
    @pytest.mark.asyncio
    async def test_une_indexation_perimee_n_ecrit_pas(self, db_session, monkeypatch):
        """L'invariant qui compte : une indexation dépassée ne doit rien écrire.

        Première version de ce test : « jamais deux tâches en même temps ». Trop
        strict, et surtout à côté du sujet — une annulation ne prend effet qu'au
        prochain point d'attente, donc un chevauchement transitoire existe
        forcément. Ce qui importe n'est pas qu'elles ne se croisent jamais, mais
        qu'une indexation remplacée n'aille pas au bout de son travail après
        avoir supprimé l'entrée existante.
        """
        from app.services import user_profile as module

        ecritures: list[str] = []

        async def indexation_lente(profile):
            await asyncio.sleep(0.05)
            ecritures.append(profile.name)

        monkeypatch.setattr(module, "_embed_profile", indexation_lente)

        await module.set_user_profile(db_session, module.UserProfile(name="Ancien"))
        await module.set_user_profile(db_session, module.UserProfile(name="Nouveau"))
        await _attendre_les_indexations()

        assert ecritures == ["Nouveau"], (
            f"écritures constatées : {ecritures}. L'indexation périmée a écrit "
            "malgré son remplacement, ou la plus récente a été perdue."
        )

    @pytest.mark.asyncio
    async def test_le_dernier_profil_enregistre_gagne(self, db_session, monkeypatch):
        """Un double clic ne doit pas laisser l'ancien nom dans l'index."""
        from app.services import user_profile as module

        indexes: list[str] = []

        async def indexation(profile):
            await asyncio.sleep(0.02)
            indexes.append(profile.name)

        monkeypatch.setattr(module, "_embed_profile", indexation)

        await module.set_user_profile(db_session, module.UserProfile(name="Jérome"))
        await module.set_user_profile(db_session, module.UserProfile(name="Jérôme"))
        await _attendre_les_indexations()

        assert indexes[-1] == "Jérôme", (
            f"l'index garde « {indexes[-1]} » alors que le profil enregistré "
            "porte « Jérôme » : la correction du testeur est perdue"
        )


class TestLaSuppressionNeGelePasNonPlus:
    def test_la_suppression_qdrant_sort_de_la_boucle(self):
        """Même piège que l'ajout : `delete_by_entity` est synchrone."""
        import inspect

        from app.services import user_profile as module

        source = inspect.getsource(module)
        bloc_index = source[source.index("async def _embed_profile"):]

        assert "qdrant.delete_by_entity(" not in bloc_index, (
            "la suppression synchrone gèle la boucle d'événements, comme le "
            "faisait l'ajout avant sa correction"
        )
