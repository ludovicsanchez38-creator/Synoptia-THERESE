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
    async def test_une_conversation_libre_voit_toute_la_memoire(
        self, db_session, monkeypatch
    ):
        """Garde-fou : ne pas amputer la mémoire de ceux qui n'utilisent pas les projets."""
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
        assert appels[0].get("scope") is None, (
            "une conversation sans projet ne doit pas être cloisonnée : "
            "l'utilisateur perdrait l'accès à ses propres documents"
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

        sans_perimetre = [
            noeud.lineno
            for noeud in appels
            if "conversation_id" not in {kw.arg for kw in noeud.keywords}
        ]
        assert not sans_perimetre, (
            f"appels sans périmètre aux lignes {sans_perimetre} : la recherche "
            "mémoire y reste non cloisonnée, un document d'un autre projet peut "
            "être injecté"
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
