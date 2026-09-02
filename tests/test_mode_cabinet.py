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
    """Le point qui a fait tomber la V1 du design.

    Ces tests EXÉCUTENT la recherche et lisent l'argument réellement passé.
    Un premier jet se contentait de `"souvenirs_globaux_visibles" in
    inspect.getsource(...)` : la relecture a montré qu'un revert
    `include_global=True  # souvenirs_globaux_visibles(scope)` serait resté
    vert. Troisième fois aujourd'hui qu'un test de lecture de source rassure
    au lieu de vérifier.
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("cabinet", "attendu"),
        [(False, True), (True, False)],
        ids=["carnet partagé → global visible", "mode cabinet → global fermé"],
    )
    async def test_le_rag_passe_include_global_selon_la_politique(
        self, monkeypatch, cabinet, attendu
    ):
        from app.routers import chat as routeur_chat

        cloisonnement.poser_mode_cabinet(cabinet)
        arguments = {}

        class _QdrantEspion:
            async def async_search(self, **kwargs):
                arguments.update(kwargs)
                return []

        monkeypatch.setattr(routeur_chat, "get_qdrant_service", lambda: _QdrantEspion())

        async def _perimetre(*_args, **_kwargs):
            return ("project", "dossier-rousset")

        monkeypatch.setattr(routeur_chat, "_perimetre_de_conversation", _perimetre)

        await routeur_chat._get_memory_context("le dossier", None, session=None)

        assert arguments.get("include_global") is attendu, (
            f"cabinet={cabinet} : le RAG doit passer include_global={attendu}, "
            f"reçu {arguments.get('include_global')!r}"
        )

    @pytest.mark.asyncio
    async def test_l_outil_read_contact_lit_la_meme_politique(self, client):
        """Vérifié par le comportement SQL, pas par la source.

        Couvert en détail par TestEtancheiteReelleDuDossier ; on garde ici
        l'assertion de symétrie : les deux portes changent ensemble.
        """
        from app.models.database import get_session_context
        from app.models.entities import Contact
        from app.services.memory_tools import _cloison_contacts
        from sqlalchemy import select

        async with get_session_context() as session:
            session.add(
                Contact(first_name="Temoin", last_name="Global",
                        display_name="Temoin Global", scope="global")
            )
            await session.commit()

            resultats = {}
            for cabinet in (False, True):
                cloisonnement.poser_mode_cabinet(cabinet)
                trouves = await session.execute(
                    _cloison_contacts(select(Contact), "project", "un-dossier", None)
                )
                resultats[cabinet] = any(
                    c.last_name == "Global" for c in trouves.scalars().all()
                )

            assert resultats == {False: True, True: False}, (
                "la porte SQL doit suivre la même politique que le RAG"
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
        from app.models.database import get_session_context
        from app.models.entities import Contact
        from app.services.memory_tools import _cloison_contacts
        from sqlalchemy import select

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
        from app.models.database import get_session_context
        from app.models.entities import Contact
        from app.services.memory_tools import _cloison_contacts
        from sqlalchemy import select

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


class TestLActivationNEstJamaisSilencieuse:
    """Le point le plus grave de la relecture.

    « Toute fiche née de l'écran est `global`. Cabinet allumé, conversation
    Rousset : plus de Valette, plus de Mme Rousset non plus. Tu as malgré tout
    livré POST /api/config/mode-cabinet, qui pose le cache tout de suite. Aucun
    écran, aucun compteur, aucun garde. Un curl suffit à vider le dossier de sa
    propre personne. »

    L'activation doit donc DIRE combien de fiches deviendront invisibles, et
    exiger que l'appelant l'ait vu.
    """

    @pytest.mark.asyncio
    async def test_activer_sans_confirmation_est_refuse_et_compte_les_fiches(self, client):
        from app.models.database import get_session_context
        from app.models.entities import Contact

        async with get_session_context() as session:
            session.add(
                Contact(first_name="Germaine", last_name="Rousset",
                        display_name="Germaine Rousset", scope="global")
            )
            await session.commit()

        reponse = await client.post("/api/config/mode-cabinet?enabled=true")

        assert reponse.status_code == 409, (
            "activer le cloisonnement sans avoir vu combien de fiches il masque "
            "vide le dossier en silence"
        )
        # Le compte doit être EXPLOITABLE par l'écran qui l'affiche, donc dans
        # un champ, pas dans une phrase. Le gestionnaire global de l'app aplatit
        # les HTTPException en `str(detail)` : la route rend donc une
        # JSONResponse.
        detail = reponse.json()
        assert detail["fiches_generales"] >= 1
        assert "dossier" in detail["message"].lower(), (
            "le message doit dire CE QUE l'utilisateur perd, pas seulement "
            "qu'il faut confirmer"
        )
        assert cloisonnement.mode_cabinet_actif() is False, (
            "un refus ne doit surtout pas avoir posé le cache au passage"
        )

    @pytest.mark.asyncio
    async def test_activer_en_confirmant_fonctionne(self, client):
        reponse = await client.post("/api/config/mode-cabinet?enabled=true&confirme=true")

        assert reponse.status_code == 200
        assert cloisonnement.mode_cabinet_actif() is True

    @pytest.mark.asyncio
    async def test_couper_le_mode_ne_demande_aucune_confirmation(self, client):
        """Revenir au carnet partagé ne masque rien : rien à confirmer."""
        cloisonnement.poser_mode_cabinet(True)

        reponse = await client.post("/api/config/mode-cabinet?enabled=false")

        assert reponse.status_code == 200
        assert cloisonnement.mode_cabinet_actif() is False


class TestLaPorteDeriveeNeContournePasLeCompte:
    """
    Revue de release (Soso, 28/08).

    `POST /api/config/mode-cabinet` refuse au premier appel (409) en annonçant
    combien de fiches vont sortir du champ des réponses, et n'accepte qu'au
    second, confirmé. Mais `PUT /api/config/preferences/mode_cabinet` écrit la
    même préférence sans rien compter : au redémarrage, `main.py` la relit et
    pose le mode. Le cloisonnement s'activerait sans que personne ait vu le
    nombre, donc sans que personne ait pu constater que des fiches allaient
    devenir invisibles à THÉRÈSE.

    Portée réelle, mesurée : la route est aujourd'hui INATTEIGNABLE par HTTP.
    Son paramètre `value: str | int | float | bool | list | dict` fait répondre
    « Field required » à toutes les formes essayées (corps booléen, corps
    chaîne, corps enveloppé, paramètre d'URL) — pour mode_cabinet comme pour
    n'importe quelle préférence. Le contournement n'est donc pas exploitable
    en l'état, et cette garde est une défense en profondeur : elle tient si le
    jour où la route est réparée, personne ne repense au comptage.

    D'où l'appel direct à la fonction, comme pour `qwen_base_url`
    (`test_dette_0434_llm.py`) : c'est la GARDE qui est prouvée ici, pas le
    transport, qui lui ne passe pas.
    """

    @pytest.mark.asyncio
    async def test_la_porte_generique_refuse_mode_cabinet(self, db_session):
        from app.routers.config import set_preference
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as leve:
            await set_preference(key="mode_cabinet", value="true", session=db_session)
        assert leve.value.status_code == 400
        assert "mode-cabinet" in str(leve.value.detail), (
            "le refus doit dire par où passer, sinon il ressemble à une panne"
        )

    @pytest.mark.asyncio
    async def test_le_refus_ne_depend_pas_de_la_casse(self, db_session):
        from app.routers.config import set_preference
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            await set_preference(key="MODE_CABINET", value="true", session=db_session)

    @pytest.mark.asyncio
    async def test_une_preference_ordinaire_passe_toujours(self, db_session):
        """La garde vise une clé, pas la route : sans ceci, elle pourrait tout fermer."""
        from app.routers.config import set_preference

        resultat = await set_preference(
            key="theme_preference", value="dark", session=db_session
        )
        assert resultat is not None


class TestLaSuppressionGeneriqueNeCoupePasLeCloisonnement:
    """B-053 (RP05) — la porte dérivée avait un jumeau resté ouvert.

    `PUT /api/config/preferences/mode_cabinet` refuse (400) parce que le mode
    a sa propre porte. `DELETE /api/config/preferences/{key}`, lui, n'avait
    reçu aucune garde : il rendait 200, effaçait la préférence, et le
    cloisonnement d'un cabinet tombait sans comptage, sans confirmation et
    sans trace. Pire, `poser_mode_cabinet` n'étant pas appelé, la base disait
    « coupé » pendant que le cache du processus disait encore « actif ».

    Contrairement au PUT, cette route est ATTEIGNABLE en HTTP (aucun corps
    requis) : le contournement était donc exploitable en l'état.
    """

    @pytest.mark.asyncio
    async def test_la_cle_mode_cabinet_ne_se_supprime_pas_par_la_route_generique(
        self, client
    ):
        active = await client.post(
            "/api/config/mode-cabinet?enabled=true&confirme=true"
        )
        assert active.status_code == 200, active.text
        assert cloisonnement.mode_cabinet_actif() is True

        efface = await client.delete("/api/config/preferences/mode_cabinet")

        assert efface.status_code == 400, efface.text
        assert "mode-cabinet" in efface.json()["message"]

        etat = await client.get("/api/config/mode-cabinet")
        assert etat.json() == {"enabled": True}
        assert cloisonnement.mode_cabinet_actif() is True

    @pytest.mark.asyncio
    async def test_le_refus_de_suppression_ne_depend_pas_de_la_casse(self, client):
        active = await client.post(
            "/api/config/mode-cabinet?enabled=true&confirme=true"
        )
        assert active.status_code == 200, active.text

        efface = await client.delete("/api/config/preferences/MODE_CABINET")

        assert efface.status_code == 400, efface.text

    @pytest.mark.asyncio
    async def test_une_preference_ordinaire_se_supprime_toujours(self, client):
        """La garde vise une clé, pas la route."""
        pose = await client.post("/api/config/web-search?enabled=true")
        assert pose.status_code == 200, pose.text

        efface = await client.delete("/api/config/preferences/web_search_enabled")

        assert efface.status_code == 200, efface.text
        assert efface.json()["deleted"] is True
