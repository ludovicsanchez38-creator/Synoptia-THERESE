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

from tests.aide_lecture_source import ordre_dans_le_code


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
    """Ce que le code garantit, vérifié sur le code lui-même.

    Ces invariants ne sont pas reproductibles fidèlement par un test de course :
    ils dépendent de l'ordonnanceur. Les vérifier structurellement vaut mieux
    que de les vérifier par un test qui ment une fois sur deux.
    """

    def test_chaque_sauvegarde_prend_un_numero_de_generation(self):
        import inspect

        from app.services import user_profile as module

        source = inspect.getsource(module.set_user_profile)

        assert "_GENERATION_PROFIL += 1" in source
        assert "_indexer_en_arriere_plan(profile, _GENERATION_PROFIL)" in source, (
            "la génération n'est pas transmise à la tâche : elle ne pourra pas "
            "savoir qu'elle est périmée"
        )

    def test_une_generation_depassee_renonce_avant_d_ecrire(self):
        import inspect

        from app.services import user_profile as module

        source = inspect.getsource(module._indexer_en_arriere_plan)

        assert "generation != _GENERATION_PROFIL" in source
        # L'ordre est décisif : le contrôle doit être DANS la section critique
        # et AVANT l'appel qui écrit.
        assert ordre_dans_le_code(
            source, "_VERROU_INDEXATION", "generation != _GENERATION_PROFIL"
        ), "le contrôle doit avoir lieu après la prise du verrou"
        assert ordre_dans_le_code(
            source, "generation != _GENERATION_PROFIL", "_embed_profile(profile)"
        ), "le contrôle doit précéder l'écriture, pas la suivre"

    def test_aucune_tache_n_est_annulee_en_vol(self):
        """L'annulation a été essayée, et elle effaçait le profil."""
        import inspect

        from app.services import user_profile as module

        source = inspect.getsource(module)

        assert ".cancel()" not in source, (
            "une tâche est annulée : `asyncio.to_thread` n'étant pas annulable, "
            "le travail engagé continuerait et pourrait effacer le profil"
        )

    def test_les_taches_sont_retenues_par_une_reference(self):
        """Sans référence forte, le ramasse-miettes peut annuler une tâche."""
        import inspect

        from app.services import user_profile as module

        source = inspect.getsource(module.set_user_profile)

        assert "_INDEXATIONS_EN_COURS.add(tache)" in source


class TestLesAppelsQdrantNeGelentPasLeServeur:
    """Trois appels synchrones ont été trouvés, pas un seul.

    Le serveur n'a qu'un processus : un appel synchrone de 19 secondes gèle la
    requête d'un autre écran, celle d'un utilisateur qui n'a rien demandé.
    """

    def test_aucun_appel_qdrant_synchrone_ne_subsiste(self):
        import inspect

        from app.services import user_profile as module

        source = inspect.getsource(module)

        for appel in ("qdrant.add_memory(", "qdrant.delete_by_entity("):
            assert appel not in source, (
                f"{appel} est appelé directement : il gèlerait la boucle "
                "d'événements pendant toute sa durée"
            )
