"""BUG-172 — « Délai de 30 000 ms dépassé » alors que le profil est enregistré.

Un testeur installe THÉRÈSE sur une machine modeste (AMD E1-7010, 1,5 GHz). À la
création du profil, tout premier écran du logiciel, il voit « Délai de 30 000 ms
dépassé ». Il croit que l'installation a échoué.

Les journaux du sidecar disent l'inverse : « User profile saved: Jérôme
DELAUNAY », HTTP 200, puis les contrôles de santé répondent normalement. Le
profil était enregistré. Ce que l'interface a abandonné, c'est l'attente.

La cause n'est pas la lenteur de sa machine, c'est l'ordre des opérations. Le
profil est écrit en base (`user_profile.py`, `session.commit()`), PUIS le vecteur
sémantique est calculé — 19 secondes chez lui — et la réponse HTTP n'est renvoyée
qu'après. Le client, lui, abandonne à 30 secondes.

Allonger ce délai serait le mauvais correctif : il déplacerait le seuil sans
supprimer l'attente, et une machine plus lente le franchirait à nouveau. Le
travail durable est fait ; c'est ce qui reste à faire qui doit sortir du chemin
de la réponse.

Second défaut, releve par la revue : le calcul du vecteur appelle la version
SYNCHRONE de Qdrant. Sorti de la requête sans sortir de la boucle d'événements,
il gèlerait simplement une AUTRE requête — le serveur n'a qu'un seul processus.
"""
import asyncio

import pytest


class TestLaReponseNAttendPasLeVecteur:
    @pytest.mark.asyncio
    async def test_le_profil_est_rendu_sans_attendre_l_indexation(
        self, db_session, monkeypatch
    ):
        """Le cœur du bug : 19 secondes d'attente pour un travail déjà fait."""
        from app.services import user_profile as module

        indexation_lancee = asyncio.Event()

        async def indexation_interminable(profile):
            indexation_lancee.set()
            await asyncio.sleep(60)  # plus long que tout délai client

        monkeypatch.setattr(module, "_embed_profile", indexation_interminable)

        profil = module.UserProfile(name="Jérôme DELAUNAY")

        enregistre = await asyncio.wait_for(
            module.set_user_profile(db_session, profil), timeout=5.0
        )

        assert enregistre.name == "Jérôme DELAUNAY", (
            "la sauvegarde attend la fin de l'indexation : sur une machine "
            "lente, l'utilisateur voit un faux échec alors que son profil est "
            "bien enregistré"
        )

    @pytest.mark.asyncio
    async def test_l_indexation_se_fait_quand_meme(self, db_session, monkeypatch):
        """Le verrou inverse : répondre vite ne doit pas signifier oublier.

        Sans ce test, un correctif pourrait supprimer l'indexation au lieu de la
        différer — la question « qui suis-je ? » resterait alors sans réponse.
        """
        from app.services import user_profile as module

        appels: list[str] = []

        async def indexation_rapide(profile):
            appels.append(profile.name)

        monkeypatch.setattr(module, "_embed_profile", indexation_rapide)

        await module.set_user_profile(db_session, module.UserProfile(name="Jérôme"))
        await asyncio.sleep(0.1)  # laisser la tâche différée s'exécuter

        assert appels == ["Jérôme"], (
            "le profil n'est plus indexé du tout : la recherche sémantique ne "
            "retrouvera jamais son propriétaire"
        )

    @pytest.mark.asyncio
    async def test_une_indexation_qui_echoue_ne_perd_pas_le_profil(
        self, db_session, monkeypatch
    ):
        """Une tâche différée qui échoue ne doit pas emporter la sauvegarde."""
        from app.services import user_profile as module

        async def indexation_cassee(profile):
            raise RuntimeError("Qdrant indisponible")

        monkeypatch.setattr(module, "_embed_profile", indexation_cassee)

        profil = await module.set_user_profile(
            db_session, module.UserProfile(name="Jérôme")
        )
        await asyncio.sleep(0.1)

        assert profil.name == "Jérôme"


class TestLIndexationNeGelePasLeServeur:
    """Le serveur n'a qu'un processus : un calcul synchrone bloque tout.

    Différer l'indexation sans la sortir de la boucle d'événements déplacerait
    simplement le gel sur une autre requête, celle d'un utilisateur qui n'a rien
    demandé.
    """

    def test_l_indexation_n_appelle_pas_la_version_synchrone(self):
        import inspect

        from app.services import user_profile as module

        source = inspect.getsource(module._embed_profile)

        assert "qdrant.add_memory(" not in source, (
            "l'indexation appelle la version synchrone de Qdrant : les 19 s "
            "gèleraient une requête arbitraire au lieu de celle du profil"
        )
        assert (
            "async_add_memory" in source or "to_thread" in source
        ), "l'indexation doit passer par la voie asynchrone ou par un thread"
