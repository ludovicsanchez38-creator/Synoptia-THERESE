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


    @pytest.mark.asyncio
    async def test_une_conversation_libre_ne_voit_pas_les_projets_d_un_dossier(
        self, db_session
    ):
        """La branche `global` de la cloison projets n'était couverte par rien.

        C'est le régime par DÉFAUT : une conversation non rattachée résout son
        périmètre à `("global", None)`. Sans filtre, créer « Chantier
        confidentiel » depuis n'importe quelle conversation retrouvait le
        projet d'un dossier client, rendait son identifiant, et refusait la
        création — la fuite exacte que cette fonction existe pour empêcher.

        Écrit après l'avoir cassée pour de bon : un remplacement inverse mal
        ciblé avait remis `return requete`, et aucun test ne s'en est aperçu.
        """
        from app.models.entities import Project
        from app.services.memory_tools import execute_memory_tool

        db_session.add(
            Project(
                id="projet-secret", name="Chantier confidentiel",
                scope="project", scope_id="projet-a",
            )
        )
        await db_session.commit()

        resultat = await execute_memory_tool(
            "create_project",
            {"name": "Chantier confidentiel"},
            db_session,
            scope="global",
        )

        assert "projet-secret" not in resultat, (
            "l'identifiant d'un projet d'un dossier client est divulgué à une "
            "conversation qui n'y est pas rattachée"
        )
        assert not json.loads(resultat).get("already_existed"), (
            "la création est refusée à cause d'un homonyme invisible"
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


class TestLesCheminsSlashEtInline:
    """Blocant de la revue : `/contact` et `[contact: ...]` créaient en global.

    Le scénario reproduit par la revue : depuis une conversation du projet A,
    `/contact Alice tel=0601020304` crée un contact GLOBAL ; depuis le projet B,
    `read_contact("Alice")` rend son téléphone. La cloison ne servait à rien
    pour tout ce qui était saisi par commande.
    """

    @pytest.mark.asyncio
    async def test_un_contact_cree_par_slash_reste_dans_son_projet(self, db_session):
        import json

        from app.services.memory_tools import execute_memory_tool
        from app.services.slash_commands import execute_slash_command_outcome

        # Projet A : création par commande.
        await execute_slash_command_outcome(
            "contact", "Alice Secret tel=0601020304", db_session,
            scope="project", scope_id="projet-a", conversation_id="conv-a",
        )

        # Projet B : lecture.
        depuis_b = await execute_memory_tool(
            "read_contact", {"query": "Alice"}, db_session,
            scope="project", scope_id="projet-b", conversation_id="conv-b",
        )
        assert "0601020304" not in depuis_b, (
            "le contact créé par /contact depuis le projet A est lisible "
            "depuis le projet B"
        )

        # Projet A : il doit rester lisible, sinon la commande serait inutile.
        depuis_a = await execute_memory_tool(
            "read_contact", {"query": "Alice"}, db_session,
            scope="project", scope_id="projet-a", conversation_id="conv-a",
        )
        assert "0601020304" in depuis_a, (
            "le contact n'est plus lisible depuis le projet qui l'a créé"
        )
        del json

    def test_les_appelants_du_chat_transmettent_le_perimetre(self):
        """Même vérification de câblage que pour le contexte documentaire."""
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
            and n.func.id == "execute_slash_command_outcome"
        ]
        assert appels, "aucun appel trouvé : le test ne prouverait rien"

        defauts = [
            n.lineno
            for n in appels
            if not {"scope", "scope_id"} <= {kw.arg for kw in n.keywords}
        ]
        assert not defauts, (
            f"commandes exécutées sans périmètre aux lignes {defauts} : les "
            "entités créées seront visibles depuis tous les projets"
        )


class TestLeContactDeLaConversationResteVisible:
    @pytest.mark.asyncio
    async def test_un_contact_de_la_conversation_courante_est_lisible(self, db_session):
        """RÉGRESSION ÉVITÉE, trouvée en revue.

        L'interface enregistre les contacts suggérés avec
        `scope="conversation"`. Une première version du filtre les excluait :
        un contact tout juste validé devenait introuvable dans la conversation
        même qui venait de le créer. La cloison cassait l'usage qu'elle devait
        protéger.
        """
        from app.models.entities import Contact
        from app.services.memory_tools import execute_memory_tool

        db_session.add(
            Contact(
                id="c-conv", first_name="Hugo", last_name="Suggéré",
                phone="0655555555", scope="conversation", scope_id="conv-42",
            )
        )
        await db_session.commit()

        resultat = await execute_memory_tool(
            "read_contact", {"query": "Hugo"}, db_session,
            scope="global", conversation_id="conv-42",
        )
        assert "0655555555" in resultat, (
            "le contact enregistré depuis cette conversation y est introuvable"
        )

        ailleurs = await execute_memory_tool(
            "read_contact", {"query": "Hugo"}, db_session,
            scope="global", conversation_id="conv-99",
        )
        assert "0655555555" not in ailleurs, (
            "un contact de conversation fuit vers les autres conversations"
        )


class TestLesProjetsAussi:
    """Dernier blocant : même classe de fuite, trois portes d'entrée.

    `/projet`, `[projet: …]` et l'outil LLM `create_project` créaient tous le
    projet en GLOBAL, quelle que soit la conversation. Son embedding remontait
    donc dans tous les dossiers.
    """

    @pytest.mark.asyncio
    async def test_un_projet_cree_par_slash_appartient_a_son_dossier(self, db_session):
        import json

        from app.models.entities import Project
        from app.services.slash_commands import execute_slash_command_outcome
        from sqlmodel import select

        await execute_slash_command_outcome(
            "projet", "Chantier confidentiel", db_session,
            scope="project", scope_id="projet-a", conversation_id="conv-a",
        )

        cree = (
            await db_session.execute(
                select(Project).where(Project.name == "Chantier confidentiel")
            )
        ).scalar_one()

        assert cree.scope == "project", (
            "le projet naît global : son embedding remontera dans tous les dossiers"
        )
        assert cree.scope_id == "projet-a"
        del json

    @pytest.mark.asyncio
    async def test_l_outil_llm_scope_aussi_le_projet(self, db_session):
        import json

        from app.models.entities import Project
        from app.services.memory_tools import execute_memory_tool
        from sqlmodel import select

        resultat = await execute_memory_tool(
            "create_project", {"name": "Dossier B"}, db_session,
            scope="project", scope_id="projet-b", conversation_id="conv-b",
        )
        assert not json.loads(resultat).get("error"), resultat

        cree = (
            await db_session.execute(select(Project).where(Project.name == "Dossier B"))
        ).scalar_one()
        assert cree.scope == "project" and cree.scope_id == "projet-b"


class TestLeRagRetrouveLesSouvenirsDeSaConversation:
    def test_le_filtre_accepte_le_perimetre_de_conversation(self):
        """Régression relevée en revue : un contact validé depuis la
        conversation était invisible du RAG dans cette même conversation.

        La cloison SQL l'acceptait déjà ; le filtre vectoriel, non.
        """
        from unittest.mock import MagicMock

        from app.services import qdrant as module

        module.embed_text = lambda _t: [0.0] * 768
        service = module.QdrantService.__new__(module.QdrantService)
        faux_client = MagicMock()
        faux_client.query_points.return_value = MagicMock(points=[])
        service._client = faux_client
        service._initialized = True

        service.search(
            query="x", scope="global", scope_id=None, conversation_id="conv-42"
        )

        filtre = faux_client.query_points.call_args.kwargs["query_filter"].model_dump(
            exclude_none=True
        )
        branches = next(
            (c["should"] for c in filtre.get("must", []) if "should" in c), []
        )
        valeurs = {
            (cond.get("key"), (cond.get("match") or {}).get("value"))
            for branche in branches
            for cond in branche.get("must", [branche])
            if cond.get("key")
        }
        assert ("scope", "conversation") in valeurs and (
            "scope_id",
            "conv-42",
        ) in valeurs, (
            "le RAG ignore les souvenirs de la conversation courante : un "
            "contact tout juste validé y reste introuvable"
        )


class TestLeModeTransversalNOuvrePasLesAutresConversations:
    """BLOQUANT de la revue de clôture : « Tous les projets » ouvrait tout.

    Le mode transversal rendait `(None, None)`, donc AUCUN filtre : les
    contacts enregistrés dans n'importe quelle conversation remontaient, avec
    coordonnées et notes. Le sélecteur annonce « Tous les projets » — il doit
    ouvrir les dossiers, pas la vie privée des autres conversations.
    """

    @pytest.mark.asyncio
    async def test_un_contact_d_une_autre_conversation_reste_prive(self, db_session):
        from app.models.entities import Contact
        from app.services.memory_tools import execute_memory_tool

        db_session.add(
            Contact(
                id="c-priv", first_name="Hugo", last_name="Privé",
                phone="0655555555", notes="secret conv A",
                scope="conversation", scope_id="conv-a",
            )
        )
        await db_session.commit()

        resultat = await execute_memory_tool(
            "read_contact", {"query": "Hugo"}, db_session,
            scope="all", conversation_id="conv-x",
        )

        assert "0655555555" not in resultat, (
            "« Tous les projets » divulgue un contact d'une autre conversation"
        )
        assert "secret conv A" not in resultat

    @pytest.mark.asyncio
    async def test_le_mode_transversal_voit_bien_tous_les_projets(self, db_session):
        """Garde-fou : le mode doit tenir sa promesse."""
        from app.models.entities import Contact
        from app.services.memory_tools import execute_memory_tool

        db_session.add(
            Contact(
                id="c-p1", first_name="Iris", last_name="Dossier",
                phone="0666666666", scope="project", scope_id="projet-z",
            )
        )
        await db_session.commit()

        resultat = await execute_memory_tool(
            "read_contact", {"query": "Iris"}, db_session,
            scope="all", conversation_id="conv-x",
        )
        assert "0666666666" in resultat, (
            "le mode transversal ne voit pas les dossiers : il ment aussi"
        )

    def test_le_filtre_vectoriel_cloisonne_aussi_le_mode_transversal(self):
        from unittest.mock import MagicMock

        from app.services import qdrant as module

        module.embed_text = lambda _t: [0.0] * 768
        service = module.QdrantService.__new__(module.QdrantService)
        faux = MagicMock()
        faux.query_points.return_value = MagicMock(points=[])
        service._client = faux
        service._initialized = True

        service.search(query="x", scope="all", conversation_id="conv-x")

        filtre = faux.query_points.call_args.kwargs["query_filter"]
        assert filtre is not None, (
            "le mode transversal ne pose aucun filtre : les souvenirs de "
            "toutes les conversations remontent"
        )
        rendu = filtre.model_dump(exclude_none=True)
        branches = next(
            (c["should"] for c in rendu.get("must", []) if "should" in c), []
        )
        valeurs = {
            (cond.get("key"), (cond.get("match") or {}).get("value"))
            for branche in branches
            for cond in branche.get("must", [branche])
            if cond.get("key")
        }

        # Ce qu'il DOIT admettre : tous les dossiers, les souvenirs généraux,
        # et la conversation courante.
        assert ("scope", "project") in valeurs, "les dossiers devraient rester visibles"
        assert ("scope", "global") in valeurs
        assert ("scope_id", "conv-x") in valeurs

        # Ce qu'il ne doit PAS admettre : une conversation quelconque. La
        # branche `conversation` n'existe qu'appariée à l'identifiant courant.
        conversations_admises = {
            v for (k, v) in valeurs if k == "scope_id" and v and v.startswith("conv-")
        }
        assert conversations_admises == {"conv-x"}, (
            f"d'autres conversations sont admises : {conversations_admises}"
        )


class TestLaDeduplicationDesProjetsEstCloisonnee:
    @pytest.mark.asyncio
    async def test_creer_un_projet_homonyme_ne_revele_pas_celui_d_un_autre(
        self, db_session
    ):
        """Même fuite que pour les contacts, oubliée sur les projets.

        Depuis le dossier B, créer « Chantier confidentiel » renvoyait
        l'identifiant de celui du dossier A avec `already_existed: true` — donc
        son existence — et refusait la création du projet propre à B.
        """
        import json

        from app.models.entities import Project
        from app.services.memory_tools import execute_memory_tool

        db_session.add(
            Project(
                id="secret-a", name="Chantier confidentiel",
                scope="project", scope_id="projet-a",
            )
        )
        await db_session.commit()

        resultat = await execute_memory_tool(
            "create_project", {"name": "Chantier confidentiel"}, db_session,
            scope="project", scope_id="projet-b", conversation_id="conv-b",
        )

        assert "secret-a" not in resultat, (
            "l'identifiant du projet d'un autre dossier est divulgué"
        )
        donnees = json.loads(resultat)
        assert not donnees.get("already_existed"), (
            "la création est refusée à cause d'un homonyme invisible"
        )
        assert not donnees.get("error"), donnees

        # La seconde ligne doit RÉELLEMENT exister : sans elle, on aurait juste
        # remplacé une divulgation par un échec silencieux.
        from sqlmodel import select

        homonymes = (
            await db_session.execute(
                select(Project).where(Project.name == "Chantier confidentiel")
            )
        ).scalars().all()
        assert len(homonymes) == 2, (
            f"le projet propre au dossier B n'a pas été créé ({len(homonymes)} ligne(s))"
        )

    @pytest.mark.asyncio
    async def test_la_directive_inline_projet_porte_aussi_le_perimetre(
        self, db_session
    ):
        """Troisième porte, annoncée mais jamais testée (relevé en revue)."""
        from app.models.entities import Project
        from app.services.slash_commands import execute_slash_command_outcome
        from sqlmodel import select

        # `[projet: ...]` passe par le même exécuteur que la commande slash.
        await execute_slash_command_outcome(
            "projet", "Dossier inline", db_session,
            scope="project", scope_id="projet-inline", conversation_id="conv-i",
        )

        cree = (
            await db_session.execute(
                select(Project).where(Project.name == "Dossier inline")
            )
        ).scalar_one()
        assert cree.scope == "project" and cree.scope_id == "projet-inline"


class TestUneCreationNEstJamaisPublieeSansLeVouloir:
    """DERNIER BLOQUANT de la revue : promotion silencieuse `all` → `global`.

    Tout ce qui n'était pas `project` était rangé en `global`, donc PUBLIÉ
    PARTOUT. Depuis une conversation « Tous les projets », créer un contact le
    rendait visible dans tous les dossiers et toutes les conversations, sans
    aucun choix explicite de publication.

    Une création sans dossier reste dans SA conversation. L'utilisateur peut la
    promouvoir ensuite ; l'inverse ne se rattrape pas.
    """

    @pytest.mark.asyncio
    async def test_un_contact_cree_en_mode_transversal_reste_dans_sa_conversation(
        self, db_session
    ):
        from app.models.entities import Contact
        from app.services.memory_tools import execute_memory_tool
        from sqlmodel import select

        resultat = await execute_memory_tool(
            "create_contact",
            {"first_name": "Léa", "last_name": "Secret", "phone": "0612345678"},
            db_session,
            scope="all",
            conversation_id="conv-a",
        )
        contact_id = json.loads(resultat)["contact_id"]

        cree = (
            await db_session.execute(select(Contact).where(Contact.id == contact_id))
        ).scalar_one()
        assert cree.scope == "conversation" and cree.scope_id == "conv-a", (
            f"contact publié en {cree.scope} : il devient visible partout"
        )

        # Et concrètement : introuvable depuis une autre conversation.
        ailleurs = await execute_memory_tool(
            "read_contact", {"query": "Léa"}, db_session,
            scope="global", conversation_id="conv-b",
        )
        assert "0612345678" not in ailleurs, (
            "le contact créé en mode transversal fuit vers une autre conversation"
        )

    @pytest.mark.asyncio
    async def test_un_projet_cree_en_mode_transversal_reste_dans_sa_conversation(
        self, db_session
    ):
        from app.models.entities import Project
        from app.services.memory_tools import execute_memory_tool
        from sqlmodel import select

        await execute_memory_tool(
            "create_project", {"name": "Dossier transversal"}, db_session,
            scope="all", conversation_id="conv-a",
        )

        cree = (
            await db_session.execute(
                select(Project).where(Project.name == "Dossier transversal")
            )
        ).scalar_one()
        assert cree.scope == "conversation" and cree.scope_id == "conv-a"

    def test_les_pieces_jointes_suivent_la_meme_regle(self):
        """Le chat ne doit pas publier une pièce jointe faute de dossier."""
        import pathlib

        chemin = (
            pathlib.Path(__file__).resolve().parents[1]
            / "src" / "backend" / "app" / "routers" / "chat.py"
        )
        source = chemin.read_text(encoding="utf-8")
        assert 'perimetre_fichiers, perimetre_fichiers_id = "conversation"' in source, (
            "une pièce jointe sans dossier redevient globale : elle sera "
            "consultable depuis tous les autres projets"
        )
        assert 'else "global"' not in source.split("perimetre_fichiers")[1][:200], (
            "le repli global sur les pièces jointes est toujours là"
        )
