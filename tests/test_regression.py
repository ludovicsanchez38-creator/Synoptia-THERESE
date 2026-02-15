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
    """Port fixe 17293 au lieu de 8000 hardcodé (v0.1.19 : port fixe)."""

    def test_main_accepts_port_argument(self):
        """main.py accepte --port en argument CLI."""
        content = MAIN_PY.read_text(encoding="utf-8")
        assert "--port" in content, "main.py doit accepter --port"

    def test_main_default_port_17293(self):
        """main.py doit utiliser le port 17293 par défaut."""
        content = MAIN_PY.read_text(encoding="utf-8")
        assert "default=17293" in content, (
            "main.py doit utiliser default=17293 (pas 8000)"
        )

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

    def test_retry_ipc_mechanism(self):
        """initApiBase() doit retenter l'IPC si le port n'est pas valide."""
        content = API_CORE_TS.read_text(encoding="utf-8")
        assert "MAX_RETRIES" in content, (
            "initApiBase doit avoir un mécanisme de retry IPC"
        )
        assert "RETRY_DELAY" in content, (
            "initApiBase doit avoir un délai entre les retries IPC"
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


# ============================================================
# BUG-014 (v0.1.12) - Splash timeout premier lancement
# Le splash screen doit avoir un timeout >= 120s.
# (Vérifié par review du code source - pas de test automatique ici,
# couvert par le test de non-régression existant via inspection manuelle.)
# ============================================================


# ============================================================
# BUG-015 (v0.1.15) - Port mismatch panels (CRM, Email, etc.)
# Les fenêtres secondaires doivent recevoir le port backend via URL.
# initApiBase() doit lire le paramètre ?port= de l'URL.
# ============================================================


TAURI_LIB_RS = (
    Path(__file__).resolve().parent.parent
    / "src" / "frontend" / "src-tauri" / "src" / "lib.rs"
)
WINDOW_MANAGER_TS = FRONTEND / "services" / "windowManager.ts"
MESSAGE_LIST_TSX = FRONTEND / "components" / "chat" / "MessageList.tsx"


class TestBUG015PortMismatchPanels:
    """Les fenêtres panels doivent recevoir le port backend via l'URL."""

    def test_window_manager_passes_port(self):
        """windowManager doit passer le port backend en paramètre URL."""
        content = WINDOW_MANAGER_TS.read_text(encoding="utf-8")
        assert "port=" in content, (
            "windowManager doit passer ?port=XXXX dans l'URL du panel"
        )
        assert "getApiBase" in content, (
            "windowManager doit utiliser getApiBase() pour récupérer le port courant"
        )

    def test_api_core_reads_url_port(self):
        """initApiBase() doit lire le paramètre ?port= de l'URL."""
        content = API_CORE_TS.read_text(encoding="utf-8")
        assert "urlParams" in content or "URLSearchParams" in content, (
            "initApiBase doit parser les paramètres URL"
        )
        assert "portParam" in content or "urlParams.get('port')" in content, (
            "initApiBase doit lire le paramètre 'port' de l'URL"
        )

    def test_url_port_checked_before_ipc(self):
        """Le paramètre URL doit être vérifié AVANT le retry IPC Tauri."""
        content = API_CORE_TS.read_text(encoding="utf-8")
        url_pos = content.find("URLSearchParams")
        ipc_pos = content.find("MAX_RETRIES")
        assert url_pos > 0, "URLSearchParams absent de initApiBase"
        assert ipc_pos > 0, "MAX_RETRIES absent de initApiBase"
        assert url_pos < ipc_pos, (
            "Le paramètre URL doit être vérifié AVANT le retry IPC"
        )


# ============================================================
# BUG-009 (v0.1.15) - Zombie killer Rust : tasklist fallback
# Le kill_zombie_backends Rust doit avoir un fallback tasklist
# pour Windows 11 25H2+ où wmic est supprimé.
# ============================================================


class TestBUG009RustTasklistFallback:
    """Fallback tasklist dans le zombie killer Rust (Windows 11 25H2+)."""

    def test_rust_has_wmic(self):
        """lib.rs doit utiliser wmic pour détecter les zombies Windows."""
        content = TAURI_LIB_RS.read_text(encoding="utf-8")
        assert "wmic" in content, (
            "lib.rs doit utiliser wmic pour la détection de zombies Windows"
        )

    def test_rust_has_tasklist_fallback(self):
        """lib.rs doit avoir un fallback tasklist quand wmic est indisponible."""
        content = TAURI_LIB_RS.read_text(encoding="utf-8")
        assert "tasklist" in content, (
            "lib.rs doit avoir un fallback tasklist pour Windows 11 25H2+"
        )

    def test_rust_tasklist_after_wmic(self):
        """tasklist doit être utilisé APRÈS wmic (fallback, pas remplacement)."""
        content = TAURI_LIB_RS.read_text(encoding="utf-8")
        wmic_pos = content.find('"wmic"')
        tasklist_pos = content.find('"tasklist"')
        assert wmic_pos > 0, '"wmic" absent de lib.rs'
        assert tasklist_pos > 0, '"tasklist" absent de lib.rs'
        assert wmic_pos < tasklist_pos, (
            "wmic doit être essayé AVANT tasklist (tasklist est le fallback)"
        )

    def test_rust_windows_handle_wait(self):
        """lib.rs doit attendre après taskkill pour libérer les handles fichier."""
        content = TAURI_LIB_RS.read_text(encoding="utf-8")
        # Vérifier qu'il y a un sleep après le bloc Windows
        assert "from_secs(3)" in content or "from_secs(2)" in content, (
            "lib.rs doit attendre après taskkill pour la libération des handles"
        )


# ============================================================
# Scroll streaming (v0.1.15) - Pas de saccades pendant le streaming
# MessageList doit utiliser scrollTop instantané pendant le streaming.
# ============================================================


class TestScrollStreaming:
    """Scroll instantané pendant le streaming (pas de smooth qui saccade)."""

    def test_instant_scroll_during_streaming(self):
        """MessageList doit utiliser scrollTop direct pendant le streaming."""
        content = MESSAGE_LIST_TSX.read_text(encoding="utf-8")
        assert "scrollTop" in content, (
            "MessageList doit utiliser container.scrollTop pour le scroll instantané"
        )
        assert "scrollHeight" in content, (
            "MessageList doit utiliser container.scrollHeight pour le scroll bas"
        )

    def test_user_scroll_detection(self):
        """MessageList doit détecter quand l'utilisateur scrolle vers le haut."""
        content = MESSAGE_LIST_TSX.read_text(encoding="utf-8")
        assert "userScrolledUp" in content, (
            "MessageList doit tracker si l'utilisateur a scrollé vers le haut"
        )

    def test_smooth_scroll_only_when_not_streaming(self):
        """scrollIntoView smooth ne doit être utilisé que hors streaming."""
        content = MESSAGE_LIST_TSX.read_text(encoding="utf-8")
        assert "isStreaming" in content, (
            "MessageList doit conditionner le type de scroll sur isStreaming"
        )
        assert "behavior: 'smooth'" in content, (
            "MessageList doit garder le smooth scroll pour les messages normaux"
        )


# ============================================================
# BUG-017 (v0.1.16) - Redirection TEMP sidecar Windows
# PyInstaller extrait dans %TEMP%/_MEIxxxx, scanné par Defender.
# lib.rs doit rediriger TEMP/TMP/TMPDIR vers ~/.therese/runtime/
# ============================================================


class TestBUG017TempSidecarRedirect:
    """Redirection TEMP/TMP/TMPDIR vers ~/.therese/runtime/ pour éviter Defender."""

    def test_rust_sets_tmpdir(self):
        """lib.rs doit rediriger TMPDIR vers ~/.therese/runtime/."""
        content = TAURI_LIB_RS.read_text(encoding="utf-8")
        assert '"TMPDIR"' in content, (
            "lib.rs doit définir TMPDIR pour rediriger l'extraction PyInstaller"
        )

    def test_rust_sets_temp(self):
        """lib.rs doit rediriger TEMP vers ~/.therese/runtime/."""
        content = TAURI_LIB_RS.read_text(encoding="utf-8")
        assert '"TEMP"' in content, (
            "lib.rs doit définir TEMP pour Windows"
        )

    def test_rust_sets_tmp(self):
        """lib.rs doit rediriger TMP vers ~/.therese/runtime/."""
        content = TAURI_LIB_RS.read_text(encoding="utf-8")
        assert '"TMP"' in content, (
            "lib.rs doit définir TMP pour Windows"
        )

    def test_rust_runtime_dir_created(self):
        """lib.rs doit créer le dossier ~/.therese/runtime/ avant le sidecar."""
        content = TAURI_LIB_RS.read_text(encoding="utf-8")
        assert "runtime" in content, (
            "lib.rs doit référencer le dossier runtime"
        )
        assert "create_dir_all" in content, (
            "lib.rs doit créer le dossier runtime avec create_dir_all"
        )


# ============================================================
# BUG-018 (v0.1.16) - probeHealth accepte "degraded"
# Le splash screen doit accepter status "degraded" en plus de "healthy".
# Un backend degraded = fonctionnel mais un service non-critique pas prêt.
# ============================================================


SPLASH_SCREEN_TSX = FRONTEND / "components" / "SplashScreen.tsx"


class TestBUG018DegradedStatus:
    """probeHealth doit accepter le status 'degraded' en plus de 'healthy'."""

    def test_probe_accepts_degraded(self):
        """probeHealth doit traiter 'degraded' comme un statut valide."""
        content = SPLASH_SCREEN_TSX.read_text(encoding="utf-8")
        assert "degraded" in content, (
            "probeHealth doit accepter le status 'degraded'"
        )

    def test_probe_accepts_healthy(self):
        """probeHealth doit toujours accepter 'healthy'."""
        content = SPLASH_SCREEN_TSX.read_text(encoding="utf-8")
        assert "healthy" in content, (
            "probeHealth doit accepter le status 'healthy'"
        )


# ============================================================
# BUG-020 (v0.1.17) - Timeout splash Windows insuffisant
# Le backend peut mettre 2min27s+ à démarrer sur Windows
# (extraction PyInstaller + scan Defender + chargement modèles 975 Mo RAM).
# TIMEOUT_MS doit être >= 600_000 (10 min) et POLL_INTERVAL >= 2_000.
# ============================================================


class TestBUG020SplashTimeout:
    """Timeout splash 10 min et polling 2s pour Windows lent."""

    def test_timeout_at_least_600s(self):
        """TIMEOUT_MS doit être >= 600_000 (10 min)."""
        content = SPLASH_SCREEN_TSX.read_text(encoding="utf-8")
        # Chercher la constante TIMEOUT_MS
        import re
        match = re.search(r"TIMEOUT_MS\s*=\s*([\d_]+)", content)
        assert match, "TIMEOUT_MS non trouvé dans SplashScreen.tsx"
        value = int(match.group(1).replace("_", ""))
        assert value >= 600_000, (
            f"TIMEOUT_MS = {value} ms, doit être >= 600_000 (10 min) "
            "pour supporter le démarrage lent sur Windows"
        )

    def test_poll_interval_at_least_2s(self):
        """POLL_INTERVAL doit être >= 2_000 (2s) pour réduire la charge."""
        content = SPLASH_SCREEN_TSX.read_text(encoding="utf-8")
        import re
        match = re.search(r"POLL_INTERVAL\s*=\s*([\d_]+)", content)
        assert match, "POLL_INTERVAL non trouvé dans SplashScreen.tsx"
        value = int(match.group(1).replace("_", ""))
        assert value >= 2_000, (
            f"POLL_INTERVAL = {value} ms, doit être >= 2_000 (2s) "
            "pour ne pas surcharger le réseau pendant le boot"
        )

    def test_adaptive_messages(self):
        """Le splash doit afficher des messages adaptés au temps écoulé."""
        content = SPLASH_SCREEN_TSX.read_text(encoding="utf-8")
        # Vérifier qu'il y a des messages pour les longues attentes (>= 60s)
        assert "60_000" in content or "60000" in content, (
            "Le splash doit avoir un message après 60s d'attente"
        )
        assert "120_000" in content or "120000" in content, (
            "Le splash doit avoir un message après 120s d'attente"
        )

    def test_logarithmic_progress(self):
        """La barre de progression doit être logarithmique (pas linéaire)."""
        content = SPLASH_SCREEN_TSX.read_text(encoding="utf-8")
        assert "log1p" in content or "Math.log" in content, (
            "La progression doit être logarithmique pour rester informative "
            "sans stresser l'utilisateur sur les longues attentes"
        )


# ============================================================
# BUG-020/021 (v0.1.18) - Preload embeddings non-bloquant
# Le preload_embedding_model doit être lancé en fire-and-forget
# via asyncio.create_task, pas awaité directement.
# ============================================================

CHAT_LAYOUT_TSX = FRONTEND / "components" / "chat" / "ChatLayout.tsx"
MEMORY_PANEL_TSX = FRONTEND / "components" / "memory" / "MemoryPanel.tsx"
MESSAGE_BUBBLE_TSX = FRONTEND / "components" / "chat" / "MessageBubble.tsx"
CHAT_HEADER_TSX = FRONTEND / "components" / "chat" / "ChatHeader.tsx"
EMAIL_PANEL_TSX = FRONTEND / "components" / "email" / "EmailPanel.tsx"


class TestBUG020LazyLoading:
    """Le preload embeddings ne doit pas bloquer le démarrage du serveur HTTP."""

    def test_preload_not_awaited_directly_in_lifespan(self):
        """preload_embedding_model() ne doit PAS être awaité directement dans le lifespan."""
        content = APP_MAIN_PY.read_text(encoding="utf-8")
        # Vérifier que le await n'est PAS au niveau d'indentation du lifespan (4 espaces)
        # mais seulement dans une sous-fonction (8+ espaces) lancée via create_task
        for line in content.split("\n"):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            if stripped.startswith("await preload_embedding_model()"):
                assert indent > 4, (
                    "preload_embedding_model() ne doit PAS être awaité directement "
                    "dans le lifespan (indentation 4) - utiliser asyncio.create_task()"
                )

    def test_preload_uses_create_task(self):
        """Le preload doit être lancé via asyncio.create_task (fire-and-forget)."""
        content = APP_MAIN_PY.read_text(encoding="utf-8")
        assert "create_task" in content, (
            "Le preload embeddings doit utiliser asyncio.create_task()"
        )
        assert "preload_embedding" in content, (
            "Le preload embeddings doit référencer preload_embedding_model"
        )


# ============================================================
# BUG-021 (v0.1.18) - Saccades streaming scroll
# Le scroll pendant le streaming doit être throttlé via rAF.
# ============================================================


class TestBUG021StreamingScroll:
    """Scroll throttlé via requestAnimationFrame pendant le streaming."""

    def test_raf_used_for_streaming_scroll(self):
        """MessageList doit utiliser requestAnimationFrame pendant le streaming."""
        content = MESSAGE_LIST_TSX.read_text(encoding="utf-8")
        assert "requestAnimationFrame" in content, (
            "MessageList doit utiliser requestAnimationFrame pour throttler le scroll streaming"
        )

    def test_raf_ref_present(self):
        """MessageList doit avoir un ref pour tracker le rAF en cours."""
        content = MESSAGE_LIST_TSX.read_text(encoding="utf-8")
        assert "rafRef" in content, (
            "MessageList doit avoir un rafRef pour éviter les appels rAF redondants"
        )


# ============================================================
# UX (v0.1.18) - Sidebar conversations visible par défaut
# ============================================================


class TestUXSidebarDefault:
    """La sidebar conversations doit être visible au premier lancement."""

    def test_sidebar_default_true(self):
        """showConversationSidebar doit être initialisé à true."""
        content = CHAT_LAYOUT_TSX.read_text(encoding="utf-8")
        assert "useState(true)" in content, (
            "showConversationSidebar doit être initialisé à true (sidebar visible par défaut)"
        )
        # Vérifier que c'est bien le bon useState (celui de showConversationSidebar)
        lines = content.split("\n")
        for line in lines:
            if "showConversationSidebar" in line and "useState" in line:
                assert "useState(true)" in line, (
                    "showConversationSidebar doit utiliser useState(true)"
                )
                break


# ============================================================
# UX (v0.1.18) - Cohérence nommage Mémoire
# ============================================================


class TestUXNamingConsistency:
    """Le panel mémoire doit afficher "Mémoire" (pas "Espace de travail")."""

    def test_no_espace_de_travail(self):
        """MemoryPanel ne doit plus contenir "Espace de travail"."""
        content = MEMORY_PANEL_TSX.read_text(encoding="utf-8")
        assert "Espace de travail" not in content, (
            "MemoryPanel doit afficher 'Mémoire' au lieu de 'Espace de travail'"
        )


# ============================================================
# UX (v0.1.18) - Tooltip tokens/EUR
# ============================================================


class TestUXTokenTooltip:
    """Le compteur tokens/EUR doit avoir un tooltip explicatif."""

    def test_usage_has_title_attribute(self):
        """Le conteneur usage/cost doit avoir un attribut title (tooltip)."""
        content = MESSAGE_BUBBLE_TSX.read_text(encoding="utf-8")
        # Chercher le title près du Coins/usage
        assert 'title="' in content and "tokens" in content, (
            "Le conteneur usage/cost doit avoir un attribut title (tooltip)"
        )
        assert "pas une facture" in content or "coût estimé" in content.lower(), (
            "Le tooltip doit expliquer que ce n'est pas une facture"
        )


# ============================================================
# UX (v0.1.18) - Logo THÉRÈSE cliquable
# ============================================================


class TestUXLogoClickable:
    """Le logo THÉRÈSE doit être cliquable (nouvelle conversation)."""

    def test_logo_has_onclick(self):
        """Le logo dans ChatHeader doit avoir un onClick pour créer une conversation."""
        content = CHAT_HEADER_TSX.read_text(encoding="utf-8")
        # Le logo doit être dans un élément cliquable
        assert "createConversation" in content, (
            "ChatHeader doit utiliser createConversation pour le logo"
        )
        # Vérifier qu'il y a un onClick sur un élément contenant THÉRÈSE
        lines = content.split("\n")
        found_clickable_logo = False
        for i, line in enumerate(lines):
            if "THÉRÈSE" in line:
                # Vérifier les lignes avant pour un onClick
                context = "\n".join(lines[max(0, i - 5):i + 1])
                if "onClick" in context:
                    found_clickable_logo = True
                    break
        assert found_clickable_logo, (
            "Le logo THÉRÈSE doit être dans un élément cliquable (onClick)"
        )


# ============================================================
# UX (v0.1.18) - Bouton déconnecter compte email
# ============================================================


class TestUXEmailDisconnect:
    """EmailPanel doit permettre de déconnecter un compte email."""

    def test_disconnect_button_present(self):
        """EmailPanel doit contenir un bouton de déconnexion."""
        content = EMAIL_PANEL_TSX.read_text(encoding="utf-8")
        assert "handleDisconnectAccount" in content, (
            "EmailPanel doit avoir une fonction handleDisconnectAccount"
        )
        assert "LogOut" in content or "Déconnecter" in content, (
            "EmailPanel doit avoir un bouton de déconnexion visible"
        )

    def test_disconnect_calls_api(self):
        """handleDisconnectAccount doit appeler l'API disconnectEmailAccount."""
        content = EMAIL_PANEL_TSX.read_text(encoding="utf-8")
        assert "disconnectEmailAccount" in content, (
            "EmailPanel doit appeler api.disconnectEmailAccount()"
        )


# ============================================================
# Port fixe 17293 (v0.1.19) - Suppression du port dynamique
# Le port dynamique (find_free_port) causait BUG-002, 008, 011, 015.
# Le port fixe 17293 simplifie toute la chaîne.
# ============================================================

CONFIG_PY = SRC / "app" / "config.py"


class TestPortFixe17293:
    """Port fixe 17293 utilisé partout (lib.rs, main.py, core.ts, config.py)."""

    def test_rust_uses_fixed_port(self):
        """lib.rs doit utiliser le port fixe 17293 (pas find_free_port)."""
        content = TAURI_LIB_RS.read_text(encoding="utf-8")
        assert "17293" in content, (
            "lib.rs doit contenir le port fixe 17293"
        )
        assert "find_free_port" not in content, (
            "lib.rs ne doit plus contenir find_free_port (port dynamique supprimé)"
        )

    def test_rust_no_tcplistener_bind(self):
        """lib.rs ne doit plus utiliser TcpListener::bind pour trouver un port."""
        content = TAURI_LIB_RS.read_text(encoding="utf-8")
        assert "TcpListener::bind" not in content, (
            "lib.rs ne doit plus utiliser TcpListener::bind (port dynamique supprimé)"
        )

    def test_main_py_default_port_17293(self):
        """main.py doit avoir default=17293 pour --port."""
        content = MAIN_PY.read_text(encoding="utf-8")
        assert "default=17293" in content, (
            "main.py doit utiliser default=17293 pour le port"
        )

    def test_config_py_port_17293(self):
        """config.py doit définir port: int = 17293."""
        content = CONFIG_PY.read_text(encoding="utf-8")
        assert "port: int = 17293" in content, (
            "config.py doit définir le port par défaut à 17293"
        )

    def test_core_ts_fallback_17293(self):
        """core.ts doit utiliser le port 17293 comme fallback."""
        content = API_CORE_TS.read_text(encoding="utf-8")
        assert "http://127.0.0.1:17293" in content, (
            "core.ts doit utiliser http://127.0.0.1:17293 comme API_BASE"
        )

    def test_core_ts_no_port_8000_check(self):
        """core.ts ne doit plus vérifier port !== 8000."""
        content = API_CORE_TS.read_text(encoding="utf-8")
        assert "port !== 8000" not in content, (
            "core.ts ne doit plus contenir 'port !== 8000' (port fixe, plus besoin)"
        )
        assert "port != 8000" not in content, (
            "core.ts ne doit plus contenir 'port != 8000' (port fixe, plus besoin)"
        )


# ============================================================
# BUG-022 (v0.1.20) - CORS Windows (http://tauri.localhost)
# Tauri 2.0 sur Windows utilise http://tauri.localhost comme origin.
# Le CORS backend doit l'autoriser sinon fetch() échoue silencieusement.
# ============================================================


class TestBUG022CORSWindowsOrigin:
    """BUG-022 : CORS bloquait le fetch health sur Windows (http://tauri.localhost absent)."""

    def test_cors_has_http_tauri_localhost(self):
        """L'origin Windows DOIT être dans la liste CORS."""
        content = APP_MAIN_PY.read_text(encoding="utf-8")
        assert "http://tauri.localhost" in content, (
            "main.py doit contenir http://tauri.localhost dans les origins CORS"
        )

    def test_cors_has_all_three_origins(self):
        """Les 3 origins Tauri production DOIVENT être présents."""
        content = APP_MAIN_PY.read_text(encoding="utf-8")
        assert "tauri://localhost" in content, (
            "main.py doit contenir tauri://localhost (macOS/Linux)"
        )
        assert "https://tauri.localhost" in content, (
            "main.py doit contenir https://tauri.localhost (HTTPS legacy)"
        )
        assert "http://tauri.localhost" in content, (
            "main.py doit contenir http://tauri.localhost (Windows/Android)"
        )

    def test_probe_health_has_error_logging(self):
        """probeHealth ne doit plus avoir de catch silencieux."""
        content = SPLASH_SCREEN_TSX.read_text(encoding="utf-8")
        assert "console.error" in content, (
            "probeHealth doit logger les erreurs avec console.error (plus de catch silencieux)"
        )

    def test_probe_health_timeout_at_least_5s(self):
        """Le timeout du health check doit être >= 5000ms."""
        content = SPLASH_SCREEN_TSX.read_text(encoding="utf-8")
        assert "createTimeoutSignal(5000)" in content, (
            "probeHealth doit utiliser un timeout de 5000ms minimum"
        )

    def test_private_network_access_header(self):
        """Le header Access-Control-Allow-Private-Network doit être géré."""
        content = APP_MAIN_PY.read_text(encoding="utf-8")
        assert "Access-Control-Allow-Private-Network" in content, (
            "main.py doit gérer le header PNA pour WebView2 143+"
        )


# ============================================================
# BUG-023 (v0.2.0) - Race condition email (loadMessages concurrent)
# Zustand persist hydration déclenche loadMessages() plusieurs fois.
# AbortController + garde isLoadingRef + getState() au lieu de closure.
# ============================================================


EMAIL_LIST_TSX = FRONTEND / "components" / "email" / "EmailList.tsx"


class TestBUG023EmailRaceCondition:
    """BUG-023 : race condition loadMessages (AbortController + garde + pas de closure stale)."""

    def test_abort_controller_present(self):
        """EmailList doit utiliser un AbortController pour annuler les chargements concurrents."""
        content = EMAIL_LIST_TSX.read_text(encoding="utf-8")
        assert "AbortController" in content, (
            "EmailList doit utiliser AbortController pour annuler les loadMessages concurrents"
        )
        assert "abortControllerRef" in content, (
            "EmailList doit stocker l'AbortController dans un ref"
        )

    def test_loading_guard_present(self):
        """EmailList doit avoir un garde isLoadingRef pour éviter les appels concurrents."""
        content = EMAIL_LIST_TSX.read_text(encoding="utf-8")
        assert "isLoadingRef" in content, (
            "EmailList doit avoir un isLoadingRef pour bloquer les appels concurrents"
        )

    def test_no_stale_closure(self):
        """EmailList doit utiliser getState() au lieu d'une closure stale pour le cache."""
        content = EMAIL_LIST_TSX.read_text(encoding="utf-8")
        assert "useEmailStore.getState()" in content, (
            "EmailList doit utiliser useEmailStore.getState() pour lire le cache "
            "(pas une closure stale qui ne se met pas à jour)"
        )

    def test_abort_on_cleanup(self):
        """EmailList doit abort() au démontage du composant."""
        content = EMAIL_LIST_TSX.read_text(encoding="utf-8")
        # Vérifier qu'il y a un cleanup return dans un useEffect qui appelle abort
        assert "abortControllerRef.current" in content, (
            "EmailList doit vérifier abortControllerRef.current dans le cleanup"
        )
        assert ".abort()" in content, (
            "EmailList doit appeler .abort() pour annuler le chargement en cours"
        )


# ============================================================
# OpenRouter provider (v0.2.0) - Nouveau provider LLM
# API OpenAI-compatible à https://openrouter.ai/api/v1/chat/completions
# ============================================================


PROVIDERS_DIR = SRC / "app" / "services" / "providers"
OPENROUTER_PY = PROVIDERS_DIR / "openrouter.py"
PROVIDERS_INIT_PY = PROVIDERS_DIR / "__init__.py"
LLM_PY = SRC / "app" / "services" / "llm.py"


class TestOpenRouterProvider:
    """Provider OpenRouter (API OpenAI-compatible, 200+ modèles)."""

    def test_openrouter_file_exists(self):
        """Le fichier openrouter.py doit exister dans les providers."""
        assert OPENROUTER_PY.exists(), (
            "src/backend/app/services/providers/openrouter.py doit exister"
        )

    def test_openrouter_in_init(self):
        """OpenRouterProvider doit être exporté dans __init__.py."""
        content = PROVIDERS_INIT_PY.read_text(encoding="utf-8")
        assert "OpenRouterProvider" in content, (
            "OpenRouterProvider doit être exporté dans providers/__init__.py"
        )

    def test_openrouter_in_provider_map(self):
        """OPENROUTER doit être dans le provider_map de llm.py."""
        content = LLM_PY.read_text(encoding="utf-8")
        assert "OPENROUTER" in content, (
            "LLMProvider.OPENROUTER doit être dans le provider_map de llm.py"
        )
        assert "OpenRouterProvider" in content, (
            "OpenRouterProvider doit être importé dans llm.py"
        )

    def test_openrouter_api_url(self):
        """Le provider doit utiliser l'URL API OpenRouter."""
        content = OPENROUTER_PY.read_text(encoding="utf-8")
        assert "openrouter.ai/api/v1" in content, (
            "openrouter.py doit utiliser l'API OpenRouter (openrouter.ai/api/v1)"
        )


# ============================================================
# Fal image provider (v0.2.0) - Génération d'images Flux Pro v1.1
# API Fal à https://fal.run/fal-ai/flux-pro/v1.1
# ============================================================


IMAGE_GENERATOR_PY = SRC / "app" / "services" / "image_generator.py"


class TestFalImageProvider:
    """Provider Fal pour la génération d'images (Flux Pro v1.1)."""

    def test_fal_in_image_provider_enum(self):
        """FAL doit être dans l'enum ImageProvider."""
        content = IMAGE_GENERATOR_PY.read_text(encoding="utf-8")
        assert "FAL" in content, (
            "ImageProvider.FAL doit exister dans image_generator.py"
        )
        assert "fal-flux-pro" in content, (
            "FAL doit avoir la valeur 'fal-flux-pro' dans l'enum"
        )

    def test_fal_generation_method(self):
        """La méthode _generate_fal doit exister dans ImageGeneratorService."""
        content = IMAGE_GENERATOR_PY.read_text(encoding="utf-8")
        assert "_generate_fal" in content, (
            "ImageGeneratorService doit avoir une méthode _generate_fal()"
        )
        assert "fal.run" in content or "fal-ai/flux-pro" in content, (
            "_generate_fal doit utiliser l'API Fal (fal.run ou fal-ai/flux-pro)"
        )


# ============================================================
# Fix version À propos (v0.2.0) - Panels Tauri contexte JS séparé
# AboutTab doit fetch la version si elle est null (panels séparés).
# ============================================================


ABOUT_TAB_TSX = FRONTEND / "components" / "settings" / "AboutTab.tsx"


class TestAboutVersionDisplay:
    """AboutTab doit récupérer la version même dans un panel séparé."""

    def test_about_tab_fetches_version(self):
        """AboutTab doit appeler checkHealth si la version est null."""
        content = ABOUT_TAB_TSX.read_text(encoding="utf-8")
        assert "checkHealth" in content, (
            "AboutTab doit importer et utiliser checkHealth() pour récupérer la version "
            "dans les panels Tauri (contexte JS séparé)"
        )


# ============================================================
# BUG-024 (v0.2.0) - Profil utilisateur : champs facturation
# Le schema Pydantic doit inclure address, siren, tva_intra
# sinon le POST /profile les perd silencieusement.
# ============================================================


SCHEMAS_PY = SRC / "app" / "models" / "schemas.py"
CONFIG_ROUTER_PY = SRC / "app" / "routers" / "config.py"


class TestBUG024ProfileSave:
    """BUG-024 : les champs facturation (address, siren, tva_intra) doivent être dans le schema."""

    def test_profile_schema_has_billing_fields(self):
        """UserProfileUpdate doit contenir address, siren, tva_intra."""
        content = SCHEMAS_PY.read_text(encoding="utf-8")
        # Parser l'AST pour trouver la classe UserProfileUpdate
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "UserProfileUpdate":
                class_source = ast.get_source_segment(content, node)
                assert "address" in class_source, (
                    "UserProfileUpdate doit avoir le champ 'address'"
                )
                assert "siren" in class_source, (
                    "UserProfileUpdate doit avoir le champ 'siren'"
                )
                assert "tva_intra" in class_source, (
                    "UserProfileUpdate doit avoir le champ 'tva_intra'"
                )
                break
        else:
            pytest.fail("Classe UserProfileUpdate non trouvée dans schemas.py")

    def test_profile_response_has_billing_fields(self):
        """UserProfileResponse doit contenir address, siren, tva_intra."""
        content = SCHEMAS_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "UserProfileResponse":
                class_source = ast.get_source_segment(content, node)
                assert "address" in class_source, (
                    "UserProfileResponse doit avoir le champ 'address'"
                )
                assert "siren" in class_source, (
                    "UserProfileResponse doit avoir le champ 'siren'"
                )
                assert "tva_intra" in class_source, (
                    "UserProfileResponse doit avoir le champ 'tva_intra'"
                )
                break
        else:
            pytest.fail("Classe UserProfileResponse non trouvée dans schemas.py")


# ============================================================
# Boutons fenêtre Windows/Linux (v0.2.0)
# ChatHeader doit détecter la plateforme et adapter les boutons.
# macOS : traffic lights à gauche. Windows/Linux : boutons à droite.
# ============================================================


class TestWindowControlsPlatform:
    """ChatHeader doit adapter les boutons fenêtre selon la plateforme."""

    def test_platform_detection_in_header(self):
        """ChatHeader doit détecter macOS vs Windows/Linux."""
        content = CHAT_HEADER_TSX.read_text(encoding="utf-8")
        assert "isMac" in content, (
            "ChatHeader doit avoir une variable isMac pour la détection de plateforme"
        )
        assert "navigator.platform" in content, (
            "ChatHeader doit utiliser navigator.platform pour détecter l'OS"
        )


# ============================================================
# Anti-bump texte streaming (v0.2.0)
# CSS containment + batch 50ms pour éviter les layout shifts.
# ============================================================


CHAT_INPUT_TSX = FRONTEND / "components" / "chat" / "ChatInput.tsx"


class TestStreamingAntiFlicker:
    """Optimisations anti-flicker pour le streaming (containment + batch)."""

    def test_message_bubble_has_css_containment(self):
        """MessageBubble doit utiliser CSS containment pour isoler les repaints."""
        content = MESSAGE_BUBBLE_TSX.read_text(encoding="utf-8")
        assert "contain" in content, (
            "MessageBubble doit utiliser la propriété CSS 'contain' pour isoler les repaints"
        )

    def test_streaming_batch_interval(self):
        """ChatInput doit batcher les updates streaming avec setInterval (pas rAF pur)."""
        content = CHAT_INPUT_TSX.read_text(encoding="utf-8")
        assert "setInterval" in content, (
            "ChatInput doit utiliser setInterval pour batcher les updates streaming"
        )
        assert "50" in content, (
            "ChatInput doit utiliser un intervalle de 50ms pour le batch streaming"
        )
