"""L'indexation du profil : ce qui est réellement garanti.

Rappel du contexte. Le profil est enregistré, puis son vecteur sémantique
calculé en tâche de fond — 19 secondes sur la machine du testeur. Deux
sauvegardes rapprochées (son double clic) lancent donc deux indexations sur la
même entité, et chacune commence par supprimer l'ancienne.

Trois approches ont été essayées avant d'arriver ici :

1. un simple verrou : il sérialise mais ne garantit pas l'ordre de DÉMARRAGE,
   donc l'index pouvait garder l'ancien nom ;
2. l'annulation de la tâche périmée : PIRE, car `asyncio.to_thread` n'est pas
   annulable. Annuler libère le verrou, mais le travail engagé continue dans le
   thread — une ancienne suppression pouvait se terminer après le nouvel ajout
   et laisser l'index vide ;
3. un numéro de génération, retenu : une tâche renonce AVANT d'entrer dans la
   section critique si sa génération est dépassée ; une tâche déjà entrée va au
   bout, et la suivante repasse derrière elle. Rien n'est interrompu en vol.

Note de méthode. Deux tests de course ont été écrits puis retirés : ils
dépendaient de l'ordre d'ordonnancement d'asyncio et passaient isolément mais
pas en suite. Un test non déterministe est pire que pas de test — il fait perdre
du temps, puis finit ignoré. Ce qui est vérifiable l'est ici ; le comportement
concurrent est décrit par les invariants structurels, faute de pouvoir être
reproduit fidèlement.
"""
import asyncio

import pytest


async def _attendre_les_indexations() -> None:
    from app.services.user_profile import _INDEXATIONS_EN_COURS

    for _ in range(100):
        if not _INDEXATIONS_EN_COURS:
            return
        await asyncio.sleep(0.02)


class TestLIndexationSeFaitEtNeBloqueRien:
    @pytest.mark.asyncio
    async def test_le_profil_est_indexe(self, db_session, monkeypatch):
        from app.services import user_profile as module

        indexes: list[str] = []

        async def indexation(profile):
            indexes.append(profile.name)

        monkeypatch.setattr(module, "_embed_profile", indexation)

        await module.set_user_profile(db_session, module.UserProfile(name="Jérôme"))
        await _attendre_les_indexations()

        assert indexes == ["Jérôme"], (
            "le profil n'est pas indexé : la question « qui suis-je ? » "
            "restera sans réponse"
        )


class TestLesInvariantsDeConcurrence:
    """Ce que le code garantit, vérifié par son COMPORTEMENT (B-395).

    Les quatre tests précédents lisaient le texte de la source (`inspect.getsource`)
    et cherchaient des chaînes : ils rougissaient sur une réécriture équivalente et
    restaient verts si un appel synchrone revenait sous un autre nom. Ici, la
    course est rendue déterministe par des portes explicites : la première
    indexation est bloquée EN PLEINE écriture, les suivantes s'empilent derrière
    le verrou, puis la porte s'ouvre. Le verrou asyncio sert dans l'ordre.
    """

    @pytest.mark.asyncio
    async def test_une_sauvegarde_engagee_va_au_bout_une_depassee_renonce_la_derniere_gagne(
        self, db_session, monkeypatch
    ):
        from app.services import user_profile as module

        porte = asyncio.Event()
        engagee = asyncio.Event()
        indexes: list[str] = []

        async def indexation(profile):
            engagee.set()
            await porte.wait()
            indexes.append(profile.name)

        monkeypatch.setattr(module, "_embed_profile", indexation)

        await module.set_user_profile(db_session, module.UserProfile(name="Ancien"))
        await asyncio.wait_for(engagee.wait(), timeout=2)
        # Tant qu'elle court, la tâche est retenue par une référence forte :
        # sans cela le ramasse-miettes pourrait l'annuler en vol.
        assert module._INDEXATIONS_EN_COURS, "la tâche d'indexation n'est retenue nulle part"

        # Deux sauvegardes rapprochées (le double clic) pendant que la première écrit.
        await module.set_user_profile(db_session, module.UserProfile(name="Intermédiaire"))
        await module.set_user_profile(db_session, module.UserProfile(name="Dernier"))

        porte.set()
        await _attendre_les_indexations()

        assert indexes == ["Ancien", "Dernier"], (
            "attendu : la tâche déjà engagée va au bout (rien n'est annulé en vol), "
            "la génération dépassée renonce sans écrire, la dernière écrit ; "
            f"obtenu : {indexes}"
        )
        assert not module._INDEXATIONS_EN_COURS, "une tâche terminée reste référencée"


class TestLesAppelsQdrantNeGelentPasLeServeur:
    """Le serveur n'a qu'un processus : un appel synchrone de 19 secondes gèle la
    requête d'un autre écran. Les opérations Qdrant doivent donc s'exécuter HORS
    du fil de la boucle d'événements. Vérifié en observant le fil d'exécution
    réel, pas le texte de la source (B-395)."""

    @pytest.mark.asyncio
    async def test_aucune_operation_qdrant_ne_s_execute_sur_le_fil_de_la_boucle(self, monkeypatch):
        import threading

        from app.services import user_profile as module

        fil_de_la_boucle = threading.get_ident()
        appels: dict[str, int] = {}

        class FauxQdrant:
            def delete_by_entity(self, entity_id):
                appels["delete_by_entity"] = threading.get_ident()

            def add_memory(self, **kwargs):
                appels["add_memory"] = threading.get_ident()

            async def async_add_memory(self, **kwargs):
                await asyncio.to_thread(self.add_memory, **kwargs)

        monkeypatch.setattr(module, "get_qdrant_service", lambda: FauxQdrant())

        await module._embed_profile(module.UserProfile(name="Jérôme", company="Synoptïa"))

        assert set(appels) == {"delete_by_entity", "add_memory"}, appels
        for nom, fil in appels.items():
            assert fil != fil_de_la_boucle, (
                f"{nom} s'est exécuté sur le fil de la boucle d'événements : "
                "il la gèlerait pendant toute sa durée"
            )
