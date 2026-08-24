"""Caractérisation des trois producteurs d'index AVANT extraction (0.45).

Le design project.sync V2.1 impose d'extraire l'indexation et le retrait vers
des services partagés. Ces tests GÈLENT le comportement observable actuel de
chaque appelant : si l'extraction le change sans le décider, ils deviennent
rouges. Ils décrivent aussi, en le nommant, un défaut assumé qui sera corrigé
volontairement (et documenté) par le service de retrait.

Trois familles, trois comportements distincts :
- la route /api/files/index : fragments 1000/200, verrou par chemin, anciens
  vecteurs supprimés SEULEMENT quand le nouveau contenu est prêt (N1) ;
- l'upload de projet : fragments 1000/200, périmètre projet VOULU, mais
  vecteurs supprimés AVANT la nouvelle écriture (défaut préexistant) ;
- le trombone du chat : fragments 500/50 (settings), n'indexe que l'absent.
"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def fichier_texte(tmp_path: Path) -> Path:
    fichier = tmp_path / "document.txt"
    fichier.write_text("contenu " * 200, encoding="utf-8")
    return fichier


class TestLaRouteIndexEstGelee:
    @pytest.mark.asyncio
    async def test_fragments_1000_200(self, client, fichier_texte, monkeypatch):
        from app.routers import files as module
        from app.services import indexation

        decoupages: list[tuple[int, int]] = []

        async def espionne(texte, chunk_size, overlap):
            decoupages.append((chunk_size, overlap))
            return [texte[:50]]

        monkeypatch.setattr(indexation, "chunk_text_async", espionne)
        monkeypatch.setattr(
            module, "extract_text_async", AsyncMock(return_value="du texte")
        )
        qdrant = AsyncMock()
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: qdrant)

        reponse = await module.index_payload(str(fichier_texte))

        assert decoupages == [(1000, 200)]
        assert reponse.chunk_count == 1

    @pytest.mark.asyncio
    async def test_l_ancien_index_survit_jusqu_au_nouveau_contenu(
        self, client, fichier_texte, monkeypatch
    ):
        """Invariant N1 : delete_by_entity n'est appelé qu'une fois les
        nouveaux items construits - jamais avant l'extraction."""
        from app.routers import files as module
        from app.services import indexation

        journal: list[str] = []
        qdrant = AsyncMock()
        qdrant.async_delete_by_entity.side_effect = (
            lambda *a, **k: journal.append("suppression")
        )
        qdrant.async_add_memories.side_effect = (
            lambda *a, **k: journal.append("ecriture")
        )
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: qdrant)
        monkeypatch.setattr(
            module, "extract_text_async", AsyncMock(return_value="du texte")
        )

        await module.index_payload(str(fichier_texte))
        journal.clear()
        await module.index_payload(str(fichier_texte))  # réindexation

        assert journal == ["suppression", "ecriture"], (
            "en réindexation, la suppression doit précéder immédiatement "
            "l'écriture - pas l'extraction"
        )


class TestLUploadDeProjetEstGele:
    async def _uploader(self, client, nom="piece.txt"):
        import io

        resp = await client.post("/api/memory/projects", json={"name": "Projet gelé"})
        assert resp.status_code in (200, 201), resp.text
        projet_id = resp.json()["id"]
        resp = await client.post(
            "/api/files/upload",
            files={"file": (nom, io.BytesIO(b"contenu de projet " * 50), "text/plain")},
            data={"project_id": projet_id},
        )
        return resp, projet_id

    @pytest.mark.asyncio
    async def test_perimetre_projet_voulu_et_fragments_1000_200(
        self, client, monkeypatch
    ):
        from app.services import indexation

        decoupages: list[tuple[int, int]] = []

        async def espionne(texte, chunk_size, overlap):
            decoupages.append((chunk_size, overlap))
            return [texte[:50]]

        monkeypatch.setattr(indexation, "chunk_text_async", espionne)
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: AsyncMock())

        resp, projet_id = await self._uploader(client)

        assert resp.status_code == 200, resp.text
        corps = resp.json()
        assert corps["scope"] == "project"
        assert corps["scope_id"] == projet_id
        assert decoupages == [(1000, 200)]

    @pytest.mark.asyncio
    async def test_le_re_upload_respecte_l_invariant_n1(
        self, client, monkeypatch
    ):
        """CORRECTION VOLONTAIRE (migration vers le service central) : l'upload
        supprimait les anciens vecteurs AVANT d'extraire le nouveau contenu -
        un échec d'extraction laissait le document sans aucun vecteur. Passé
        par le cœur commun, il applique l'invariant N1 de la route : la
        suppression ne précède que l'écriture, jamais l'extraction."""
        from app.services import indexation

        journal: list[str] = []
        qdrant = AsyncMock()
        qdrant.async_delete_by_entity.side_effect = (
            lambda *a, **k: journal.append("suppression")
        )
        qdrant.async_add_memories.side_effect = (
            lambda *a, **k: journal.append("ecriture")
        )
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: qdrant)

        resp, projet_id = await self._uploader(client)
        assert resp.status_code == 200

        # ré-upload du même nom dans le même projet
        import io

        journal.clear()
        resp = await client.post(
            "/api/files/upload",
            files={"file": ("piece.txt", io.BytesIO(b"nouveau contenu " * 50), "text/plain")},
            data={"project_id": projet_id},
        )
        assert resp.status_code == 200
        assert journal == ["suppression", "ecriture"], (
            "au ré-upload, la suppression doit précéder immédiatement "
            "l'écriture - jamais l'extraction (invariant N1, désormais "
            "partagé par tous les producteurs)"
        )


class TestLeTromboneEstGele:
    def test_fragments_500_50_depuis_la_configuration(self):
        from app.config import settings

        assert settings.chunk_size == 500
        assert settings.chunk_overlap == 50

    def test_le_trombone_lit_bien_la_configuration(self):
        """Le chemin de secours du chat découpe via settings.chunk_size :
        c'est CE couplage que l'extraction devra préserver ou décider de
        changer - pas le changer par accident."""
        import inspect

        from app.routers import chat as module

        source = inspect.getsource(module)
        assert "chunk_size=settings.chunk_size" in source
        assert "overlap=settings.chunk_overlap" in source


class TestLeModeSyncVerifieAvantDEcrire:
    """Correction 1 du challenge V2.1 : vérifier le scope au RETOUR est trop
    tard - le service accepte les attendus (sha256, périmètre), les vérifie
    sous verrou AVANT toute écriture, et extrait depuis une copie stable :
    les octets indexés sont exactement les octets vérifiés."""

    @pytest.mark.asyncio
    async def test_un_contenu_modifie_depuis_le_plan_ne_s_indexe_pas(
        self, client, fichier_texte, monkeypatch
    ):
        from app.services import indexation

        qdrant = AsyncMock()
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: qdrant)
        monkeypatch.setattr(indexation, "extract_text", lambda _p: "texte")

        with pytest.raises(indexation.ContenuModifieDepuisLePlan):
            await indexation.index_payload(
                str(fichier_texte), sha256_attendu="0" * 64
            )

        qdrant.async_add_memories.assert_not_awaited()
        qdrant.async_delete_by_entity.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_un_perimetre_possede_ailleurs_est_un_conflit_avant_ecriture(
        self, client, fichier_texte, monkeypatch
    ):
        import hashlib

        from app.services import indexation

        qdrant = AsyncMock()
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: qdrant)
        monkeypatch.setattr(indexation, "extract_text", lambda _p: "texte")

        # le fichier appartient déjà, de façon VOULUE, au périmètre global
        await indexation.index_payload(str(fichier_texte), scope="global")
        qdrant.reset_mock()

        empreinte = hashlib.sha256(fichier_texte.read_bytes()).hexdigest()
        with pytest.raises(indexation.ConflitDePerimetre):
            await indexation.index_payload(
                str(fichier_texte),
                scope="project", scope_id="p-1",
                sha256_attendu=empreinte,
            )

        qdrant.async_add_memories.assert_not_awaited()
        qdrant.async_delete_by_entity.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_le_mode_sync_extrait_depuis_la_copie_stable(
        self, client, fichier_texte, monkeypatch
    ):
        """Les octets extraits sont ceux de la copie vérifiée, pas du fichier
        source qui peut encore bouger (rsync ne connaît pas notre verrou)."""
        import hashlib

        from app.services import indexation

        sources: list[str] = []

        def extraction_espionne(chemin):
            sources.append(str(chemin))
            return "texte"

        monkeypatch.setattr(indexation, "extract_text", extraction_espionne)
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: AsyncMock())

        empreinte = hashlib.sha256(fichier_texte.read_bytes()).hexdigest()
        reponse = await indexation.index_payload(
            str(fichier_texte), scope="project", scope_id="p-1",
            sha256_attendu=empreinte,
        )

        assert reponse.chunk_count >= 1
        assert sources and sources[0] != str(fichier_texte), (
            "l'extraction doit lire la copie stable, pas la source vivante"
        )
