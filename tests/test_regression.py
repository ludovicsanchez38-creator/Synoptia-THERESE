"""
THÉRÈSE v2 - Tests de non-régression

Chaque fix critique (v0.1.2 à v0.1.11) a un test ici.
Si un de ces tests échoue, c'est qu'un fix a régressé.

Convention : un test par bug, nommé test_BUGXXX_description.
"""

import ast
import inspect
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Chemins sources
SRC = Path(__file__).resolve().parent.parent / "src" / "backend"
MAIN_PY = SRC / "main.py"
APP_MAIN_PY = SRC / "app" / "main.py"
EMBEDDINGS_PY = SRC / "app" / "services" / "embeddings.py"
ENCRYPTION_PY = SRC / "app" / "services" / "encryption.py"
USER_PROFILE_PY = SRC / "app" / "services" / "user_profile.py"

FRONTEND = Path(__file__).resolve().parent.parent / "src" / "frontend" / "src"
API_CORE_TS = FRONTEND / "services" / "api" / "core.ts"


# ============================================================
# BUG-002 (v0.1.2) - Port dynamique
# Le backend ne doit PAS utiliser un port hardcodé 8000.
# Il doit accepter --port en argument CLI.
# ============================================================


class TestBUG002PortDynamique:
    """Port dynamique au lieu de 8000 hardcodé."""

    def test_main_accepts_port_argument(self):
        """main.py accepte --port en argument CLI."""
        content = MAIN_PY.read_text(encoding="utf-8")
        assert "--port" in content, "main.py doit accepter --port"

    def test_main_accepts_host_argument(self):
        """main.py accepte --host en argument CLI."""
        content = MAIN_PY.read_text(encoding="utf-8")
        assert "--host" in content, "main.py doit accepter --host"

    def test_api_core_singleton_init(self):
        """initApiBase() doit être un singleton (promesse partagée)."""
        content = API_CORE_TS.read_text(encoding="utf-8")
        assert "_initPromise" in content, "initApiBase doit utiliser un singleton _initPromise"
        assert "if (_initPromise) return _initPromise" in content, (
            "initApiBase doit retourner la promesse existante si déjà en cours"
        )

    def test_api_core_retry_ipc(self):
        """initApiBase() doit retenter l'IPC Tauri (pas une seule tentative)."""
        content = API_CORE_TS.read_text(encoding="utf-8")
        assert "MAX_RETRIES" in content, "initApiBase doit avoir un mécanisme de retry"
        assert "RETRY_DELAY" in content, "initApiBase doit avoir un délai entre les retries"


# ============================================================
# BUG-003 (v0.1.3) - Verrou Qdrant
# Le fichier .lock Qdrant doit être nettoyé au démarrage.
# ============================================================


class TestBUG003QdrantLock:
    """Nettoyage du verrou Qdrant au démarrage."""

    def test_qdrant_lock_cleanup_in_main(self):
        """main.py doit nettoyer le .lock Qdrant au démarrage."""
        content = MAIN_PY.read_text(encoding="utf-8")
        assert ".lock" in content, "main.py doit gérer le fichier .lock Qdrant"
        assert "lock_file.unlink()" in content or "lock_file.unlink" in content, (
            "main.py doit supprimer le fichier .lock"
        )


# ============================================================
# BUG-005 (v0.1.4) - DLL Windows
# PyInstaller ne doit PAS strip/UPX les DLL sur Windows.
# ============================================================


class TestBUG005DLLWindows:
    """PyInstaller strip=False et upx=False sur Windows."""

    def test_backend_spec_no_strip_windows(self):
        """backend.spec ne doit PAS strip sur Windows."""
        spec_file = SRC / "backend.spec"
        if spec_file.exists():
            content = spec_file.read_text(encoding="utf-8")
            # Le spec doit désactiver strip sur Windows (strip=False ou conditionnel)
            assert 'strip=False' in content or 'win32' in content, (
                "backend.spec doit désactiver strip sur Windows (crash DLL)"
            )


# ============================================================
# BUG-007 (v0.1.5) - Zombies backend
# Le cleanup doit tuer les anciens processus backend.
# ============================================================


class TestBUG007Zombies:
    """Nettoyage des processus zombies au démarrage."""

    def test_zombie_cleanup_exists(self):
        """main.py doit avoir une fonction de nettoyage des zombies."""
        content = MAIN_PY.read_text(encoding="utf-8")
        assert "_kill_zombie_backends" in content, (
            "main.py doit contenir _kill_zombie_backends()"
        )

    def test_zombie_cleanup_skips_self(self):
        """Le cleanup ne doit pas tuer le processus courant."""
        content = MAIN_PY.read_text(encoding="utf-8")
        assert "current_pid" in content, "Le cleanup doit connaître son propre PID"
        assert "pid != current_pid" in content, "Le cleanup doit exclure son propre PID"

    def test_zombie_cleanup_skips_parent(self):
        """Le cleanup ne doit pas tuer le parent (bootloader PyInstaller)."""
        content = MAIN_PY.read_text(encoding="utf-8")
        assert "parent_pid" in content, "Le cleanup doit connaître le PID parent"


# ============================================================
# BUG-008 (v0.1.5) - Port mismatch
# freeze_support doit être avant tout import lourd.
# ============================================================


class TestBUG008FreezeSupport:
    """freeze_support avant les imports lourds."""

    def test_freeze_support_before_app_import(self):
        """freeze_support() doit être appelé AVANT from app.main import app."""
        content = MAIN_PY.read_text(encoding="utf-8")
        freeze_pos = content.find("multiprocessing.freeze_support()")
        app_pos = content.find("from app.main import app")
        assert freeze_pos > 0, "freeze_support() absent"
        assert app_pos > 0, "import app.main absent"
        assert freeze_pos < app_pos, "freeze_support() doit précéder import app.main"


# ============================================================
# BUG-011 (v0.1.10) - IPC Mac M1
# initApiBase() doit retenter si le port IPC est 8000.
# ============================================================


class TestBUG011IPCMacM1:
    """Retry IPC Tauri pour Mac M1."""

    def test_retry_on_default_port(self):
        """initApiBase() doit retenter si le port reçu est 8000 (défaut)."""
        content = API_CORE_TS.read_text(encoding="utf-8")
        assert "port !== 8000" in content or "port != 8000" in content, (
            "initApiBase doit détecter le port par défaut 8000 et retenter"
        )


# ============================================================
# BUG-012 (v0.1.11) - Crash Mac M4 Max (MPS)
# Les embeddings doivent forcer device='cpu'.
# ============================================================


class TestBUG012CrashMacM4Max:
    """Force CPU pour les embeddings (pas MPS/Metal)."""

    def test_embeddings_force_cpu(self):
        """SentenceTransformer doit être initialisé avec device='cpu'."""
        content = EMBEDDINGS_PY.read_text(encoding="utf-8")
        assert 'device="cpu"' in content or "device='cpu'" in content, (
            "SentenceTransformer doit forcer device='cpu' pour éviter le crash MPS sur M4 Max"
        )

    def test_embeddings_no_mps(self):
        """Le code ne doit PAS utiliser device='mps' ou device='cuda'."""
        content = EMBEDDINGS_PY.read_text(encoding="utf-8")
        assert 'device="mps"' not in content, "device='mps' crashe sur M4 Max"
        assert "device='mps'" not in content, "device='mps' crashe sur M4 Max"
        assert 'device="cuda"' not in content, "device='cuda' n'existe pas sur macOS"

    @patch("app.services.embeddings.SentenceTransformer")
    def test_embeddings_constructor_receives_cpu(self, mock_st):
        """Vérifie que SentenceTransformer reçoit bien device='cpu' à l'exécution."""
        from app.services.embeddings import EmbeddingsService

        # Reset singleton
        EmbeddingsService._instance = None
        EmbeddingsService._model = None

        mock_st.return_value = MagicMock()
        mock_st.return_value.get_sentence_embedding_dimension.return_value = 768

        service = EmbeddingsService()
        _ = service.model

        mock_st.assert_called_once()
        call_kwargs = mock_st.call_args
        assert call_kwargs.kwargs.get("device") == "cpu" or (
            len(call_kwargs.args) >= 1 and "cpu" in str(call_kwargs)
        ), "SentenceTransformer doit recevoir device='cpu'"

        # Cleanup
        EmbeddingsService._instance = None
        EmbeddingsService._model = None


# ============================================================
# BUG-013 (v0.1.11) - Keychain bloque le démarrage
# L'encryption doit être lazy (pas d'init au __new__).
# ============================================================


class TestBUG013KeychainLazy:
    """Init lazy du service de chiffrement (pas de Keychain au boot)."""

    def test_encryption_new_does_not_initialize(self):
        """EncryptionService.__new__() ne doit PAS appeler _initialize()."""
        content = ENCRYPTION_PY.read_text(encoding="utf-8")

        # Trouver le corps de __new__
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "__new__":
                # Vérifier qu'aucun appel à _initialize n'est dans __new__
                new_source = ast.get_source_segment(content, node)
                assert "_initialize" not in new_source, (
                    "__new__() ne doit PAS appeler _initialize() - "
                    "le Keychain doit être contacté au premier encrypt/decrypt, pas au boot"
                )
                break
        else:
            pytest.fail("__new__() non trouvé dans EncryptionService")

    def test_encryption_has_ensure_initialized(self):
        """Le service doit avoir _ensure_initialized() pour le lazy init."""
        content = ENCRYPTION_PY.read_text(encoding="utf-8")
        assert "_ensure_initialized" in content, (
            "EncryptionService doit avoir _ensure_initialized() pour le lazy init"
        )

    def test_encrypt_calls_ensure_initialized(self):
        """encrypt() doit appeler _ensure_initialized() avant de chiffrer."""
        content = ENCRYPTION_PY.read_text(encoding="utf-8")

        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "encrypt":
                encrypt_source = ast.get_source_segment(content, node)
                assert "_ensure_initialized" in encrypt_source, (
                    "encrypt() doit appeler _ensure_initialized()"
                )
                break

    def test_decrypt_calls_ensure_initialized(self):
        """decrypt() doit appeler _ensure_initialized() avant de déchiffrer."""
        content = ENCRYPTION_PY.read_text(encoding="utf-8")

        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "decrypt":
                decrypt_source = ast.get_source_segment(content, node)
                assert "_ensure_initialized" in decrypt_source, (
                    "decrypt() doit appeler _ensure_initialized()"
                )
                break

    def test_fernet_none_after_construction(self):
        """_fernet doit être None juste après la construction (avant premier usage)."""
        from app.services.encryption import EncryptionService

        # Reset singleton
        EncryptionService._instance = None
        EncryptionService._fernet = None
        EncryptionService._using_keychain = False

        service = EncryptionService()
        assert service._fernet is None, (
            "_fernet doit rester None après __new__() - "
            "l'init lazy ne se déclenche qu'au premier encrypt/decrypt"
        )

        # Cleanup
        EncryptionService._instance = None
        EncryptionService._fernet = None
        EncryptionService._using_keychain = False

    def test_startup_profile_no_decrypt(self):
        """Le preload profil au démarrage doit utiliser allow_decrypt=False."""
        content = APP_MAIN_PY.read_text(encoding="utf-8")
        assert "allow_decrypt=False" in content, (
            "Le preload profil utilisateur doit passer allow_decrypt=False "
            "pour ne pas déclencher le Keychain au démarrage"
        )


# ============================================================
# Sécurité - XSS emails
# Le rendu HTML des emails doit être sanitisé.
# ============================================================


class TestXSSEmailSanitization:
    """Sanitisation HTML des emails (DOMPurify)."""

    def test_email_html_sanitized(self):
        """Le rendu email doit utiliser DOMPurify ou une sanitisation équivalente."""
        # Chercher dans tous les fichiers email du frontend
        email_dir = FRONTEND / "components" / "email"
        if not email_dir.exists():
            email_dir = FRONTEND / "components" / "panels"

        found_sanitize = False
        found_dangerous = False

        for ts_file in FRONTEND.rglob("*.tsx"):
            content = ts_file.read_text(encoding="utf-8")
            if "dangerouslySetInnerHTML" in content:
                found_dangerous = True
                # Vérifier que DOMPurify ou sanitize est utilisé
                if "sanitize" in content.lower() or "dompurify" in content.lower():
                    found_sanitize = True

        if found_dangerous:
            assert found_sanitize, (
                "dangerouslySetInnerHTML utilisé sans sanitisation - "
                "utiliser DOMPurify.sanitize() pour éviter les XSS"
            )
