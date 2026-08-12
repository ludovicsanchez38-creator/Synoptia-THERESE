"""BUG-165 — le cloisonnement de la 0.43 ne s'applique pas aux pièces jointes.

La 0.43 a posé une règle claire : une pièce jointe déposée DANS une conversation
de projet appartient à ce projet, et ne doit pas ressortir ailleurs. Le code qui
l'applique existe bien (`_get_file_context`, `chat.py`, bloc `scope=scope`).

Il n'est jamais atteint.

Le composeur pré-indexe chaque pièce jointe dès l'attachement, AVANT l'envoi
(`ChatInput.indexAttachment` -> `POST /api/files/index`), et cette route appelle
`index_payload` sans périmètre, donc avec son défaut `scope="global"`. Quand le
message part et que `_get_file_context` s'exécute, le `FileMetadata` existe déjà :
tout le bloc `if not existing:` — celui qui pose le périmètre de la conversation —
est du code mort sur ce flux.

Conséquence concrète : le devis d'un client déposé dans sa conversation reste
consultable depuis la conversation d'un autre client. C'est exactement la fuite
que la 0.43 annonçait avoir fermée.

Ces tests décrivent le comportement attendu, pas l'implémentation : peu importe
que le périmètre soit posé à l'indexation ou corrigé à l'envoi, un fichier joint
dans une conversation de projet doit porter le périmètre de ce projet.
"""
import pytest


class TestUnePieceJointeNaitDansLePerimetreDeSaConversation:
    @pytest.mark.asyncio
    async def test_indexer_depuis_une_conversation_de_projet_pose_ce_projet(
        self, db_session, monkeypatch, tmp_path
    ):
        """Le cœur du bug : le composeur indexe en global, le périmètre est perdu."""
        from app.models.entities import Conversation
        from app.routers import files as files_router

        conversation = Conversation(id="conv-a", title="Client A", project_id="projet-a")
        db_session.add(conversation)
        await db_session.commit()

        fichier = tmp_path / "devis-client-a.txt"
        fichier.write_text("Devis confidentiel du client A", encoding="utf-8")

        perimetres: list[tuple[str, str | None]] = []

        async def faux_index_payload(
            path, est_abandonnee=None, scope="global", scope_id=None,
            perimetre_provisoire=False,
        ):
            perimetres.append((scope, scope_id))
            return None

        monkeypatch.setattr(files_router, "index_payload", faux_index_payload)

        await files_router.index_file(
            files_router.FileIndexRequest(path=str(fichier), conversation_id="conv-a"),
            _requete_factice(),
        )

        assert perimetres, "l'indexation n'a pas été lancée"
        scope, scope_id = perimetres[0]
        assert scope == "project", (
            "une pièce jointe déposée dans une conversation de projet naît encore "
            "GLOBALE : elle reste lisible depuis tous les autres dossiers clients"
        )
        assert scope_id == "projet-a"

    @pytest.mark.asyncio
    async def test_indexer_hors_conversation_reste_global(
        self, db_session, monkeypatch, tmp_path
    ):
        """Verrou de non-régression : l'explorateur continue d'indexer en global.

        Sans ce test, un correctif trop large ferait disparaître du périmètre
        général les documents que l'utilisateur indexe volontairement pour tous
        ses dossiers.
        """
        from app.routers import files as files_router

        fichier = tmp_path / "modele-de-facture.txt"
        fichier.write_text("Modèle réutilisable", encoding="utf-8")

        perimetres: list[tuple[str, str | None]] = []

        async def faux_index_payload(
            path, est_abandonnee=None, scope="global", scope_id=None,
            perimetre_provisoire=False,
        ):
            perimetres.append((scope, scope_id))
            return None

        monkeypatch.setattr(files_router, "index_payload", faux_index_payload)

        await files_router.index_file(
            files_router.FileIndexRequest(path=str(fichier)),
            _requete_factice(),
        )

        assert perimetres[0] == ("global", None)


class TestUnFichierDejaIndexeEstReclasseALEnvoi:
    @pytest.mark.asyncio
    async def test_un_fichier_global_pre_indexe_rejoint_le_projet_de_la_conversation(
        self, db_session, monkeypatch, tmp_path
    ):
        """Le filet : la conversation peut ne pas exister au moment de l'attachement.

        Un nouveau chat n'a pas encore d'identifiant côté backend quand
        l'utilisateur attache son fichier. Le périmètre ne peut alors être posé
        qu'à l'envoi. Sans ce rattrapage, le premier fichier de chaque nouvelle
        conversation resterait global.
        """
        from app.models.entities import Conversation, FileMetadata
        from app.routers import chat as chat_router

        conversation = Conversation(id="conv-b", title="Client B", project_id="projet-b")
        db_session.add(conversation)

        fichier = tmp_path / "contrat-client-b.txt"
        fichier.write_text("Contrat confidentiel du client B", encoding="utf-8")

        # Tel que le composeur l'a laissé : indexé, mais global.
        db_session.add(
            FileMetadata(
                path=str(fichier),
                name=fichier.name,
                extension=".txt",
                size=fichier.stat().st_size,
                mime_type="text/plain",
                scope="global",
                scope_id=None,
                # Tel que le composeur le pose quand la conversation n'existe
                # pas encore côté backend : périmètre par défaut, rectifiable.
                scope_provisoire=True,
            )
        )
        await db_session.commit()

        await chat_router._get_file_context(
            str(fichier),
            db_session,
            command="fichier",
            scope="project",
            scope_id="projet-b",
        )

        from sqlmodel import select

        resultat = await db_session.execute(
            select(FileMetadata).where(FileMetadata.path == str(fichier))
        )
        meta = resultat.scalar_one()
        assert meta.scope == "project", (
            "le fichier pré-indexé par le composeur reste global : le "
            "cloisonnement de la 0.43 ne s'applique pas aux pièces jointes"
        )
        assert meta.scope_id == "projet-b"


def _requete_factice():
    """Objet minimal tenant lieu de `Request` : seul `is_disconnected` est lu."""

    async def jamais_deconnecte() -> bool:
        return False

    return type("RequeteFactice", (), {"is_disconnected": staticmethod(jamais_deconnecte)})()


class TestUnPerimetreVouluNEstJamaisReecrit:
    """Findings critiques de la revue Soso sur le premier correctif.

    Le rattrapage rectifiait tout fichier « global ». Deux dégâts possibles :
    confisquer un document que l'utilisateur avait délibérément rendu général
    depuis l'explorateur, et laisser une conversation du projet B capter un
    document du projet A.

    D'où la provenance : seul un périmètre PROVISOIRE — posé par défaut parce
    que la conversation n'était pas encore connue — peut être rectifié.
    """

    @pytest.mark.asyncio
    async def test_un_document_volontairement_general_n_est_pas_confisque(
        self, db_session, tmp_path
    ):
        from app.models.entities import Conversation, FileMetadata
        from app.routers import chat as chat_router

        db_session.add(Conversation(id="conv-c", title="Client C", project_id="projet-c"))

        fichier = tmp_path / "modele-de-devis.txt"
        fichier.write_text("Modèle réutilisable pour tous les dossiers", encoding="utf-8")

        db_session.add(
            FileMetadata(
                path=str(fichier), name=fichier.name, extension=".txt",
                size=fichier.stat().st_size, mime_type="text/plain",
                scope="global", scope_id=None,
                scope_provisoire=False,  # indexé depuis l'explorateur : voulu
            )
        )
        await db_session.commit()

        await chat_router._get_file_context(
            str(fichier), db_session, command="fichier",
            scope="project", scope_id="projet-c",
        )

        from sqlmodel import select

        meta = (
            await db_session.execute(
                select(FileMetadata).where(FileMetadata.path == str(fichier))
            )
        ).scalar_one()
        assert meta.scope == "global", (
            "un document rendu général par l'utilisateur a été confisqué par "
            "la première conversation de projet qui l'a joint"
        )

    @pytest.mark.asyncio
    async def test_un_document_d_un_projet_n_est_pas_capte_par_un_autre(
        self, db_session, tmp_path
    ):
        from app.models.entities import Conversation, FileMetadata
        from app.routers import chat as chat_router

        db_session.add(Conversation(id="conv-d", title="Client D", project_id="projet-d"))

        fichier = tmp_path / "contrat-client-a.txt"
        fichier.write_text("Contrat du client A", encoding="utf-8")

        db_session.add(
            FileMetadata(
                path=str(fichier), name=fichier.name, extension=".txt",
                size=fichier.stat().st_size, mime_type="text/plain",
                scope="project", scope_id="projet-a", scope_provisoire=False,
            )
        )
        await db_session.commit()

        await chat_router._get_file_context(
            str(fichier), db_session, command="fichier",
            scope="project", scope_id="projet-d",
        )

        from sqlmodel import select

        meta = (
            await db_session.execute(
                select(FileMetadata).where(FileMetadata.path == str(fichier))
            )
        ).scalar_one()
        assert meta.scope_id == "projet-a", (
            "le document du projet A est devenu propriété du projet D : "
            "joindre un fichier ne doit jamais le déplacer d'un dossier client "
            "vers un autre"
        )


class TestUnDocumentNEstJamaisClasseHorsDePortee:
    @pytest.mark.asyncio
    async def test_une_conversation_tous_les_projets_ne_classe_pas_en_all(
        self, db_session
    ):
        """`all` décrit ce qu'on peut LIRE, jamais ce qu'on possède.

        Écrit sur un document, il le rendait introuvable : le filtre `all`
        relit `global`, `project` et la conversation courante, jamais `all`.
        """
        from app.models.entities import Conversation
        from app.routers import chat as chat_router

        db_session.add(
            Conversation(id="conv-tous", title="Transversal", memory_scope="all")
        )
        await db_session.commit()

        scope, scope_id = await chat_router.perimetre_de_piece_jointe(
            "conv-tous", db_session
        )

        assert scope != "all", (
            "le document serait classé dans un périmètre que la recherche "
            "ne relit jamais : il disparaîtrait de partout"
        )
        assert (scope, scope_id) == ("conversation", "conv-tous")
