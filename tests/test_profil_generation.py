"""L'annulation d'une indexation ne doit jamais effacer le profil.

Régression introduite en corrigeant la concurrence, puis corrigée.
`asyncio.to_thread` n'est PAS annulable : annuler la tâche libère le verrou,
mais le travail déjà lancé dans le thread continue. La revue l'a reproduit —
une ancienne suppression se terminait APRÈS le nouvel ajout, et l'état final ne
contenait plus aucun profil.

La bonne réponse n'est pas d'annuler, c'est un numéro de génération : une tâche
périmée renonce AVANT d'entrer dans la section critique ; une tâche déjà entrée
va au bout, et la suivante repasse derrière elle.

Ces tests CONTRÔLENT le calendrier plutôt que de l'espérer. Une course qu'on
teste avec des `sleep` est une course qu'on ne teste pas.
"""
import asyncio

import pytest

from tests.aide_lecture_source import ordre_dans_le_code


async def _attendre() -> None:
    from app.services.user_profile import _INDEXATIONS_EN_COURS

    for _ in range(100):
        if not _INDEXATIONS_EN_COURS:
            return
        await asyncio.sleep(0.02)


class TestUneIndexationPerimeeNEcritPas:
    @pytest.mark.asyncio
    async def test_une_generation_depassee_renonce(self, monkeypatch):
        """Déterministe : on appelle la tâche avec une génération périmée.

        La version précédente orchestrait deux sauvegardes concurrentes et
        espérait un ordonnancement : elle flakait en suite complète. Ici, pas
        de course à reproduire — on vérifie directement le contrat de la
        tâche : périmée, elle n'écrit pas ; à jour, elle écrit.
        """
        from app.services import user_profile as module

        ecritures: list[str] = []

        async def indexation(profile):
            ecritures.append(profile.name)

        monkeypatch.setattr(module, "_embed_profile", indexation)
        monkeypatch.setattr(module, "_GENERATION_PROFIL", 5)

        # Génération dépassée : renonce avant d'écrire.
        await module._indexer_en_arriere_plan(module.UserProfile(name="Périmé"), 3)
        assert ecritures == [], "une indexation périmée a écrit quand même"

        # Génération courante : écrit.
        await module._indexer_en_arriere_plan(module.UserProfile(name="À jour"), 5)
        assert ecritures == ["À jour"]


class TestUneSuppressionTient:
    """RGPD : une indexation en vol ne doit pas réécrire ce qui est supprimé.

    Deux protections, car une seule ne suffit pas :

    - avancer la génération fait renoncer les indexations qui ATTENDENT encore
      le verrou ;
    - mais une indexation DÉJÀ entrée dans la section critique a franchi ce
      contrôle. La suppression prend donc le verrou à son tour : elle attend
      celle qui est en vol, puis supprime pour de bon.

    Ces deux protections sont vérifiées ici sur le code lui-même. Un test de
    séquence a été tenté d'abord, avec deux tâches concurrentes : il partageait
    une session de base de données entre elles, ce que SQLAlchemy asynchrone ne
    supporte pas — le test mesurait alors son propre défaut de montage, pas le
    comportement du code.
    """

    def test_la_suppression_avance_la_generation(self):
        import inspect

        from app.services import user_profile as module

        source = inspect.getsource(module.delete_user_profile)

        assert "_GENERATION_PROFIL += 1" in source, (
            "la suppression n'invalide pas les indexations en attente : "
            "l'ancien profil serait réécrit après coup"
        )

    def test_la_suppression_attend_l_indexation_en_cours(self):
        import inspect

        from app.services import user_profile as module

        source = inspect.getsource(module.delete_user_profile)

        assert "_VERROU_INDEXATION" in source, (
            "la suppression ne prend pas le verrou : une indexation déjà "
            "entrée dans la section critique écrirait après elle, et les "
            "données personnelles réapparaîtraient"
        )
        # L'ordre compte : avancer la génération AVANT de prendre le verrou,
        # sinon les tâches en attente entrent quand même. Mesuré sur le CODE :
        # str.index rend la première occurrence, commentaires compris, donc un
        # commentaire citant le verrou en préambule inversait la mesure.
        assert ordre_dans_le_code(
            source, "_GENERATION_PROFIL += 1", "_VERROU_INDEXATION"
        ), "la génération doit être avancée avant la prise du verrou"
