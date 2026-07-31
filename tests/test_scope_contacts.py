"""
0.43 - Le cloisonnement doit aussi couvrir les CONTACTS.

Relevé en revue : la cloison posée sur les documents laissait entière une
seconde porte. `read_contact` charge tous les contacts
(`memory_tools.py:433`) et rend nom, téléphone, e-mail, notes et activités.
Un contact rattaché au projet A est donc lisible depuis une conversation du
projet B — il suffit que le modèle appelle l'outil.

C'est la même fuite que pour les documents, sur un autre chemin, et avec des
données plus sensibles : des coordonnées et des notes de client.

`Contact` porte déjà `scope` / `scope_id` (E3-05), comme `FileMetadata`. Ils
n'étaient simplement jamais consultés à la lecture.
"""
import json

import pytest


class TestLesOutilsMemoireRespectentLePerimetre:
    @pytest.mark.asyncio
    async def test_un_contact_d_un_autre_projet_n_est_pas_lisible(self, db_session):
        from app.models.entities import Contact
        from app.services.memory_tools import execute_memory_tool

        db_session.add(
            Contact(
                id="c-a",
                first_name="Amélie",
                last_name="Duran",
                phone="0600000000",
                notes="Budget confidentiel du client A",
                scope="project",
                scope_id="projet-a",
            )
        )
        await db_session.commit()

        brut = await execute_memory_tool(
            "read_contact",
            {"query": "Amélie"},
            db_session,
            scope="project",
            scope_id="projet-b",
        )
        resultat = json.dumps(brut) if not isinstance(brut, str) else brut

        assert "0600000000" not in resultat, (
            "les coordonnées d'un contact d'un autre projet sont divulguées"
        )
        assert "Budget confidentiel" not in resultat, (
            "les notes d'un contact d'un autre projet sont divulguées"
        )

    @pytest.mark.asyncio
    async def test_un_contact_du_projet_courant_reste_lisible(self, db_session):
        """Garde-fou : la cloison ne doit pas rendre l'outil inutile."""
        from app.models.entities import Contact
        from app.services.memory_tools import execute_memory_tool

        db_session.add(
            Contact(
                id="c-b",
                first_name="Bernard",
                last_name="Martin",
                phone="0611111111",
                scope="project",
                scope_id="projet-b",
            )
        )
        await db_session.commit()

        resultat = await execute_memory_tool(
            "read_contact",
            {"query": "Bernard"},
            db_session,
            scope="project",
            scope_id="projet-b",
        )

        assert "0611111111" in resultat, (
            "le contact du projet courant devrait être lisible : la cloison "
            "rendrait l'outil inutilisable"
        )

    @pytest.mark.asyncio
    async def test_un_contact_general_reste_lisible_depuis_un_projet(self, db_session):
        """Les contacts généraux valent pour tous les projets, comme les documents."""
        from app.models.entities import Contact
        from app.services.memory_tools import execute_memory_tool

        db_session.add(
            Contact(id="c-g", first_name="Camille", last_name="Global", phone="0622222222")
        )
        await db_session.commit()

        resultat = await execute_memory_tool(
            "read_contact",
            {"query": "Camille"},
            db_session,
            scope="project",
            scope_id="projet-b",
        )

        assert "0622222222" in resultat

    @pytest.mark.asyncio
    async def test_sans_perimetre_le_comportement_ne_change_pas(self, db_session):
        """Les appels qui ne fournissent pas de périmètre ne sont pas cloisonnés."""
        from app.models.entities import Contact
        from app.services.memory_tools import execute_memory_tool

        db_session.add(
            Contact(
                id="c-x", first_name="Denis", last_name="Projet",
                phone="0633333333", scope="project", scope_id="projet-a",
            )
        )
        await db_session.commit()

        resultat = await execute_memory_tool("read_contact", {"query": "Denis"}, db_session)

        assert "0633333333" in resultat


class TestLeChatTransmetLePerimetreAuxOutils:
    def test_l_appel_des_outils_memoire_passe_le_perimetre(self):
        """Le filtre ne sert à rien si la boucle d'outils ne le transmet pas.

        Même piège que pour `_get_memory_context` : une fonction correcte,
        jamais alimentée. On le vérifie sur l'arbre syntaxique.
        """
        import ast
        import pathlib

        chemin = (
            pathlib.Path(__file__).resolve().parents[1]
            / "src" / "backend" / "app" / "routers" / "chat.py"
        )
        arbre = ast.parse(chemin.read_text(encoding="utf-8"))

        appels = [
            n
            for n in ast.walk(arbre)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "execute_memory_tool"
        ]
        assert appels, "aucun appel trouvé : le test ne prouverait rien"

        sans_perimetre = [
            n.lineno
            for n in appels
            if not {"scope", "scope_id"} <= {kw.arg for kw in n.keywords}
        ]
        assert not sans_perimetre, (
            f"appels sans périmètre aux lignes {sans_perimetre} : les contacts "
            "d'un autre projet restent lisibles depuis cette conversation"
        )
