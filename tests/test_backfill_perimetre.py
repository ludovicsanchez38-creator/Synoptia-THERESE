"""
0.43 - Reclasser les documents indexés avant que le périmètre existe.

Le filtre de recherche accepte trois branches : le projet demandé, `global`, et
les payloads SANS clé `scope`. Cette troisième branche a été ajoutée en 0.42
pour ne pas faire disparaître d'un coup toute la mémoire documentaire
existante.

Elle a un effet de bord que la revue a mis au jour : un document du projet A
indexé AVANT la 0.42 n'a pas de `scope` dans son payload. Il est donc traité
comme global — et remonte dans une conversation du projet B. La cloison ne le
couvre pas.

La base, elle, sait : `FileMetadata.scope` / `scope_id` sont renseignés depuis
longtemps. Le payload vectoriel est le seul à l'ignorer. Il suffit donc de le
reclasser depuis la base, sans toucher aux embeddings — donc sans réencoder
quoi que ce soit, et sans jamais rien supprimer.

Ce qui reste inclassable (un point vectoriel sans ligne en base) est marqué
explicitement plutôt que promu global : un document dont on ignore le
rattachement ne doit pas devenir visible partout.
"""
import pytest


class FauxQdrant:
    """Un Qdrant en mémoire, réduit à ce que le backfill utilise."""

    def __init__(self, points: dict[str, dict]):
        # points : id -> payload
        self.points = points
        self.payloads_ecrits: list[tuple[list[str], dict]] = []
        self.suppressions: list[str] = []

    def points_sans_perimetre(self) -> list[tuple[str, dict]]:
        return [(pid, p) for pid, p in self.points.items() if "scope" not in p]

    def definir_perimetre(self, point_ids: list[str], scope: str, scope_id: str | None):
        self.payloads_ecrits.append((point_ids, {"scope": scope, "scope_id": scope_id}))
        for pid in point_ids:
            self.points[pid]["scope"] = scope
            self.points[pid]["scope_id"] = scope_id

    def delete_by_entity(self, entity_id: str) -> int:
        self.suppressions.append(entity_id)
        return 0


class TestBackfillDuPerimetre:
    @pytest.mark.asyncio
    async def test_un_document_de_projet_est_reclasse(self, db_session, monkeypatch):
        """Le cas de la fuite : legacy + projet en base = payload à reclasser."""
        from app.models.entities import FileMetadata
        from app.services import perimetre_backfill

        fichier = FileMetadata(
            id="fic-a",
            path="/tmp/rapport-a.txt",
            name="rapport-a.txt",
            extension=".txt",
            size=10,
            scope="project",
            scope_id="projet-a",
        )
        db_session.add(fichier)
        await db_session.commit()

        faux = FauxQdrant({
            "p1": {"entity_id": "fic-a", "type": "file"},
            "p2": {"entity_id": "fic-a", "type": "file"},
        })
        monkeypatch.setattr(perimetre_backfill, "get_qdrant_service", lambda: faux)

        reclasses = await perimetre_backfill.reclasser_payloads_sans_perimetre(db_session)

        assert reclasses == 2, "les deux fragments du document devaient être reclassés"
        assert faux.points["p1"]["scope"] == "project"
        assert faux.points["p1"]["scope_id"] == "projet-a"
        assert faux.suppressions == [], "aucun vecteur ne doit être supprimé"

    @pytest.mark.asyncio
    async def test_un_document_global_est_marque_global(self, db_session, monkeypatch):
        from app.models.entities import FileMetadata
        from app.services import perimetre_backfill

        db_session.add(
            FileMetadata(
                id="fic-g", path="/tmp/notes.txt", name="notes.txt",
                extension=".txt", size=10, scope="global", scope_id=None,
            )
        )
        await db_session.commit()

        faux = FauxQdrant({"p1": {"entity_id": "fic-g", "type": "file"}})
        monkeypatch.setattr(perimetre_backfill, "get_qdrant_service", lambda: faux)

        await perimetre_backfill.reclasser_payloads_sans_perimetre(db_session)

        assert faux.points["p1"]["scope"] == "global"

    @pytest.mark.asyncio
    async def test_un_point_orphelin_n_est_pas_promu_global(
        self, db_session, monkeypatch
    ):
        """Un point sans ligne en base : on ignore son rattachement.

        Le promouvoir global le rendrait visible dans TOUS les projets. On le
        marque inclassable, ce qui l'exclut des recherches cloisonnées sans
        jamais le supprimer.
        """
        from app.services import perimetre_backfill

        faux = FauxQdrant({"p1": {"entity_id": "fichier-disparu", "type": "file"}})
        monkeypatch.setattr(perimetre_backfill, "get_qdrant_service", lambda: faux)

        await perimetre_backfill.reclasser_payloads_sans_perimetre(db_session)

        assert faux.points["p1"]["scope"] == perimetre_backfill.SCOPE_INCLASSABLE, (
            "un document au rattachement inconnu ne doit pas devenir visible "
            "dans tous les projets"
        )
        assert faux.suppressions == []


    @pytest.mark.asyncio
    async def test_les_souvenirs_non_documentaires_sont_laisses_intacts(
        self, db_session, monkeypatch
    ):
        """RÉGRESSION ÉVITÉE, trouvée en revue.

        La collection ne contient pas que des documents : les contacts, les
        projets et le profil y ont aussi leurs embeddings, et aucune ligne dans
        `FileMetadata`. Une première version du backfill les marquait donc tous
        inclassables — ils disparaissaient des modes `global` et `project`,
        c'est-à-dire de l'usage courant. Le cloisonnement des contacts se fait
        en SQL, pas par ce périmètre vectoriel.
        """
        from app.services import perimetre_backfill

        faux = FauxQdrant({
            "c1": {"entity_id": "contact-1", "type": "contact"},
            "pr1": {"entity_id": "projet-1", "type": "project"},
        })
        monkeypatch.setattr(perimetre_backfill, "get_qdrant_service", lambda: faux)

        reclasses = await perimetre_backfill.reclasser_payloads_sans_perimetre(db_session)

        assert reclasses == 0
        assert "scope" not in faux.points["c1"], (
            "l'embedding d'un contact a été classé par le backfill documentaire : "
            "il disparaîtrait de la mémoire courante"
        )
        assert "scope" not in faux.points["pr1"]

    @pytest.mark.asyncio
    async def test_le_backfill_est_idempotent(self, db_session, monkeypatch):
        """Il tourne au démarrage : un second passage ne doit rien réécrire."""
        from app.models.entities import FileMetadata
        from app.services import perimetre_backfill

        db_session.add(
            FileMetadata(
                id="fic-a", path="/tmp/a.txt", name="a.txt",
                extension=".txt", size=10, scope="project", scope_id="projet-a",
            )
        )
        await db_session.commit()

        faux = FauxQdrant({"p1": {"entity_id": "fic-a", "type": "file"}})
        monkeypatch.setattr(perimetre_backfill, "get_qdrant_service", lambda: faux)

        premier = await perimetre_backfill.reclasser_payloads_sans_perimetre(db_session)
        second = await perimetre_backfill.reclasser_payloads_sans_perimetre(db_session)

        assert premier == 1
        assert second == 0, "le second passage réécrit des payloads déjà classés"


class TestLeFiltreNAcceptePlusLInclassable:
    def test_un_payload_inclassable_est_exclu_des_recherches_de_projet(self):
        """Sinon le backfill n'aurait rien changé pour ces points."""
        from unittest.mock import MagicMock

        from app.services import qdrant as module

        module.embed_text = lambda _t: [0.0] * 768
        service = module.QdrantService.__new__(module.QdrantService)
        faux_client = MagicMock()
        faux_client.query_points.return_value = MagicMock(points=[])
        service._client = faux_client
        service._initialized = True

        service.search(query="x", scope="project", scope_id="projet-b")

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
        from app.services.perimetre_backfill import SCOPE_INCLASSABLE

        assert ("scope", SCOPE_INCLASSABLE) not in valeurs
