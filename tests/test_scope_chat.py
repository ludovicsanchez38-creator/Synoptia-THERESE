"""
0.43 - Le cloisonnement documentaire appliqué au chat.

La 0.42 a livré la moitié du travail : les documents portent enfin leur
périmètre dans le payload Qdrant, et `QdrantService.search` sait filtrer
dessus. Mais le contexte du chat cherchait toujours SANS aucune cloison
(`_get_memory_context`, `chat.py:302`) — un document rattaché au projet A
pouvait donc ressortir dans une conversation qui parle du projet B.

Pour un assistant qui agrège les données de plusieurs clients, c'est un défaut
de confidentialité, pas une gêne d'ergonomie : l'utilisateur ne voit pas d'où
vient le contexte injecté, et le modèle non plus.

Ce qui manquait : une conversation n'avait aucun rattachement. `Conversation`
ne portait ni projet ni périmètre.

Choix de conception, à garder en tête en lisant ces tests :

- une conversation RATTACHÉE à un projet ne voit que les documents de ce projet
  et les documents globaux ;
- une conversation LIBRE continue de tout voir. C'est le comportement actuel,
  et le moins surprenant : quelqu'un qui discute hors projet veut sa mémoire
  entière. Cloisonner par défaut ferait disparaître des documents sans que
  personne ne l'ait demandé.
"""
import pytest


class TestUneConversationPeutEtreRattacheeAUnProjet:
    def test_le_modele_porte_le_rattachement(self):
        from app.models.entities import Conversation

        conversation = Conversation(title="Audit client A", project_id="projet-a")
        assert conversation.project_id == "projet-a"

    def test_le_rattachement_est_facultatif(self):
        """Une conversation libre reste la norme : rien ne doit devenir obligatoire."""
        from app.models.entities import Conversation

        assert Conversation(title="Notes").project_id is None


class TestLeContexteDuChatEstCloisonne:
    @pytest.mark.asyncio
    async def test_une_conversation_de_projet_ne_voit_que_son_projet(
        self, db_session, monkeypatch
    ):
        """Le cœur du sujet : plus de fuite d'un projet vers un autre."""
        from app.models.entities import Conversation
        from app.routers import chat as chat_router

        conversation = Conversation(id="conv-a", title="Client A", project_id="projet-a")
        db_session.add(conversation)
        await db_session.commit()

        appels: list[dict] = []

        async def faux_search(**kwargs):
            appels.append(kwargs)
            return []

        faux_qdrant = type("Faux", (), {"async_search": staticmethod(faux_search)})()
        monkeypatch.setattr(chat_router, "get_qdrant_service", lambda: faux_qdrant)

        await chat_router._get_memory_context(
            "où en est le dossier ?", conversation_id="conv-a", session=db_session
        )

        assert appels, "aucune recherche mémoire lancée"
        assert appels[0].get("scope") == "project", (
            "la recherche n'est pas cloisonnée : un document d'un autre projet "
            "peut être injecté dans cette conversation"
        )
        assert appels[0].get("scope_id") == "projet-a"

    @pytest.mark.asyncio
    async def test_une_conversation_libre_ne_voit_que_les_documents_generaux(
        self, db_session, monkeypatch
    ):
        """MOINDRE PRIVILÈGE — décision révisée après la revue.

        La première version laissait une conversation libre voir TOUS les
        projets. Défendable si le périmètre n'était qu'une préférence de
        pertinence ; intenable dès lors qu'on le présente comme une protection
        entre clients. Le défaut doit suivre la règle qu'il annonce.

        Ce que l'utilisateur perd : rien s'il n'utilise pas les projets — ses
        documents sont globaux. S'il en utilise, une conversation libre cesse
        de piocher dans les dossiers clients, ce qui est précisément le but.
        Le mode « tous les projets » reste accessible, explicitement.
        """
        from app.models.entities import Conversation
        from app.routers import chat as chat_router

        conversation = Conversation(id="conv-libre", title="Notes")
        db_session.add(conversation)
        await db_session.commit()

        appels: list[dict] = []

        async def faux_search(**kwargs):
            appels.append(kwargs)
            return []

        faux_qdrant = type("Faux", (), {"async_search": staticmethod(faux_search)})()
        monkeypatch.setattr(chat_router, "get_qdrant_service", lambda: faux_qdrant)

        await chat_router._get_memory_context(
            "rappelle-moi", conversation_id="conv-libre", session=db_session
        )

        assert appels, "aucune recherche mémoire lancée"
        assert appels[0].get("scope") == "global", (
            "une conversation libre pioche encore dans les dossiers clients : "
            "le défaut ne respecte pas la règle qu'il annonce"
        )

    @pytest.mark.asyncio
    async def test_le_mode_tous_les_projets_reste_possible_explicitement(
        self, db_session, monkeypatch
    ):
        """Le moindre privilège ne doit pas supprimer l'usage transversal.

        Chercher dans toute la mémoire reste légitime — cela devient un choix
        assumé, affiché, au lieu d'être le comportement par défaut silencieux.
        """
        from app.models.entities import Conversation
        from app.routers import chat as chat_router

        conversation = Conversation(
            id="conv-transverse", title="Revue générale", memory_scope="all"
        )
        db_session.add(conversation)
        await db_session.commit()

        appels: list[dict] = []

        async def faux_search(**kwargs):
            appels.append(kwargs)
            return []

        faux_qdrant = type("Faux", (), {"async_search": staticmethod(faux_search)})()
        monkeypatch.setattr(chat_router, "get_qdrant_service", lambda: faux_qdrant)

        await chat_router._get_memory_context(
            "compare les dossiers", conversation_id="conv-transverse", session=db_session
        )

        assert appels and appels[0].get("scope") is None, (
            "le mode transversal explicite doit lever la cloison"
        )

    @pytest.mark.asyncio
    async def test_sans_conversation_connue_rien_ne_casse(self, db_session, monkeypatch):
        """Les appels historiques (sans conversation) doivent continuer de marcher."""
        from app.routers import chat as chat_router

        appels: list[dict] = []

        async def faux_search(**kwargs):
            appels.append(kwargs)
            return []

        faux_qdrant = type("Faux", (), {"async_search": staticmethod(faux_search)})()
        monkeypatch.setattr(chat_router, "get_qdrant_service", lambda: faux_qdrant)

        await chat_router._get_memory_context("bonjour")

        assert appels and appels[0].get("scope") is None


class TestLaFrontiereEchoueFermee:
    @pytest.mark.asyncio
    async def test_un_rattachement_illisible_ne_rouvre_pas_la_memoire(
        self, db_session, monkeypatch
    ):
        """Finding MAJEUR de la revue : la cloison s'élargissait sur incident.

        La première version retombait sur une recherche globale dès que la
        lecture du rattachement échouait. Une simple erreur SQLite transitoire
        transformait donc une conversation cloisonnée en conversation ouverte,
        sans que rien ne le signale — le contexte d'un autre client pouvait
        être injecté.

        Une frontière de confidentialité doit échouer FERMÉE.
        """
        from app.routers import chat as chat_router

        appels: list[dict] = []

        async def faux_search(**kwargs):
            appels.append(kwargs)
            return []

        faux_qdrant = type("Faux", (), {"async_search": staticmethod(faux_search)})()
        monkeypatch.setattr(chat_router, "get_qdrant_service", lambda: faux_qdrant)

        class SessionQuiCasse:
            async def get(self, *_args, **_kwargs):
                raise RuntimeError("base momentanément indisponible")

        await chat_router._get_memory_context(
            "question", conversation_id="conv-x", session=SessionQuiCasse()
        )

        assert appels, "aucune recherche lancée"
        assert appels[0].get("scope") is not None, (
            "la recherche est repartie en mode global sur incident : une "
            "conversation cloisonnée peut recevoir le contexte d'un autre client"
        )
        assert appels[0].get("scope_id") == chat_router._PERIMETRE_INDETERMINE


class TestLeCablageReelDuChat:
    def test_tous_les_appels_du_chat_transmettent_la_conversation(self):
        """Le paramètre ne sert à rien si personne ne le passe.

        Les tests ci-dessus appellent `_get_memory_context` directement : ils
        prouvent que la fonction cloisonne, pas qu'elle est appelée ainsi. Le
        défaut que ce chantier corrige est précisément là — une infrastructure
        complète, correcte, et jamais branchée.

        On vérifie donc le câblage à la source : dans `routers/chat.py`, TOUT
        appel à `_get_memory_context` doit transmettre `conversation_id`.
        L'analyse est faite sur l'arbre syntaxique, pas par recherche de texte :
        un appel reformaté ou passé sur plusieurs lignes reste détecté.
        """
        import ast
        import pathlib

        chemin = (
            pathlib.Path(__file__).resolve().parents[1]
            / "src" / "backend" / "app" / "routers" / "chat.py"
        )
        arbre = ast.parse(chemin.read_text(encoding="utf-8"))

        appels = [
            noeud
            for noeud in ast.walk(arbre)
            if isinstance(noeud, ast.Call)
            and isinstance(noeud.func, ast.Name)
            and noeud.func.id == "_get_memory_context"
        ]

        assert appels, "aucun appel trouvé : le test ne prouverait rien"

        # Les DEUX arguments sont nécessaires : sans `session`,
        # `_perimetre_de_conversation` rend `(None, None)` et la cloison ne
        # s'applique pas. La première version de ce test n'exigeait que
        # `conversation_id` — elle restait verte avec un câblage cassé (relevé
        # en revue). On vérifie aussi que les valeurs ne sont pas des littéraux
        # `None`, qui satisferaient la présence du mot-clé sans rien cloisonner.
        defauts: list[str] = []
        for noeud in appels:
            passes = {kw.arg: kw.value for kw in noeud.keywords}
            for requis in ("conversation_id", "session"):
                valeur = passes.get(requis)
                if valeur is None:
                    defauts.append(f"ligne {noeud.lineno} : `{requis}` absent")
                elif isinstance(valeur, ast.Constant) and valeur.value is None:
                    defauts.append(f"ligne {noeud.lineno} : `{requis}=None` en dur")

        assert not defauts, (
            "la recherche mémoire n'est pas cloisonnée — "
            + " ; ".join(defauts)
            + ". Un document d'un autre projet peut être injecté."
        )


class TestRattacherUneConversation:
    """Sans moyen de rattacher, `project_id` reste NULL et la cloison ne
    s'applique jamais. Une colonne morte, c'est-à-dire exactement le défaut que
    ce chantier corrige."""

    def test_la_reponse_expose_le_rattachement(self, client):
        """L'interface doit pouvoir afficher à quoi la conversation est rattachée."""
        creation = client.post("/api/chat/conversations", json={"title": "Client A"})
        assert creation.status_code in (200, 201), creation.text
        conversation_id = creation.json()["id"]

        lecture = client.get(f"/api/chat/conversations/{conversation_id}")
        assert lecture.status_code == 200
        assert "project_id" in lecture.json(), (
            "le rattachement n'est pas exposé : l'utilisateur ne peut pas savoir "
            "quels documents sa conversation consultera"
        )

    def test_rattacher_puis_detacher(self, client):
        creation = client.post("/api/chat/conversations", json={"title": "Client A"})
        conversation_id = creation.json()["id"]

        projet = client.post(
            "/api/memory/projects", json={"name": "Projet Alpha", "status": "active"}
        )
        assert projet.status_code in (200, 201), projet.text
        project_id = projet.json()["id"]

        rattachement = client.patch(
            f"/api/chat/conversations/{conversation_id}/project",
            json={"project_id": project_id},
        )
        assert rattachement.status_code == 200, rattachement.text
        assert rattachement.json()["project_id"] == project_id

        detachement = client.patch(
            f"/api/chat/conversations/{conversation_id}/project",
            json={"project_id": None},
        )
        assert detachement.status_code == 200
        assert detachement.json()["project_id"] is None

    def test_un_projet_inconnu_est_refuse(self, client):
        """Rattacher à un projet inexistant cloisonnerait sur du vide : la
        conversation ne verrait plus aucun document, sans explication."""
        creation = client.post("/api/chat/conversations", json={"title": "Client A"})
        conversation_id = creation.json()["id"]

        reponse = client.patch(
            f"/api/chat/conversations/{conversation_id}/project",
            json={"project_id": "projet-qui-n-existe-pas"},
        )
        assert reponse.status_code == 404, reponse.text


class TestSuppressionDUnProjet:
    def test_supprimer_un_projet_detache_ses_conversations(self, client):
        """Finding de la revue : `project_id` n'est pas une clé étrangère.

        Sans ce ménage, la conversation reste cloisonnée sur un identifiant
        supprimé : le backend continue de filtrer dessus — donc plus aucun
        document — pendant que le sélecteur, ne trouvant plus le projet dans la
        liste, affiche « Toute la mémoire ». L'écran mentirait sur la cloison.
        """
        projet = client.post(
            "/api/memory/projects", json={"name": "Projet éphémère", "status": "active"}
        )
        project_id = projet.json()["id"]

        conversation = client.post("/api/chat/conversations", json={"title": "Suivi"})
        conversation_id = conversation.json()["id"]
        client.patch(
            f"/api/chat/conversations/{conversation_id}/project",
            json={"project_id": project_id},
        )

        suppression = client.delete(f"/api/memory/projects/{project_id}")
        assert suppression.status_code == 200, suppression.text

        relue = client.get(f"/api/chat/conversations/{conversation_id}")
        assert relue.status_code == 200
        assert relue.json()["project_id"] is None, (
            "la conversation reste rattachée à un projet supprimé : elle ne "
            "verra plus aucun document, alors que l'interface annoncera "
            "« Toute la mémoire »"
        )


class TestMigrationDesBasesExistantes:
    def test_la_colonne_est_ajoutee_a_une_base_deja_installee(self, tmp_path):
        """Le piège documenté : `create_all()` n'ajoute AUCUNE colonne.

        Les testeurs ont déjà une base 0.42. Sans migration ad hoc explicite, la
        colonne manquerait et toute lecture de conversation planterait — aucun
        `alembic upgrade head` ne tourne au démarrage packagé.
        """
        import sqlite3

        from app.models.database import apply_adhoc_migrations

        chemin = tmp_path / "therese.db"
        with sqlite3.connect(chemin) as conn:
            # Une table `conversations` telle qu'elle existe en 0.42.
            conn.execute(
                "CREATE TABLE conversations ("
                "id TEXT PRIMARY KEY, title TEXT, summary TEXT, "
                "created_at TEXT, updated_at TEXT)"
            )
            conn.commit()

        apply_adhoc_migrations(chemin)

        with sqlite3.connect(chemin) as conn:
            colonnes = {row[1] for row in conn.execute("PRAGMA table_info(conversations)")}
            index = {row[1] for row in conn.execute("PRAGMA index_list(conversations)")}
        assert "ix_conversations_project_id" in index, (
            "l'index manque sur une base existante : `Field(index=True)` ne "
            "s'applique qu'à `create_all()`, jamais à un ALTER TABLE. Le "
            "filtrage par projet balaierait toute la table."
        )
        assert "project_id" in colonnes, (
            "la colonne manque sur une base existante : la lecture des "
            "conversations échouerait après mise à jour"
        )

    def test_la_migration_est_idempotente(self, tmp_path):
        """Elle tourne à chaque démarrage : deux passages ne doivent pas lever."""
        import sqlite3

        from app.models.database import apply_adhoc_migrations

        chemin = tmp_path / "therese.db"
        with sqlite3.connect(chemin) as conn:
            conn.execute(
                "CREATE TABLE conversations ("
                "id TEXT PRIMARY KEY, title TEXT, summary TEXT, "
                "created_at TEXT, updated_at TEXT)"
            )
            conn.commit()

        apply_adhoc_migrations(chemin)
        apply_adhoc_migrations(chemin)
