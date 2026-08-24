"""Service de retrait d'index - idempotent et fail-closed (0.45, fondation).

Challenge du design V2 : `delete_file` avalait toute erreur Qdrant puis
supprimait quand même la ligne SQLite - des vecteurs orphelins restaient
servis par la recherche, sans plus aucune métadonnée pour les retrouver.
Le contrat du service : Qdrant D'ABORD et en entier, la base ENSUITE ;
une erreur laisse la ligne en place (l'état reste réparable) ; une entité
déjà absente est un succès de reprise ; un `file_id_attendu` qui ne
correspond plus est un conflit, jamais une suppression.
"""

from unittest.mock import AsyncMock

import pytest


async def _indexer_un_fichier(tmp_path, monkeypatch) -> str:
    from app.services import indexation

    fichier = tmp_path / "a-retirer.txt"
    fichier.write_text("contenu " * 50, encoding="utf-8")
    monkeypatch.setattr(indexation, "extract_text", lambda _p: "texte")
    monkeypatch.setattr(indexation, "get_qdrant_service", lambda: AsyncMock())
    reponse = await indexation.index_payload(str(fichier))
    return reponse.id


class TestLeRetraitEstFailClosed:
    @pytest.mark.asyncio
    async def test_nominal_qdrant_puis_sqlite(self, client, tmp_path, monkeypatch):
        from app.models.database import get_session_context
        from app.models.entities import FileMetadata
        from app.services import indexation, retrait_index
        from sqlmodel import select

        file_id = await _indexer_un_fichier(tmp_path, monkeypatch)
        qdrant = AsyncMock()
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: qdrant)

        resultat = await retrait_index.retirer_de_lindex(file_id_attendu=file_id)

        assert resultat.retire is True
        qdrant.async_delete_by_entity.assert_awaited_once_with(file_id)
        async with get_session_context() as session:
            reste = await session.execute(
                select(FileMetadata).where(FileMetadata.id == file_id)
            )
            assert reste.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_une_erreur_qdrant_laisse_la_ligne_en_place(
        self, client, tmp_path, monkeypatch
    ):
        from app.models.database import get_session_context
        from app.models.entities import FileMetadata
        from app.services import indexation, retrait_index
        from sqlmodel import select

        file_id = await _indexer_un_fichier(tmp_path, monkeypatch)
        qdrant = AsyncMock()
        qdrant.async_delete_by_entity.side_effect = RuntimeError("qdrant muet")
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: qdrant)

        with pytest.raises(RuntimeError):
            await retrait_index.retirer_de_lindex(file_id_attendu=file_id)

        async with get_session_context() as session:
            reste = await session.execute(
                select(FileMetadata).where(FileMetadata.id == file_id)
            )
            assert reste.scalar_one_or_none() is not None, (
                "l'ancien delete_file supprimait la ligne malgré l'échec "
                "Qdrant : les vecteurs orphelins restaient servis, sans plus "
                "aucune métadonnée pour les retrouver"
            )

    @pytest.mark.asyncio
    async def test_une_entite_absente_est_un_succes_de_reprise(self, client, monkeypatch):
        from app.services import indexation, retrait_index

        qdrant = AsyncMock()
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: qdrant)

        resultat = await retrait_index.retirer_de_lindex(file_id_attendu="disparu")

        assert resultat.retire is True
        assert resultat.deja_absent is True
        # même absente de la base, l'entité peut avoir des vecteurs restants
        # (crash entre les deux suppressions) : on nettoie quand même.
        qdrant.async_delete_by_entity.assert_awaited_once_with("disparu")

    @pytest.mark.asyncio
    async def test_un_chemin_dont_l_identite_a_change_est_un_conflit(
        self, client, tmp_path, monkeypatch
    ):
        """Entre un plan et son apply, un chemin supprimé puis réindexé désigne
        une NOUVELLE entité : l'ancien plan ne doit pas la retirer."""
        from app.services import indexation, retrait_index

        file_id = await _indexer_un_fichier(tmp_path, monkeypatch)
        qdrant = AsyncMock()
        monkeypatch.setattr(indexation, "get_qdrant_service", lambda: qdrant)

        chemin = str(tmp_path / "a-retirer.txt")
        resultat = await retrait_index.retirer_par_chemin(
            chemin, file_id_attendu="une-autre-entite"
        )

        assert resultat.retire is False
        assert resultat.conflit is True
        qdrant.async_delete_by_entity.assert_not_awaited()
        del file_id  # l'entité réelle n'a pas bougé
