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

        # Vérifier la présence des mots-clés NE SUFFIT PAS : `scope=None` en dur
        # les satisferait sans rien cloisonner (relevé en revue).
        defauts: list[str] = []
        for n in appels:
            passes = {kw.arg: kw.value for kw in n.keywords}
            for requis in ("scope", "scope_id"):
                valeur = passes.get(requis)
                if valeur is None:
                    defauts.append(f"ligne {n.lineno} : `{requis}` absent")
                elif isinstance(valeur, ast.Constant) and valeur.value is None:
                    defauts.append(f"ligne {n.lineno} : `{requis}=None` en dur")

        assert not defauts, (
            "les contacts d'un autre projet restent lisibles — " + " ; ".join(defauts)
        )


class TestLaCreationNeDivulguePasUnHomonyme:
    @pytest.mark.asyncio
    async def test_creer_un_contact_ne_revele_pas_celui_d_un_autre_projet(
        self, db_session
    ):
        """Finding de la revue : la déduplication ignorait le périmètre.

        Depuis le projet B, créer « Alice Durand » alors qu'elle n'existe que
        dans le projet A renvoyait son nom ET son identifiant avec
        `already_existed: true` — donc son existence — puis empêchait la
        création du contact propre à B.
        """
        from app.models.entities import Contact
        from app.services.memory_tools import execute_memory_tool

        db_session.add(
            Contact(
                id="secret-a", first_name="Alice", last_name="Durand",
                scope="project", scope_id="projet-a",
            )
        )
        await db_session.commit()

        resultat = await execute_memory_tool(
            "create_contact",
            {"first_name": "Alice", "last_name": "Durand"},
            db_session,
            scope="project",
            scope_id="projet-b",
        )

        assert "secret-a" not in resultat, (
            "l'identifiant d'un contact d'un autre projet est divulgué"
        )
        donnees = json.loads(resultat)
        assert not donnees.get("already_existed"), (
            "la création est refusée à cause d'un homonyme invisible pour "
            "l'utilisateur : il ne peut plus créer son propre contact"
        )


class TestLeBridgeMCPNEstPasUnePorteDerobee:
    """Le bridge MCP expose des routes GLOBALES (`list_contacts`,
    `get_contact`, `search_memory`). C'est légitime : il sert les sessions
    d'agent de l'Atelier, qui travaillent sur tout l'espace de l'utilisateur et
    n'ont pas de conversation cloisonnée.

    Cela deviendrait un contournement le jour où ces outils seraient exposés au
    CHAT, présenté comme cloisonné : le modèle pourrait alors lire les contacts
    de tous les projets en passant par le bridge. Ce test verrouille la
    séparation pour qu'un tel branchement ne passe pas inaperçu.
    """

    def test_le_bridge_reste_reserve_aux_sessions_d_agent(self):
        import pathlib

        racine = pathlib.Path(__file__).resolve().parents[1] / "src" / "backend" / "app"
        porteurs = [
            chemin
            for chemin in racine.rglob("*.py")
            if "therese-bridge" in chemin.read_text(encoding="utf-8")
        ]
        noms = sorted(c.name for c in porteurs)

        assert noms == ["agents.py"], (
            "le bridge MCP est référencé hors du lancement de session d'agent "
            f"({noms}) : s'il est exposé au chat, le cloisonnement des contacts "
            "est contournable. Cloisonner ces outils avant de les brancher."
        )


class TestLesFuitesResiduellesSontFermees:
    """Blocants de la revue de clôture."""

    @pytest.mark.asyncio
    async def test_le_mode_global_ne_voit_pas_les_contacts_de_projet(self, db_session):
        """Le mode global est le DÉFAUT : sans filtre, personne n'était cloisonné.

        `_cloison_contacts` ne filtrait que `scope == "project"`. Une
        conversation libre — le cas courant — lisait donc tous les contacts,
        projets compris.
        """
        from app.models.entities import Contact
        from app.services.memory_tools import execute_memory_tool

        db_session.add(
            Contact(
                id="c-proj", first_name="Fabien", last_name="Client",
                phone="0644444444", scope="project", scope_id="projet-a",
            )
        )
        await db_session.commit()

        resultat = await execute_memory_tool(
            "read_contact", {"query": "Fabien"}, db_session, scope="global"
        )

        assert "0644444444" not in resultat, (
            "une conversation libre lit les contacts d'un dossier client"
        )

    @pytest.mark.asyncio
    async def test_un_contact_cree_depuis_un_projet_lui_appartient(self, db_session):
        """Sinon la cloison ne tiendrait que sur l'existant."""
        import json

        from app.models.entities import Contact
        from app.services.memory_tools import execute_memory_tool
        from sqlmodel import select

        resultat = await execute_memory_tool(
            "create_contact",
            {"first_name": "Gaby", "last_name": "Nouvelle"},
            db_session,
            scope="project",
            scope_id="projet-a",
        )
        contact_id = json.loads(resultat)["contact_id"]

        cree = (
            await db_session.execute(select(Contact).where(Contact.id == contact_id))
        ).scalar_one()

        assert cree.scope == "project", (
            "le contact naît global : il sera visible depuis tous les dossiers"
        )
        assert cree.scope_id == "projet-a"


class TestLesPiecesJointesPortentLePerimetre:
    def test_le_chat_transmet_le_perimetre_a_l_indexation(self):
        """Une pièce jointe déposée dans un dossier client lui appartient.

        Sans périmètre, elle naissait globale : consultable depuis tous les
        autres dossiers dès l'instant où elle était jointe.
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
            and n.func.id == "_get_file_context"
        ]
        assert appels, "aucun appel trouvé : le test ne prouverait rien"

        defauts = [
            n.lineno
            for n in appels
            if not {"scope", "scope_id"} <= {kw.arg for kw in n.keywords}
        ]
        assert not defauts, (
            f"pièces jointes indexées sans périmètre aux lignes {defauts} : "
            "elles seront consultables depuis tous les autres projets"
        )
