"""
J2 (31/07/2026) - Le cloisonnement documentaire n'était pas branché.

Le filtrage par périmètre (E3-05) existe des DEUX côtés :

- en base, `FileMetadata` porte `scope` et `scope_id`, correctement renseignés
  par l'upload de pièce jointe de projet (`files.py:465`) ;
- côté vectoriel, `QdrantService.search` sait filtrer sur `scope` / `scope_id`
  avec repli sur les entrées globales (`qdrant.py:264`).

Mais AUCUN payload indexé n'écrit ces deux clés : l'upload de projet range un
`project_id` ad hoc (`files.py:496`), l'indexation générique n'range rien
(`files.py`), et les pièces jointes du chat non plus (`chat.py:247`).

Conséquences réelles, toutes deux mauvaises :

1. Le filtre ne peut RIEN trouver. Une recherche `scope="project"` ne remonte
   aucun document du projet, puisque la clé n'existe pas dans le payload.
2. Faute de filtre appliqué, le contexte du chat (`_get_memory_context`,
   `chat.py:309`) cherche sans aucun périmètre : un document rattaché à un
   projet peut ressortir dans une conversation qui n'a rien à voir. Pour un
   assistant qui agrège des données de plusieurs clients, c'est un défaut de
   confidentialité, pas une gêne d'ergonomie.

Ces tests verrouillent l'écriture du périmètre dans le payload. Le filtrage à
la lecture est verrouillé séparément.
"""
from pathlib import Path

import pytest


@pytest.fixture()
def fichier(tmp_path: Path) -> Path:
    chemin = tmp_path / "compte-rendu.txt"
    chemin.write_text("Contenu confidentiel du client A. " * 100, encoding="utf-8")
    return chemin


class FauxQdrant:
    def __init__(self):
        self.ajouts = []

    async def async_delete_by_entity(self, entity_id):
        return 1

    async def async_add_memories(self, items):
        self.ajouts.append(items)
        return None

    def add_memories(self, items):
        self.ajouts.append(items)
        return []

    @property
    def tous_les_items(self):
        return [item for lot in self.ajouts for item in lot]


class TestLePerimetreEstEcritDansLePayload:
    @pytest.mark.asyncio
    async def test_un_document_de_projet_porte_son_perimetre(
        self, db_session, fichier, monkeypatch
    ):
        """Sans ces clés, `search(scope=...)` ne peut jamais retrouver ce document."""
        from app.routers import files as files_router

        faux = FauxQdrant()
        monkeypatch.setattr(files_router, "get_qdrant_service", lambda: faux)
        monkeypatch.setattr(files_router, "extract_text", lambda _p: "texte extrait")

        await files_router.index_payload(
            path=str(fichier), scope="project", scope_id="projet-alpha"
        )

        items = faux.tous_les_items
        assert items, "aucun vecteur écrit : le test ne prouverait rien"
        for item in items:
            metadonnees = item["metadata"]
            assert metadonnees.get("scope") == "project", (
                "le périmètre n'est pas dans le payload : le filtre de recherche "
                "ne pourra jamais retrouver ce document par son projet"
            )
            assert metadonnees.get("scope_id") == "projet-alpha"

    @pytest.mark.asyncio
    async def test_un_document_sans_projet_est_explicitement_global(
        self, db_session, fichier, monkeypatch
    ):
        """Un périmètre absent et un périmètre global ne doivent pas se confondre.

        Le filtre Qdrant compare `scope` à la valeur littérale `"global"` : une
        clé absente n'y répond pas. Sans écriture explicite, un document indexé
        depuis le composeur deviendrait invisible dès qu'un filtre est posé.
        """
        from app.routers import files as files_router

        faux = FauxQdrant()
        monkeypatch.setattr(files_router, "get_qdrant_service", lambda: faux)
        monkeypatch.setattr(files_router, "extract_text", lambda _p: "texte extrait")

        await files_router.index_payload(path=str(fichier))

        items = faux.tous_les_items
        assert items, "aucun vecteur écrit : le test ne prouverait rien"
        for item in items:
            assert item["metadata"].get("scope") == "global", (
                "un document sans projet doit être marqué global, sinon il "
                "disparaît de toute recherche filtrée"
            )

    @pytest.mark.asyncio
    async def test_le_vrai_upload_de_projet_ecrit_aussi_le_perimetre(
        self, db_session, fichier, monkeypatch
    ):
        """Contre-vérification Soso : `index_payload` n'est PAS le chemin réel.

        Les tests ci-dessus appellent `index_payload` directement. Or l'upload
        d'une pièce jointe de projet (`POST /files/upload`) construit ses items
        Qdrant lui-même, avec un `project_id` ad hoc et sans `scope`.

        Le défaut est pire que l'absence de filtre : la branche
        `IsEmptyCondition` ajoutée pour préserver les documents legacy traite un
        payload sans `scope` comme GLOBAL. Un document tout juste versé dans le
        projet A remonterait donc dans une recherche du projet B — la fuite que
        ce chantier est censé fermer.
        """
        from app.routers import files as files_router

        faux = FauxQdrant()
        monkeypatch.setattr(files_router, "get_qdrant_service", lambda: faux)

        items = files_router.construire_items_indexation(
            chunks=["un fragment"],
            file_id="fic-1",
            file_name="compte-rendu.txt",
            chemin=str(fichier),
            scope="project",
            scope_id="projet-alpha",
        )

        assert items, "aucun item construit"
        for item in items:
            assert item["metadata"].get("scope") == "project", (
                "le périmètre manque : le document sera pris pour un document "
                "global et ressortira dans les autres projets"
            )
            assert item["metadata"].get("scope_id") == "projet-alpha"

    @pytest.mark.asyncio
    async def test_le_perimetre_est_aussi_enregistre_en_base(
        self, db_session, fichier, monkeypatch
    ):
        """La base et le vectoriel doivent raconter la même histoire."""
        from app.routers import files as files_router

        faux = FauxQdrant()
        monkeypatch.setattr(files_router, "get_qdrant_service", lambda: faux)
        monkeypatch.setattr(files_router, "extract_text", lambda _p: "texte extrait")

        resultat = await files_router.index_payload(
            path=str(fichier), scope="project", scope_id="projet-alpha"
        )

        assert resultat.scope == "project"
        assert resultat.scope_id == "projet-alpha"
