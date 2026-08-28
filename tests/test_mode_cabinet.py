"""C3 — le mode cloisonné ferme LES DEUX portes, pas une seule.

Campagne dix personas, finding F5 de l'avocat. Sa conversation était rattachée
au dossier Rousset, et THÉRÈSE lui a ressorti la lettre de licenciement d'un
autre client plus le traitement anxiolytique de sa cliente.

Le piège, relevé par la relecture de design : il y a DEUX lecteurs de la
mémoire, et fermer un seul ne protège rien.

  * la recherche vectorielle (`_get_memory_context` → `qdrant.async_search`,
    paramètre `include_global`) — c'est elle qui répond au premier tour ;
  * l'outil `read_contact` (`_cloison_contacts`), qui interroge SQL — c'est lui
    qui répond au second, quand le modèle demande la fiche par son nom.

« Tu fermerais le RAG, l'outil SQL recrache le secret. »

Le mode est un RÉGLAGE, pas un défaut : pour un artisan qui a un carnet
d'adresses commun à ses chantiers, le cloisonnement strict serait une punition.
Pour un avocat, c'est la condition d'usage.
"""
import pytest

from app.services import cloisonnement


@pytest.fixture(autouse=True)
def _defaut_neutre():
    cloisonnement.poser_mode_cabinet(None)
    yield
    cloisonnement.poser_mode_cabinet(None)


class TestLaPolitiqueEstUnique:
    """Une seule décision, lue par les deux lecteurs."""

    def test_le_defaut_reste_le_carnet_partage(self):
        """Ne pas punir l'artisan pour protéger l'avocat."""
        assert cloisonnement.mode_cabinet_actif() is False
        assert cloisonnement.souvenirs_globaux_visibles() is True

    def test_le_mode_cabinet_ferme_les_souvenirs_globaux(self):
        cloisonnement.poser_mode_cabinet(True)
        assert cloisonnement.souvenirs_globaux_visibles() is False

    def test_une_conversation_libre_reste_ouverte_meme_en_mode_cabinet(self):
        """Sans dossier, il n'y a rien à cloisonner.

        Fermer ici ne protégerait personne et casserait l'usage courant : une
        question posée hors dossier n'a aucun périmètre à respecter.
        """
        cloisonnement.poser_mode_cabinet(True)
        assert cloisonnement.souvenirs_globaux_visibles(scope=None) is True
        assert cloisonnement.souvenirs_globaux_visibles(scope="global") is True

    def test_le_mode_ne_ferme_que_les_conversations_rattachees(self):
        cloisonnement.poser_mode_cabinet(True)
        assert cloisonnement.souvenirs_globaux_visibles(scope="project") is False


class TestLesDeuxPortesLisentLaMemePolitique:
    """Le point qui a fait tomber la V1 du design."""

    def test_la_recherche_vectorielle_consulte_la_politique(self):
        import inspect

        from app.routers import chat

        source = inspect.getsource(chat._get_memory_context)
        assert "souvenirs_globaux_visibles" in source, (
            "le RAG doit passer include_global selon la politique, pas le défaut"
        )

    def test_l_outil_read_contact_consulte_la_meme_politique(self):
        import inspect

        from app.services import memory_tools

        source = inspect.getsource(memory_tools._cloison_contacts)
        assert "souvenirs_globaux_visibles" in source, (
            "sans cela, le modèle demande la fiche par son nom et obtient le "
            "secret que le RAG venait de lui cacher"
        )


class TestEtancheiteReelleDuDossier:
    """Le test que la relecture réclamait : on écrit un secret, on le cherche.

    Pas de lecture de source ici. On pose une fiche GLOBALE contenant un secret
    (le cas exact de l'avocat : le traitement médical de sa cliente vit dans sa
    fiche, pas dans un fichier), puis on interroge depuis une conversation
    rattachée à un AUTRE dossier.

    Les deux moitiés comptent : le secret doit disparaître en mode cabinet, et
    rester accessible sans le mode — sinon on aurait « corrigé » l'avocat en
    cassant l'artisan.
    """

    @pytest.mark.asyncio
    async def test_le_carnet_general_disparait_du_dossier_en_mode_cabinet(self, client):
        from sqlalchemy import select

        from app.models.database import get_session_context
        from app.models.entities import Contact
        from app.services.memory_tools import _cloison_contacts

        async with get_session_context() as session:
            session.add(
                Contact(
                    first_name="Germaine",
                    last_name="Rousset",
                    display_name="Germaine Rousset",
                    notes="Traitement anxiolytique prescrit par le Dr Klein",
                    scope="global",
                )
            )
            await session.commit()

            # Conversation rattachée au dossier « Valette », carnet partagé.
            cloisonnement.poser_mode_cabinet(False)
            ouvert = await session.execute(
                _cloison_contacts(select(Contact), "project", "dossier-valette", None)
            )
            assert any(
                c.last_name == "Rousset" for c in ouvert.scalars().all()
            ), "sans le mode, le carnet général reste visible — c'est le défaut"

            # Même requête, mode cabinet.
            cloisonnement.poser_mode_cabinet(True)
            ferme = await session.execute(
                _cloison_contacts(select(Contact), "project", "dossier-valette", None)
            )
            assert not any(c.last_name == "Rousset" for c in ferme.scalars().all()), (
                "en mode cabinet, le secret d'un autre dossier ne doit pas "
                "remonter dans celui-ci"
            )

    @pytest.mark.asyncio
    async def test_une_conversation_libre_voit_toujours_son_carnet(self, client):
        """Le mode ne doit pas rendre l'application inutilisable hors dossier."""
        from sqlalchemy import select

        from app.models.database import get_session_context
        from app.models.entities import Contact
        from app.services.memory_tools import _cloison_contacts

        async with get_session_context() as session:
            session.add(
                Contact(first_name="Alain", last_name="Moreau",
                        display_name="Alain Moreau", scope="global")
            )
            await session.commit()

            cloisonnement.poser_mode_cabinet(True)
            resultat = await session.execute(
                _cloison_contacts(select(Contact), "global", None, None)
            )
            assert any(c.last_name == "Moreau" for c in resultat.scalars().all()), (
                "hors dossier, il n'y a rien à cloisonner : fermer ici ne "
                "protégerait personne et casserait l'usage courant"
            )


class TestLeModeEstAtteignable:
    """Une politique qu'aucun écran n'expose est un contrôle mort.

    Même leçon que `ContactCreate.scope`, qui porte un périmètre depuis la
    revue L6 sans qu'aucun formulaire ne l'envoie.
    """

    def test_le_demarrage_charge_le_reglage(self):
        import inspect

        from app import main

        assert "poser_mode_cabinet" in inspect.getsource(main), (
            "le mode doit survivre à un redémarrage, comme la préférence de "
            "recherche web"
        )

    def test_le_reglage_previent_la_politique_quand_il_change(self):
        import inspect

        from app.routers import config as routeur_config

        assert "poser_mode_cabinet" in inspect.getsource(routeur_config), (
            "sans cela, activer le mode n'aurait effet qu'au prochain démarrage"
        )
