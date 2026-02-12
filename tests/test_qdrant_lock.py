"""
THÉRÈSE v2 - Tests du retry Qdrant sur lock stale

Vérifie que QdrantService gère correctement le cas où le fichier .lock
est resté d'un ancien process et empêche l'initialisation.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestQdrantLockRetry:
    """Tests de la logique de retry quand le lock Qdrant est stale."""

    def test_init_client_retries_on_already_accessed(self):
        """Si QdrantClient lève 'already accessed', le service doit supprimer le .lock et réessayer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            qdrant_path = Path(tmpdir) / "qdrant"
            qdrant_path.mkdir()
            lock_file = qdrant_path / ".lock"
            lock_file.touch()

            mock_settings = MagicMock()
            mock_settings.qdrant_path = qdrant_path
            mock_settings.data_dir = Path(tmpdir)
            mock_settings.qdrant_collection = "test_collection"
            mock_settings.embedding_dimensions = 768

            call_count = 0

            def mock_qdrant_client(path: str) -> MagicMock:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise RuntimeError(
                        "Storage folder is already accessed by another instance of Qdrant client."
                    )
                # Deuxième appel : succès
                client = MagicMock()
                client.get_collections.return_value = MagicMock(collections=[])
                client.create_collection = MagicMock()
                return client

            with (
                patch("app.services.qdrant.settings", mock_settings),
                patch("app.services.qdrant.QdrantClient", side_effect=mock_qdrant_client),
            ):
                from app.services.qdrant import QdrantService

                # Réinitialiser le singleton pour ce test
                QdrantService._instance = None
                QdrantService._client = None
                QdrantService._initialized = False

                service = QdrantService()
                service._init_client()

                # Le client doit avoir été initialisé (2 tentatives)
                assert call_count == 2
                assert service._client is not None
                # Le fichier .lock doit avoir été supprimé
                assert not lock_file.exists()

    def test_init_client_raises_on_other_runtime_error(self):
        """Les RuntimeError non liées au lock doivent remonter normalement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            qdrant_path = Path(tmpdir) / "qdrant"
            qdrant_path.mkdir()

            mock_settings = MagicMock()
            mock_settings.qdrant_path = qdrant_path
            mock_settings.data_dir = Path(tmpdir)

            def mock_qdrant_client(path: str) -> MagicMock:
                raise RuntimeError("Corrupted storage index")

            with (
                patch("app.services.qdrant.settings", mock_settings),
                patch("app.services.qdrant.QdrantClient", side_effect=mock_qdrant_client),
            ):
                from app.services.qdrant import QdrantService

                QdrantService._instance = None
                QdrantService._client = None
                QdrantService._initialized = False

                service = QdrantService()
                with pytest.raises(RuntimeError, match="Corrupted storage index"):
                    service._init_client()

    def test_init_client_success_without_lock(self):
        """Sans lock stale, l'initialisation doit fonctionner directement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            qdrant_path = Path(tmpdir) / "qdrant"
            qdrant_path.mkdir()

            mock_settings = MagicMock()
            mock_settings.qdrant_path = qdrant_path
            mock_settings.data_dir = Path(tmpdir)
            mock_settings.qdrant_collection = "test_collection"
            mock_settings.embedding_dimensions = 768

            mock_client = MagicMock()
            mock_client.get_collections.return_value = MagicMock(collections=[])

            with (
                patch("app.services.qdrant.settings", mock_settings),
                patch("app.services.qdrant.QdrantClient", return_value=mock_client),
            ):
                from app.services.qdrant import QdrantService

                QdrantService._instance = None
                QdrantService._client = None
                QdrantService._initialized = False

                service = QdrantService()
                service._init_client()

                assert service._client is not None
                assert service._initialized is True

    def test_singleton_pattern(self):
        """QdrantService doit être un singleton."""
        from app.services.qdrant import QdrantService

        QdrantService._instance = None

        a = QdrantService()
        b = QdrantService()

        assert a is b
