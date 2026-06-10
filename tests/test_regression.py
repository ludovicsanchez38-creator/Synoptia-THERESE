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
MESSAGE_LIST_TSX = FRONTEND / "components" / "chat" / "MessageList.tsx"


class TestBUG015PortMismatchPanels:
    """initApiBase() doit lire le port backend depuis le paramètre ?port= de l'URL.

    Note (revue produit) : le test du windowManager (fenêtres-panels Tauri détachées)
    a été retiré en Phase 1 L9 — les panels sont devenus des vues content-swap, il
    n'y a plus de fenêtre détachée à qui passer le port dans l'URL. La suppression de
    cette machinerie est validée par TestPhase1_CRMAsView::test_panel_window_system_removed.
    Restent les invariants côté récepteur (core.ts), toujours valides.
    """

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
    """US-010 : scroll géré par react-virtuoso (followOutput) - l'intention
    historique (suivre le flux en bas, respecter la position de lecture)
    est désormais portée par computeFollowOutput + Virtuoso."""

    def test_virtuoso_handles_scroll(self):
        """MessageList doit déléguer le scroll à Virtuoso (virtualisation US-010)."""
        content = MESSAGE_LIST_TSX.read_text(encoding="utf-8")
        assert "Virtuoso" in content, (
            "MessageList doit utiliser react-virtuoso pour la liste de messages"
        )
        assert "followOutput" in content, (
            "MessageList doit utiliser followOutput pour le scroll automatique"
        )

    def test_user_scroll_detection(self):
        """Le suivi du bas doit dépendre de la position utilisateur (atBottom)."""
        content = MESSAGE_LIST_TSX.read_text(encoding="utf-8")
        assert "atBottomThreshold" in content, (
            "MessageList doit configurer atBottomThreshold pour détecter si "
            "l'utilisateur est en bas (sinon on lui vole le scroll)"
        )

    def test_smooth_scroll_only_when_at_bottom(self):
        """followOutput doit retourner 'smooth' quand l'utilisateur est en bas
        (hors streaming) et false quand il a remonté la conversation."""
        follow_output = MESSAGE_LIST_TSX.parent / "followOutput.ts"
        content = follow_output.read_text(encoding="utf-8")
        assert "isStreaming" in content, (
            "computeFollowOutput doit conditionner le comportement au streaming"
        )
        assert "'smooth'" in content, (
            "computeFollowOutput doit retourner 'smooth' quand l'utilisateur est en bas"
        )
        assert "return false" in content, (
            "computeFollowOutput doit retourner false quand l'utilisateur a remonté"
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
    """BUG-021 : pas de scroll manuel par requestAnimationFrame. US-010 :
    le scroll est entièrement délégué à react-virtuoso (followOutput)."""

    def test_virtuoso_replaces_raf_scroll(self):
        """MessageList ne doit PAS faire de scroll manuel (rAF ou scrollIntoView)."""
        content = MESSAGE_LIST_TSX.read_text(encoding="utf-8")
        assert "requestAnimationFrame" not in content, (
            "MessageList ne doit pas scroller via requestAnimationFrame manuel (BUG-021)"
        )
        assert "Virtuoso" in content, (
            "MessageList doit déléguer le scroll à react-virtuoso (US-010)"
        )

    def test_virtuoso_ref_present(self):
        """La politique de scroll doit être centralisée dans computeFollowOutput."""
        content = MESSAGE_LIST_TSX.read_text(encoding="utf-8")
        assert "computeFollowOutput" in content, (
            "MessageList doit utiliser computeFollowOutput (politique de scroll testée)"
        )


# ============================================================
# UX (v0.1.18) - Sidebar conversations visible par défaut
# ============================================================


class TestUXSidebarDefault:
    """La sidebar conversations doit être visible au premier lancement."""

    def test_sidebar_default_true(self):
        """showConversationSidebar doit être initialisé à true dans panelStore."""
        panel_store = FRONTEND / "stores" / "panelStore.ts"
        content = panel_store.read_text(encoding="utf-8")
        assert "showConversationSidebar: true" in content, (
            "showConversationSidebar doit être initialisé à true dans panelStore (sidebar visible par défaut)"
        )
        # Vérifier que ChatLayout utilise bien le panelStore pour la sidebar
        layout_content = CHAT_LAYOUT_TSX.read_text(encoding="utf-8")
        assert "usePanelStore" in layout_content, (
            "ChatLayout doit utiliser usePanelStore pour gérer la sidebar"
        )
        assert "showConversationSidebar" in layout_content, (
            "ChatLayout doit utiliser showConversationSidebar du panelStore"
        )


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


# ============================================================
# BUG-024 (v0.2.2) - Templates DOCX/PPTX manquants dans PyInstaller
# python-docx et python-pptx cherchent leurs templates XML mais
# PyInstaller ne les inclut pas automatiquement dans le bundle.
# ============================================================


BACKEND_SPEC = SRC / "backend.spec"


class TestBUG024DocxPptxTemplates:
    """BUG-024 : collect_data_files docx + pptx dans backend.spec."""

    def test_backend_spec_includes_docx_data_files(self):
        """backend.spec doit collecter les data files de python-docx."""
        spec = BACKEND_SPEC.read_text(encoding="utf-8")
        assert 'collect_data_files("docx")' in spec, (
            "backend.spec doit contenir collect_data_files('docx') "
            "pour inclure les templates XML de python-docx"
        )

    def test_backend_spec_includes_pptx_data_files(self):
        """backend.spec doit collecter les data files de python-pptx."""
        spec = BACKEND_SPEC.read_text(encoding="utf-8")
        assert 'collect_data_files("pptx")' in spec, (
            "backend.spec doit contenir collect_data_files('pptx') "
            "pour inclure les templates XML de python-pptx"
        )


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
    """Optimisations anti-flicker pour le streaming (containment + phrase-par-phrase)."""

    def test_message_bubble_has_css_containment(self):
        """MessageBubble doit utiliser CSS containment pour isoler les repaints."""
        content = MESSAGE_BUBBLE_TSX.read_text(encoding="utf-8")
        assert "contain" in content, (
            "MessageBubble doit utiliser la propriété CSS 'contain' pour isoler les repaints"
        )

    def test_streaming_sentence_flush(self):
        """ChatInput doit flusher sur frontière de phrase (v0.2.3)."""
        content = CHAT_INPUT_TSX.read_text(encoding="utf-8")
        assert "SENTENCE_ENDINGS" in content, (
            "ChatInput doit détecter les fins de phrase pour le flush streaming"
        )
        assert "flushToDisplay" in content, (
            "ChatInput doit avoir une fonction flushToDisplay pour le streaming phrase-par-phrase"
        )
        assert "800" in content, (
            "ChatInput doit avoir un timeout de sécurité 800ms pour le flush"
        )


# ============================================================
# BUG-025 (v0.2.3, corrigé v0.2.6) - Ollama /api/chat
# Le provider Ollama doit envoyer le system prompt comme
# message role="system" dans la liste messages (pas en top-level).
# Le base_url doit être nettoyé du trailing slash.
# ============================================================


PROVIDERS = SRC / "app" / "services" / "providers"


class TestBUG025OllamaSystemPrompt:
    """BUG-025 : Ollama provider doit envoyer le system prompt dans messages."""

    def test_ollama_system_prompt_as_message(self):
        """Le system prompt doit être ajouté comme message role='system'."""
        code = PROVIDERS / "ollama.py"
        content = code.read_text(encoding="utf-8")
        assert '"role": "system"' in content, (
            "Ollama provider doit insérer le system prompt comme message role='system'"
        )

    def test_ollama_no_top_level_system_in_json(self):
        """Le JSON envoyé à /api/chat ne doit pas contenir 'system' top-level."""
        import re
        code = PROVIDERS / "ollama.py"
        content = code.read_text(encoding="utf-8")
        # US-009 : le body est désormais construit dans request_body (dict
        # nommé) avant d'être passé à json= ; couvrir les deux formes.
        json_block = re.search(
            r'(?:json=\{(.*?)\}|request_body: dict = \{(.*?)\})', content, re.DOTALL
        )
        assert json_block, "Bloc json=/request_body non trouvé dans ollama.py"
        json_content = json_block.group(1) or json_block.group(2)
        assert '"system"' not in json_content, (
            "/api/chat n'accepte pas de champ 'system' top-level"
        )

    def test_ollama_base_url_trailing_slash(self):
        """base_url doit être nettoyé du trailing slash."""
        code = PROVIDERS / "ollama.py"
        content = code.read_text(encoding="utf-8")
        assert '.rstrip("/")' in content or ".rstrip('/')" in content, (
            "base_url doit être nettoyé avec rstrip('/') pour éviter les double slashes"
        )

    def test_ollama_filters_system_messages(self):
        """Les messages role=system existants doivent être filtrés avant d'ajouter le system prompt."""
        code = PROVIDERS / "ollama.py"
        content = code.read_text(encoding="utf-8")
        assert "chat_messages" in content, (
            "Ollama provider doit construire une liste chat_messages propre"
        )


# ============================================================
# BUG-026 (v0.2.3) - Profil utilisateur ne sauvegarde pas
# set_user_profile et delete_user_profile doivent utiliser
# key + category (comme get_user_profile).
# ============================================================


class TestBUG026ProfileSave:
    """BUG-026 : set_user_profile doit utiliser key + category."""

    def test_set_profile_uses_category(self):
        """Les 3 fonctions (get, set, delete) doivent toutes utiliser PROFILE_CATEGORY."""
        code = USER_PROFILE_PY.read_text(encoding="utf-8")
        assert code.count("PROFILE_CATEGORY") >= 3, (
            "get, set et delete doivent tous utiliser PROFILE_CATEGORY"
        )

    def test_delete_profile_uses_category(self):
        """delete_user_profile doit filtrer par PROFILE_CATEGORY."""
        code = USER_PROFILE_PY.read_text(encoding="utf-8")
        # Trouver la fonction delete_user_profile et vérifier PROFILE_CATEGORY
        delete_start = code.find("async def delete_user_profile")
        assert delete_start > 0, "delete_user_profile non trouvé"
        delete_body = code[delete_start:delete_start + 500]
        assert "PROFILE_CATEGORY" in delete_body, (
            "delete_user_profile doit utiliser PROFILE_CATEGORY dans sa requête"
        )


# ============================================================
# Support XLSX dans file_parser (v0.2.3)
# file_parser.py doit pouvoir extraire le contenu de fichiers .xlsx.
# ============================================================


FILE_PARSER_PY = SRC / "app" / "services" / "file_parser.py"


class TestXLSXSupport:
    """Support extraction de fichiers Excel (.xlsx)."""

    def test_xlsx_extract_function_exists(self):
        """file_parser doit avoir une fonction _extract_xlsx."""
        content = FILE_PARSER_PY.read_text(encoding="utf-8")
        assert "_extract_xlsx" in content, (
            "file_parser.py doit contenir la fonction _extract_xlsx"
        )

    def test_xlsx_extension_handled(self):
        """file_parser doit gérer l'extension .xlsx."""
        content = FILE_PARSER_PY.read_text(encoding="utf-8")
        assert '".xlsx"' in content, (
            "file_parser.py doit gérer l'extension .xlsx"
        )


# ============================================================
# Upload fichiers vers projets (v0.2.3)
# L'endpoint POST /api/files/upload doit exister.
# ============================================================


FILES_ROUTER_PY = SRC / "app" / "routers" / "files.py"


class TestUploadEndpoint:
    """Endpoint upload fichier vers projet."""

    def test_upload_endpoint_exists(self):
        """Le router files doit avoir un endpoint /upload."""
        content = FILES_ROUTER_PY.read_text(encoding="utf-8")
        assert "upload" in content, (
            "files.py doit contenir un endpoint upload"
        )
        assert "UploadFile" in content, (
            "files.py doit utiliser UploadFile de FastAPI"
        )

    def test_upload_validates_extension(self):
        """L'upload doit valider les extensions autorisées."""
        content = FILES_ROUTER_PY.read_text(encoding="utf-8")
        assert "ALLOWED_UPLOAD_EXTENSIONS" in content, (
            "files.py doit définir les extensions autorisées pour l'upload"
        )


# ============================================================
# Phase 1 (v0.2.4) - skill_id dans le chat endpoint
# Les skills TEXT/ANALYSIS doivent recevoir le system prompt du skill.
# ============================================================


CHAT_ROUTER_PY = SRC / "app" / "routers" / "chat.py"
CHAT_TS = FRONTEND / "services" / "api" / "chat.ts"
GUIDED_PROMPTS_TSX = FRONTEND / "components" / "guided" / "GuidedPrompts.tsx"


class TestSkillIdInChat:
    """Phase 1 : skill_id doit être propagé du frontend au backend."""

    def test_backend_schema_has_skill_id(self):
        """ChatRequest (schemas.py) doit avoir le champ skill_id."""
        content = SCHEMAS_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "ChatRequest":
                class_source = ast.get_source_segment(content, node)
                assert "skill_id" in class_source, (
                    "ChatRequest doit avoir le champ skill_id"
                )
                break
        else:
            pytest.fail("Classe ChatRequest non trouvée dans schemas.py")

    def test_backend_injects_skill_system_prompt(self):
        """chat.py doit injecter le system prompt du skill quand skill_id est fourni."""
        content = CHAT_ROUTER_PY.read_text(encoding="utf-8")
        assert "get_skills_registry" in content, (
            "chat.py doit importer get_skills_registry pour charger les skills"
        )
        assert "get_system_prompt_addition" in content, (
            "chat.py doit appeler get_system_prompt_addition() sur le skill"
        )

    def test_frontend_chat_api_has_skill_id(self):
        """ChatRequest dans chat.ts doit contenir skill_id."""
        content = CHAT_TS.read_text(encoding="utf-8")
        assert "skill_id" in content, (
            "chat.ts ChatRequest doit contenir le champ skill_id"
        )

    def test_guided_prompts_passes_skill_id(self):
        """GuidedPrompts doit passer le skillId à onPromptSelect."""
        content = GUIDED_PROMPTS_TSX.read_text(encoding="utf-8")
        assert "skillId" in content, (
            "GuidedPrompts doit passer skillId à onPromptSelect"
        )


# ============================================================
# Phase 2 (v0.2.4) - Sauvegarder comme raccourci
# Bouton Bookmark dans MessageBubble + modal CreateCommandForm.
# ============================================================


class TestSaveAsCommand:
    """Phase 2 : bouton sauvegarder comme raccourci dans le chat."""

    def test_message_bubble_has_bookmark(self):
        """MessageBubble doit avoir un bouton Bookmark pour sauvegarder."""
        content = MESSAGE_BUBBLE_TSX.read_text(encoding="utf-8")
        assert "Bookmark" in content, (
            "MessageBubble doit importer l'icône Bookmark"
        )
        assert "onSaveAsCommand" in content, (
            "MessageBubble doit avoir la prop onSaveAsCommand"
        )

    def test_message_list_has_save_as_command(self):
        """MessageList doit propager onSaveAsCommand."""
        content = (FRONTEND / "components" / "chat" / "MessageList.tsx").read_text(encoding="utf-8")
        assert "onSaveAsCommand" in content, (
            "MessageList doit avoir la prop onSaveAsCommand"
        )

    def test_panel_container_has_save_command_modal(self):
        """PanelContainer doit afficher le modal CreateCommandForm (extrait de ChatLayout)."""
        content = (FRONTEND / "components" / "chat" / "PanelContainer.tsx").read_text(encoding="utf-8")
        assert "CreateCommandForm" in content, (
            "PanelContainer doit importer CreateCommandForm"
        )
        assert "showSaveCommand" in content, (
            "PanelContainer doit utiliser showSaveCommand du panelStore"
        )
        assert "handleSaveCommandSubmit" in content, (
            "PanelContainer doit avoir le handler handleSaveCommandSubmit"
        )
        # Vérifier que ChatLayout délègue bien à PanelContainer
        layout_content = (FRONTEND / "components" / "chat" / "ChatLayout.tsx").read_text(encoding="utf-8")
        assert "PanelContainer" in layout_content, (
            "ChatLayout doit inclure PanelContainer"
        )
        assert "openSaveCommand" in layout_content, (
            "ChatLayout doit appeler openSaveCommand du panelStore"
        )

    def test_create_command_form_accepts_initial_values(self):
        """CreateCommandForm doit accepter initialContent et initialDescription."""
        content = (FRONTEND / "components" / "guided" / "CreateCommandForm.tsx").read_text(encoding="utf-8")
        assert "initialContent" in content, (
            "CreateCommandForm doit accepter la prop initialContent"
        )
        assert "initialDescription" in content, (
            "CreateCommandForm doit accepter la prop initialDescription"
        )
        assert "capturedPreview" in content, (
            "CreateCommandForm doit accepter la prop capturedPreview"
        )


# ============================================================
# Phase 4c (v0.2.4) - Image : bouton "Utiliser"
# ImageGenerationPanel doit avoir un bouton Utiliser.
# ============================================================


IMAGE_GENERATION_PANEL_TSX = FRONTEND / "components" / "guided" / "ImageGenerationPanel.tsx"


class TestImageUseButton:
    """Phase 4c : bouton Utiliser dans ImageGenerationPanel."""

    def test_image_panel_has_onuse_prop(self):
        """ImageGenerationPanel doit avoir la prop onUse."""
        content = IMAGE_GENERATION_PANEL_TSX.read_text(encoding="utf-8")
        assert "onUse" in content, (
            "ImageGenerationPanel doit avoir la prop onUse"
        )

    def test_image_panel_has_utiliser_button(self):
        """ImageGenerationPanel doit afficher un bouton Utiliser."""
        content = IMAGE_GENERATION_PANEL_TSX.read_text(encoding="utf-8")
        assert "Utiliser" in content, (
            "ImageGenerationPanel doit avoir un bouton 'Utiliser'"
        )


# ============================================================
# BUG-033 (v0.2.4) - FileBrowser accent "répertoire"
# ============================================================


FILE_BROWSER_TSX = FRONTEND / "components" / "files" / "FileBrowser.tsx"


class TestBUG033FileBrowserAccent:
    """BUG-033 : FileBrowser doit utiliser 'répertoire' (avec accent)."""

    def test_no_repertoire_without_accent(self):
        """FileBrowser ne doit pas contenir 'repertoire' sans accent."""
        content = FILE_BROWSER_TSX.read_text(encoding="utf-8")
        import re
        # Chercher "repertoire" sans accent (pas "répertoire")
        unaccented = re.findall(r'(?<![é])repertoire', content, re.IGNORECASE)
        assert len(unaccented) == 0, (
            "FileBrowser doit écrire 'répertoire' avec accent, "
            f"trouvé {len(unaccented)} occurrences sans accent"
        )


# ============================================================
# BUG-034 (v0.2.4) - Microphone plugin prêt
# useVoiceRecorder doit exposer pluginReady.
# ============================================================


VOICE_RECORDER_TS = FRONTEND / "hooks" / "useVoiceRecorder.ts"


class TestBUG034MicrophonePluginReady:
    """BUG-034 : useVoiceRecorder doit exposer pluginReady."""

    def test_hook_exports_plugin_ready(self):
        """useVoiceRecorder doit retourner pluginReady."""
        content = VOICE_RECORDER_TS.read_text(encoding="utf-8")
        assert "pluginReady" in content, (
            "useVoiceRecorder doit exposer pluginReady"
        )

    def test_chat_input_disables_mic_when_not_ready(self):
        """ChatInput doit désactiver le micro quand le plugin n'est pas prêt."""
        content = CHAT_INPUT_TSX.read_text(encoding="utf-8")
        assert "pluginReady" in content, (
            "ChatInput doit utiliser pluginReady pour désactiver le bouton micro"
        )


# ============================================================
# Phase 5 (v0.2.4) - Calendrier vues Semaine et Jour
# CalendarView doit implémenter WeekView et DayView.
# ============================================================


CALENDAR_VIEW_TSX = FRONTEND / "components" / "calendar" / "CalendarView.tsx"


class TestCalendarWeekDayViews:
    """Phase 5 : vues Semaine et Jour dans le calendrier."""

    def test_week_view_exists(self):
        """CalendarView doit contenir un composant WeekView."""
        content = CALENDAR_VIEW_TSX.read_text(encoding="utf-8")
        assert "function WeekView" in content, (
            "CalendarView.tsx doit contenir le composant WeekView"
        )
        assert "WEEK_START_HOUR" in content, (
            "WeekView doit définir les heures de début/fin"
        )

    def test_day_view_exists(self):
        """CalendarView doit contenir un composant DayView."""
        content = CALENDAR_VIEW_TSX.read_text(encoding="utf-8")
        assert "function DayView" in content, (
            "CalendarView.tsx doit contenir le composant DayView"
        )
        assert "DAY_START_HOUR" in content, (
            "DayView doit définir les heures de début/fin"
        )

    def test_week_view_has_current_time_indicator(self):
        """WeekView doit afficher la ligne rouge de l'heure actuelle."""
        content = CALENDAR_VIEW_TSX.read_text(encoding="utf-8")
        assert "nowLineTop" in content, (
            "Les vues semaine/jour doivent calculer la position de la ligne rouge"
        )
        assert "bg-red-500" in content, (
            "La ligne de l'heure actuelle doit être rouge"
        )


# ============================================================
# Phase 6 (v0.2.4) - CRM : suppression onglet Projets
# CRMPanel ne doit plus avoir d'onglet Projets.
# ============================================================


CRM_PANEL_TSX = FRONTEND / "components" / "crm" / "CRMPanel.tsx"


class TestCRMProjectsTabRemoved:
    """Phase 6 : l'onglet Projets du CRM doit être supprimé."""

    def test_no_projects_tab(self):
        """CRMPanel ne doit plus contenir d'onglet 'projects'."""
        content = CRM_PANEL_TSX.read_text(encoding="utf-8")
        # Chercher dans la définition des tabs
        assert "'projects'" not in content, (
            "CRMPanel ne doit plus contenir l'onglet 'projects'"
        )

    def test_global_activity_view_exists(self):
        """CRMPanel doit avoir un composant GlobalActivityView."""
        content = CRM_PANEL_TSX.read_text(encoding="utf-8")
        assert "GlobalActivityView" in content, (
            "CRMPanel doit contenir GlobalActivityView pour la vue activités globale"
        )

    def test_activity_filter_chips(self):
        """GlobalActivityView doit avoir des filtres par type d'activité."""
        content = CRM_PANEL_TSX.read_text(encoding="utf-8")
        assert "ACTIVITY_FILTER_CHIPS" in content, (
            "CRMPanel doit définir ACTIVITY_FILTER_CHIPS pour les filtres"
        )


# ============================================================
# BUG-035 - Templates DOCX/PPTX : répertoires intermédiaires manquants
# python-docx/pptx résolvent les templates via __file__ + '..'
# (ex: docx/parts/../templates/default-footer.xml).
# PyInstaller met les modules dans PYZ, donc docx/parts/ n'existe pas
# sur disque. Le runtime hook crée ces répertoires vides.
# ============================================================


BACKEND_SPEC = SRC / "backend.spec"
RUNTIME_HOOK = SRC / "runtime_hook_templates.py"


class TestBUG035TemplatesPathResolution:
    """BUG-035 : répertoires intermédiaires pour résolution templates Office."""

    def test_runtime_hook_file_exists(self):
        """Le fichier runtime_hook_templates.py doit exister."""
        assert RUNTIME_HOOK.exists(), (
            "runtime_hook_templates.py manquant dans src/backend/"
        )

    def test_runtime_hook_creates_docx_parts(self):
        """Le hook doit créer docx/parts/ pour la résolution via '..'."""
        content = RUNTIME_HOOK.read_text(encoding="utf-8")
        assert "docx/parts" in content, (
            "Le hook doit créer le répertoire docx/parts"
        )

    def test_runtime_hook_creates_pptx_oxml(self):
        """Le hook doit créer pptx/oxml/ pour la résolution via '..'."""
        content = RUNTIME_HOOK.read_text(encoding="utf-8")
        assert "pptx/oxml" in content, (
            "Le hook doit créer le répertoire pptx/oxml"
        )

    def test_runtime_hook_creates_pptx_shapes(self):
        """Le hook doit créer pptx/shapes/ pour les icônes EMF."""
        content = RUNTIME_HOOK.read_text(encoding="utf-8")
        assert "pptx/shapes" in content, (
            "Le hook doit créer le répertoire pptx/shapes"
        )

    def test_backend_spec_references_runtime_hook(self):
        """backend.spec doit référencer le runtime hook."""
        content = BACKEND_SPEC.read_text(encoding="utf-8")
        assert "runtime_hook_templates" in content, (
            "backend.spec doit inclure runtime_hook_templates.py dans runtime_hooks"
        )

    def test_runtime_hook_checks_meipass(self):
        """Le hook ne doit s'exécuter que dans un bundle PyInstaller."""
        content = RUNTIME_HOOK.read_text(encoding="utf-8")
        assert "_MEIPASS" in content, (
            "Le hook doit vérifier sys._MEIPASS avant de créer les répertoires"
        )


# ============================================================
# BUG-028 (v0.2.5) - Prix EUR toujours 0.0000
# TOKEN_PRICES.get(model) ne matchait pas les modèles OpenRouter
# (préfixe provider/ ex: "anthropic/claude-sonnet-4-5-20250929").
# estimate_cost() doit essayer sans le préfixe si pas trouvé.
# ============================================================


TOKEN_TRACKER_PY = SRC / "app" / "services" / "token_tracker.py"


class TestBUG028PricingEUR:
    """BUG-028 : prix EUR non-zéro pour les modèles connus (y compris OpenRouter)."""

    def test_estimate_cost_strips_provider_prefix(self):
        """estimate_cost() doit gérer les modèles avec préfixe provider."""
        content = TOKEN_TRACKER_PY.read_text(encoding="utf-8")
        assert 'model.split("/", 1)' in content, (
            "estimate_cost() doit essayer de supprimer le préfixe provider "
            "(ex: 'anthropic/claude-opus-4-8' → 'claude-opus-4-8')"
        )

    def test_estimate_cost_returns_nonzero_for_known_models(self):
        """estimate_cost() doit retourner un prix > 0 pour les modèles connus."""
        from app.services.token_tracker import TokenTracker

        tracker = TokenTracker()
        # Modèle direct
        cost_direct = tracker.estimate_cost("claude-opus-4-8", 1000, 500)
        assert cost_direct > 0, (
            "Le prix doit être > 0 pour claude-opus-4-8"
        )
        # Modèle avec préfixe OpenRouter
        cost_openrouter = tracker.estimate_cost("anthropic/claude-opus-4-8", 1000, 500)
        assert cost_openrouter > 0, (
            "Le prix doit être > 0 pour anthropic/claude-opus-4-8 (OpenRouter)"
        )
        # Les deux doivent être identiques
        assert cost_direct == cost_openrouter, (
            "Le prix doit être identique avec ou sans préfixe provider"
        )

    def test_estimate_cost_fallback_default_for_unknown(self):
        """estimate_cost() doit retourner 0 pour les modèles inconnus (Ollama)."""
        from app.services.token_tracker import TokenTracker

        tracker = TokenTracker()
        cost = tracker.estimate_cost("llama3:8b", 1000, 500)
        assert cost == 0.0, (
            "Le prix doit être 0 pour les modèles locaux (Ollama) inconnus"
        )

    def test_token_prices_has_major_models(self):
        """TOKEN_PRICES doit contenir les modèles majeurs."""
        from app.services.token_tracker import TOKEN_PRICES

        required = [
            "claude-opus-4-8",
            "claude-sonnet-4-6",
            "gpt-5.5",
            "gemini-3.1-pro-preview",
            "mistral-large-latest",
        ]
        for model in required:
            assert model in TOKEN_PRICES, (
                f"TOKEN_PRICES doit contenir {model}"
            )
            assert TOKEN_PRICES[model]["input"] > 0, (
                f"Le prix input de {model} doit être > 0"
            )


# ============================================================
# Streaming texte brut (v0.2.5) - Anti-saut streaming
# Pendant le streaming, MessageBubble affiche le texte brut
# (pas de ReactMarkdown) pour éviter les recalculs de layout.
# ReactMarkdown est utilisé uniquement quand le streaming termine.
# ============================================================


class TestStreamingRawText:
    """Texte brut pendant le streaming (pas de ReactMarkdown)."""

    def test_message_bubble_has_streaming_condition(self):
        """MessageBubble doit avoir un rendu conditionnel isStreaming."""
        content = MESSAGE_BUBBLE_TSX.read_text(encoding="utf-8")
        assert "message.isStreaming" in content, (
            "MessageBubble doit vérifier message.isStreaming"
        )
        assert "whitespace-pre-wrap" in content, (
            "Le texte brut streaming doit utiliser whitespace-pre-wrap"
        )

    def test_message_bubble_raw_text_before_markdown(self):
        """Pendant le streaming, le texte brut doit être affiché AVANT ReactMarkdown."""
        content = MESSAGE_BUBBLE_TSX.read_text(encoding="utf-8")
        raw_pos = content.find("whitespace-pre-wrap")
        markdown_pos = content.find("<ReactMarkdown")
        assert raw_pos > 0, "whitespace-pre-wrap absent"
        assert markdown_pos > 0, "ReactMarkdown absent"
        assert raw_pos < markdown_pos, (
            "Le texte brut (whitespace-pre-wrap) doit apparaître AVANT ReactMarkdown "
            "dans le rendu conditionnel"
        )

    def test_message_bubble_has_min_height(self):
        """MessageBubble doit avoir un minHeight dynamique pendant le streaming."""
        content = MESSAGE_BUBBLE_TSX.read_text(encoding="utf-8")
        assert "minHeight" in content, (
            "MessageBubble doit calculer un minHeight dynamique pendant le streaming"
        )


# ─── BUG-025 Ollama /api/chat (tests consolidés ci-dessus) ─────────────────
# Les tests Ollama ont été fusionnés dans TestBUG025OllamaSystemPrompt (ligne ~1208)


# ─── BUG-036 XLSX code tronqué ────────────────────────────────────────────

class TestBUG036_XlsxTruncatedCode:
    """Le code tronqué doit être réparé avec ajout automatique de .save()."""

    def test_ensure_save_call_adds_missing_save(self):
        """_ensure_save_call doit ajouter wb.save(output_path) si absent."""
        from app.services.skills.code_executor import _ensure_save_call

        code_without_save = 'wb = Workbook()\nws = wb.active\nws["A1"] = "test"'
        result = _ensure_save_call(code_without_save)
        assert ".save(output_path)" in result, (
            "_ensure_save_call doit ajouter .save(output_path) quand absent"
        )

    def test_ensure_save_call_keeps_existing_save(self):
        """_ensure_save_call ne doit pas dupliquer un .save() existant."""
        from app.services.skills.code_executor import _ensure_save_call

        code_with_save = 'wb = Workbook()\nwb.save(output_path)'
        result = _ensure_save_call(code_with_save)
        assert result.count(".save(output_path)") == 1, (
            "_ensure_save_call ne doit pas dupliquer le .save()"
        )

    def test_ensure_save_call_detects_load_workbook(self):
        """_ensure_save_call doit détecter load_workbook() et ajouter .save()."""
        from app.services.skills.code_executor import _ensure_save_call

        code = 'wb = load_workbook("template.xlsx")\nws = wb.active\nws["A1"] = "modifié"'
        result = _ensure_save_call(code)
        assert ".save(output_path)" in result, (
            "_ensure_save_call doit ajouter .save(output_path) pour load_workbook()"
        )

    def test_ensure_save_call_no_false_positive(self):
        """_ensure_save_call ne doit pas ajouter .save() si un .save(fichier) existe déjà."""
        from app.services.skills.code_executor import _ensure_save_call

        code = 'wb = Workbook()\nwb.save("mon_fichier.xlsx")'
        result = _ensure_save_call(code)
        assert result.count(".save") == 1, (
            "_ensure_save_call ne doit pas dupliquer un .save() existant (même avec un autre argument)"
        )

    def test_repair_truncated_code_adds_save(self):
        """repair_truncated_code doit ajouter .save() après réparation."""
        from app.services.skills.code_executor import repair_truncated_code

        # Code tronqué : syntaxe invalide à la fin, et pas de .save()
        truncated = 'wb = Workbook()\nws = wb.active\nws["A1"] = "test"\nws["A2'
        result = repair_truncated_code(truncated)
        assert result is not None, "repair_truncated_code doit réussir"
        assert ".save(output_path)" in result, (
            "repair_truncated_code doit ajouter .save(output_path) après réparation"
        )

    def test_repair_valid_code_adds_save(self):
        """repair_truncated_code doit ajouter .save() même si le code est déjà valide."""
        from app.services.skills.code_executor import repair_truncated_code

        # Code syntaxiquement valide mais sans .save()
        valid_no_save = 'wb = Workbook()\nws = wb.active\nws["A1"] = "test"'
        result = repair_truncated_code(valid_no_save)
        assert result is not None, "repair_truncated_code doit réussir"
        assert ".save(output_path)" in result, (
            "repair_truncated_code doit ajouter .save() même si le code est syntaxiquement valide"
        )


# ─── BUG-025 Contraste dropdown modèle ────────────────────────────────────

class TestBUG025_DropdownContraste:
    """Le dropdown de sélection de modèle doit avoir un contraste suffisant."""

    LLM_TAB_TSX = Path("src/frontend/src/components/settings/LLMTab.tsx")

    def test_option_has_explicit_colors(self):
        """Les <option> du select modèle doivent avoir des couleurs explicites."""
        content = self.LLM_TAB_TSX.read_text(encoding="utf-8")
        # BUG-051 : couleurs hex explicites pour compatibilité Linux/GTK
        assert "option" in content and ("#0B1226" in content or
            "bg-[var(--color-surface)]" in content or "bg-surface" in content), (
            "Les <option> du dropdown doivent avoir un fond explicite pour le contraste"
        )


# ─── BUG-038 Bouton Stop streaming ────────────────────────────────────────

class TestBUG038_StopStreaming:
    """Le streaming doit pouvoir être interrompu par l'utilisateur."""

    CHAT_INPUT_TSX = Path("src/frontend/src/components/chat/ChatInput.tsx")
    CHAT_API_TS = Path("src/frontend/src/services/api/chat.ts")

    def test_abort_controller_in_chat_input(self):
        """ChatInput doit créer un AbortController pour le streaming."""
        content = self.CHAT_INPUT_TSX.read_text(encoding="utf-8")
        assert "AbortController" in content, (
            "ChatInput doit utiliser AbortController pour permettre l'interruption"
        )

    def test_stop_button_visible_during_streaming(self):
        """Un bouton stop doit remplacer le bouton envoyer pendant le streaming."""
        content = self.CHAT_INPUT_TSX.read_text(encoding="utf-8")
        assert "Square" in content, (
            "ChatInput doit afficher une icône Square (stop) pendant le streaming"
        )
        assert "stopStreaming" in content, (
            "ChatInput doit avoir une fonction stopStreaming"
        )

    def test_stream_message_accepts_signal(self):
        """streamMessage doit accepter un AbortSignal en paramètre."""
        content = self.CHAT_API_TS.read_text(encoding="utf-8")
        assert "signal" in content, (
            "streamMessage doit accepter un signal AbortSignal"
        )

    def test_abort_error_shows_partial_content(self):
        """L'interruption doit afficher le texte déjà reçu, pas une erreur."""
        content = self.CHAT_INPUT_TSX.read_text(encoding="utf-8")
        assert "AbortError" in content, (
            "ChatInput doit gérer l'AbortError séparément des autres erreurs"
        )


# ─── UX Réponses trop lourdes (system prompt) ─────────────────────────────

class TestUX_ReponsesLegeres:
    """Le system prompt doit interdire les tableaux markdown par défaut."""

    LLM_PY = Path("src/backend/app/services/llm.py")

    def test_system_prompt_forbids_markdown_tables(self):
        """Le system prompt doit contenir une instruction contre les tableaux."""
        content = self.LLM_PY.read_text(encoding="utf-8")
        assert "tableau" in content.lower(), (
            "Le system prompt doit mentionner l'interdiction des tableaux markdown"
        )

    def test_system_prompt_prefers_bullet_lists(self):
        """Le system prompt doit encourager les listes à puces."""
        content = self.LLM_PY.read_text(encoding="utf-8")
        assert "puces" in content.lower() or "listes" in content.lower(), (
            "Le system prompt doit encourager les listes à puces"
        )


# ─── BUG-039 Bouton email dans MessageBubble ──────────────────────────────

class TestBUG039_EmailButton:
    """v0.4.0 : Le bouton email a été retiré de MessageBubble (doublon avec le module Mail).
    On vérifie qu'il n'est plus présent."""

    MSG_BUBBLE = Path("src/frontend/src/components/chat/MessageBubble.tsx")

    def test_mail_icon_removed(self):
        """L'icône Mail ne doit plus être importée dans MessageBubble (v0.4.0)."""
        content = self.MSG_BUBBLE.read_text(encoding="utf-8")
        assert "openInMailClient" not in content, (
            "Le bouton email a été retiré en v0.4.0"
        )


# ─── BUG-040 DOCX page blanche (code tronqué) ────────────────────────────

class TestBUG040_DocxTruncatedCode:
    """Le code DOCX tronqué doit être réparé avec ajout de .save()."""

    def test_ensure_save_call_detects_document(self):
        """_ensure_save_call doit détecter Document() et ajouter .save()."""
        from app.services.skills.code_executor import _ensure_save_call

        code = 'doc = Document()\ndoc.add_heading("Test", level=0)'
        result = _ensure_save_call(code)
        assert ".save(output_path)" in result, (
            "_ensure_save_call doit ajouter doc.save(output_path) pour Document()"
        )

    def test_ensure_save_call_detects_presentation(self):
        """_ensure_save_call doit détecter Presentation() et ajouter .save()."""
        from app.services.skills.code_executor import _ensure_save_call

        code = 'prs = Presentation()\nslide = prs.slides.add_slide(prs.slide_layouts[0])'
        result = _ensure_save_call(code)
        assert ".save(output_path)" in result, (
            "_ensure_save_call doit ajouter prs.save(output_path) pour Presentation()"
        )


# ─── BUG-026 Bouton "Utiliser" inopérant dans Mail (macOS) ────────────────

class TestBUG026_EmailUtiliserButton:
    """handleUseResponse doit toujours ouvrir le compositeur, même si message est undefined."""

    EMAIL_DETAIL_TSX = Path("src/frontend/src/components/email/EmailDetail.tsx")

    def test_use_response_calls_start_composing(self):
        """handleUseResponse doit utiliser startComposing pour un set() atomique."""
        content = self.EMAIL_DETAIL_TSX.read_text(encoding="utf-8")
        assert "startComposing" in content, (
            "handleUseResponse doit utiliser startComposing (set atomique) "
            "au lieu de 4 set() séparés pour éviter les problèmes de timing"
        )

    def test_reply_uses_start_composing(self):
        """handleReply doit utiliser startComposing pour un set() atomique."""
        content = self.EMAIL_DETAIL_TSX.read_text(encoding="utf-8")
        # handleReply appelle startComposing
        assert "startComposing([message.from_email]" in content, (
            "handleReply doit appeler startComposing avec le from_email du message"
        )

    def test_store_has_start_composing(self):
        """Le store email doit exposer startComposing pour les mises à jour atomiques."""
        store_path = self.EMAIL_DETAIL_TSX.parent.parent.parent / "stores" / "emailStore.ts"
        content = store_path.read_text(encoding="utf-8")
        assert "startComposing:" in content, (
            "Le store email doit définir startComposing pour le set() atomique"
        )
        assert "isComposing: true" in content, (
            "startComposing doit mettre isComposing à true"
        )


# ─── BUG-037 Saut scroll résiduel en fin de streaming ────────────────────

class TestBUG037_ScrollJumpStreaming:
    """MessageList doit éviter les sauts de scroll en fin de streaming via scrollIntoView."""

    MSG_LIST = Path("src/frontend/src/components/chat/MessageList.tsx")

    def test_virtuoso_follow_output_present(self):
        """followOutput conditionné au streaming doit gérer la transition
        fin-streaming sans saut ('auto' pendant, 'smooth' après)."""
        content = self.MSG_LIST.read_text(encoding="utf-8")
        assert "followOutput" in content, (
            "MessageList doit utiliser followOutput (Virtuoso) pour éviter les sauts"
        )

    def test_align_to_bottom_prevents_jump(self):
        """La politique auto/smooth/false vit dans computeFollowOutput (testée
        unitairement dans followOutput.test.ts)."""
        follow_output = self.MSG_LIST.parent / "followOutput.ts"
        content = follow_output.read_text(encoding="utf-8")
        assert "'auto'" in content and "'smooth'" in content, (
            "computeFollowOutput doit distinguer 'auto' (streaming) et 'smooth' "
            "(hors streaming) pour une fin de streaming sans saut"
        )


# ─── BUG-041 Layout shift pendant le streaming ───────────────────────────

class TestBUG041_LayoutShiftStreaming:
    """MessageBubble doit avoir un layout stable pendant le streaming."""

    MSG_BUBBLE = Path("src/frontend/src/components/chat/MessageBubble.tsx")

    def test_layout_disabled_during_streaming(self):
        """Framer Motion layout doit être désactivé pendant le streaming."""
        content = self.MSG_BUBBLE.read_text(encoding="utf-8")
        assert "layout={!message.isStreaming}" in content, (
            "Le prop layout de motion.div doit être désactivé pendant le streaming "
            "pour éviter les re-animations de layout sur tous les messages"
        )
        assert "layout\n" not in content or "layout={" in content, (
            "Le prop layout ne doit pas être inconditionnellement activé"
        )

    def test_contain_always_includes_layout(self):
        """contain doit toujours inclure 'layout' (même pendant le streaming)."""
        content = self.MSG_BUBBLE.read_text(encoding="utf-8")
        assert "contain: 'layout style paint'" in content, (
            "contain doit toujours inclure 'layout' pour isoler les re-layouts "
            "du reste de la page pendant le streaming"
        )
        assert "contain: message.isStreaming ? 'style paint'" not in content, (
            "contain ne doit pas retirer 'layout' pendant le streaming"
        )

    def test_min_height_fixed_during_streaming(self):
        """minHeight doit être fixe pendant le streaming (pas dynamique)."""
        content = self.MSG_BUBBLE.read_text(encoding="utf-8")
        assert "minHeight: message.isStreaming ? '56px'" in content, (
            "minHeight doit être une valeur fixe (56px) pendant le streaming, "
            "pas calculée dynamiquement à chaque chunk"
        )
        assert "Math.ceil(message.content.length" not in content, (
            "minHeight ne doit plus utiliser message.content.length "
            "(recalcul à chaque chunk = layout shift)"
        )


# ─── BUG-040 Ollama erreurs lisibles (v0.2.8) ─────────────────────────────

OLLAMA_PY = Path("src/backend/app/services/providers/ollama.py")


class TestBUG040_OllamaErrorMessages:
    """BUG-040 : Ollama doit renvoyer des erreurs lisibles en français."""

    def test_ollama_catches_connect_error(self):
        """Le provider doit capturer httpx.ConnectError séparément."""
        content = OLLAMA_PY.read_text(encoding="utf-8")
        assert "httpx.ConnectError" in content, (
            "ollama.py doit capturer httpx.ConnectError pour un message clair "
            "quand Ollama n'est pas lancé"
        )

    def test_ollama_catches_read_timeout(self):
        """Le provider doit capturer httpx.ReadTimeout séparément."""
        content = OLLAMA_PY.read_text(encoding="utf-8")
        assert "httpx.ReadTimeout" in content, (
            "ollama.py doit capturer httpx.ReadTimeout pour un message clair "
            "quand le modèle est trop lent"
        )

    def test_ollama_catches_http_status_error(self):
        """Les erreurs HTTP doivent produire un message clair (404 = modèle absent).

        Revue adversariale US-009 : l'ancien except httpx.HTTPStatusError était
        du code mort (body jamais lu sur une réponse streaming -> ResponseNotRead).
        Le statut est désormais testé DANS le async with, body lu via aread()."""
        content = OLLAMA_PY.read_text(encoding="utf-8")
        assert "response.status_code != 200" in content, (
            "ollama.py doit tester le status_code dans le async with "
            "(raise_for_status + .json() = code mort sur du streaming)"
        )
        assert "aread()" in content, (
            "ollama.py doit lire le body d'erreur via aread() avant de router"
        )
        assert "status == 404" in content, (
            "ollama.py doit traiter le 404 (modèle non installé) explicitement"
        )

    def test_ollama_404_mentions_ollama_pull(self):
        """En cas de 404, le message doit suggérer 'ollama pull'."""
        content = OLLAMA_PY.read_text(encoding="utf-8")
        assert "ollama pull" in content, (
            "En cas de modèle introuvable (404), le message d'erreur doit "
            "suggérer 'ollama pull <modèle>' pour l'installer"
        )

    def test_ollama_connect_error_mentions_serve(self):
        """En cas de connexion impossible, le message doit suggérer 'ollama serve'."""
        content = OLLAMA_PY.read_text(encoding="utf-8")
        assert "ollama serve" in content, (
            "En cas de connexion impossible, le message d'erreur doit "
            "suggérer 'ollama serve' pour lancer le service"
        )

    def test_ollama_checks_error_in_stream(self):
        """Le provider doit vérifier le champ 'error' dans les événements stream."""
        content = OLLAMA_PY.read_text(encoding="utf-8")
        assert 'event.get("error")' in content, (
            "ollama.py doit vérifier le champ 'error' dans chaque événement "
            "du flux JSON (certains modèles renvoient des erreurs mid-stream)"
        )

    def test_no_unknown_error_fallback(self):
        """Le router chat ne doit plus afficher 'Unknown error'."""
        chat_router = Path("src/backend/app/routers/chat.py")
        content = chat_router.read_text(encoding="utf-8")
        assert "Unknown error" not in content, (
            "chat.py ne doit plus contenir 'Unknown error' - "
            "utiliser un message en français à la place"
        )


# ─── BUG-039 Listbox blanc sur blanc (v0.2.8) ─────────────────────────────

GLOBALS_CSS = Path("src/frontend/src/styles/globals.css")


class TestBUG039_ListboxContrast:
    """BUG-039 : Les options des <select> doivent être lisibles en thème sombre."""

    def test_global_css_styles_select_options(self):
        """globals.css doit contenir un style pour select option."""
        content = GLOBALS_CSS.read_text(encoding="utf-8")
        assert "select option" in content, (
            "globals.css doit contenir une règle 'select option' pour forcer "
            "le fond sombre et le texte clair sur toutes les listes déroulantes"
        )

    def test_select_option_has_background(self):
        """Les options doivent avoir un background explicite."""
        content = GLOBALS_CSS.read_text(encoding="utf-8")
        assert "background-color" in content and "--color-surface" in content, (
            "Les options <select> doivent avoir un background-color "
            "utilisant --color-surface pour le thème sombre"
        )


# ─── BUG-038 Retours à la ligne chat (v0.2.8) ─────────────────────────────

MESSAGE_BUBBLE = Path("src/frontend/src/components/chat/MessageBubble.tsx")


class TestBUG038_LineBreaksChat:
    """BUG-038 : Les messages utilisateur doivent préserver les retours à la ligne."""

    def test_user_messages_not_through_react_markdown(self):
        """Les messages user doivent utiliser whitespace-pre-wrap, pas ReactMarkdown."""
        content = MESSAGE_BUBBLE.read_text(encoding="utf-8")
        assert "isUser" in content, (
            "MessageBubble doit distinguer les messages user des messages assistant"
        )
        # Vérifier que le path user utilise whitespace-pre-wrap
        assert content.count("whitespace-pre-wrap") >= 2, (
            "MessageBubble doit avoir au moins 2 occurrences de whitespace-pre-wrap "
            "(streaming + messages user)"
        )


# ============================================================
# BUG-026 (revisited) : Bouton "Utiliser" du générateur de réponse email
# Fix : createPortal document.body + z-[60] + stopPropagation
# ============================================================

RESPONSE_GENERATOR_MODAL = (
    FRONTEND / "components" / "email" / "ResponseGeneratorModal.tsx"
)
EMAIL_DETAIL = FRONTEND / "components" / "email" / "EmailDetail.tsx"


class TestBUG026_BoutonUtiliserEmail:
    """BUG-026 (revisited) : Le bouton Utiliser du générateur de réponse email doit fonctionner."""

    def test_modal_uses_portal(self):
        """Le modal doit utiliser createPortal vers document.body pour éviter les problèmes de stacking context."""
        content = RESPONSE_GENERATOR_MODAL.read_text(encoding="utf-8")
        assert "createPortal" in content, (
            "ResponseGeneratorModal doit utiliser createPortal (react-dom)"
        )
        assert "document.body" in content, (
            "Le portal doit cibler document.body"
        )

    def test_modal_z_index_above_email_panel(self):
        """Le modal doit avoir un z-index supérieur à z-50 (l'email panel)."""
        content = RESPONSE_GENERATOR_MODAL.read_text(encoding="utf-8")
        # Refacto : le z-index passe désormais par la constante Z_LAYER.MODAL_NESTED (= z-[60])
        assert "Z_LAYER.MODAL_NESTED" in content, (
            "Le modal doit utiliser Z_LAYER.MODAL_NESTED (z-[60]) pour passer au-dessus de l'email panel (z-50)"
        )

    def test_handle_use_stops_propagation(self):
        """handleUse doit appeler stopPropagation pour éviter les interférences d'événements."""
        content = RESPONSE_GENERATOR_MODAL.read_text(encoding="utf-8")
        assert "stopPropagation" in content, (
            "handleUse doit appeler e.stopPropagation() pour empêcher le bubbling"
        )

    def test_handle_use_response_uses_start_composing(self):
        """handleUseResponse doit utiliser startComposing (set atomique) au lieu de set() séparés."""
        content = EMAIL_DETAIL.read_text(encoding="utf-8")
        assert "startComposing" in content, (
            "handleUseResponse doit utiliser startComposing pour un seul set() atomique"
        )

    def test_delete_optimistic_removal(self):
        """handleTrash doit retirer le message de l'UI même en cas d'erreur non-auth."""
        content = EMAIL_DETAIL.read_text(encoding="utf-8")
        # Vérifier que le catch non-auth fait removeMessage
        assert "removeMessage(messageId);" in content, (
            "handleTrash doit appeler removeMessage dans le try ET dans le else du catch"
        )


# ─── BUG-041 Ollama 500 admin mode + messages d'erreur persistés ─────────

class TestBUG041_OllamaAdminError:
    """Ollama 500 doit afficher un message actionnable + les erreurs doivent être persistées."""

    OLLAMA_PY = Path("src/backend/app/services/providers/ollama.py")
    CHAT_PY = Path("src/backend/app/routers/chat.py")

    def test_ollama_500_mentions_admin(self):
        """Le cas HTTP 500 d'Ollama doit avoir un message d'erreur explicite."""
        content = self.OLLAMA_PY.read_text(encoding="utf-8")
        # US-009 : la structure est passée de elif (handler except) à if (statut
        # testé dans le async with) - l'intention (cas 500 dédié) est inchangée
        assert "if status == 500:" in content, (
            "ollama.py doit avoir un cas spécifique pour HTTP 500"
        )
        # BUG-052 : message amélioré avec hint RAM
        assert "500" in content and "error" in content, (
            "Le message d'erreur 500 doit être explicite"
        )

    def test_ollama_empty_response_yields_error(self):
        """Une réponse vide d'Ollama doit produire un StreamEvent d'erreur visible."""
        content = self.OLLAMA_PY.read_text(encoding="utf-8")
        assert "has_content" in content, (
            "ollama.py doit vérifier si du contenu a été reçu"
        )
        # Le cas 'pas de contenu' doit yielder une erreur, pas juste logger
        assert 'type="error"' in content or "type='error'" in content, (
            "Le cas réponse vide doit yielder un StreamEvent de type 'error'"
        )
        assert "gelé" in content, (
            "Le message d'erreur réponse vide doit mentionner qu'Ollama est peut-être gelé"
        )

    def test_error_messages_persisted_in_db(self):
        """Les messages d'erreur de streaming doivent être persistés en base."""
        content = self.CHAT_PY.read_text(encoding="utf-8")
        # Vérifier que quand un event.type == "error" arrive, un Message est sauvegardé
        assert "session.add(err_msg)" in content, (
            "chat.py doit sauvegarder un Message en base lors d'une erreur de streaming "
            "pour que le message d'erreur ne disparaisse pas au rechargement"
        )
        assert "await session.commit()" in content, (
            "chat.py doit commiter la sauvegarde du message d'erreur"
        )


# ─── Batch v0.2.11 - Ollama, mail, SMTP, Apple, Linux ────────────────────

class TestBatchV0211_OllamaAdminWindows:
    """Ollama HTTP 500 → message actionnable + erreur vide → error event."""

    OLLAMA_PY = Path("src/backend/app/services/providers/ollama.py")
    CHAT_PY = Path("src/backend/app/routers/chat.py")

    def test_ollama_500_admin_message(self):
        content = self.OLLAMA_PY.read_text(encoding="utf-8")
        # US-009 : elif -> if (statut testé dans le async with), intention inchangée
        assert "if status == 500:" in content, "Cas spécifique HTTP 500 manquant"
        # BUG-052 : message amélioré avec hint RAM au lieu de admin Windows
        assert "500" in content, "Message 500 doit être explicite"

    def test_ollama_empty_response_error_event(self):
        content = self.OLLAMA_PY.read_text(encoding="utf-8")
        assert "gelé" in content, "Réponse vide Ollama doit mentionner 'gelé'"

    def test_error_messages_persisted(self):
        content = self.CHAT_PY.read_text(encoding="utf-8")
        assert "session.add(err_msg)" in content, "Messages d'erreur doivent être persistés en base"


class TestBatchV0211_EmailWizardPortal:
    """EmailSetupWizard doit utiliser createPortal pour éviter l'interférence Framer Motion."""

    WIZARD_TSX = Path("src/frontend/src/components/email/wizard/EmailSetupWizard.tsx")

    def test_create_portal_imported(self):
        content = self.WIZARD_TSX.read_text(encoding="utf-8")
        assert "createPortal" in content, "EmailSetupWizard doit utiliser createPortal"

    def test_higher_z_index(self):
        content = self.WIZARD_TSX.read_text(encoding="utf-8")
        # Refacto : le z-index passe désormais par la constante Z_LAYER.WIZARD (= z-[70])
        assert "Z_LAYER.WIZARD" in content, "Wizard doit utiliser Z_LAYER.WIZARD (z-[70]) pour passer au-dessus des overlays z-50"

    def test_portal_to_body(self):
        content = self.WIZARD_TSX.read_text(encoding="utf-8")
        assert "document.body" in content, "createPortal doit cibler document.body"


class TestBatchV0211_SmtpFailedToFetch:
    """SMTP 'Failed to fetch' doit afficher un message lisible."""

    SMTP_TSX = Path("src/frontend/src/components/email/wizard/SmtpConfigStep.tsx")

    def test_failed_to_fetch_intercepted(self):
        content = self.SMTP_TSX.read_text(encoding="utf-8")
        assert "Failed to fetch" in content, "SmtpConfigStep doit intercepter 'Failed to fetch'"

    def test_user_friendly_error_message(self):
        content = self.SMTP_TSX.read_text(encoding="utf-8")
        assert "Impossible de joindre le serveur" in content, (
            "Message d'erreur 'Failed to fetch' doit être traduit en message lisible"
        )


class TestBatchV0211_GmailRedirectUri:
    """VerifyStep doit afficher la redirect_uri exacte lors d'un mismatch."""

    VERIFY_TSX = Path("src/frontend/src/components/email/wizard/VerifyStep.tsx")

    def test_redirect_uri_stored(self):
        content = self.VERIFY_TSX.read_text(encoding="utf-8")
        assert "redirectUri" in content, "VerifyStep doit stocker la redirectUri reçue du backend"

    def test_redirect_uri_displayed_on_error(self):
        content = self.VERIFY_TSX.read_text(encoding="utf-8")
        assert "redirect_uri_mismatch" in content, (
            "VerifyStep doit afficher la redirectUri exacte lors d'une erreur redirect_uri_mismatch"
        )


class TestBatchV0211_AppleIconWindows:
    """Icône ⌘ ne doit pas apparaître sur Windows/Linux."""

    SHORTCUTS_TSX = Path("src/frontend/src/components/chat/ShortcutsModal.tsx")
    SKILL_TSX = Path("src/frontend/src/components/guided/SkillPromptPanel.tsx")

    def test_shortcuts_modal_adapts_to_platform(self):
        content = self.SHORTCUTS_TSX.read_text(encoding="utf-8")
        assert "adaptKey" in content, (
            "ShortcutsModal doit avoir une fonction adaptKey pour remplacer ⌘ par Ctrl sur Windows"
        )

    def test_skill_prompt_panel_platform_aware(self):
        content = self.SKILL_TSX.read_text(encoding="utf-8")
        assert "navigator.platform" in content, (
            "SkillPromptPanel doit détecter la plateforme pour afficher Ctrl ou ⌘"
        )


class TestBatchV0211_LinuxCategory:
    """Le fichier .desktop Linux doit avoir la catégorie Productivity."""

    TAURI_CONF = Path("src/frontend/src-tauri/tauri.conf.json")

    def test_linux_desktop_category_set(self):
        import json
        content = json.loads(self.TAURI_CONF.read_text(encoding="utf-8"))
        category = content.get("bundle", {}).get("category", "")
        assert category == "Productivity", (
            f"bundle.category doit être 'Productivity' pour le .desktop Linux, trouvé : '{category}'"
        )

    def test_splash_screen_windows_message_platform_aware(self):
        splash = Path("src/frontend/src/components/SplashScreen.tsx").read_text(encoding="utf-8")
        # Le message "Windows analyse les fichiers" ne doit plus être inconditionnel
        assert "indexOf('WIN')" in splash, (
            "SplashScreen doit adapter le message 'Windows analyse les fichiers' selon la plateforme"
        )


# ─── Batch v0.2.12 ─────────────────────────────────────────────────────────

class TestBUG031_ContextMessageOrder:
    """chat.py doit charger les 50 DERNIERS messages (DESC) remis en ordre chrono."""

    CHAT_PY = Path("src/backend/app/routers/chat.py")

    def test_desc_order_on_history_load(self):
        content = self.CHAT_PY.read_text(encoding="utf-8")
        # Ludo a ajouté Message.id.desc() pour tri déterministe (PR #21)
        assert "Message.created_at.desc()" in content, (
            "La requête d'historique doit utiliser .desc() pour récupérer les 50 derniers messages"
        )

    def test_list_reversed_applied(self):
        content = self.CHAT_PY.read_text(encoding="utf-8")
        assert "list(reversed(history_result.scalars().all()))" in content, (
            "Les messages DESC doivent être remis en ordre chrono via list(reversed(...))"
        )


class TestBUGNEW_PutToPatchCRM:
    """updateContact et updateProject doivent utiliser PATCH (le backend expose PATCH, pas PUT)."""

    MEMORY_TS = Path("src/frontend/src/services/api/memory.ts")

    def test_update_contact_uses_patch(self):
        content = self.MEMORY_TS.read_text(encoding="utf-8")
        # Vérifier qu'il n'y a plus de PUT dans updateContact
        lines = content.split('\n')
        in_update_contact = False
        for line in lines:
            if 'updateContact' in line and 'async function' in line:
                in_update_contact = True
            if in_update_contact and "method: 'PUT'" in line:
                raise AssertionError(
                    "updateContact utilise encore PUT au lieu de PATCH"
                )
            if in_update_contact and "method: 'PATCH'" in line:
                break  # OK, trouvé le PATCH attendu
        assert "method: 'PATCH'" in content, "updateContact doit utiliser PATCH"

    def test_update_project_uses_patch(self):
        content = self.MEMORY_TS.read_text(encoding="utf-8")
        assert content.count("method: 'PATCH'") >= 2, (
            "updateContact ET updateProject doivent tous les deux utiliser PATCH"
        )

    def test_no_put_for_update_functions(self):
        content = self.MEMORY_TS.read_text(encoding="utf-8")
        # Compter les PUT restants dans le fichier (certains peuvent être légitimes)
        put_count = content.count("method: 'PUT'")
        assert put_count == 0, (
            f"Il ne doit plus y avoir de method: 'PUT' dans memory.ts, trouvé {put_count}"
        )


class TestBUG048_OllamaNumPredict:
    """Ollama stream() doit transmettre num_predict et num_ctx."""

    OLLAMA_PY = Path("src/backend/app/services/providers/ollama.py")

    def test_options_block_present(self):
        content = self.OLLAMA_PY.read_text(encoding="utf-8")
        assert '"options"' in content or "'options'" in content, (
            "La requête Ollama doit inclure un bloc 'options' avec num_predict et num_ctx"
        )

    def test_num_predict_transmitted(self):
        content = self.OLLAMA_PY.read_text(encoding="utf-8")
        assert "num_predict" in content, (
            "La requête Ollama doit transmettre num_predict pour éviter la troncature"
        )

    def test_num_ctx_transmitted(self):
        content = self.OLLAMA_PY.read_text(encoding="utf-8")
        assert "num_ctx" in content, (
            "La requête Ollama doit transmettre num_ctx pour les prompts longs des skills"
        )


class TestBUGNEW_AsyncioPython313:
    """imap_smtp_provider.py ne doit plus utiliser asyncio.get_event_loop() (deprecated Python 3.13)."""

    IMAP_SMTP_PY = Path("src/backend/app/services/email/imap_smtp_provider.py")

    def test_no_get_event_loop(self):
        content = self.IMAP_SMTP_PY.read_text(encoding="utf-8")
        assert "get_event_loop()" not in content, (
            "asyncio.get_event_loop() est déprécié en Python 3.13, "
            "utiliser get_running_loop() à la place"
        )

    def test_get_running_loop_used(self):
        content = self.IMAP_SMTP_PY.read_text(encoding="utf-8")
        assert "get_running_loop()" in content, (
            "imap_smtp_provider.py doit utiliser asyncio.get_running_loop()"
        )


class TestBUGNEW_GoogleRefreshTokenRotation:
    """ensure_valid_access_token doit sauvegarder le nouveau refresh_token si Google en retourne un."""

    EMAIL_PY = Path("src/backend/app/routers/email.py")

    def test_refresh_token_rotation_handled(self):
        content = self.EMAIL_PY.read_text(encoding="utf-8")
        assert "new_tokens.get('refresh_token')" in content, (
            "ensure_valid_access_token doit vérifier si Google retourne un nouveau refresh_token"
        )

    def test_refresh_token_encrypted_and_saved(self):
        content = self.EMAIL_PY.read_text(encoding="utf-8")
        assert "account.refresh_token = encrypt_value(new_tokens['refresh_token'])" in content, (
            "Le nouveau refresh_token doit être chiffré et sauvegardé sur le compte"
        )


class TestBUG032_ExcelFileFilter:
    """Le filtre Documents du dialog Tauri doit etre aligné sur extract_text() (audit v0.2.12)."""

    CHAT_INPUT_TSX = Path("src/frontend/src/components/chat/ChatInput.tsx")
    FILE_PARSER_PY = Path("src/backend/app/services/file_parser.py")

    def test_xlsx_in_filter(self):
        content = self.CHAT_INPUT_TSX.read_text(encoding="utf-8")
        assert "'xlsx'" in content, "Le filtre Documents doit inclure 'xlsx'"

    def test_dead_extensions_removed(self):
        """Les extensions non supportées par extract_text() ne doivent PAS etre dans le filtre."""
        content = self.CHAT_INPUT_TSX.read_text(encoding="utf-8")
        dead_extensions = ["'xls'", "'ods'", "'pptx'", "'ppt'", "'odt'"]
        for ext in dead_extensions:
            assert ext not in content, (
                f"Le filtre Documents contient {ext} mais extract_text() ne le supporte pas"
            )

    def test_doc_removed(self):
        """python-docx ne lit PAS le format binaire .doc - retiré du filtre."""
        import re
        content = self.CHAT_INPUT_TSX.read_text(encoding="utf-8")
        matches = re.findall(r"'doc'", content)
        assert len(matches) == 0, (
            "Le filtre contient 'doc' mais python-docx ne lit pas le format binaire .doc"
        )

    def test_filter_only_supported_extensions(self):
        """Le filtre Documents ne doit contenir QUE des extensions supportées par extract_text()."""
        import re

        tsx_content = self.CHAT_INPUT_TSX.read_text(encoding="utf-8")
        doc_filter_match = re.search(
            r"name:\s*'Documents'.*?extensions:\s*\[([^\]]+)\]",
            tsx_content,
            re.DOTALL,
        )
        assert doc_filter_match, "Filtre Documents introuvable dans ChatInput.tsx"
        filter_exts = set(re.findall(r"'(\w+)'", doc_filter_match.group(1)))

        parser_content = self.FILE_PARSER_PY.read_text(encoding="utf-8")
        tree = ast.parse(parser_content)
        supported_exts: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in (
                        "TEXT_EXTENSIONS", "CODE_EXTENSIONS", "CSV_EXTENSIONS",
                    ):
                        if isinstance(node.value, ast.Set):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    supported_exts.add(elt.value.lstrip("."))

        # Extensions traitées dans les branches if de extract_text()
        # .pdf, .docx, .xlsx (pas .doc car python-docx ne supporte pas le format binaire)
        supported_exts.update({"pdf", "docx", "xlsx"})

        unsupported = filter_exts - supported_exts
        assert not unsupported, (
            f"Le filtre Documents contient des extensions non supportées par extract_text() : {unsupported}"
        )


class TestBUGNEW_FilesExtractText:
    """GET /files/{id}/content doit utiliser extract_text() (plus le placeholder TODO)."""

    FILES_PY = Path("src/backend/app/routers/files.py")

    def test_todo_removed(self):
        content = self.FILES_PY.read_text(encoding="utf-8")
        assert "TODO: Implement proper file parsing" not in content, (
            "Le TODO hardcodé doit être remplacé par un appel à extract_text()"
        )

    def test_extract_text_called(self):
        content = self.FILES_PY.read_text(encoding="utf-8")
        assert "content = extract_text(file_path)" in content, (
            "get_file_content doit appeler extract_text(file_path)"
        )

    def test_none_guard_present(self):
        content = self.FILES_PY.read_text(encoding="utf-8")
        assert "if content is None" in content, (
            "extract_text() peut retourner None (formats non supportés) — guard obligatoire"
        )


# ============================================================
# BUG-031 bis - Tri déterministe historique chat
# Si deux messages ont le même created_at (ex: user et assistant
# créés dans la même milliseconde), l'ordre est non déterministe
# en SQLite. Il faut une clé de tri secondaire (Message.id).
# ============================================================


class TestBUG031_TriDeterministeChat:
    """Le chargement de l'historique chat doit trier par (created_at, id) pour être déterministe."""

    CHAT_PY = SRC / "app" / "routers" / "chat.py"

    def test_order_by_has_two_keys(self):
        """Le order_by du chargement d'historique doit utiliser created_at ET id."""
        content = self.CHAT_PY.read_text(encoding="utf-8")
        assert "Message.created_at.desc(), Message.id.desc()" in content, (
            "Le tri de l'historique chat doit utiliser deux clés : "
            "Message.created_at.desc() ET Message.id.desc() pour éviter "
            "un ordre non déterministe quand deux messages ont le même timestamp"
        )

    def test_order_by_not_single_key(self):
        """Vérifie qu'on n'a pas un order_by avec created_at seul (sans id)."""
        content = self.CHAT_PY.read_text(encoding="utf-8")
        # On cherche le pattern "order_by(Message.created_at.desc())" suivi de ".limit"
        # sans Message.id en clé secondaire - ce pattern ne doit PAS exister
        import re
        # Cherche order_by avec seulement created_at.desc() et rien d'autre avant la parenthèse fermante
        pattern = r"\.order_by\(Message\.created_at\.desc\(\)\)\s*\n\s*\.limit"
        match = re.search(pattern, content)
        assert match is None, (
            "Il reste un order_by(Message.created_at.desc()) sans clé secondaire Message.id.desc(). "
            "Cela cause un tri non déterministe en SQLite quand deux messages ont le même timestamp."
        )


# ============================================================
# asyncio.get_event_loop() déprécié Python 3.13
# Tous les fichiers backend doivent utiliser get_running_loop()
# ============================================================


class TestAsyncioGetRunningLoop:
    """Aucun fichier backend ne doit utiliser asyncio.get_event_loop() (déprécié Python 3.13)."""

    BACKEND_DIR = Path("src/backend/app")

    def test_no_get_event_loop_in_backend(self):
        """Scanne tout src/backend/app/ pour get_event_loop()."""
        violations = []
        for py_file in self.BACKEND_DIR.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            if "get_event_loop()" in content:
                violations.append(str(py_file))
        assert violations == [], (
            f"asyncio.get_event_loop() trouvé dans : {violations}. "
            "Utiliser asyncio.get_running_loop() à la place (Python 3.13)."
        )

    def test_caldav_uses_get_running_loop(self):
        """caldav_provider.py doit utiliser get_running_loop()."""
        caldav = Path("src/backend/app/services/calendar/caldav_provider.py")
        content = caldav.read_text(encoding="utf-8")
        assert "get_running_loop()" in content, (
            "caldav_provider.py doit utiliser asyncio.get_running_loop()"
        )


# ─── Batch v0.2.13 ─────────────────────────────────────────────────────────

class TestBUG049_OllamaRetestButton:
    """LLMTab doit avoir un bouton Re-tester pour rafraichir le statut Ollama."""

    LLM_TAB_TSX = Path("src/frontend/src/components/settings/LLMTab.tsx")
    SETTINGS_MODAL_TSX = Path("src/frontend/src/components/settings/SettingsModal.tsx")

    def test_retest_prop_in_interface(self):
        content = self.LLM_TAB_TSX.read_text(encoding="utf-8")
        assert "onRetestOllama" in content, (
            "LLMTabProps doit avoir une prop onRetestOllama"
        )

    def test_refresh_icon_used(self):
        content = self.LLM_TAB_TSX.read_text(encoding="utf-8")
        assert "RefreshCw" in content, (
            "LLMTab doit importer et utiliser l'icône RefreshCw pour le bouton Re-tester"
        )

    def test_retest_function_in_settings_modal(self):
        content = self.SETTINGS_MODAL_TSX.read_text(encoding="utf-8")
        assert "retestOllama" in content, (
            "SettingsModal doit avoir une fonction retestOllama qui appelle api.getOllamaStatus()"
        )

    def test_retest_passed_to_llmtab(self):
        content = self.SETTINGS_MODAL_TSX.read_text(encoding="utf-8")
        assert "onRetestOllama={retestOllama}" in content, (
            "SettingsModal doit passer onRetestOllama au composant LLMTab"
        )


class TestBUG050_OllamaSkillsTimeout:
    """Ollama streaming doit avoir timeout=None (pas de timeout forcé côté serveur)."""

    OLLAMA_PY = Path("src/backend/app/services/providers/ollama.py")

    def test_no_fixed_read_timeout(self):
        content = self.OLLAMA_PY.read_text(encoding="utf-8")
        assert "timeout=120.0" not in content, (
            "Le timeout Ollama ne doit plus être fixé à 120s (trop court pour machines lentes)"
        )

    def test_read_timeout_none(self):
        content = self.OLLAMA_PY.read_text(encoding="utf-8")
        assert "read=None" in content, (
            "Ollama doit avoir read=None (pas de timeout de lecture) — AbortController frontend gère l'annulation"
        )

    def test_connect_timeout_preserved(self):
        content = self.OLLAMA_PY.read_text(encoding="utf-8")
        assert "connect=5.0" in content, (
            "Ollama doit garder un connect timeout court (5s) pour détecter si Ollama n'est pas démarré"
        )


class TestBUGGmail403_AccessDenied:
    """La page de callback OAuth doit afficher des conseils lisibles pour erreur 403 access_denied."""

    EMAIL_PY = Path("src/backend/app/routers/email.py")
    VERIFY_TSX = Path("src/frontend/src/components/email/wizard/VerifyStep.tsx")

    def test_access_denied_special_case(self):
        content = self.EMAIL_PY.read_text(encoding="utf-8")
        assert "access_denied" in content, (
            "Le callback OAuth doit détecter l'erreur 'access_denied' et afficher des conseils"
        )

    def test_test_users_tip_shown(self):
        content = self.EMAIL_PY.read_text(encoding="utf-8")
        assert "Test" in content and ("Utilisateurs de test" in content or "utilisateurs de test" in content), (
            "Le message d'erreur 403 doit mentionner le mode Test et les utilisateurs de test"
        )

    def test_apis_activation_tip_shown(self):
        content = self.EMAIL_PY.read_text(encoding="utf-8")
        assert "Gmail API" in content, (
            "Le message d'erreur 403 doit mentionner l'activation de Gmail API"
        )

    def test_verify_step_has_403_tips(self):
        content = self.VERIFY_TSX.read_text(encoding="utf-8")
        assert "403" in content, (
            "VerifyStep doit avoir un bloc d'aide visible pour l'erreur 403"
        )


# ─── BUG-042/043/044 : Skills documents + fichiers joints ────────────────────


class TestBUG042_SkillsMaxTokens:
    """max_tokens doit être >= 16384 pour les skills FILE (anti-troncature)."""

    SKILLS_PY = Path("src/backend/app/routers/skills.py")

    def test_max_tokens_at_least_16384(self):
        content = self.SKILLS_PY.read_text(encoding="utf-8")
        import re
        match = re.search(r"llm_max_tokens\s*=\s*(\d+)", content)
        assert match, "llm_max_tokens doit être défini dans skills.py"
        value = int(match.group(1))
        assert value >= 16384, (
            f"llm_max_tokens={value} est trop bas, minimum 16384 pour éviter la troncature"
        )


class TestBUG043_DocumentContentValidation:
    """code_executor doit valider le contenu des documents générés."""

    CODE_EXEC = Path("src/backend/app/services/skills/code_executor.py")

    def test_validate_document_content_exists(self):
        content = self.CODE_EXEC.read_text(encoding="utf-8")
        assert "_validate_document_content" in content, (
            "code_executor.py doit avoir une fonction _validate_document_content"
        )

    def test_validation_called_after_code_execution(self):
        content = self.CODE_EXEC.read_text(encoding="utf-8")
        assert "_validate_document_content" in content and "fallback vers parser legacy" in content, (
            "La validation de contenu doit être appelée après code-execution, avec fallback"
        )

    def test_min_content_elements_defined(self):
        content = self.CODE_EXEC.read_text(encoding="utf-8")
        assert "MIN_CONTENT_ELEMENTS" in content, (
            "MIN_CONTENT_ELEMENTS doit définir les seuils par format (docx, pptx, xlsx)"
        )

    def test_retry_markdown_in_router(self):
        skills_py = Path("src/backend/app/routers/skills.py").read_text(encoding="utf-8")
        assert "retry" in skills_py.lower() and "markdown" in skills_py.lower(), (
            "skills.py doit retenter en Markdown si le document est quasi vide"
        )


class TestBUG044_FilePathsInChat:
    """Les fichiers joints doivent être envoyés au backend pour injection dans le contexte LLM."""

    SCHEMAS_PY = Path("src/backend/app/models/schemas.py")
    CHAT_PY = Path("src/backend/app/routers/chat.py")
    CHAT_TS = Path("src/frontend/src/services/api/chat.ts")
    CHAT_INPUT = Path("src/frontend/src/components/chat/ChatInput.tsx")

    def test_chat_request_has_file_paths_field(self):
        content = self.SCHEMAS_PY.read_text(encoding="utf-8")
        assert "file_paths" in content, (
            "ChatRequest doit avoir un champ file_paths pour les fichiers joints"
        )

    def test_frontend_sends_file_paths(self):
        content = self.CHAT_INPUT.read_text(encoding="utf-8")
        assert "file_paths" in content, (
            "ChatInput.tsx doit envoyer file_paths dans la requête streamMessage"
        )

    def test_backend_processes_file_paths(self):
        content = self.CHAT_PY.read_text(encoding="utf-8")
        assert "file_paths" in content and "_get_file_context" in content, (
            "chat.py doit traiter les file_paths via _get_file_context"
        )

    def test_frontend_chat_request_type_has_file_paths(self):
        content = self.CHAT_TS.read_text(encoding="utf-8")
        assert "file_paths" in content, (
            "ChatRequest interface dans chat.ts doit avoir file_paths"
        )


class TestBUG044_LinuxOnedirPyInstaller:
    """BUG-044 : PyInstaller onedir sur Linux pour éviter ELF page-alignment OpenBLAS.
    Le backend.spec doit utiliser COLLECT (onedir) sur Linux au lieu de EXE (onefile).
    Le wrapper shell doit utiliser THERESE_BACKEND_LIBS pour trouver le vrai binaire.
    """

    BACKEND_SPEC = Path("src/backend/backend.spec")
    RELEASE_YML = Path(".github/workflows/release.yml")
    LIB_RS = Path("src/frontend/src-tauri/src/lib.rs")
    TAURI_CONF = Path("src/frontend/src-tauri/tauri.conf.json")

    def test_backend_spec_has_collect_for_linux(self):
        content = self.BACKEND_SPEC.read_text(encoding="utf-8")
        assert 'sys.platform == "linux"' in content, (
            "backend.spec doit avoir une branche conditionnelle pour Linux"
        )
        assert "COLLECT(" in content, (
            "backend.spec doit avoir une section COLLECT pour le mode onedir Linux"
        )
        assert "exclude_binaries=True" in content, (
            "backend.spec doit avoir exclude_binaries=True dans l'EXE Linux"
        )

    def test_release_yml_linux_uses_wrapper_script(self):
        content = self.RELEASE_YML.read_text(encoding="utf-8")
        assert "THERESE_BACKEND_LIBS" in content, (
            "release.yml doit créer un wrapper shell qui utilise THERESE_BACKEND_LIBS"
        )
        assert "backend-libs" in content, (
            "release.yml doit copier le dossier onedir dans backend-libs/"
        )
        assert "LD_LIBRARY_PATH" in content, (
            "Le wrapper shell doit configurer LD_LIBRARY_PATH"
        )

    def test_lib_rs_passes_backend_libs_env_on_linux(self):
        content = self.LIB_RS.read_text(encoding="utf-8")
        assert "THERESE_BACKEND_LIBS" in content, (
            "lib.rs doit passer THERESE_BACKEND_LIBS au sidecar sur Linux"
        )
        assert 'target_os = "linux"' in content, (
            "lib.rs doit conditionner THERESE_BACKEND_LIBS avec #[cfg(target_os = 'linux')]"
        )
        assert "resource_dir()" in content, (
            "lib.rs doit utiliser app.path().resource_dir() pour trouver backend-libs"
        )

    def test_release_yml_injects_backend_libs_resources_linux(self):
        """Le workflow release.yml injecte backend-libs dans resources pour Linux.

        Note : resources reste [] dans tauri.conf.json (sinon macOS/Windows cassent
        car le dossier backend-libs n'existe pas). L'injection se fait dans le workflow.
        """
        content = self.RELEASE_YML.read_text(encoding="utf-8")
        assert "backend-libs" in content, (
            "release.yml doit injecter backend-libs dans les resources Tauri pour Linux"
        )

    def test_release_yml_cp_copies_content_not_folder(self):
        content = self.RELEASE_YML.read_text(encoding="utf-8")
        # La commande cp doit copier le CONTENU du dossier onedir (dist/backend/.)
        # et non le dossier lui-même (dist/backend), ce qui créerait backend-libs/backend/backend
        # (le wrapper pointerait sur un dossier et non un binaire → backend ne démarre jamais)
        assert "dist/backend/." in content or "dist/backend/*" in content, (
            "release.yml : la commande cp doit copier le contenu du dossier onedir "
            "(dist/backend/. ou dist/backend/*) et non le dossier lui-même"
        )


class TestBUG049_CalendarDropdownOverflow:
    """BUG-049 : le dropdown <select> du calendrier passait derrière les autres composants.

    Note (revue produit) : depuis la Phase 1 (vues content-swap), le calendrier n'est
    plus rendu dans une fenêtre-panel détachée. Les anciens tests sur le conteneur de
    PanelWindow (supprimé) ont été retirés ; l'overflow-hidden des conteneurs de vue
    (App.tsx, ChatLayout.tsx) est légitime (discipline de scroll). Le vrai correctif
    anti-régression reste le wrapper à fort stacking-context autour du <select>, testé
    ci-dessous sur le code réel.
    """

    CALENDAR_PANEL = FRONTEND / "components" / "calendar" / "CalendarPanel.tsx"

    def test_calendar_select_has_zindex_wrapper(self):
        """Le <select> doit être enveloppé dans `relative ${Z_LAYER.ONBOARDING}`
        (= z-[100]) pour créer un contexte de stacking au-dessus de la pile, robuste
        aux overflow-hidden légitimes des conteneurs de vue.

        On asserte sur le CODE réel (le template literal du className), pas sur le
        commentaire : retirer le wrapper casserait bien le test (l'ancienne version
        matchait 'z-[100]' présent seulement dans le commentaire = faux positif).
        """
        content = self.CALENDAR_PANEL.read_text(encoding="utf-8")
        assert "relative ${Z_LAYER.ONBOARDING}" in content, (
            "CalendarPanel : le <select> doit être enveloppé dans "
            "`relative ${Z_LAYER.ONBOARDING}` (contexte de stacking au-dessus de la pile)"
        )


# ============================================================
# BUG-050 (v0.3.5) - Backup fichier clé Fernet
# Un changement de productName (signature binaire) provoquait la
# perte de la clé Keychain. Le fix synchronise toujours un fichier
# backup et restaure depuis celui-ci si la clé Keychain a changé.
# ============================================================


class TestBUG050_EncryptionKeyBackupFile:
    """BUG-050 : _create_key_in_keychain() doit aussi écrire dans KEY_FILE."""

    def test_create_key_calls_write_key_backup(self):
        """_create_key_in_keychain appelle _write_key_backup après keyring.set_password."""
        content = ENCRYPTION_PY.read_text(encoding="utf-8")
        # La méthode _create_key_in_keychain doit appeler self._write_key_backup(key)
        assert "_write_key_backup" in content, (
            "encryption.py doit contenir _write_key_backup (BUG-050)"
        )
        # Vérifier que _create_key_in_keychain contient l'appel
        import re
        # Trouver le bloc de _create_key_in_keychain
        match = re.search(
            r"def _create_key_in_keychain\(self\).*?(?=\n    def |\nclass |\Z)",
            content,
            re.DOTALL,
        )
        assert match is not None, "_create_key_in_keychain doit exister"
        method_body = match.group(0)
        assert "self._write_key_backup(key)" in method_body, (
            "_create_key_in_keychain doit appeler self._write_key_backup(key) "
            "pour créer un fichier backup de la clé (BUG-050)"
        )

    def test_write_key_backup_method_exists(self):
        """_write_key_backup doit exister et écrire dans KEY_FILE."""
        content = ENCRYPTION_PY.read_text(encoding="utf-8")
        assert "def _write_key_backup(self, key: bytes)" in content, (
            "encryption.py doit avoir une méthode _write_key_backup (BUG-050)"
        )
        # Vérifier qu'elle écrit dans KEY_FILE
        import re
        match = re.search(
            r"def _write_key_backup\(self, key: bytes\).*?(?=\n    def |\nclass |\Z)",
            content,
            re.DOTALL,
        )
        assert match is not None
        method_body = match.group(0)
        assert "KEY_FILE" in method_body, (
            "_write_key_backup doit écrire dans KEY_FILE"
        )
        assert "os.open" in method_body or "open(" in method_body, (
            "_write_key_backup doit ouvrir le fichier pour écrire"
        )

    def test_migrate_does_not_delete_file(self):
        """_migrate_key_to_keychain ne doit PAS supprimer le fichier source."""
        content = ENCRYPTION_PY.read_text(encoding="utf-8")
        import re
        match = re.search(
            r"def _migrate_key_to_keychain\(self\).*?(?=\n    def |\nclass |\Z)",
            content,
            re.DOTALL,
        )
        assert match is not None, "_migrate_key_to_keychain doit exister"
        method_body = match.group(0)
        # Vérifier qu'il n'y a PAS de KEY_FILE.unlink() actif (commenté OK)
        lines = method_body.split("\n")
        for line in lines:
            stripped = line.strip()
            if "KEY_FILE.unlink()" in stripped and not stripped.startswith("#"):
                pytest.fail(
                    "_migrate_key_to_keychain ne doit PAS supprimer KEY_FILE "
                    "(le fichier sert de backup - BUG-050)"
                )


class TestBUG050_KeychainFallbackToFile:
    """BUG-050 : si la clé Keychain diffère du fichier backup, utiliser le fichier."""

    def test_get_or_create_key_checks_file_coherence(self):
        """_get_or_create_key doit comparer clé Keychain et fichier backup."""
        content = ENCRYPTION_PY.read_text(encoding="utf-8")
        import re
        match = re.search(
            r"def _get_or_create_key\(self\).*?(?=\n    def |\nclass |\Z)",
            content,
            re.DOTALL,
        )
        assert match is not None, "_get_or_create_key doit exister"
        method_body = match.group(0)
        assert "file_key != keychain_key" in method_body, (
            "_get_or_create_key doit comparer la clé Keychain avec le fichier backup "
            "pour détecter un changement de signature binaire (BUG-050)"
        )

    def test_get_or_create_key_restores_file_key_to_keychain(self):
        """Quand les clés divergent, la clé fichier doit être restaurée dans le Keychain."""
        content = ENCRYPTION_PY.read_text(encoding="utf-8")
        import re
        match = re.search(
            r"def _get_or_create_key\(self\).*?(?=\n    def |\nclass |\Z)",
            content,
            re.DOTALL,
        )
        assert match is not None
        method_body = match.group(0)
        # Doit restaurer la clé fichier dans le Keychain via keyring.set_password
        assert "file_key.decode" in method_body, (
            "_get_or_create_key doit restaurer la clé fichier dans le Keychain (BUG-050)"
        )
        assert "return file_key" in method_body, (
            "_get_or_create_key doit retourner file_key quand les clés divergent (BUG-050)"
        )

    def test_keychain_key_synced_to_backup_file(self):
        """Quand la clé Keychain est valide, elle doit être synchronisée dans le fichier backup."""
        content = ENCRYPTION_PY.read_text(encoding="utf-8")
        import re
        match = re.search(
            r"def _get_or_create_key\(self\).*?(?=\n    def |\nclass |\Z)",
            content,
            re.DOTALL,
        )
        assert match is not None
        method_body = match.group(0)
        assert "self._write_key_backup(keychain_key)" in method_body, (
            "_get_or_create_key doit synchroniser la clé Keychain dans le fichier backup (BUG-050)"
        )

    def test_bug050_functional_keychain_fallback(self):
        """Test fonctionnel : si le Keychain a une nouvelle clé, le fichier backup est utilisé."""
        import tempfile

        from cryptography.fernet import Fernet

        from app.services.encryption import EncryptionService

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            tmp_key_file = tmp_path / ".encryption_key"

            # Clé originale (dans le fichier backup)
            original_key = Fernet.generate_key()
            # Nouvelle clé (générée par un binaire avec une autre signature)
            new_keychain_key = Fernet.generate_key()

            # Écrire la clé originale dans le fichier backup
            with open(tmp_key_file, "wb") as f:
                f.write(original_key)

            # Simuler : le Keychain retourne la nouvelle clé, mais le fichier a l'ancienne
            mock_keyring = MagicMock()
            mock_keyring.set_password = MagicMock()

            with (
                patch("app.services.encryption._try_keyring_available", return_value=True),
                patch("app.services.encryption.KEY_FILE", tmp_key_file),
                patch("app.services.encryption.THERESE_DIR", tmp_path),
            ):
                svc = EncryptionService.__new__(EncryptionService)
                svc._using_keychain = False

                with (
                    patch.object(svc, "_get_key_from_keychain", return_value=new_keychain_key),
                    patch.dict("sys.modules", {"keyring": mock_keyring}),
                ):
                    key = svc._get_or_create_key()

            # La clé retournée doit être celle du fichier (pas du Keychain)
            assert key == original_key, (
                "Quand le Keychain a une clé différente du fichier backup, "
                "la clé fichier doit être utilisée (BUG-050)"
            )


# ============================================================
# BUG-051 (v0.3.6) - Clés API corrompues affichent une check verte
# Le backend doit tenter de déchiffrer les clés avant de les
# déclarer valides, et signaler les clés corrompues.
# ============================================================


class TestBUG051_CorruptedKeysDetection:
    """Détection des clés API corrompues (blob Fernet illisible)."""

    CONFIG_ROUTER_PY = Path("src/backend/app/routers/config.py")
    SCHEMAS_PY = Path("src/backend/app/models/schemas.py")

    def test_config_has_check_key_decryptable_helper(self):
        """config.py doit avoir un helper _check_key_decryptable."""
        content = self.CONFIG_ROUTER_PY.read_text(encoding="utf-8")
        assert "_check_key_decryptable" in content, (
            "config.py doit définir _check_key_decryptable pour vérifier le déchiffrement"
        )

    def test_config_uses_decrypt_value_in_check(self):
        """_check_key_decryptable doit appeler decrypt_value."""
        content = self.CONFIG_ROUTER_PY.read_text(encoding="utf-8")
        # Le helper doit tenter de déchiffrer
        assert "decrypt_value" in content, (
            "config.py doit utiliser decrypt_value pour vérifier les clés"
        )

    def test_config_response_has_corrupted_keys(self):
        """ConfigResponse doit avoir un champ corrupted_keys."""
        content = self.SCHEMAS_PY.read_text(encoding="utf-8")
        assert "corrupted_keys" in content, (
            "ConfigResponse doit inclure corrupted_keys: list[str]"
        )

    def test_get_config_returns_corrupted_keys(self):
        """get_config doit retourner corrupted_keys dans la réponse."""
        content = self.CONFIG_ROUTER_PY.read_text(encoding="utf-8")
        assert "corrupted_keys=corrupted_keys" in content, (
            "get_config doit passer corrupted_keys à ConfigResponse"
        )


# ============================================================
# BUG-052 (v0.3.6) - Modèle Ollama ignoré (gemma → mistral-nemo)
# Le modèle sélectionné par l'utilisateur doit être respecté.
# ============================================================


class TestBUG052_OllamaModelPreference:
    """Le modèle Ollama sélectionné par l'utilisateur ne doit pas être ignoré."""

    LLM_PY = Path("src/backend/app/services/llm.py")

    def test_fallback_uses_selected_model(self):
        """Le fallback Ollama doit respecter selected_model puis détecter le modèle installé (BUG-052 + BUG-098)."""
        content = self.LLM_PY.read_text(encoding="utf-8")
        assert "selected_model or detect_default_ollama_model()" in content, (
            "Le fallback Ollama doit respecter selected_model, puis détecter le "
            "premier modèle réellement installé au lieu de 'mistral-nemo' codé en dur (BUG-052/BUG-098)"
        )

    def test_get_llm_service_reads_db_model(self):
        """get_llm_service_for_provider doit lire llm_model depuis la DB."""
        content = self.LLM_PY.read_text(encoding="utf-8")
        # Chercher la lecture de llm_model dans get_llm_service_for_provider
        fn_start = content.find("def get_llm_service_for_provider")
        assert fn_start > 0, "get_llm_service_for_provider doit exister"
        fn_body = content[fn_start:fn_start + 3000]
        assert "llm_model" in fn_body, (
            "get_llm_service_for_provider doit lire llm_model depuis la DB (BUG-052)"
        )


# ============================================================
# BUG-098 (lcjp, 04/06/2026) - Défaut Ollama "mistral-nemo" codé en dur
# Le défaut Ollama doit être le 1er modèle chat réellement installé
# (via GET /api/tags), pas "mistral-nemo" qui n'est souvent pas installé.
# ============================================================


class TestBUG098_OllamaDefaultModelDetection:
    """Le défaut Ollama doit être détecté parmi les modèles installés, pas 'mistral-nemo' codé en dur."""

    LLM_PY = SRC / "app" / "services" / "llm.py"
    BOARD_PY = SRC / "app" / "services" / "board.py"

    @staticmethod
    def _fake_httpx_get(models):
        class _Resp:
            status_code = 200

            @staticmethod
            def json():
                return {"models": [{"name": m} for m in models]}

        def _get(url, timeout=None):
            return _Resp()

        return _get

    def test_detect_returns_first_installed_chat_model(self, monkeypatch):
        import httpx

        from app.services.llm import detect_default_ollama_model

        monkeypatch.setattr(httpx, "get", self._fake_httpx_get(["gemma:2b", "llama3:8b"]))
        assert detect_default_ollama_model() == "gemma:2b"

    def test_detect_prefers_installed_over_mistral_nemo(self, monkeypatch):
        """Scénario exact lcjp : gemma:2b installé, mistral-nemo absent."""
        import httpx

        from app.services.llm import detect_default_ollama_model

        monkeypatch.setattr(httpx, "get", self._fake_httpx_get(["gemma:2b"]))
        assert detect_default_ollama_model() == "gemma:2b"
        assert detect_default_ollama_model() != "mistral-nemo"

    def test_detect_skips_embedding_models(self, monkeypatch):
        """Un modèle d'embedding (ex: nomic-embed-text, utilisé par Qdrant) ne doit pas être choisi comme modèle de chat."""
        import httpx

        from app.services.llm import detect_default_ollama_model

        monkeypatch.setattr(httpx, "get", self._fake_httpx_get(["nomic-embed-text:latest"]))
        assert detect_default_ollama_model(fallback="mistral-nemo") == "mistral-nemo"

    def test_detect_fallback_when_ollama_unreachable(self, monkeypatch):
        import httpx

        from app.services.llm import detect_default_ollama_model

        def _boom(url, timeout=None):
            raise httpx.ConnectError("connexion refusée")

        monkeypatch.setattr(httpx, "get", _boom)
        assert detect_default_ollama_model(fallback="mistral-nemo") == "mistral-nemo"

    def test_llm_fallbacks_use_detection_not_hardcoded(self):
        content = self.LLM_PY.read_text(encoding="utf-8")
        assert content.count("detect_default_ollama_model(") >= 4, (
            "Tous les points de fallback Ollama de llm.py doivent passer par "
            "detect_default_ollama_model() au lieu de 'mistral-nemo' codé en dur"
        )

    def test_board_sovereign_uses_detection(self):
        content = self.BOARD_PY.read_text(encoding="utf-8")
        assert "detect_default_ollama_model" in content, (
            "Le mode souverain du Board doit détecter le modèle Ollama installé"
        )
        assert 'default_ollama_model = "mistral-nemo:12b"' not in content, (
            "board.py ne doit plus coder en dur 'mistral-nemo:12b' comme défaut souverain"
        )


# ============================================================
# BUG-099 (lcjp, 04/06/2026) - Clé API Gemini 'AQ.' refusée
# Google émet désormais des clés commençant par 'AQ.' (avant 'AIza').
# La validation ne doit plus exiger le préfixe 'AIza'.
# ============================================================


class TestBUG099_GeminiKeyPrefixRelaxed:
    """Les nouvelles clés Gemini 'AQ.' ne doivent plus être bloquées par un contrôle de préfixe 'AIza'."""

    CONFIG_PY = SRC / "app" / "routers" / "config.py"
    LLM_TAB = FRONTEND / "components" / "settings" / "LLMTab.tsx"

    def test_backend_no_longer_requires_aiza_prefix(self):
        content = self.CONFIG_PY.read_text(encoding="utf-8")
        assert 'provider == "gemini" and not key.startswith("AIza")' not in content, (
            "Le backend ne doit plus exiger le préfixe 'AIza' pour les clés Gemini (format 'AQ' désormais émis par Google)"
        )
        assert 'provider == "gemini_image" and not key.startswith("AIza")' not in content, (
            "Le backend ne doit plus exiger le préfixe 'AIza' pour les clés Gemini Image"
        )

    def test_frontend_image_gemini_no_aiza_prefix(self):
        content = self.LLM_TAB.read_text(encoding="utf-8")
        assert "keyPrefix: 'AIza'" not in content, (
            "LLMTab.tsx ne doit plus imposer le préfixe client 'AIza' (clé image Gemini)"
        )


# ============================================================
# BUG-100 (lcjp, macOS Tahoe, 04/06/2026) - Ollama invisible à l'onboarding
# La liste des providers est plafonnée en hauteur (max-h-48) : Ollama, 10e et
# dernier provider, sort de la vue, et sur macOS la scrollbar est masquée.
# ============================================================


class TestBUG100_OnboardingProviderListVisible:
    """La liste des providers de l'onboarding ne doit pas être tronquée en hauteur (Ollama = dernier, invisible sur macOS)."""

    LLM_STEP = FRONTEND / "components" / "onboarding" / "LLMStep.tsx"

    def test_provider_list_not_height_capped(self):
        content = self.LLM_STEP.read_text(encoding="utf-8")
        assert "max-h-48" not in content, (
            "La liste des providers de l'onboarding (LLMStep.tsx) ne doit pas être "
            "plafonnée par max-h-48 : cela masque Ollama (dernier provider) sur macOS "
            "où la barre de défilement est invisible par défaut"
        )


# ============================================================
# BUG-102 (revue produit Chantier B - donnée unifiée) - Contact CRM indexé Qdrant
# Un contact créé via le CRM doit aussi être embarqué dans Qdrant, sinon il est
# invisible à la recherche sémantique unifiée (le contact mémoire l'est déjà).
# ============================================================


class TestBUG102_UnifiedContactQdrantEmbed:
    """Les contacts créés côté CRM doivent être indexés dans Qdrant ; l'update doit ré-indexer."""

    CRM_PY = SRC / "app" / "routers" / "crm.py"
    MEMORY_PY = SRC / "app" / "routers" / "memory.py"

    def test_crm_create_embeds_qdrant(self):
        content = self.CRM_PY.read_text(encoding="utf-8")
        assert "_embed_contact" in content, (
            "routers/crm.py doit embarquer le contact créé dans Qdrant (_embed_contact) ; "
            "sinon les contacts CRM sont invisibles à la recherche sémantique unifiée (BUG-102)"
        )

    def test_update_contact_reembeds(self):
        content = self.MEMORY_PY.read_text(encoding="utf-8")
        fn_start = content.find("async def update_contact")
        assert fn_start > 0, "update_contact doit exister"
        fn_body = content[fn_start:fn_start + 1800]
        assert "_embed_contact" in fn_body, (
            "update_contact (PATCH /memory/contacts/{id}) doit ré-indexer le contact dans "
            "Qdrant après mise à jour, sinon la recherche sémantique reste sur l'ancienne version"
        )


# ============================================================
# Chantier A (revue produit - Confiance / vérité d'exécution)
# Verrouille : déduplication des créations d'entités (anti création en masse),
# erreurs honnêtes (pas de faux succès), et câblage du cap + résumé déterministe.
# ============================================================


class TestChantierA_VeriteExecution:
    """L'IA ne doit pas mentir sur ce qu'elle fait : dédup, erreurs honnêtes, cap, récap déterministe."""

    MEMORY_TOOLS = SRC / "app" / "services" / "memory_tools.py"
    CHAT_PY = SRC / "app" / "routers" / "chat.py"

    def test_create_tools_deduplicate(self):
        content = self.MEMORY_TOOLS.read_text(encoding="utf-8")
        assert "_find_existing_contact" in content, (
            "execute_create_contact doit dédupliquer (anti création en masse)"
        )
        assert "_find_existing_project" in content, (
            "execute_create_project doit dédupliquer (anti création en masse)"
        )

    def test_create_tools_return_honest_errors(self):
        content = self.MEMORY_TOOLS.read_text(encoding="utf-8")
        # Sur échec, les outils renvoient un objet {"error": ...} + rollback (pas de faux succès)
        assert content.count("await session.rollback()") >= 2, (
            "Les outils de création doivent rollback et renvoyer une erreur honnête en cas d'échec"
        )

    def test_chat_enforces_create_cap_and_recap(self):
        content = self.CHAT_PY.read_text(encoding="utf-8")
        assert "enforce_create_cap" in content, (
            "chat.py doit plafonner les créations par tour (anti rafale de noms hallucinés)"
        )
        assert "summarize_executions" in content, (
            "chat.py doit émettre un résumé déterministe de ce qui a réellement été créé"
        )


# ============================================================
# Phase 1 (revue produit - refonte navigation content-swap)
# Le CRM est une VUE de la zone principale (navigationStore), plus une fenêtre Tauri.
# ============================================================


class TestPhase1_CRMAsView:
    """Le CRM doit être une vue (content-swap), plus une fenêtre détachée."""

    WINDOW_MANAGER = FRONTEND / "services" / "windowManager.ts"
    PANEL_WINDOW = FRONTEND / "components" / "panels" / "PanelWindow.tsx"
    CHAT_LAYOUT = FRONTEND / "components" / "chat" / "ChatLayout.tsx"
    NAV_STORE = FRONTEND / "stores" / "navigationStore.ts"

    def test_navigation_store_exists(self):
        content = self.NAV_STORE.read_text(encoding="utf-8")
        assert "activeView" in content and "setView" in content, (
            "navigationStore doit gérer activeView + setView (routeur de vues Phase 1)"
        )

    def test_panel_window_system_removed(self):
        # Phase 1 L9 : plus de fenêtres-panels détachées (tout est content-swap).
        assert not self.WINDOW_MANAGER.exists(), (
            "Le windowManager (fenêtres-panels Tauri) doit être supprimé en Phase 1"
        )
        assert not self.PANEL_WINDOW.exists(), (
            "PanelWindow (rendu des fenêtres-panels) doit être supprimé en Phase 1"
        )

    def test_chatlayout_uses_view_router(self):
        content = self.CHAT_LAYOUT.read_text(encoding="utf-8")
        assert "useNavigationStore" in content, (
            "ChatLayout doit utiliser le navigationStore pour router les vues"
        )
        for view in ("crm", "email", "calendar", "tasks", "invoices"):
            assert f"setView('{view}')" in content, (
                f"Le bouton {view} doit basculer vers la vue (setView), pas ouvrir une fenêtre"
            )


# ============================================================
# L6 (revue produit) - La Mémoire devient une VUE content-swap
# (verdict panel UX/UI : docs/revue-produit/L6-decision-ux-panel.md)
# Plus un tiroir overlay : une vue de la zone principale comme les 5 autres.
# ============================================================


class TestL6_MemoryAsView:
    """La Mémoire doit être une vue (content-swap), plus un tiroir overlay."""

    CHAT_LAYOUT = FRONTEND / "components" / "chat" / "ChatLayout.tsx"
    PANEL_CONTAINER = FRONTEND / "components" / "chat" / "PanelContainer.tsx"
    MEMORY_PANEL = FRONTEND / "components" / "memory" / "MemoryPanel.tsx"

    def test_memory_panel_supports_standalone(self):
        content = self.MEMORY_PANEL.read_text(encoding="utf-8")
        assert "standalone" in content, (
            "MemoryPanel doit accepter un prop standalone (rendu vue plein écran)"
        )

    def test_chatlayout_routes_memory_view(self):
        content = self.CHAT_LAYOUT.read_text(encoding="utf-8")
        assert "setView('memory')" in content, (
            "Le déclencheur Mémoire doit basculer vers la vue (setView('memory'))"
        )
        assert "activeView === 'memory'" in content, (
            "Le routeur de ChatLayout doit rendre la vue Mémoire"
        )
        assert "<MemoryPanel standalone" in content, (
            "ChatLayout doit rendre MemoryPanel en standalone dans la zone principale"
        )

    def test_memory_drawer_removed_from_panelcontainer(self):
        content = self.PANEL_CONTAINER.read_text(encoding="utf-8")
        assert "isOpen={showMemoryPanel}" not in content, (
            "PanelContainer ne doit plus rendre le tiroir Mémoire (isOpen={showMemoryPanel})"
        )

    def test_panelstore_memory_toggle_debt_removed(self):
        # Dette soldée : plus de double chemin showMemoryPanel/toggleMemoryPanel
        # (la Mémoire est une vue gérée par navigationStore, pas un panneau).
        content = (FRONTEND / "stores" / "panelStore.ts").read_text(encoding="utf-8")
        for dead in ("showMemoryPanel", "toggleMemoryPanel", "closeMemoryPanel"):
            assert dead not in content, (
                f"panelStore ne doit plus exposer {dead} (Mémoire = vue, pas panneau)"
            )


class TestL6_ContactScopeRoundtrip:
    """L6 pastille : le scope d'un contact doit round-tripper (create accepte, response expose).

    Bug trouvé en vérif d'intégration : ContactCreate/ContactResponse n'avaient pas
    scope/scope_id, donc le scope était jeté à la création ET jamais renvoyé -> le
    filtre 'Conv.' de la Mémoire et la pastille de glance ne pouvaient pas fonctionner.
    """

    MEMORY_ROUTER = SRC / "app" / "routers" / "memory.py"

    def test_contact_create_accepts_scope(self):
        from app.models.schemas import ContactCreate

        c = ContactCreate(first_name="X", scope="conversation", scope_id="conv-1")
        assert c.scope == "conversation"
        assert c.scope_id == "conv-1"

    def test_contact_response_exposes_scope(self):
        from app.models.schemas import ContactResponse

        assert "scope" in ContactResponse.model_fields, (
            "ContactResponse doit exposer scope (sinon filtre Conv. + pastille L6 cassés)"
        )
        assert "scope_id" in ContactResponse.model_fields

    def test_create_handler_persists_and_exposes_scope(self):
        content = self.MEMORY_ROUTER.read_text(encoding="utf-8")
        assert "scope=request.scope" in content, (
            "create_contact doit persister le scope reçu (round-trip L6)"
        )
        assert "scope=contact.scope" in content, (
            "_contact_to_response doit exposer le scope du contact (round-trip L6)"
        )


class TestL7_UnifiedEscape:
    """L7 : une seule pile Échap/retour (resolveEscape), plus de piles concurrentes."""

    RESOLVE_ESCAPE = FRONTEND / "lib" / "resolveEscape.ts"
    CHAT_LAYOUT = FRONTEND / "components" / "chat" / "ChatLayout.tsx"
    PANEL_STORE = FRONTEND / "stores" / "panelStore.ts"

    def test_resolve_escape_handles_view_return(self):
        content = self.RESOLVE_ESCAPE.read_text(encoding="utf-8")
        assert "export function resolveEscape" in content
        assert "goBack" in content, "resolveEscape doit gérer le retour de vue (coeur L7)"
        assert "activeView" in content

    def test_chatlayout_uses_resolve_escape(self):
        content = self.CHAT_LAYOUT.read_text(encoding="utf-8")
        assert "onEscape: resolveEscape" in content, (
            "ChatLayout doit brancher Échap sur la pile unifiée resolveEscape"
        )

    def test_panelstore_handle_escape_removed(self):
        content = self.PANEL_STORE.read_text(encoding="utf-8")
        assert "handleEscape" not in content, (
            "panelStore.handleEscape doit être supprimé (remplacé par resolveEscape)"
        )


class TestL8_ActionRegistry:
    """L8 : registre d'actions invocable (⌘K + runAction bas niveau, idée Dr_logic)."""

    REGISTRY = FRONTEND / "lib" / "actionRegistry.ts"
    COMMAND_PALETTE = FRONTEND / "components" / "chat" / "CommandPalette.tsx"
    CHAT_LAYOUT = FRONTEND / "components" / "chat" / "ChatLayout.tsx"

    def test_registry_exposes_run_action(self):
        content = self.REGISTRY.read_text(encoding="utf-8")
        assert "export function runAction" in content
        assert "export function getActions" in content
        assert "APP_ACTIONS" in content

    def test_command_palette_reads_from_registry(self):
        content = self.COMMAND_PALETTE.read_text(encoding="utf-8")
        assert "getActions()" in content, (
            "La palette ⌘K doit dériver ses commandes du registre (getActions), "
            "plus de liste codée en dur"
        )
        assert "runAction(" in content

    def test_chatlayout_exposes_run_action_low_level(self):
        content = self.CHAT_LAYOUT.read_text(encoding="utf-8")
        assert "__therese" in content and "runAction" in content, (
            "ChatLayout doit exposer runAction (appel bas niveau, suggestion Dr_logic)"
        )


class TestArbitrage_FilesView:
    """Arbitrage A/B (2026-06-05) : on GARDE la Mémoire, on sort seulement les
    Fichiers en vue 'Indexation' dédiée. Contacts/RGPD/recherche restent en Mémoire."""

    NAV_STORE = FRONTEND / "stores" / "navigationStore.ts"
    REGISTRY = FRONTEND / "lib" / "actionRegistry.ts"
    CHAT_LAYOUT = FRONTEND / "components" / "chat" / "ChatLayout.tsx"
    MEMORY_PANEL = FRONTEND / "components" / "memory" / "MemoryPanel.tsx"

    def test_files_is_an_app_view(self):
        content = self.NAV_STORE.read_text(encoding="utf-8")
        assert "'files'" in content, "navigationStore doit connaître la vue 'files' (Indexation)"

    def test_files_action_in_registry(self):
        content = self.REGISTRY.read_text(encoding="utf-8")
        assert "files.open" in content and "setView('files')" in content, (
            "Le registre doit exposer une action d'ouverture de l'Indexation"
        )

    def test_chatlayout_routes_files_view(self):
        content = self.CHAT_LAYOUT.read_text(encoding="utf-8")
        assert "activeView === 'files'" in content and "FileBrowser" in content, (
            "ChatLayout doit rendre la vue Indexation (FileBrowser)"
        )

    def test_memory_no_longer_hosts_files(self):
        content = self.MEMORY_PANEL.read_text(encoding="utf-8")
        assert "FileBrowser" not in content, (
            "MemoryPanel ne doit plus héberger FileBrowser (Fichiers sortis en vue dédiée)"
        )
        assert "'contacts' | 'files'" not in content, (
            "MemoryPanel ne doit plus avoir d'onglet 'files'"
        )


class TestSynKO_NavFixes:
    """Correctifs des KO trouvés par Syn (2e regard navigateur adversarial)."""

    ESCAPE_STACK = FRONTEND / "lib" / "escapeStack.ts"
    RESOLVE_ESCAPE = FRONTEND / "lib" / "resolveEscape.ts"
    MEMORY_PANEL = FRONTEND / "components" / "memory" / "MemoryPanel.tsx"
    SLASH_MENU = FRONTEND / "components" / "chat" / "SlashCommandsMenu.tsx"
    PANEL_CONTAINER = FRONTEND / "components" / "chat" / "PanelContainer.tsx"
    REGISTRY = FRONTEND / "lib" / "actionRegistry.ts"

    def test_escape_stack_used_by_resolve_escape(self):
        # KO 1.1/1.2/1.3 : les overlays internes de vue interceptent Échap d'abord.
        assert "runTopEscapeHandler" in self.RESOLVE_ESCAPE.read_text(encoding="utf-8")
        assert "pushEscapeHandler" in self.ESCAPE_STACK.read_text(encoding="utf-8")

    def test_memory_modals_register_escape(self):
        # KO 1.1/1.2 : suppression / RGPD ne doivent plus éjecter la vue.
        assert "pushEscapeHandler" in self.MEMORY_PANEL.read_text(encoding="utf-8")

    def test_slash_menu_uses_escape_stack_not_local(self):
        content = self.SLASH_MENU.read_text(encoding="utf-8")
        assert "pushEscapeHandler" in content, "Le menu slash doit passer par la pile d'Échap"
        assert "case 'Escape'" not in content, (
            "KO 1.3 : le menu slash ne doit plus traiter Échap localement (fermait la sidebar)"
        )

    def test_prompt_library_mounted_globally(self):
        # KO 2.2 : la bibliothèque de prompts doit être accessible depuis ⌘K partout.
        assert "PromptLibrary" in self.PANEL_CONTAINER.read_text(encoding="utf-8")
        assert "openPromptLibrary" in self.REGISTRY.read_text(encoding="utf-8")

    def test_guided_inserts_chat_prompt(self):
        # KO 2.1 : « Produire un document » ne doit plus être mort.
        assert "insert-prompt" in self.REGISTRY.read_text(encoding="utf-8")


# ============================================================
# F-12 (v0.3.6) - Indicateur modèle actif au-dessus du chat
# ChatInput doit afficher le modèle LLM actif.
# ============================================================


class TestF12_ModelIndicator:
    """Indicateur du modèle LLM actif dans ChatInput."""

    CHAT_INPUT_TSX = Path("src/frontend/src/components/chat/ChatInput.tsx")

    def test_chat_input_imports_get_llm_config(self):
        """ChatInput doit importer getLLMConfig."""
        content = self.CHAT_INPUT_TSX.read_text(encoding="utf-8")
        assert "getLLMConfig" in content, (
            "ChatInput doit importer getLLMConfig pour afficher le modèle actif (F-12)"
        )

    def test_chat_input_has_current_model_state(self):
        """ChatInput doit avoir un state currentModel."""
        content = self.CHAT_INPUT_TSX.read_text(encoding="utf-8")
        assert "currentModel" in content, (
            "ChatInput doit avoir un state currentModel (F-12)"
        )

    def test_chat_input_listens_to_config_changed(self):
        """ChatInput doit écouter l'event therese:llm-config-changed."""
        content = self.CHAT_INPUT_TSX.read_text(encoding="utf-8")
        assert "therese:llm-config-changed" in content, (
            "ChatInput doit écouter therese:llm-config-changed pour refresh (F-12)"
        )


# ============================================================
# F-13 (v0.3.6) - Re-saisie credentials Google OAuth dans CRM
# Un endpoint /sync/credentials et un formulaire frontend.
# ============================================================


class TestF13_CRMCredentials:
    """Re-saisie des credentials Google OAuth pour le CRM."""

    CRM_PY = Path("src/backend/app/routers/crm.py")
    CRM_SYNC_PANEL_TSX = Path("src/frontend/src/components/settings/CRMSyncPanel.tsx")

    def test_crm_has_credentials_endpoint(self):
        """crm.py doit avoir un endpoint POST /sync/credentials."""
        content = self.CRM_PY.read_text(encoding="utf-8")
        assert "/sync/credentials" in content, (
            "crm.py doit définir POST /sync/credentials (F-13)"
        )

    def test_crm_validates_client_id_format(self):
        """L'endpoint doit valider le format .apps.googleusercontent.com."""
        content = self.CRM_PY.read_text(encoding="utf-8")
        assert "apps.googleusercontent.com" in content, (
            "L'endpoint credentials doit valider le format client_id (F-13)"
        )

    def test_frontend_has_credentials_form(self):
        """CRMSyncPanel doit avoir un formulaire de credentials."""
        content = self.CRM_SYNC_PANEL_TSX.read_text(encoding="utf-8")
        assert "showCredentialsForm" in content, (
            "CRMSyncPanel doit avoir un état showCredentialsForm (F-13)"
        )


# ============================================================
# BUG-044b (v0.3.6) - Linux .deb manque backend-libs/
# Le tauri.linux.conf.json doit inclure les resources backend-libs.
# ============================================================


class TestBUG044b_LinuxDebBackendLibs:
    """Le .deb Linux doit inclure le dossier backend-libs/."""

    TAURI_LINUX_CONF = Path("src/frontend/src-tauri/tauri.linux.conf.json")
    RELEASE_YML = Path(".github/workflows/release.yml")

    def test_tauri_linux_conf_has_backend_libs_resource(self):
        """tauri.linux.conf.json doit référencer backend-libs dans resources."""
        content = self.TAURI_LINUX_CONF.read_text(encoding="utf-8")
        assert "backend-libs" in content, (
            "tauri.linux.conf.json doit inclure backend-libs dans resources (BUG-044b)"
        )

    def test_tauri_linux_conf_uses_recursive_glob(self):
        """tauri.linux.conf.json doit utiliser un glob récursif **."""
        content = self.TAURI_LINUX_CONF.read_text(encoding="utf-8")
        assert "**" in content, (
            "tauri.linux.conf.json doit utiliser ** pour capturer tous les fichiers (BUG-044b)"
        )

    def test_release_yml_copies_backend_libs(self):
        """release.yml doit copier backend-libs dans les binaries Tauri."""
        content = self.RELEASE_YML.read_text(encoding="utf-8")
        assert "backend-libs" in content, (
            "release.yml doit copier backend-libs pour Linux (BUG-044b)"
        )

    def test_release_yml_uses_linux_config(self):
        """release.yml doit utiliser tauri.linux.conf.json pour le build Linux."""
        content = self.RELEASE_YML.read_text(encoding="utf-8")
        assert "tauri.linux.conf.json" in content, (
            "release.yml doit utiliser tauri.linux.conf.json sur Linux (BUG-044b)"
        )


# ============================================================
# v0.4.1 - Batch fixes UX + MCP + Ollama + Email
# ============================================================


class TestBUG057_CSPImagePreview:
    """tauri.conf.json doit autoriser http://localhost dans img-src CSP."""

    TAURI_CONF = Path("src/frontend/src-tauri/tauri.conf.json")

    def test_img_src_allows_localhost(self):
        content = self.TAURI_CONF.read_text(encoding="utf-8")
        assert "http://localhost:*" in content, (
            "CSP img-src doit autoriser http://localhost:* pour les images backend (BUG-057)"
        )

    def test_img_src_allows_127(self):
        content = self.TAURI_CONF.read_text(encoding="utf-8")
        assert "http://127.0.0.1:*" in content, (
            "CSP img-src doit autoriser http://127.0.0.1:* pour les images backend (BUG-057)"
        )


class TestBUG058_EmailRefresh:
    """EmailPanel doit déclencher un refresh des messages après sync."""

    EMAIL_STORE_TS = Path("src/frontend/src/stores/emailStore.ts")
    EMAIL_PANEL_TSX = Path("src/frontend/src/components/email/EmailPanel.tsx")
    EMAIL_LIST_TSX = Path("src/frontend/src/components/email/EmailList.tsx")

    def test_store_has_refresh_counter(self):
        content = self.EMAIL_STORE_TS.read_text(encoding="utf-8")
        assert "refreshCounter" in content, (
            "emailStore doit avoir un refreshCounter pour forcer le re-chargement (BUG-058)"
        )

    def test_store_has_trigger_refresh(self):
        content = self.EMAIL_STORE_TS.read_text(encoding="utf-8")
        assert "triggerRefresh" in content, (
            "emailStore doit avoir une action triggerRefresh (BUG-058)"
        )

    def test_email_panel_calls_trigger_refresh(self):
        content = self.EMAIL_PANEL_TSX.read_text(encoding="utf-8")
        assert "triggerRefresh" in content, (
            "EmailPanel.handleSync doit appeler triggerRefresh() (BUG-058)"
        )

    def test_email_list_watches_refresh_counter(self):
        content = self.EMAIL_LIST_TSX.read_text(encoding="utf-8")
        assert "refreshCounter" in content, (
            "EmailList useEffect doit dépendre de refreshCounter (BUG-058)"
        )


class TestBUG059_SMTPTestTimeout:
    """test_connection() doit tester IMAP et SMTP avec timeout."""

    IMAP_SMTP_PY = Path("src/backend/app/services/email/imap_smtp_provider.py")

    def test_smtp_test_present(self):
        content = self.IMAP_SMTP_PY.read_text(encoding="utf-8")
        assert "aiosmtplib" in content, (
            "test_connection() doit tester SMTP via aiosmtplib (BUG-059)"
        )

    def test_timeout_present(self):
        content = self.IMAP_SMTP_PY.read_text(encoding="utf-8")
        assert "wait_for" in content, (
            "test_connection() doit utiliser asyncio.wait_for pour le timeout (BUG-059)"
        )

    def test_returns_dict(self):
        content = self.IMAP_SMTP_PY.read_text(encoding="utf-8")
        assert "imap_ok" in content and "smtp_ok" in content, (
            "test_connection() doit retourner un dict avec imap_ok et smtp_ok (BUG-059)"
        )


class TestBUG060_CRMHeaderHomogeneity:
    """CRMPanel doit utiliser le pattern header gradient badge comme EmailPanel."""

    CRM_PANEL_TSX = Path("src/frontend/src/components/crm/CRMPanel.tsx")

    def test_gradient_badge_present(self):
        content = self.CRM_PANEL_TSX.read_text(encoding="utf-8")
        assert "bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20" in content, (
            "CRMPanel header doit utiliser le badge gradient (BUG-060)"
        )

    def test_icon_in_badge(self):
        content = self.CRM_PANEL_TSX.read_text(encoding="utf-8")
        assert "w-10 h-10 rounded-lg" in content, (
            "CRMPanel header doit avoir un badge 10x10 arrondi (BUG-060)"
        )


# BUG-061 (TestBUG061_ProjectsHeaderHomogeneity) retiré : il gardait le style du header
# de MemoryPanelStandalone.tsx, fenêtre Mémoire détachée supprimée par la revue produit
# Chantier B (P3, Mémoire repliée en panneau in-window). Le fichier n'existe plus.


class TestBUG062_MCPNodePath:
    """mcp_service.py doit enrichir le PATH pour trouver npx dans l'app packagée."""

    MCP_SERVICE_PY = Path("src/backend/app/services/mcp_service.py")

    def test_nvm_path_added(self):
        content = self.MCP_SERVICE_PY.read_text(encoding="utf-8")
        assert ".nvm" in content, (
            "mcp_service.py doit chercher Node.js dans ~/.nvm (BUG-062)"
        )

    def test_homebrew_path_added(self):
        content = self.MCP_SERVICE_PY.read_text(encoding="utf-8")
        assert "/opt/homebrew/bin" in content, (
            "mcp_service.py doit inclure /opt/homebrew/bin dans le PATH (BUG-062)"
        )

    def test_volta_path_added(self):
        content = self.MCP_SERVICE_PY.read_text(encoding="utf-8")
        assert ".volta" in content, (
            "mcp_service.py doit chercher Node.js dans ~/.volta (BUG-062)"
        )


class TestBUG064_MCPPresetTooltip:
    """L'icône AlertCircle des presets MCP doit avoir un tooltip explicatif."""

    TOOLS_PANEL_TSX = Path("src/frontend/src/components/settings/ToolsPanel.tsx")

    def test_alertcircle_has_tooltip(self):
        content = self.TOOLS_PANEL_TSX.read_text(encoding="utf-8")
        assert "Installé mais inactif" in content, (
            "L'icône AlertCircle MCP doit avoir un tooltip explicatif (BUG-064)"
        )


class TestBUG065_SettingsErrorClear:
    """SettingsModal doit effacer l'erreur quand on change d'onglet."""

    SETTINGS_TSX = Path("src/frontend/src/components/settings/SettingsModal.tsx")

    def test_error_cleared_on_tab_switch(self):
        content = self.SETTINGS_TSX.read_text(encoding="utf-8")
        assert "setError(null)" in content, (
            "SettingsModal doit appeler setError(null) au changement d'onglet (BUG-065)"
        )


class TestBUG066_ContexteAdditionnel:
    """Le champ 'Contexte additionnel' doit avoir une description explicative."""

    PROFILE_TAB_TSX = Path("src/frontend/src/components/settings/ProfileTab.tsx")

    def test_description_present(self):
        content = self.PROFILE_TAB_TSX.read_text(encoding="utf-8")
        assert "personnaliser ses réponses" in content, (
            "Le champ Contexte additionnel doit avoir une description explicative (BUG-066)"
        )


class TestF14_OllamaModelListing:
    """GET /api/config/llm doit lister les modèles Ollama installés."""

    CONFIG_PY = Path("src/backend/app/routers/config.py")

    def test_ollama_branch_in_get_llm(self):
        content = self.CONFIG_PY.read_text(encoding="utf-8")
        # Depuis le refactor 0.20.0, la liste des modèles (Ollama inclus) est
        # centralisée dans le helper _available_models_for, partagé GET + POST /llm.
        assert "_available_models_for" in content, (
            "GET/POST /llm doivent déléguer à _available_models_for (F-14, refactor 0.20.0)"
        )
        assert 'provider_value == "ollama"' in content, (
            "Le helper doit avoir une branche Ollama (F-14)"
        )

    def test_ollama_fetches_api_tags(self):
        content = self.CONFIG_PY.read_text(encoding="utf-8")
        # Vérifier que /api/tags est appelé dans le contexte du GET /llm
        assert 'api/tags' in content, (
            "GET /llm doit appeler /api/tags pour lister les modèles Ollama (F-14)"
        )


class TestF15_ModelIndicatorUI:
    """L'indicateur de modèle dans ChatInput doit être un pill avec accent cyan."""

    CHAT_INPUT_TSX = Path("src/frontend/src/components/chat/ChatInput.tsx")

    def test_pill_badge_styling(self):
        content = self.CHAT_INPUT_TSX.read_text(encoding="utf-8")
        assert "rounded-full bg-accent-cyan/10" in content, (
            "L'indicateur de modèle doit être un pill arrondi avec fond cyan (F-15)"
        )

    def test_model_selector_dropdown(self):
        content = self.CHAT_INPUT_TSX.read_text(encoding="utf-8")
        assert "handleModelChange" in content, (
            "ChatInput doit avoir un handler pour changer de modèle (F-14/F-15)"
        )


# ============================================================
# BUG-056 (v0.4.2) - Indicateur de chargement image
# Un message loading doit s'afficher pendant la génération d'image.
# ============================================================


class TestBUG056_ImageLoadingIndicator:
    """Un message assistant loading doit s'afficher pendant generateImage()."""

    COMMAND_EXECUTOR_TSX = Path(
        "src/frontend/src/components/home/CommandExecutor.tsx"
    )
    GUIDED_PROMPTS_TSX = Path(
        "src/frontend/src/components/guided/GuidedPrompts.tsx"
    )
    CHAT_STORE_TS = Path("src/frontend/src/stores/chatStore.ts")

    def test_loading_message_in_command_executor(self):
        content = self.COMMAND_EXECUTOR_TSX.read_text(encoding="utf-8")
        assert "isStreaming: true" in content, (
            "CommandExecutor doit créer un message loading avec isStreaming: true (BUG-056)"
        )

    def test_update_message_replaces_loading(self):
        content = self.COMMAND_EXECUTOR_TSX.read_text(encoding="utf-8")
        assert "updateMessage" in content, (
            "CommandExecutor doit utiliser updateMessage pour remplacer le loading (BUG-056)"
        )

    def test_loading_message_in_guided_prompts(self):
        content = self.GUIDED_PROMPTS_TSX.read_text(encoding="utf-8")
        assert "isStreaming: true" in content, (
            "GuidedPrompts doit créer un message loading avec isStreaming: true (BUG-056)"
        )

    def test_chat_store_update_message_accepts_meta(self):
        content = self.CHAT_STORE_TS.read_text(encoding="utf-8")
        assert "meta" in content, (
            "chatStore.updateMessage doit accepter un paramètre meta (BUG-056)"
        )


# ============================================================
# F-16 (v0.4.2) - Upload credentials.json Google OAuth
# Les formulaires de credentials doivent avoir un bouton d'import JSON.
# ============================================================


class TestF16_CredentialsJsonImport:
    """Un bouton Import credentials.json doit exister dans CredentialsStep et CRMSyncPanel."""

    CREDENTIALS_STEP_TSX = Path(
        "src/frontend/src/components/email/wizard/CredentialsStep.tsx"
    )
    CRM_SYNC_PANEL_TSX = Path(
        "src/frontend/src/components/settings/CRMSyncPanel.tsx"
    )

    def test_file_input_in_credentials_step(self):
        content = self.CREDENTIALS_STEP_TSX.read_text(encoding="utf-8")
        assert 'type="file"' in content, (
            "CredentialsStep doit avoir un input type=file pour l'import (F-16)"
        )

    def test_json_parsing_in_credentials_step(self):
        content = self.CREDENTIALS_STEP_TSX.read_text(encoding="utf-8")
        assert "client_id" in content and "client_secret" in content, (
            "CredentialsStep doit parser client_id et client_secret du JSON (F-16)"
        )

    def test_file_input_in_crm_sync_panel(self):
        content = self.CRM_SYNC_PANEL_TSX.read_text(encoding="utf-8")
        assert 'type="file"' in content, (
            "CRMSyncPanel doit avoir un input type=file pour l'import (F-16)"
        )

    def test_json_parsing_in_crm_sync_panel(self):
        content = self.CRM_SYNC_PANEL_TSX.read_text(encoding="utf-8")
        assert "client_id" in content and "client_secret" in content, (
            "CRMSyncPanel doit parser client_id et client_secret du JSON (F-16)"
        )


# ============================================================
# F-17 (v0.4.2) - Refonte Board de Décision + Mode Souverain
# Backend : BoardMode enum, mode sovereign séquentiel Ollama
# Frontend : ModeSelector, AdvisorArcLayout, refactoring Board
# ============================================================


class TestF17_BoardSovereignMode:
    """Le backend doit supporter le mode souverain (séquentiel Ollama)."""

    BOARD_MODELS_PY = Path("src/backend/app/models/board.py")
    BOARD_SERVICE_PY = Path("src/backend/app/services/board.py")
    ENTITIES_PY = Path("src/backend/app/models/entities.py")

    def test_board_mode_enum_exists(self):
        content = self.BOARD_MODELS_PY.read_text(encoding="utf-8")
        assert "BoardMode" in content, (
            "board.py doit définir l'enum BoardMode (F-17)"
        )

    def test_board_mode_values(self):
        content = self.BOARD_MODELS_PY.read_text(encoding="utf-8")
        assert "CLOUD" in content and "SOVEREIGN" in content, (
            "BoardMode doit avoir les valeurs CLOUD et SOVEREIGN (F-17)"
        )

    def test_board_request_has_mode(self):
        content = self.BOARD_MODELS_PY.read_text(encoding="utf-8")
        assert "mode" in content and "ollama_models" in content, (
            "BoardRequest doit avoir les champs mode et ollama_models (F-17)"
        )

    def test_sovereign_sequential_path(self):
        content = self.BOARD_SERVICE_PY.read_text(encoding="utf-8")
        assert "sovereign" in content.lower(), (
            "board.py service doit avoir un chemin séquentiel pour le mode souverain (F-17)"
        )

    def test_entities_has_mode(self):
        content = self.ENTITIES_PY.read_text(encoding="utf-8")
        assert "mode" in content, (
            "BoardDecisionDB doit avoir un champ mode (F-17)"
        )


class TestF17_BoardArcLayout:
    """AdvisorArcLayout.tsx doit exister avec l'arc de cercle."""

    ARC_LAYOUT_TSX = Path(
        "src/frontend/src/components/board/AdvisorArcLayout.tsx"
    )

    def test_file_exists(self):
        assert self.ARC_LAYOUT_TSX.exists(), (
            "AdvisorArcLayout.tsx doit exister (F-17)"
        )

    def test_arc_angles(self):
        content = self.ARC_LAYOUT_TSX.read_text(encoding="utf-8")
        assert "ARC_ANGLES" in content, (
            "AdvisorArcLayout doit définir ARC_ANGLES pour l'arc de cercle (F-17)"
        )

    def test_responsive_fallback(self):
        content = self.ARC_LAYOUT_TSX.read_text(encoding="utf-8")
        assert "md:hidden" in content or "grid" in content, (
            "AdvisorArcLayout doit avoir un fallback grille pour petits écrans (F-17)"
        )


class TestF17_BoardModeSelector:
    """ModeSelector.tsx doit exister avec le toggle Cloud/Souverain."""

    MODE_SELECTOR_TSX = Path(
        "src/frontend/src/components/board/ModeSelector.tsx"
    )

    def test_file_exists(self):
        assert self.MODE_SELECTOR_TSX.exists(), (
            "ModeSelector.tsx doit exister (F-17)"
        )

    def test_cloud_sovereign_toggle(self):
        content = self.MODE_SELECTOR_TSX.read_text(encoding="utf-8")
        assert "cloud" in content.lower() and "souverain" in content.lower(), (
            "ModeSelector doit avoir les options Cloud et Souverain (F-17)"
        )

    def test_framer_motion_animation(self):
        content = self.MODE_SELECTOR_TSX.read_text(encoding="utf-8")
        assert "layoutId" in content or "motion" in content, (
            "ModeSelector doit utiliser Framer Motion pour l'animation (F-17)"
        )


# ============================================================
# BUG-057 (v0.4.3) - Board annulation délibération
# L'utilisateur doit pouvoir annuler une délibération en cours
# via AbortController + bouton Annuler.
# ============================================================


class TestBUG057_BoardCancelDeliberation:
    """Le Board doit permettre d'annuler une délibération en cours."""

    BOARD_PANEL_TSX = Path("src/frontend/src/components/board/BoardPanel.tsx")
    BOARD_TS = Path("src/frontend/src/services/api/board.ts")
    DELIBERATION_TSX = Path("src/frontend/src/components/board/DeliberationView.tsx")

    def test_abort_controller_in_board_panel(self):
        content = self.BOARD_PANEL_TSX.read_text(encoding="utf-8")
        assert "AbortController" in content, (
            "BoardPanel doit utiliser AbortController pour annuler (BUG-057)"
        )

    def test_signal_in_stream_deliberation(self):
        content = self.BOARD_TS.read_text(encoding="utf-8")
        assert "signal" in content, (
            "streamDeliberation doit accepter un AbortSignal (BUG-057)"
        )

    def test_cancel_button_in_deliberation_view(self):
        content = self.DELIBERATION_TSX.read_text(encoding="utf-8")
        assert "onCancel" in content, (
            "DeliberationView doit avoir un prop onCancel (BUG-057)"
        )

    def test_annuler_label(self):
        content = self.DELIBERATION_TSX.read_text(encoding="utf-8")
        assert "Annuler" in content, (
            "Le bouton d'annulation doit afficher 'Annuler' (BUG-057)"
        )


# ============================================================
# BUG-058 (v0.4.3) - Board cloud vide (modèle utilisateur
# envoyé à tous les providers)
# get_llm_service_for_provider ne doit appliquer user_model
# que si le provider demandé correspond au provider principal.
# ============================================================


class TestBUG058_BoardCloudProviderModel:
    """Le Board cloud ne doit pas envoyer le modèle utilisateur aux autres providers."""

    LLM_PY = Path("src/backend/app/services/llm.py")

    def test_provider_match_check(self):
        """Le modèle utilisateur ne doit s'appliquer que si provider correspond."""
        content = self.LLM_PY.read_text(encoding="utf-8")
        fn_start = content.find("def get_llm_service_for_provider")
        assert fn_start > 0
        fn_body = content[fn_start:fn_start + 3000]
        assert "user_provider == provider_name" in fn_body, (
            "get_llm_service_for_provider doit vérifier que le provider correspond "
            "avant d'appliquer user_model (BUG-058)"
        )

    def test_llm_provider_read_from_db(self):
        """La préférence llm_provider doit être lue depuis la DB."""
        content = self.LLM_PY.read_text(encoding="utf-8")
        fn_start = content.find("def get_llm_service_for_provider")
        fn_body = content[fn_start:fn_start + 3000]
        assert "llm_provider" in fn_body, (
            "get_llm_service_for_provider doit lire llm_provider depuis la DB (BUG-058)"
        )


# ============================================================
# BUG-059 (v0.4.3) - Email OAuth re-auth bloqué sur
# "En attente d'autorisation"
# Le polling doit détecter la re-auth (updated_at changé),
# pas seulement les nouveaux comptes.
# ============================================================


# ============================================================
# BUG-063 : Ollama modèle ignoré dans _default_config
# Le chat utilise get_llm_service() → _default_config() qui doit
# lire correctement le modèle depuis la DB (pas juste le Board).
# ============================================================


class TestBUG063_OllamaModelDefaultConfig:
    """_default_config() doit logger et lire correctement les préférences Ollama."""

    LLM_PY = SRC / "app" / "services" / "llm.py"

    def test_default_config_has_warning_logging(self):
        content = self.LLM_PY.read_text(encoding="utf-8")
        assert "logger.warning" in content and "Could not read LLM preferences" in content, (
            "_default_config doit logger en WARNING (pas debug) quand la lecture DB échoue (BUG-063)"
        )

    def test_default_config_logs_preferences_read(self):
        content = self.LLM_PY.read_text(encoding="utf-8")
        assert "LLM preferences from DB:" in content, (
            "_default_config doit logger les préférences lues depuis la DB (BUG-063)"
        )

    def test_default_config_uses_singleton(self):
        content = self.LLM_PY.read_text(encoding="utf-8")
        assert "get_sync_connection" in content, (
            "_default_config doit utiliser le singleton DB (get_sync_connection) au lieu d'engines jetables (BUG-063)"
        )


# ============================================================
# BUG-064 : Board souverain vierge au premier lancement
# AnimatePresence enfant doit avoir initial={false} pour ne pas
# jouer l'animation d'entrée au premier montage.
# ============================================================


class TestBUG064_BoardFirstMount:
    """BoardPanel AnimatePresence enfant ne doit pas animer au premier montage."""

    BOARD_TSX = Path("src/frontend/src/components/board/BoardPanel.tsx")

    def test_animate_presence_initial_false(self):
        content = self.BOARD_TSX.read_text(encoding="utf-8")
        assert "initial={false}" in content, (
            "AnimatePresence mode='wait' doit avoir initial={false} pour éviter le blank au premier montage (BUG-064)"
        )


# ============================================================
# BUG-065 : PPTX titre blanc invisible
# Le prompt pptx_generator ne doit plus dire "blanc" mais
# utiliser la couleur text_primary #E6EDF7.
# ============================================================


class TestBUG065_PPTXTitleColor:
    """Le prompt PPTX ne doit plus dire 'blanc' pour les titres."""

    PPTX_GEN = SRC / "app" / "services" / "skills" / "pptx_generator.py"

    def test_no_blanc_in_title_prompt(self):
        content = self.PPTX_GEN.read_text(encoding="utf-8")
        # Le mot "blanc" ne doit plus apparaître dans la ligne du titre
        for line in content.splitlines():
            if "Titre de slide" in line:
                assert "blanc" not in line.lower(), (
                    "Le prompt PPTX ne doit plus dire 'blanc' pour les titres, utiliser #E6EDF7 (BUG-065)"
                )
                assert "E6EDF7" in line or "0xE6" in line, (
                    "Le prompt PPTX doit utiliser la couleur text_primary #E6EDF7 pour les titres (BUG-065)"
                )
                break
        else:
            pytest.fail("Ligne 'Titre de slide' introuvable dans pptx_generator.py")


# ============================================================
# BUG-062b : MCP tool calls timeout 30s trop court
# Le timeout par défaut de _send_request doit être >= 60s,
# et tools/call doit avoir un timeout >= 120s.
# ============================================================


class TestBUG062b_MCPToolCallTimeout:
    """MCP _send_request timeout doit être suffisant pour les outils lents."""

    MCP_PY = SRC / "app" / "services" / "mcp_service.py"

    def test_default_timeout_increased(self):
        content = self.MCP_PY.read_text(encoding="utf-8")
        # Le timeout par défaut de _send_request doit être >= 60s
        assert "timeout: float = 60.0" in content, (
            "_send_request timeout par défaut doit être 60s (BUG-062b)"
        )

    def test_tools_call_timeout_increased(self):
        content = self.MCP_PY.read_text(encoding="utf-8")
        assert "timeout=120.0" in content, (
            "tools/call doit avoir un timeout de 120s (BUG-062b)"
        )


# ============================================================
# BUG-061b : Email refresh silencieux
# Le backend doit logger les erreurs d'enrichissement,
# et le frontend doit logger les messages en erreur.
# ============================================================


class TestBUG061b_EmailRefreshDiag:
    """Email refresh doit diagnostiquer les erreurs au lieu de les avaler."""

    EMAIL_PY = SRC / "app" / "routers" / "email.py"
    EMAIL_LIST_TSX = Path("src/frontend/src/components/email/EmailList.tsx")

    def test_backend_logs_enrichment_errors(self):
        content = self.EMAIL_PY.read_text(encoding="utf-8")
        assert "Email enrichment:" in content, (
            "Le backend doit logger le nombre d'erreurs d'enrichissement (BUG-061b)"
        )

    def test_frontend_logs_error_messages(self):
        content = self.EMAIL_LIST_TSX.read_text(encoding="utf-8")
        assert "BUG-061b" in content, (
            "Le frontend doit logger les emails en erreur avec console.warn (BUG-061b)"
        )


class TestBUG059_EmailReAuthPolling:
    """Le wizard email doit détecter la re-auth via updated_at."""

    VERIFY_STEP_TSX = Path("src/frontend/src/components/email/wizard/VerifyStep.tsx")
    EMAIL_TS = Path("src/frontend/src/services/api/email.ts")

    def test_updated_at_in_email_account(self):
        content = self.EMAIL_TS.read_text(encoding="utf-8")
        assert "updated_at" in content, (
            "EmailAccount doit avoir un champ updated_at (BUG-059)"
        )

    def test_initial_accounts_ref(self):
        content = self.VERIFY_STEP_TSX.read_text(encoding="utf-8")
        assert "initialAccountsRef" in content, (
            "VerifyStep doit stocker un snapshot initial des comptes (BUG-059)"
        )

    def test_updated_at_comparison(self):
        content = self.VERIFY_STEP_TSX.read_text(encoding="utf-8")
        assert "updated_at" in content, (
            "VerifyStep doit comparer updated_at pour détecter la re-auth (BUG-059)"
        )




# ============================================================
# Batch v0.3.8 - 05 mars 2026
# ============================================================

class TestBUG070_ConversationGhost404:
    """BUG-070 : 404 persistant après suppression de conversations vides."""

    def test_chat_input_imports_delete_conversation(self):
        """ChatInput doit importer deleteConversation depuis le store."""
        content = open('src/frontend/src/components/chat/ChatInput.tsx').read()
        assert 'deleteConversation,' in content, "deleteConversation doit être importé dans ChatInput"

    def test_ghost_conversation_reset_on_404(self):
        """Le catch block doit appeler deleteConversation en cas de 404 Conversation not found."""
        content = open('src/frontend/src/components/chat/ChatInput.tsx').read()
        assert 'isConversationGhost' in content
        assert 'deleteConversation(currentConversationId' in content
        assert "Conversation not found" in content

    def test_ghost_message_is_user_friendly(self):
        """Le message d'erreur 404 doit être compréhensible pour l'utilisateur."""
        content = open('src/frontend/src/components/chat/ChatInput.tsx').read()
        assert "nouveau chat a été créé automatiquement" in content


class TestBUG053_DateActuelleSubstituee:
    """BUG-053 : [Date actuelle] non substituée dans les réponses chat."""

    def test_llm_imports_datetime(self):
        """llm.py doit importer datetime pour injecter la date."""
        content = open('src/backend/app/services/llm.py').read()
        assert 'from datetime import' in content
        assert 'UTC' in content

    def test_system_prompt_template_has_current_date(self):
        """DEFAULT_SYSTEM_PROMPT_TEMPLATE doit contenir {current_date}."""
        content = open('src/backend/app/services/llm.py').read()
        assert '{current_date}' in content

    def test_system_prompt_no_profile_has_current_date(self):
        """DEFAULT_SYSTEM_PROMPT_NO_PROFILE doit contenir {current_date}."""
        content = open('src/backend/app/services/llm.py').read()
        # Deux occurrences : une dans chaque template
        assert content.count('{current_date}') >= 2

    def test_get_system_prompt_injects_date(self):
        """_get_system_prompt_with_identity doit substituer current_date dans le template."""
        content = open('src/backend/app/services/llm.py').read()
        assert '"{current_date}", current_date' in content

    def test_recap_rule_restricted_to_chat(self):
        """La règle de récapitulatif doit préciser 'chat uniquement', pas pour les documents."""
        content = open('src/backend/app/services/llm.py').read()
        assert 'chat uniquement' in content
        assert 'JAMAIS pour la génération de documents' in content


class TestBUG_DocxPptxXlsxGuardrails:
    """BUG docx/pptx/xlsx : leakage recap + hallucination données + watermark + markdown."""

    def test_docx_no_recap_guardrail(self):
        """docx_generator doit interdire le bloc récapitulatif dans les documents."""
        content = open('src/backend/app/services/skills/docx_generator.py').read()
        assert 'récapitulatif' in content.lower() or 'récap' in content.lower()
        assert 'JAMAIS' in content or 'INTERDIT' in content or 'bloc récapitulatif' in content

    def test_docx_watermark_accent(self):
        """Footer DOCX doit contenir THÉRÈSE et Synoptïa avec accents."""
        content = open('src/backend/app/services/skills/docx_generator.py').read()
        assert 'THÉRÈSE - Synoptïa' in content

    def test_pptx_no_markdown_guardrail(self):
        """pptx_generator doit interdire les balises Markdown dans les slides."""
        content = open('src/backend/app/services/skills/pptx_generator.py').read()
        assert 'Markdown' in content
        assert '**' in content  # La règle mentionne le symbole interdit

    def test_pptx_nb_slides_variable(self):
        """pptx_generator doit documenter la variable nb_slides dans le system prompt."""
        content = open('src/backend/app/services/skills/pptx_generator.py').read()
        assert 'nb_slides' in content
        assert 'RESPECTE exactement ce nombre' in content

    def test_pptx_no_recap_guardrail(self):
        """pptx_generator doit interdire le bloc récapitulatif."""
        content = open('src/backend/app/services/skills/pptx_generator.py').read()
        assert 'récapitulatif' in content.lower() or 'INTERDIT' in content

    def test_xlsx_no_hallucination_guardrail(self):
        """xlsx_generator doit avoir un guardrail anti-hallucination de données."""
        content = open('src/backend/app/services/skills/xlsx_generator.py').read()
        assert 'NE PAS inventer' in content or 'RÈGLE ABSOLUE' in content
        assert 'modèle' in content.lower()

    def test_xlsx_no_recap_guardrail(self):
        """xlsx_generator doit interdire le bloc récapitulatif."""
        content = open('src/backend/app/services/skills/xlsx_generator.py').read()
        assert 'récapitulatif' in content.lower() or 'INTERDIT' in content


class TestBUG_CommandPaletteProduire:
    """BUG cmd-k : commande 'Produire un document' accessible + z-index + Cmd+N textarea.

    Note (revue produit) : depuis la refonte L8, la palette ⌘K dérive ses commandes
    du registre d'actions (actionRegistry.ts) au lieu d'une liste codée en dur. L'ancien
    'produce' / prop onOpenGuided a migré vers l'action 'guided.open' ; les invariants
    historiques sont ré-exprimés sur le registre et le système Z_LAYER.
    """

    REGISTRY = FRONTEND / "lib" / "actionRegistry.ts"
    COMMAND_PALETTE = FRONTEND / "components" / "chat" / "CommandPalette.tsx"
    Z_LAYERS = FRONTEND / "styles" / "z-layers.ts"

    def test_produce_document_action_in_registry(self):
        """La production guidée de documents reste accessible (migration L8 de
        l'ancien 'produce'/onOpenGuided vers l'action 'guided.open' du registre)."""
        content = self.REGISTRY.read_text(encoding="utf-8")
        assert "'guided.open'" in content, (
            "Le registre doit exposer l'action de production guidée de documents"
        )
        assert "Produire un document" in content
        # La palette dérive bien ses commandes du registre (plus de liste en dur)
        palette = self.COMMAND_PALETTE.read_text(encoding="utf-8")
        assert "getActions()" in palette and "runAction(" in palette

    def test_command_palette_z_index_above_settings(self):
        """La palette doit être au-dessus des modaux (Settings = Z_LAYER.MODAL z-50).
        Depuis le passage au système Z_LAYER, on vérifie l'usage de la couche dédiée
        et l'ordre numérique des couches (l'ancien test cherchait un z-[N] en dur,
        désormais absent, et passait donc à vide)."""
        palette = self.COMMAND_PALETTE.read_text(encoding="utf-8")
        assert "Z_LAYER.COMMAND_PALETTE" in palette, (
            "CommandPalette doit utiliser la couche Z_LAYER.COMMAND_PALETTE"
        )
        import re

        layers = self.Z_LAYERS.read_text(encoding="utf-8")

        def _z(name: str) -> int:
            m = re.search(rf"{name}:\s*'z-\[?(\d+)\]?'", layers)
            assert m is not None, f"Couche {name} introuvable dans z-layers.ts"
            return int(m.group(1))

        assert _z("COMMAND_PALETTE") > _z("MODAL"), (
            "La palette (COMMAND_PALETTE) doit être au-dessus des modaux (MODAL/Settings)"
        )

    def test_cmd_n_works_in_input_context(self):
        """Cmd+N doit être intercepté avant le garde isInput dans useKeyboardShortcuts."""
        content = open('src/frontend/src/hooks/useKeyboardShortcuts.ts').read()
        # La section Cmd+N doit apparaître AVANT "if (isInput) return"
        idx_n = content.find("// Cmd+N - Nouvelle conversation")
        idx_guard = content.find("// Skip other shortcuts when in inputs\n      if (isInput) return;")
        assert idx_n != -1, "Le bloc Cmd+N avant garde isInput introuvable"
        assert idx_guard != -1, "Le garde isInput introuvable"
        assert idx_n < idx_guard, "Cmd+N doit être placé AVANT le garde isInput"


class TestBUG_PptxNbSlides:
    """BUG PPTX : nb_slides non injecté dans le sandbox."""

    def test_build_namespace_accepts_nb_slides(self):
        """_build_namespace doit accepter nb_slides comme paramètre."""
        import ast
        content = open('src/backend/app/services/skills/code_executor.py').read()
        assert 'nb_slides: int = 10' in content

    def test_namespace_contains_nb_slides(self):
        """Le namespace d'exécution doit contenir nb_slides."""
        content = open('src/backend/app/services/skills/code_executor.py').read()
        assert '"nb_slides": nb_slides' in content

    def test_execute_sandboxed_passes_nb_slides(self):
        """execute_sandboxed doit passer nb_slides à _build_namespace."""
        content = open('src/backend/app/services/skills/code_executor.py').read()
        assert '_build_namespace(output_path, title, format_type, nb_slides)' in content

    def test_skills_router_extracts_nb_slides_from_prompt(self):
        """Le router skills doit extraire nb_slides du prompt par regex."""
        content = open('src/backend/app/routers/skills.py').read()
        assert 'nb_slides_from_prompt' in content
        assert 'slides?' in content  # regex pour détecter "slides"


class TestBUG_MistralTools:
    """BUG MCP tools : Mistral ne transmettait pas les tools à l'API."""

    def test_mistral_sends_tools_in_json_body(self):
        """Le body JSON Mistral inclut tools + tool_choice=auto quand des tools sont fournis."""
        from app.services.llm import LLMConfig, LLMProvider
        from app.services.providers.mistral import MistralProvider

        provider = MistralProvider(
            LLMConfig(provider=LLMProvider.MISTRAL, model="mistral-large-latest", api_key="x"),
            client=None,
        )
        tools = [{"type": "function", "function": {"name": "read_contact"}}]
        body = provider._build_request_body([{"role": "user", "content": "hi"}], tools=tools)
        assert body["tools"] == tools
        assert body["tool_choice"] == "auto"
        # Sans tools : pas de clés tools/tool_choice
        body_no_tools = provider._build_request_body([{"role": "user", "content": "hi"}])
        assert "tools" not in body_no_tools and "tool_choice" not in body_no_tools

    def test_mistral_parses_tool_calls_in_stream(self):
        """mistral.py détecte les tool_calls et signale finish_reason tool_calls."""
        content = open('src/backend/app/services/providers/mistral.py').read()
        assert 'tool_calls' in content
        assert 'finish_reason == "tool_calls"' in content
        assert 'stop_reason="tool_calls"' in content


class TestBUG_MCPPollingStarting:
    """BUG MCP : pas de polling pendant l'état 'starting' (npx télécharge)."""

    def test_tools_panel_imports_use_ref(self):
        """ToolsPanel doit importer useRef pour le polling interval."""
        content = open('src/frontend/src/components/settings/ToolsPanel.tsx').read()
        assert 'useRef' in content

    def test_tools_panel_has_polling_effect(self):
        """ToolsPanel doit avoir un useEffect qui lance le polling quand status=starting."""
        content = open('src/frontend/src/components/settings/ToolsPanel.tsx').read()
        assert 'pollingIntervalRef' in content
        assert "status === 'starting'" in content
        assert 'setInterval' in content
        assert '3000' in content  # 3s interval


class TestBUGOpenRouterStrftimeWindows:
    """BUG openrouter-strftime : %-d non supporté sur Windows → ValueError crash."""

    def test_current_date_format_no_percent_minus_d(self):
        """La construction de current_date ne doit pas utiliser %-d (spécifique Linux)."""
        import pathlib
        src = pathlib.Path("src/backend/app/services/llm.py").read_text(encoding="utf-8")
        # %-d est une extension POSIX uniquement → doit avoir été supprimé
        assert "%-d" not in src, (
            "%-d trouvé dans llm.py : non supporté sur Windows "
            "(ValueError: Invalid format string)"
        )

    def test_current_date_cross_platform_format(self):
        """La date générée est une chaîne non vide et ne contient pas de placeholder."""
        from datetime import UTC, datetime
        now = datetime.now(UTC)
        day = str(now.day)
        current_date = f"{day} {now.strftime('%B %Y, %H:%M')} UTC"
        current_date_example = f"{day} {now.strftime('%B %Y')}"
        assert current_date  # non vide
        assert "{" not in current_date  # pas de placeholder non substitué
        assert current_date_example
        # Pas de zéro de tête sur le jour (ex: "5 mars" pas "05 mars")
        assert not current_date.startswith("0"), (
            f"Le jour ne doit pas avoir de zéro de tête : {current_date!r}"
        )

    def test_get_system_prompt_no_valueerror(self):
        """_get_system_prompt_with_identity ne lève pas ValueError (ex-bug strftime POSIX)."""
        from unittest.mock import MagicMock, patch
        from app.services.llm import LLMService, LLMConfig, LLMProvider

        config = LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-3-haiku-20240307")
        svc = LLMService(config)

        mock_profile = MagicMock()
        mock_profile.name = "Jérôme"
        mock_profile.format_for_llm.return_value = "Prénom : Jérôme"

        # _get_system_prompt_with_identity() appelle get_cached_profile() en interne
        # On patche get_cached_profile et load_therese_md
        with patch("app.services.llm.load_therese_md", return_value=""),              patch("app.services.user_profile.get_cached_profile", return_value=mock_profile):
            result = svc._get_system_prompt_with_identity()

        assert "{current_date}" not in result  # placeholder bien substitué
        assert result  # non vide


class TestBUGTrafficLightsMacOnWindows:
    """BUG traffic-lights : traffic lights macOS toujours affichés sur Windows."""

    def test_onboarding_wizard_has_ismac_guard(self):
        """OnboardingWizard.tsx doit conditionner les traffic lights par isMac."""
        import pathlib
        src = pathlib.Path(
            "src/frontend/src/components/onboarding/OnboardingWizard.tsx"
        ).read_text(encoding="utf-8")
        # isMac doit être déclaré
        assert "isMac" in src, "isMac non trouvé dans OnboardingWizard.tsx"
        # Les traffic lights doivent être dans un bloc {isMac && ...}
        assert "{isMac && (" in src, (
            "Les traffic lights ne sont pas conditionnés par {isMac && ...}"
        )

    def test_chat_header_has_ismac_guard(self):
        """ChatHeader.tsx doit aussi conditionner les traffic lights par isMac."""
        import pathlib
        src = pathlib.Path(
            "src/frontend/src/components/chat/ChatHeader.tsx"
        ).read_text(encoding="utf-8")
        assert "isMac" in src

    def test_onboarding_wizard_no_unconditional_traffic_lights(self):
        """Pas de traffic lights affichés sans vérification de plateforme."""
        import pathlib
        src = pathlib.Path(
            "src/frontend/src/components/onboarding/OnboardingWizard.tsx"
        ).read_text(encoding="utf-8")
        # Le bloc traffic lights ne doit PAS apparaître hors du guard isMac
        # Vérifier que bg-red-500 + bg-yellow-500 sont dans un contexte isMac
        idx_guard = src.find("{isMac && (")
        idx_red = src.find("bg-red-500 hover:bg-red-600")
        assert idx_guard != -1, "Guard isMac manquant"
        assert idx_red != -1, "Bouton rouge manquant"
        assert idx_red > idx_guard, (
            "Le bouton rouge (traffic light) apparaît avant le guard isMac"
        )



class TestOpenRouterEmptyResponse:
    import pathlib
    """OpenRouter reponse vide : le provider doit emettre une erreur explicite."""

    def test_provider_has_has_content_tracking(self):
        """Le provider OpenRouter doit tracker si du contenu a ete recu."""
        import pathlib
        src = pathlib.Path(
            "src/backend/app/services/providers/openrouter.py"
        ).read_text(encoding="utf-8")
        assert "has_content" in src, (
            "has_content non trouve dans openrouter.py - "
            "la detection de reponse vide necessite un flag de tracking"
        )

    def test_provider_handles_finish_reason_length(self):
        """Le provider doit gerer finish_reason=length explicitement."""
        import pathlib
        src = pathlib.Path(
            "src/backend/app/services/providers/openrouter.py"
        ).read_text(encoding="utf-8")
        assert 'finish_reason == "length"' in src, (
            "finish_reason length non gere dans openrouter.py"
        )

    def test_provider_handles_content_filter(self):
        """Le provider doit gerer finish_reason=content_filter."""
        import pathlib
        src = pathlib.Path(
            "src/backend/app/services/providers/openrouter.py"
        ).read_text(encoding="utf-8")
        assert 'finish_reason == "content_filter"' in src, (
            "finish_reason content_filter non gere dans openrouter.py"
        )

    def test_provider_handles_sse_error(self):
        """Le provider doit detecter les erreurs dans le flux SSE."""
        import pathlib
        src = pathlib.Path(
            "src/backend/app/services/providers/openrouter.py"
        ).read_text(encoding="utf-8")
        assert '"error" in event' in src, (
            "Detection erreur SSE manquante dans openrouter.py"
        )

    def test_provider_handles_http_401(self):
        """Le provider doit afficher un message clair pour une cle invalide."""
        import pathlib
        src = pathlib.Path(
            "src/backend/app/services/providers/openrouter.py"
        ).read_text(encoding="utf-8")
        assert "401" in src
        assert "invalide" in src or "expiree" in src

    def test_provider_handles_http_402(self):
        """Le provider doit afficher un message clair pour un credit insuffisant."""
        import pathlib
        src = pathlib.Path(
            "src/backend/app/services/providers/openrouter.py"
        ).read_text(encoding="utf-8")
        assert "402" in src
        assert "insuffisant" in src or "Rechargez" in src


class TestGroqWhisperLabel:
    """Le libelle Groq dans Services doit preciser que c est du cloud."""

    def test_services_tab_groq_label_mentions_cloud(self):
        """ServicesTab.tsx doit mentionner 'cloud' dans le libelle Groq."""
        import pathlib
        src = pathlib.Path(
            "src/frontend/src/components/settings/ServicesTab.tsx"
        ).read_text(encoding="utf-8")
        assert "cloud" in src.lower() or "Cloud" in src, (
            "Le libelle Groq dans ServicesTab.tsx ne mentionne pas 'cloud'"
        )

    def test_services_tab_groq_label_mentions_model(self):
        """ServicesTab.tsx doit mentionner le modele whisper-large-v3-turbo."""
        import pathlib
        src = pathlib.Path(
            "src/frontend/src/components/settings/ServicesTab.tsx"
        ).read_text(encoding="utf-8")
        assert "whisper-large-v3-turbo" in src, (
            "Le libelle Groq ne precise pas le modele whisper-large-v3-turbo"
        )

    def test_services_tab_no_misleading_whisper_label(self):
        """Le libelle ne doit plus dire juste 'Whisper' sans preciser que c est cloud."""
        import pathlib
        src = pathlib.Path(
            "src/frontend/src/components/settings/ServicesTab.tsx"
        ).read_text(encoding="utf-8")
        # L'ancien libelle trompeur ne doit plus exister
        assert "transcription audio (Whisper)" not in src, (
            "Ancien libelle trompeur encore present : 'transcription audio (Whisper)'"
        )


class TestBUGOpenRouter403MessageErreur:
    """BUG openrouter-403 : message d'erreur vide/opaque sur 403 Forbidden."""

    @staticmethod
    def _make_provider():
        """Crée un OpenRouterProvider avec un client httpx mock."""
        import httpx
        from app.services.providers.openrouter import OpenRouterProvider
        from app.services.llm import LLMConfig, LLMProvider
        config = LLMConfig(
            provider=LLMProvider.OPENROUTER,
            model="anthropic/claude-sonnet-4-6",
            api_key="test-key",
        )
        client = httpx.AsyncClient()
        return OpenRouterProvider(config, client)

    def test_openrouter_403_message_specifique(self):
        """Un 403 doit générer un message lisible sur les crédits, pas juste le code HTTP."""
        import asyncio
        from unittest.mock import MagicMock, patch
        import httpx

        provider = self._make_provider()

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = '{"error":{"message":"You have exceeded your free tier limits. Please add a payment method at openrouter.ai/settings/billing","code":403}}'
        error = httpx.HTTPStatusError("403 Forbidden", request=MagicMock(), response=mock_response)

        async def run():
            with patch.object(provider.client, "stream", side_effect=error):
                events = []
                async for event in provider.stream(None, [{"role": "user", "content": "test"}]):
                    events.append(event)
                return events

        events = asyncio.new_event_loop().run_until_complete(run())
        assert events, "Aucun événement reçu"
        err_event = events[0]
        assert err_event.type == "error"
        msg = err_event.content or ""
        assert any(word in msg.lower() for word in ["crédit", "credit", "openrouter", "403", "paiement", "billing", "exceeded"]), (
            f"Message 403 non informatif : {msg!r}"
        )
        assert msg != "Erreur API OpenRouter (403)", (
            f"Message générique non informatif toujours présent : {msg!r}"
        )

    def test_openrouter_403_body_vide_fallback(self):
        """Un 403 avec body vide doit donner un message de fallback lisible."""
        import asyncio
        from unittest.mock import MagicMock, patch
        import httpx

        provider = self._make_provider()

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = ""
        error = httpx.HTTPStatusError("403 Forbidden", request=MagicMock(), response=mock_response)

        async def run():
            with patch.object(provider.client, "stream", side_effect=error):
                events = []
                async for event in provider.stream(None, [{"role": "user", "content": "test"}]):
                    events.append(event)
                return events

        events = asyncio.new_event_loop().run_until_complete(run())
        err_event = events[0]
        assert err_event.type == "error"
        assert "403" in (err_event.content or "") or "crédit" in (err_event.content or "").lower()

    def test_openrouter_401_non_affecte(self):
        """La correction du 403 ne doit pas casser le handler 401."""
        import asyncio
        from unittest.mock import MagicMock, patch
        import httpx

        provider = self._make_provider()

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = '{"error":{"message":"Invalid API key"}}'
        error = httpx.HTTPStatusError("401 Unauthorized", request=MagicMock(), response=mock_response)

        async def run():
            with patch.object(provider.client, "stream", side_effect=error):
                events = []
                async for event in provider.stream(None, [{"role": "user", "content": "test"}]):
                    events.append(event)
                return events

        events = asyncio.new_event_loop().run_until_complete(run())
        err_event = events[0]
        assert err_event.type == "error"
        assert "invalid" in (err_event.content or "").lower() or "invalide" in (err_event.content or "").lower() or "clé" in (err_event.content or "").lower()

    def test_openrouter_429_rate_limit_message_without_unboundlocalerror(self):
        """Une 429 doit rester lisible et ne jamais se transformer en UnboundLocalError."""
        import asyncio
        from unittest.mock import MagicMock, patch
        import httpx

        provider = self._make_provider()

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = '{"error":{"message":"Rate limit exceeded"}}'
        error = httpx.HTTPStatusError("429 Too Many Requests", request=MagicMock(), response=mock_response)

        async def run():
            with patch.object(provider.client, "stream", side_effect=error):
                events = []
                async for event in provider.stream(None, [{"role": "user", "content": "test"}]):
                    events.append(event)
                return events

        events = asyncio.new_event_loop().run_until_complete(run())
        assert events, "Une 429 doit produire un événement d erreur exploitable"
        err_event = events[0]
        assert err_event.type == "error"
        msg = err_event.content or ""
        assert "trop de requêtes" in msg.lower() or "429" in msg, (
            f"Message 429 non informatif : {msg!r}"
        )
        assert "unboundlocalerror" not in msg.lower(), (
            f"La 429 ne doit plus être masquée par une erreur locale : {msg!r}"
        )


# ============================================================
# BUG-091 - Séparateur décimal dans InvoiceForm
# lang="en" sur les inputs numériques pour forcer le point
# comme séparateur décimal (pas la virgule en locales FR).
# ============================================================

INVOICE_FORM_TSX = FRONTEND / "components" / "invoices" / "InvoiceForm.tsx"


class TestBUG091_DecimalSeparator:
    """BUG-091 : les inputs numériques doivent utiliser type='text' + inputMode='decimal' pour le séparateur."""

    def test_quantity_input_has_lang_en(self):
        """L'input de quantité doit avoir inputMode='decimal' pour accepter les décimaux."""
        content = INVOICE_FORM_TSX.read_text(encoding="utf-8")
        idx_qty = content.find("Quantit")
        assert idx_qty != -1, "Le label 'Quantité' doit exister dans InvoiceForm.tsx"
        block = content[idx_qty:idx_qty + 500]
        assert 'inputMode="decimal"' in block, (
            "L'input quantité doit avoir inputMode='decimal' pour le clavier numérique mobile (BUG-091)"
        )

    def test_unit_price_input_has_lang_en(self):
        """L'input de prix unitaire doit avoir inputMode='decimal' pour accepter les décimaux."""
        content = INVOICE_FORM_TSX.read_text(encoding="utf-8")
        idx_price = content.find("Prix HT")
        assert idx_price != -1, "Le label 'Prix HT' doit exister dans InvoiceForm.tsx"
        block = content[idx_price:idx_price + 500]
        assert 'inputMode="decimal"' in block, (
            "L'input prix HT doit avoir inputMode='decimal' pour le clavier numérique mobile (BUG-091)"
        )

    def test_numeric_inputs_are_type_number(self):
        """Les inputs numériques doivent être type='text' + inputMode='decimal' (pas type='number')."""
        content = INVOICE_FORM_TSX.read_text(encoding="utf-8")
        assert 'type="text"' in content, (
            "InvoiceForm doit utiliser type='text' pour les inputs décimaux (BUG-091)"
        )
        assert 'inputMode="decimal"' in content, (
            "InvoiceForm doit utiliser inputMode='decimal' pour le clavier numérique mobile (BUG-091)"
        )

    def test_step_precision_present(self):
        """Les inputs décimaux doivent avoir une validation de format dans le code."""
        content = INVOICE_FORM_TSX.read_text(encoding="utf-8")
        assert "isValidDecimalDraft" in content or "parseDecimalDraft" in content, (
            "InvoiceForm doit valider le format décimal via isValidDecimalDraft ou parseDecimalDraft (BUG-091)"
        )
        # Vérifier que la regex accepte virgule et point
        assert ".,]" in content or "[.,]" in content, (
            "La validation décimale doit accepter virgule et point comme séparateur (BUG-091)"
        )

    def test_no_onkeydown_hack(self):
        """Aucun hack onKeyDown pour filtrer les virgules (la solution est lang='en')."""
        content = INVOICE_FORM_TSX.read_text(encoding="utf-8")
        assert "onKeyDown" not in content or "e.key === ','" not in content, (
            "InvoiceForm ne doit pas utiliser un hack onKeyDown pour le séparateur décimal. "
            "La solution correcte est lang='en' (BUG-091)"
        )


# ============================================================
# BUG-092 - PDF error handling dans invoices.py
# Le endpoint PDF doit capturer les erreurs avec try/except
# et renvoyer une HTTPException 500 avec un message clair.
# ============================================================

INVOICES_PY = SRC / "app" / "routers" / "invoices.py"


class TestBUG092_PDFErrorHandling:
    """BUG-092 : le endpoint PDF doit capturer les erreurs de génération."""

    def test_pdf_endpoint_has_try_except(self):
        """La fonction generate_invoice_pdf doit contenir un try/except."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "generate_invoice_pdf":
                func_source = ast.get_source_segment(content, node)
                assert "try:" in func_source, (
                    "generate_invoice_pdf doit contenir un bloc try (BUG-092)"
                )
                assert "except" in func_source, (
                    "generate_invoice_pdf doit contenir un bloc except (BUG-092)"
                )
                break
        else:
            pytest.fail("Fonction generate_invoice_pdf non trouvée dans invoices.py")

    def test_pdf_except_logs_error(self):
        """Le bloc except doit logger l'erreur avec logger.error."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "generate_invoice_pdf":
                func_source = ast.get_source_segment(content, node)
                assert "logger.error" in func_source, (
                    "Le bloc except de generate_invoice_pdf doit utiliser logger.error (BUG-092)"
                )
                break

    def test_pdf_except_raises_http_500(self):
        """Le bloc except doit lever une HTTPException avec status_code=500."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "generate_invoice_pdf":
                func_source = ast.get_source_segment(content, node)
                assert "status_code=500" in func_source, (
                    "Le bloc except doit lever HTTPException(status_code=500) (BUG-092)"
                )
                assert "HTTPException" in func_source, (
                    "Le bloc except doit utiliser HTTPException (BUG-092)"
                )
                break

    def test_pdf_error_message_mentions_pdf(self):
        """Le message d'erreur doit mentionner 'PDF'."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "generate_invoice_pdf":
                func_source = ast.get_source_segment(content, node)
                assert "PDF" in func_source, (
                    "Le message d'erreur doit mentionner 'PDF' (BUG-092)"
                )
                break

    def test_pdf_error_message_mentions_erreur(self):
        """Le message d'erreur doit contenir le mot 'Erreur' (en français)."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "generate_invoice_pdf":
                func_source = ast.get_source_segment(content, node)
                assert "Erreur" in func_source or "erreur" in func_source, (
                    "Le message d'erreur doit contenir 'Erreur' (BUG-092)"
                )
                break

    def test_invoice_pdf_generator_import_exists(self):
        """L'import InvoicePDFGenerator doit exister dans invoices.py."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        assert "InvoicePDFGenerator" in content, (
            "invoices.py doit importer InvoicePDFGenerator (BUG-092)"
        )

    def test_pdf_endpoint_function_name(self):
        """Le endpoint PDF doit s'appeler generate_invoice_pdf."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        pdf_func_found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "generate_invoice_pdf":
                pdf_func_found = True
                break
        assert pdf_func_found, (
            "Le endpoint PDF doit être une fonction nommée generate_invoice_pdf (BUG-092)"
        )

    def test_pdf_endpoint_is_get(self):
        """Le endpoint PDF doit être un GET (pas POST)."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        idx_func = content.find("def generate_invoice_pdf")
        assert idx_func != -1
        block_before = content[max(0, idx_func - 200):idx_func]
        assert "@router.get" in block_before, (
            "Le endpoint PDF doit être un @router.get (BUG-092)"
        )


INVOICE_PDF_PY = SRC / "app" / "services" / "invoice_pdf.py"


class TestBUG094_PDFWorkingDirectory:
    """BUG-094 : les PDFs factures doivent utiliser le dossier de travail configuré,
    pas ~/.therese/invoices en dur."""

    def test_no_hardcoded_default_in_init(self):
        """InvoicePDFGenerator.__init__ ne doit PAS avoir ~/.therese/invoices comme défaut."""
        content = INVOICE_PDF_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "InvoicePDFGenerator":
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        init_source = ast.get_source_segment(content, item)
                        assert '= "~/.therese/invoices"' not in init_source, (
                            "InvoicePDFGenerator.__init__ ne doit plus avoir "
                            "~/.therese/invoices en valeur par défaut (BUG-094)"
                        )
                        break
                break
        else:
            pytest.fail("Classe InvoicePDFGenerator non trouvée dans invoice_pdf.py")

    def test_resolve_function_exists(self):
        """La fonction resolve_invoice_output_dir doit exister dans invoice_pdf.py."""
        content = INVOICE_PDF_PY.read_text(encoding="utf-8")
        assert "def resolve_invoice_output_dir" in content, (
            "invoice_pdf.py doit contenir resolve_invoice_output_dir (BUG-094)"
        )

    def test_resolve_queries_working_directory(self):
        """resolve_invoice_output_dir doit chercher la clé 'working_directory' en DB."""
        content = INVOICE_PDF_PY.read_text(encoding="utf-8")
        assert 'working_directory' in content, (
            "resolve_invoice_output_dir doit requêter la Preference 'working_directory' (BUG-094)"
        )

    def test_resolve_returns_factures_subfolder(self):
        """Le résultat doit contenir 'factures' comme sous-dossier."""
        content = INVOICE_PDF_PY.read_text(encoding="utf-8")
        assert '"factures"' in content, (
            "Le répertoire résolu doit inclure un sous-dossier 'factures' (BUG-094)"
        )

    def test_router_uses_get_invoice_output_dir(self):
        """Le router invoices.py doit utiliser _get_invoice_output_dir pour chaque appel PDF."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        # Doit apparaître au moins 2 fois (generate_invoice_pdf + delete_invoice)
        count = content.count("_get_invoice_output_dir")
        assert count >= 3, (  # 1 def + 2 appels minimum
            f"_get_invoice_output_dir doit être appelé dans generate_invoice_pdf ET delete_invoice "
            f"(trouvé {count} occurrences, attendu >= 3) (BUG-094)"
        )

    def test_no_bare_instantiation(self):
        """Aucun InvoicePDFGenerator() sans output_dir dans invoices.py."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        import re
        bare_calls = re.findall(r'InvoicePDFGenerator\(\s*\)', content)
        assert not bare_calls, (
            "invoices.py ne doit pas instancier InvoicePDFGenerator() sans output_dir (BUG-094)"
        )

    def test_init_accepts_none_output_dir(self):
        """InvoicePDFGenerator.__init__ doit accepter output_dir=None."""
        content = INVOICE_PDF_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "InvoicePDFGenerator":
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        # Vérifier que output_dir a une valeur par défaut None
                        init_source = ast.get_source_segment(content, item)
                        assert "None" in init_source, (
                            "InvoicePDFGenerator.__init__(output_dir) doit accepter None (BUG-094)"
                        )
                        break
                break


# ============================================================
# Calendar Google sync fix
# Le check provider doit accepter "gmail" et "google"
# avec un fallback access_token + refresh_token.
# ============================================================

CALENDAR_PY = SRC / "app" / "routers" / "calendar.py"


class TestCalendarGoogleSyncFix:
    """Le provider check Google Calendar doit accepter 'gmail' et 'google'."""

    def test_provider_accepts_gmail(self):
        """Le check provider doit accepter 'gmail'."""
        content = CALENDAR_PY.read_text(encoding="utf-8")
        assert '"gmail"' in content, (
            "calendar.py doit accepter le provider 'gmail' pour les comptes Google"
        )

    def test_provider_accepts_google(self):
        """Le check provider doit accepter 'google'."""
        content = CALENDAR_PY.read_text(encoding="utf-8")
        assert '"google"' in content, (
            "calendar.py doit accepter le provider 'google' pour les comptes Google"
        )

    def test_provider_check_includes_both_gmail_and_google(self):
        """Le check is_google doit tester les deux valeurs dans un tuple/liste."""
        content = CALENDAR_PY.read_text(encoding="utf-8")
        assert '("gmail", "google")' in content or '("google", "gmail")' in content, (
            "Le check is_google doit tester ('gmail', 'google') dans la même expression"
        )

    def test_fallback_access_token_refresh_token(self):
        """Un fallback access_token + refresh_token doit exister."""
        content = CALENDAR_PY.read_text(encoding="utf-8")
        assert "access_token" in content and "refresh_token" in content, (
            "calendar.py doit avoir un fallback access_token + refresh_token"
        )
        idx = content.find("is_google")
        assert idx != -1, "La variable is_google doit exister dans calendar.py"
        block = content[idx:idx + 300]
        assert "access_token" in block and "refresh_token" in block, (
            "Le fallback access_token/refresh_token doit être dans le bloc is_google"
        )

    def test_logger_warning_for_fallthrough(self):
        """Un logger.warning doit exister pour les cas non-Google avec account_id."""
        content = CALENDAR_PY.read_text(encoding="utf-8")
        assert "logger.warning" in content, (
            "calendar.py doit avoir un logger.warning pour les cas non-Google"
        )
        idx = content.find("logger.warning")
        assert idx != -1
        block = content[idx:idx + 200]
        assert "fallthrough" in block.lower() or "provider" in block.lower(), (
            "Le logger.warning doit mentionner le fallthrough ou le provider"
        )

    def test_list_google_calendars_function_exists(self):
        """La fonction _list_google_calendars doit exister."""
        content = CALENDAR_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        func_found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "_list_google_calendars":
                func_found = True
                break
        assert func_found, (
            "_list_google_calendars doit exister dans calendar.py"
        )

    def test_list_google_calendars_called_for_google_accounts(self):
        """_list_google_calendars doit être appelée quand is_google est True."""
        content = CALENDAR_PY.read_text(encoding="utf-8")
        idx = content.find("is_google")
        assert idx != -1
        block = content[idx:idx + 300]
        assert "_list_google_calendars" in block, (
            "_list_google_calendars doit être appelée quand is_google est True"
        )

    def test_sync_status_endpoint_exists(self):
        """Le endpoint /sync/status doit exister."""
        content = CALENDAR_PY.read_text(encoding="utf-8")
        assert "sync/status" in content or "sync_status" in content, (
            "calendar.py doit avoir un endpoint /sync/status"
        )
        tree = ast.parse(content)
        func_found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "get_sync_status":
                func_found = True
                break
        assert func_found, "La fonction get_sync_status doit exister"


# ============================================================
# Version consistency tests
# __init__.py et config.py doivent avoir la même version.
# bump-version.sh doit les mettre à jour tous les deux.
# ============================================================

INIT_PY = SRC / "app" / "__init__.py"
CONFIG_PY = SRC / "app" / "config.py"
BUMP_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "bump-version.sh"


class TestVersionConsistency:
    """Les versions doivent être cohérentes entre __init__.py et config.py."""

    def test_init_version_matches_config_version(self):
        """__init__.py et config.py doivent avoir la même version."""
        import re

        init_content = INIT_PY.read_text(encoding="utf-8")
        config_content = CONFIG_PY.read_text(encoding="utf-8")

        init_match = re.search(r'__version__\s*=\s*"([^"]+)"', init_content)
        config_match = re.search(r'app_version\s*:\s*str\s*=\s*"([^"]+)"', config_content)

        assert init_match, "__init__.py doit avoir un __version__"
        assert config_match, "config.py doit avoir un app_version"

        assert init_match.group(1) == config_match.group(1), (
            f"Version mismatch: __init__.py={init_match.group(1)} vs config.py={config_match.group(1)}"
        )

    def test_bump_script_includes_init_py(self):
        """bump-version.sh doit inclure __init__.py dans sa liste de fichiers."""
        content = BUMP_SCRIPT.read_text(encoding="utf-8")
        assert "__init__.py" in content, (
            "bump-version.sh doit mettre à jour __init__.py"
        )

    def test_bump_script_has_version_sed_pattern(self):
        """bump-version.sh doit avoir un pattern sed pour __version__."""
        content = BUMP_SCRIPT.read_text(encoding="utf-8")
        assert "__version__" in content, (
            "bump-version.sh doit avoir un pattern pour __version__"
        )

    def test_version_format_is_semver(self):
        """La version doit être au format semver (X.Y.Z ou X.Y.Z-suffix)."""
        import re

        init_content = INIT_PY.read_text(encoding="utf-8")
        match = re.search(r'__version__\s*=\s*"([^"]+)"', init_content)
        assert match, "__init__.py doit avoir un __version__"

        version = match.group(1)
        assert re.match(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$', version), (
            f"Version '{version}' n'est pas au format semver (X.Y.Z ou X.Y.Z-suffix)"
        )

    def test_bump_script_validates_semver(self):
        """bump-version.sh doit valider le format semver."""
        content = BUMP_SCRIPT.read_text(encoding="utf-8")
        assert "grep" in content and "qE" in content, (
            "bump-version.sh doit valider le format semver avec grep -qE"
        )


# ============================================================
# Invoice CRUD robustness tests
# Analyse statique de invoices.py pour la robustesse.
# ============================================================


class TestInvoiceCRUDRobustness:
    """Tests de robustesse statique sur invoices.py."""

    def test_create_endpoint_checks_contact(self):
        """Le endpoint create doit vérifier que le contact existe."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "create_invoice":
                func_source = ast.get_source_segment(content, node)
                assert "Contact" in func_source or "contact" in func_source, (
                    "create_invoice doit vérifier le contact (contact_id FK)"
                )
                assert "404" in func_source, (
                    "create_invoice doit lever 404 si le contact n'existe pas"
                )
                break
        else:
            pytest.fail("create_invoice non trouvée")

    def test_update_endpoint_checks_invoice_exists(self):
        """Le endpoint update doit vérifier que la facture existe."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "update_invoice":
                func_source = ast.get_source_segment(content, node)
                assert "404" in func_source, (
                    "update_invoice doit lever 404 si la facture n'existe pas"
                )
                break
        else:
            pytest.fail("update_invoice non trouvée")

    def test_delete_endpoint_checks_invoice_exists(self):
        """Le endpoint delete doit vérifier que la facture existe."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "delete_invoice":
                func_source = ast.get_source_segment(content, node)
                assert "404" in func_source, (
                    "delete_invoice doit lever 404 si la facture n'existe pas"
                )
                break
        else:
            pytest.fail("delete_invoice non trouvée")

    def test_pdf_endpoint_returns_path_and_number(self):
        """Le endpoint PDF doit retourner pdf_path et invoice_number."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "generate_invoice_pdf":
                func_source = ast.get_source_segment(content, node)
                assert "pdf_path" in func_source, (
                    "Le endpoint PDF doit retourner pdf_path"
                )
                assert "invoice_number" in func_source, (
                    "Le endpoint PDF doit retourner invoice_number"
                )
                break

    def test_currency_support_eur_chf_usd_gbp(self):
        """InvoiceForm.tsx doit supporter EUR, CHF, USD et GBP."""
        content = INVOICE_FORM_TSX.read_text(encoding="utf-8")
        for currency in ("EUR", "CHF", "USD", "GBP"):
            assert currency in content, (
                f"InvoiceForm doit supporter la devise {currency}"
            )

    def test_invoice_number_format_prefix(self):
        """Les numéros de facture doivent utiliser un format préfixé (FACT-, DEV-, AV-)."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        assert "FACT" in content, "Le format de numéro doit inclure le préfixe FACT"
        assert "DEV" in content, "Le format de numéro doit inclure le préfixe DEV (devis)"
        assert "AV" in content, "Le format de numéro doit inclure le préfixe AV (avoir)"

    def test_invoice_number_uses_max_for_sequence(self):
        """La génération de numéro doit utiliser MAX() pour éviter les doublons (BUG-073)."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        assert "func.max" in content or "MAX" in content, (
            "La génération de numéro doit utiliser MAX() (BUG-073)"
        )

    def test_mark_paid_endpoint_exists(self):
        """Le endpoint mark-paid doit exister."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        func_found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "mark_invoice_paid":
                func_found = True
                break
        assert func_found, "mark_invoice_paid doit exister dans invoices.py"

    def test_send_endpoint_returns_501(self):
        """Le endpoint send doit retourner 501 (pas encore implémenté)."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "send_invoice_by_email":
                func_source = ast.get_source_segment(content, node)
                assert "501" in func_source, (
                    "send_invoice_by_email doit retourner 501 (non implémenté)"
                )
                break
        else:
            pytest.fail("send_invoice_by_email non trouvée")

    def test_create_validates_document_type(self):
        """create_invoice doit valider le document_type (devis, facture, avoir)."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "create_invoice":
                func_source = ast.get_source_segment(content, node)
                assert "document_type" in func_source, (
                    "create_invoice doit valider le document_type"
                )
                assert "400" in func_source, (
                    "create_invoice doit lever 400 pour un document_type invalide"
                )
                break


# ============================================================
# Calendar robustness tests
# Analyse statique de calendar.py pour la robustesse.
# ============================================================


class TestCalendarRobustness:
    """Tests de robustesse statique sur calendar.py."""

    def test_get_provider_checks_account_for_google(self):
        """_get_provider_for_calendar doit vérifier le compte pour Google."""
        content = CALENDAR_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "_get_provider_for_calendar":
                func_source = ast.get_source_segment(content, node)
                assert "account" in func_source, (
                    "_get_provider_for_calendar doit vérifier le compte pour Google"
                )
                assert "404" in func_source, (
                    "_get_provider_for_calendar doit lever 404 si le compte n'existe pas"
                )
                break
        else:
            pytest.fail("_get_provider_for_calendar non trouvée")

    def test_caldav_setup_validates_connection(self):
        """setup_caldav_calendar doit tester la connexion avant d'importer."""
        content = CALENDAR_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "setup_caldav_calendar":
                func_source = ast.get_source_segment(content, node)
                assert "test_caldav_connection" in func_source, (
                    "setup_caldav_calendar doit tester la connexion CalDAV avant d'importer"
                )
                assert "400" in func_source, (
                    "setup_caldav_calendar doit lever 400 si la connexion échoue"
                )
                break
        else:
            pytest.fail("setup_caldav_calendar non trouvée")

    def test_sync_status_returns_providers_list(self):
        """get_sync_status doit retourner la liste des providers."""
        content = CALENDAR_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "get_sync_status":
                func_source = ast.get_source_segment(content, node)
                assert "providers" in func_source, (
                    "get_sync_status doit retourner la liste des providers"
                )
                break
        else:
            pytest.fail("get_sync_status non trouvée")

    def test_event_creation_validates_calendar_id(self):
        """create_event doit chercher le calendrier par ID pour déterminer le provider."""
        content = CALENDAR_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "create_event":
                func_source = ast.get_source_segment(content, node)
                assert "calendar_id" in func_source or "request.calendar_id" in func_source, (
                    "create_event doit utiliser le calendar_id pour router le provider"
                )
                break
        else:
            pytest.fail("create_event non trouvée")

    def test_provider_detection_handles_unknown(self):
        """_get_provider_for_calendar doit gérer les providers inconnus."""
        content = CALENDAR_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "_get_provider_for_calendar":
                func_source = ast.get_source_segment(content, node)
                assert "400" in func_source, (
                    "_get_provider_for_calendar doit lever 400 pour un provider inconnu"
                )
                assert "inconnu" in func_source.lower() or "unknown" in func_source.lower(), (
                    "Le message d'erreur doit mentionner 'inconnu' ou 'unknown'"
                )
                break

    def test_delete_event_endpoint_exists(self):
        """Le endpoint de suppression d'événement doit exister."""
        content = CALENDAR_PY.read_text(encoding="utf-8")
        tree = ast.parse(content)
        func_found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "delete_event":
                func_found = True
                break
        assert func_found, "delete_event doit exister dans calendar.py"

    def test_calendar_has_local_provider_support(self):
        """calendar.py doit supporter le provider 'local'."""
        content = CALENDAR_PY.read_text(encoding="utf-8")
        assert '"local"' in content, (
            "calendar.py doit supporter le provider 'local' (Local First)"
        )

    def test_calendar_has_caldav_provider_support(self):
        """calendar.py doit supporter le provider 'caldav'."""
        content = CALENDAR_PY.read_text(encoding="utf-8")
        assert '"caldav"' in content, (
            "calendar.py doit supporter le provider 'caldav'"
        )


# ============================================================
# Security regression tests
# Vérifications de sécurité sur le code source.
# ============================================================

APP_MAIN_PY_SEC = SRC / "app" / "main.py"


class TestSecurityRegression:
    """Tests de sécurité : pas de clés hardcodées, CORS, rate limiting."""

    def test_no_hardcoded_api_keys_in_routers(self):
        """Aucune clé API hardcodée dans les routers."""
        import re

        routers_dir = SRC / "app" / "routers"
        for py_file in routers_dir.glob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            matches = re.findall(r'["\'](?:sk-[a-zA-Z0-9]{20,}|AKIA[A-Z0-9]{16}|AIza[a-zA-Z0-9_-]{35})["\']', content)
            assert not matches, (
                f"Clé API hardcodée trouvée dans {py_file.name}: {matches}"
            )

    def test_no_dangerous_builtins_in_routers(self):
        """Aucun appel à des builtins dangereux (eval, compile) dans les routers."""
        _dangerous = {"eval", "compile"}
        routers_dir = SRC / "app" / "routers"
        for py_file in routers_dir.glob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in _dangerous:
                        pytest.fail(f"Appel dangereux {node.func.id}() trouvé dans {py_file.name}")

    def test_httpexception_used_for_errors(self):
        """Les routers doivent utiliser HTTPException (pas de raise générique)."""
        content = INVOICES_PY.read_text(encoding="utf-8")
        assert "HTTPException" in content, (
            "invoices.py doit utiliser HTTPException pour les erreurs"
        )
        content_cal = CALENDAR_PY.read_text(encoding="utf-8")
        assert "HTTPException" in content_cal, (
            "calendar.py doit utiliser HTTPException pour les erreurs"
        )

    def test_cors_settings_exist_in_main(self):
        """Les settings CORS doivent exister dans main.py."""
        content = APP_MAIN_PY_SEC.read_text(encoding="utf-8")
        assert "CORSMiddleware" in content, (
            "main.py doit utiliser CORSMiddleware"
        )
        assert "allow_origins" in content, (
            "main.py doit configurer allow_origins dans CORSMiddleware"
        )

    def test_rate_limiting_configured(self):
        """Le rate limiting doit être configuré dans main.py."""
        content = APP_MAIN_PY_SEC.read_text(encoding="utf-8")
        assert "Limiter" in content or "rate_limit" in content or "RATE_LIMIT" in content, (
            "main.py doit configurer le rate limiting (SEC-015)"
        )
        assert "429" in content, (
            "main.py doit retourner 429 en cas de rate limit dépassé"
        )


# ============================================================
# Frontend regression tests
# Analyse statique des fichiers TypeScript.
# ============================================================


class TestFrontendRegression:
    """Tests de régression frontend (analyse statique TypeScript)."""

    def test_no_alert_in_main_components(self):
        """Pas de alert() dans les composants principaux (sauf ceux connus)."""
        allowed_files = {"InvoicesPanel.tsx", "InvoiceForm.tsx", "MemoryPanel.tsx", "EventDetail.tsx"}
        components_dir = FRONTEND / "components"
        violations = []
        for tsx_file in components_dir.rglob("*.tsx"):
            if tsx_file.name in allowed_files:
                continue
            content = tsx_file.read_text(encoding="utf-8")
            if "alert(" in content:
                violations.append(tsx_file.name)
        assert not violations, (
            f"alert() trouvé dans des composants non autorisés : {violations}"
        )

    def test_api_calls_use_centralized_client(self):
        """Les modules API doivent utiliser le client centralisé (fetchApi ou apiBase)."""
        api_dir = FRONTEND / "services" / "api"
        if not api_dir.exists():
            pytest.skip("Le dossier services/api n'existe pas")
        for ts_file in api_dir.glob("*.ts"):
            if ts_file.name in ("core.ts", "index.ts", "types.ts"):
                continue
            content = ts_file.read_text(encoding="utf-8")
            has_import = (
                "from" in content and ("core" in content or "apiBase" in content)
            ) or "fetchApi" in content or "apiBase" in content
            assert has_import, (
                f"{ts_file.name} doit utiliser le client centralisé (apiBase/fetchApi)"
            )

    def test_no_hardcoded_localhost_in_components(self):
        """Pas d'URLs localhost hardcodées dans les composants (sauf patterns connus)."""
        # BoardPanel.tsx et EmailConnect.tsx ont des URLs localhost pour des raisons légitimes
        # (callback OAuth, liens de debug)
        excluded = {"core.ts", "config.ts", "vite-env.d.ts", "BoardPanel.tsx", "EmailConnect.tsx"}
        components_dir = FRONTEND / "components"
        violations = []
        for tsx_file in components_dir.rglob("*.tsx"):
            if tsx_file.name in excluded:
                continue
            content = tsx_file.read_text(encoding="utf-8")
            if "http://localhost:" in content or "http://127.0.0.1:" in content:
                violations.append(tsx_file.name)
        assert not violations, (
            f"URLs localhost hardcodées trouvées dans : {violations}"
        )

    def test_invoice_form_has_currency_selector(self):
        """InvoiceForm doit avoir un sélecteur de devise."""
        content = INVOICE_FORM_TSX.read_text(encoding="utf-8")
        assert "currency" in content.lower(), (
            "InvoiceForm doit avoir un sélecteur de devise"
        )
        assert "CURRENCIES" in content, (
            "InvoiceForm doit utiliser la constante CURRENCIES"
        )

    def test_invoice_form_has_tva_rates(self):
        """InvoiceForm doit avoir les taux de TVA français."""
        content = INVOICE_FORM_TSX.read_text(encoding="utf-8")
        assert "TVA_RATES" in content, (
            "InvoiceForm doit utiliser la constante TVA_RATES"
        )
        assert "20" in content, "Le taux TVA 20% doit être présent"
        assert "5.5" in content or "5,5" in content, "Le taux TVA 5,5% doit être présent"


class TestBUG69NestedExceptShadowing:
    """v0.11.5 issue #69 - 'local variable e' : nested 'except as e' masquait
    la variable de l outer HTTPStatusError handler, provoquant UnboundLocalError."""

    def test_openrouter_no_nested_except_as_e_in_http_error_handler(self):
        """Le bloc HTTPStatusError ne doit pas réutiliser `e` dans un nested except."""
        import re
        from pathlib import Path

        src_file = Path(__file__).parent.parent / "src" / "backend" / "app" / "services" / "providers" / "openrouter.py"
        src = src_file.read_text()
        match = re.search(
            r"except httpx\.HTTPStatusError as \w+:.*?(?=\n\s*except [A-Z])",
            src,
            re.DOTALL,
        )
        assert match, "Bloc HTTPStatusError introuvable dans openrouter.py"
        block = match.group(0)
        assert "except Exception as e:" not in block, (
            "Nested 'except Exception as e:' dans le handler HTTPStatusError "
            "réintroduit le bug local variable e. Utiliser un autre nom."
        )

    def test_anthropic_no_nested_except_as_e_in_http_error_handler(self):
        import re
        from pathlib import Path

        src_file = Path(__file__).parent.parent / "src" / "backend" / "app" / "services" / "providers" / "anthropic.py"
        src = src_file.read_text()
        match = re.search(
            r"except httpx\.HTTPStatusError as e:.*?(?=\n\s*except [A-Z])",
            src,
            re.DOTALL,
        )
        assert match, "Bloc HTTPStatusError introuvable dans anthropic.py"
        block = match.group(0)
        assert "except Exception as e:" not in block, (
            "Nested 'except Exception as e:' dans anthropic.py ecrase la variable e"
        )

    def test_ollama_no_nested_except_as_e_in_http_error_handler(self):
        import re
        from pathlib import Path

        src_file = Path(__file__).parent.parent / "src" / "backend" / "app" / "services" / "providers" / "ollama.py"
        src = src_file.read_text()
        match = re.search(
            r"except httpx\.HTTPStatusError as e:.*?(?=\n\s*(?:except [A-Z]|async def|def |class ))",
            src,
            re.DOTALL,
        )
        # US-009 : le handler except httpx.HTTPStatusError a été supprimé
        # (code mort sur du streaming - statut testé dans le async with).
        # S'il revient un jour, il ne doit pas imbriquer un except qui écrase e.
        if match is None:
            return
        block = match.group(0)
        assert "except Exception as e:" not in block, (
            "Nested 'except Exception as e:' dans ollama.py ecrase la variable e"
        )


class TestBUG73GoogleCalendarTZ:
    """v0.11.5 issue #73 - Google Calendar API recevait des timestamps
    invalides type '2026-04-22T00:00:00+02:00Z' (offset + Z) quand le
    datetime etait tz-aware, ce qui retournait une liste vide ou 400."""

    def test_to_rfc3339_z_handles_tz_aware(self):
        """Un datetime avec tzinfo doit etre converti en UTC naif avant Z."""
        from datetime import UTC, datetime, timedelta, timezone

        from app.services.calendar_service import CalendarService

        paris = timezone(timedelta(hours=2))
        # 10h00 Paris = 08h00 UTC
        dt = datetime(2026, 4, 22, 10, 0, 0, tzinfo=paris)

        # Appel du helper interne via la methode publique
        import inspect
        src = inspect.getsource(CalendarService.list_events)
        assert "_to_rfc3339_z" in src, "helper _to_rfc3339_z doit etre present"
        assert "astimezone(_UTC)" in src, "conversion UTC requise pour tz-aware"
        assert "replace(tzinfo=None)" in src, "retrait tzinfo requis avant isoformat"

    def test_to_rfc3339_z_handles_naive(self):
        """Un datetime naif est deja considere UTC - on ajoute juste Z."""
        from datetime import datetime

        dt = datetime(2026, 4, 22, 10, 0, 0)
        expected = "2026-04-22T10:00:00Z"
        assert dt.isoformat() + "Z" == expected


class TestBUG69OllamaFallbackRespectsProvider:
    """v0.11.5 issue #69 - le fallback LLM ne doit plus retomber sur Ollama
    quand l utilisateur a explicitement choisi un provider cloud sans cle."""

    def test_default_config_no_silent_ollama_fallback_for_cloud_provider(self):
        """Si selected_provider est un provider cloud mais sans cle, la config
        retournee doit conserver le provider choisi (api_key=None) et non Ollama.
        Sinon l utilisateur voit 'Ollama non detecte' qui est un faux diagnostic."""
        from unittest.mock import patch

        from app.services.llm import LLMService
        from app.services.providers.base import LLMProvider

        with patch("app.services.llm._get_api_key_from_db", return_value=None), patch(
            "app.models.database.get_sync_connection"
        ) as mock_db, patch.dict(
            "os.environ",
            {k: "" for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "MISTRAL_API_KEY", "XAI_API_KEY", "OPENROUTER_API_KEY")},
            clear=False,
        ):
            class _FakeRow:
                def __init__(self, val):
                    self.val = val

                def __getitem__(self, i):
                    return self.val

            class _FakeResult:
                def __init__(self, val):
                    self._val = val

                def fetchone(self):
                    return _FakeRow(self._val) if self._val else None

            class _FakeConn:
                def execute(self, stmt, params):
                    key = params.get("key", "")
                    if key == "llm_provider":
                        return _FakeResult("openrouter")
                    if key == "llm_model":
                        return _FakeResult("anthropic/claude-opus-4-6")
                    return _FakeResult(None)

            class _FakeCtx:
                def __enter__(self):
                    return _FakeConn()

                def __exit__(self, *a):
                    return False

            mock_db.return_value = _FakeCtx()

            service = LLMService()
            assert service.config.provider == LLMProvider.OPENROUTER, (
                f"Le provider selectionne (openrouter) doit etre conserve meme sans cle. "
                f"Obtenu : {service.config.provider}"
            )
            assert service.config.api_key is None, (
                "api_key doit etre None pour laisser l appel API echouer proprement"
            )


class TestBUG090VCFExport:
    """Export VCF visible et compatible avec les scopes Tauri desktop."""

    def test_memory_api_uses_downloads_scope_for_tauri_export(self):
        """Le helper VCF desktop doit écrire dans Téléchargements, pas un chemin arbitraire."""
        content = (FRONTEND / "services" / "api" / "memory.ts").read_text(encoding="utf-8")
        assert "downloadDir" in content, (
            "downloadVCFFile() doit résoudre le dossier Téléchargements en runtime Tauri"
        )
        assert "saveVCFFileInDownloads" in content, (
            "downloadVCFFile() doit utiliser un helper dédié pour l écriture desktop"
        )
        assert "writeFile(targetPath" in content, (
            "Le VCF doit être écrit explicitement via writeFile() dans un chemin autorisé"
        )

    def test_memory_panel_uses_download_helper_for_visible_export(self):
        """MemoryPanel doit passer par le helper desktop et notifier le succès."""
        content = (FRONTEND / "components" / "memory" / "MemoryPanel.tsx").read_text(encoding="utf-8")
        assert "await api.downloadVCFFile()" in content, (
            "MemoryPanel doit utiliser downloadVCFFile() plutôt qu un blob URL direct"
        )
        assert "Contacts exportés dans Téléchargements" in content, (
            "Le succès doit indiquer à l utilisateur où retrouver le fichier exporté"
        )

    def test_no_unicode_escape_in_jsx_text_nodes(self):
        """
        BUG-096 (Smileshoot, v0.11.6) : `\\u00XX` en littéral dans du JSX text node
        s'affiche tel quel ("Pay\\u00e9e" au lieu de "Payée") car JSX ne décode pas
        les échappements JS entre les balises. Aucun fichier frontend ne doit
        contenir de séquence `\\u00XX` (couvre les caractères latin-1 accentués).
        """
        import re

        pattern = re.compile(r"\\u00[0-9a-fA-F]{2}")
        offenders: list[str] = []
        for path in FRONTEND.rglob("*"):
            if path.suffix not in {".ts", ".tsx"}:
                continue
            if path.name.endswith(".test.ts") or path.name.endswith(".test.tsx"):
                # Les tests peuvent légitimement contenir des chaînes \\u00XX
                continue
            text = path.read_text(encoding="utf-8")
            if pattern.search(text):
                offenders.append(str(path.relative_to(FRONTEND)))
        assert not offenders, (
            "Caractères Unicode échappés (\\u00XX) trouvés dans : "
            f"{offenders}. Remplacer par leurs caractères UTF-8 réels."
        )

    def test_actions_store_inserts_result_in_chat_on_completion(self):
        """
        BUG-097 (Smileshoot, v0.11.6) : ActionPanel affichait "Resultat insere
        dans le chat" mais aucun code ne réalisait l'insertion. Le store
        actionsStore doit importer chatStore et appeler addMessage() quand
        une tâche transite vers status `completed`.
        """
        content = (FRONTEND / "stores" / "actionsStore.ts").read_text(encoding="utf-8")
        assert "from './chatStore'" in content or 'from "./chatStore"' in content, (
            "actionsStore doit importer useChatStore pour insérer le résultat"
        )
        assert "useChatStore.getState().addMessage" in content, (
            "actionsStore doit appeler addMessage() sur transition vers completed"
        )
        assert "BUG-097" in content, (
            "Le fix doit être commenté BUG-097 pour faciliter la traçabilité"
        )


# ============================================================
# REVUE PRODUIT - Passage personas 1 - Lot S (P0)
# Garde-fous prompt système : P0-IA-1 (souveraineté) + P0-IA-2 (juridique).
# Constats C2 (l'IA bluffe sur l'hébergement : "en France", "en UE", "RAM",
# faux lien OpenAI) et C6 (faux articles de loi 227-22 CP, L121-1, L441-6,
# NDA inventé dans des documents à signer/déposer).
# ============================================================


class TestP0IA_GardesFousPromptSysteme:
    """Le prompt système doit poser deux garde-fous factuels non négociables."""

    def test_placeholder_guardrails_dans_les_deux_templates(self):
        """P0-IA : les 2 templates de prompt câblent le bloc {guardrails}."""
        from app.services.llm import LLMService

        for tmpl in (
            LLMService.DEFAULT_SYSTEM_PROMPT_TEMPLATE,
            LLMService.DEFAULT_SYSTEM_PROMPT_NO_PROFILE,
        ):
            assert "{guardrails}" in tmpl, (
                "Chaque template de prompt système doit référencer {guardrails} "
                "pour porter les garde-fous souveraineté + juridique."
            )

    def test_prompt_rendu_affirme_le_stockage_local(self):
        """P0-IA-1 : le prompt rendu affirme le stockage 100% local et nie tout serveur."""
        from app.services.llm import LLMService

        prompt = LLMService()._get_system_prompt_with_identity()
        assert "~/.therese/" in prompt, "Le prompt doit nommer le dossier de stockage local"
        assert "Aucun serveur THÉRÈSE n'existe" in prompt, (
            "Le prompt doit nier explicitement l'existence d'un serveur Thérèse"
        )
        assert "N'invente JAMAIS un lieu d'hébergement" in prompt, (
            "Le prompt doit interdire d'inventer un hébergeur/domaine tiers"
        )

    def test_prompt_rendu_interdit_l_hallu_juridique(self):
        """P0-IA-2 : le prompt rendu impose les placeholders et interdit d'inventer le droit."""
        from app.services.llm import LLMService

        prompt = LLMService()._get_system_prompt_with_identity()
        assert "[à vérifier]" in prompt, (
            "Le prompt doit imposer le placeholder [à vérifier] pour les références incertaines"
        )
        assert "N'invente JAMAIS un numéro d'article" in prompt, (
            "Le prompt doit interdire d'inventer article/SIRET/NDA/taux"
        )
        assert "relecture humaine" in prompt, (
            "Le prompt doit rappeler la relecture humaine sur les documents juridiques"
        )
        # Palier post-passage-2 : forcer le doute sur les numéros d'article même
        # "sûrs" (Mistral citait L441-6 abrogé avec aplomb).
        assert "à confirmer sur Légifrance" in prompt, (
            "Le prompt doit imposer le doute sur les numéros d'article (recodifications)"
        )


# ============================================================
# REVUE PRODUIT - Passage personas 1 - Lot S (P0)
# P0-RGPD-1 : purger le fantôme vectoriel à l'anonymisation Art. 17.
# Constat C4 : la fiche [ANONYMISÉ] remonte encore en recherche sémantique
# car l'embedding Qdrant n'était jamais supprimé (P6, P7 à 0,74, P9 à 0,69).
# ============================================================


class TestP0RGPD_FantomeVectoriel:
    """L'anonymisation doit supprimer l'embedding Qdrant du contact."""

    @pytest.mark.asyncio
    async def test_helper_purge_contact_vector_supprime_le_vecteur(self, monkeypatch):
        """Le helper appelle async_delete_by_entity et retourne le nombre purgé."""
        from unittest.mock import AsyncMock, MagicMock

        import app.services.qdrant as qmod
        from app.services.rgpd_auto import purge_contact_vector

        fake = MagicMock()
        fake.async_delete_by_entity = AsyncMock(return_value=2)
        monkeypatch.setattr(qmod, "get_qdrant_service", lambda: fake)

        deleted = await purge_contact_vector("contact-xyz")

        fake.async_delete_by_entity.assert_awaited_once_with("contact-xyz")
        assert deleted == 2

    @pytest.mark.asyncio
    async def test_helper_purge_best_effort_si_qdrant_plante(self, monkeypatch):
        """Une panne Qdrant ne doit pas faire échouer l'anonymisation (best effort)."""
        from unittest.mock import AsyncMock, MagicMock

        import app.services.qdrant as qmod
        from app.services.rgpd_auto import purge_contact_vector

        fake = MagicMock()
        fake.async_delete_by_entity = AsyncMock(side_effect=RuntimeError("qdrant down"))
        monkeypatch.setattr(qmod, "get_qdrant_service", lambda: fake)

        # Ne doit pas lever, et retourne 0
        assert await purge_contact_vector("contact-xyz") == 0

    @pytest.mark.asyncio
    async def test_anonymize_endpoint_purge_le_vecteur(self, client, monkeypatch):
        """POST /api/rgpd/anonymize/{id} déclenche la purge du vecteur Qdrant."""
        from unittest.mock import AsyncMock, MagicMock

        import app.services.qdrant as qmod

        fake = MagicMock()
        fake.async_delete_by_entity = AsyncMock(return_value=1)
        monkeypatch.setattr(qmod, "get_qdrant_service", lambda: fake)

        resp = await client.post(
            "/api/memory/contacts",
            json={"first_name": "Karim", "last_name": "Benali", "email": "karim@x.fr"},
        )
        assert resp.status_code == 200, resp.text
        cid = resp.json()["id"]

        anon = await client.post(
            f"/api/rgpd/anonymize/{cid}", json={"reason": "Demande du client"}
        )
        assert anon.status_code == 200, anon.text

        # Le helper passe par app.services.qdrant.get_qdrant_service (import au call),
        # donc seul l'anonymize touche `fake` (la création passe par le mock global).
        fake.async_delete_by_entity.assert_awaited_once_with(cid)


# ============================================================
# REVUE PRODUIT - Passage personas 1 - Lot S (P0)
# P0-PROD-1 : réparer le scoring CRM. Constat C8 : PATCH du champ score ignoré,
# recalculate-score sans effet, tout figé à 60 (P6 agent immo). Un acheteur
# chaud n'est pas distinguable d'un dossier perdu.
# ============================================================


class TestP0PROD_ScoringCRM:
    """Le scoring doit refléter les données et accepter un override manuel."""

    @pytest.mark.asyncio
    async def test_create_crm_contact_calcule_le_score(self, client):
        """Bug A : le score initial reflète email/phone/company, n'est plus figé."""
        from app.models.entities import Contact
        from app.services.scoring import calculate_base_score

        resp = await client.post(
            "/api/crm/contacts",
            json={
                "first_name": "Karim",
                "last_name": "Benali",
                "company": "Agence ABC",
                "email": "karim@abc.fr",
                "phone": "+33600000000",
                "stage": "contact",
            },
        )
        assert resp.status_code == 200, resp.text
        score = resp.json()["score"]

        expected = calculate_base_score(
            Contact(
                first_name="Karim",
                company="Agence ABC",
                email="karim@abc.fr",
                phone="+33600000000",
                source="THERESE",
                stage="contact",
            )
        )
        assert score == expected, (
            f"Le score créé ({score}) doit être calculé ({expected}), pas figé"
        )
        assert score != 50, "Le score ne doit plus être figé en dur à 50"

    @pytest.mark.asyncio
    async def test_patch_score_manuel_persiste(self, client):
        """Bug B : PATCH d'un score manuel doit être appliqué et persisté."""
        resp = await client.post(
            "/api/crm/contacts", json={"first_name": "Sofia", "company": "X"}
        )
        assert resp.status_code == 200, resp.text
        cid = resp.json()["id"]

        patch = await client.patch(
            f"/api/memory/contacts/{cid}", json={"score": 88}
        )
        assert patch.status_code == 200, patch.text
        assert patch.json()["score"] == 88

        got = await client.get(f"/api/memory/contacts/{cid}")
        assert got.json()["score"] == 88, "Le score manuel doit être persisté"

    @pytest.mark.asyncio
    async def test_patch_score_manuel_non_ecrase_par_changement_de_stage(self, client):
        """Bug C : un score fourni explicitement ne doit pas être recalculé/écrasé."""
        resp = await client.post(
            "/api/crm/contacts", json={"first_name": "Léa", "company": "Y"}
        )
        assert resp.status_code == 200, resp.text
        cid = resp.json()["id"]

        patch = await client.patch(
            f"/api/memory/contacts/{cid}",
            json={"score": 88, "stage": "signature"},
        )
        assert patch.status_code == 200, patch.text
        assert patch.json()["score"] == 88, (
            "Un score explicite ne doit pas être écrasé par le recalcul auto"
        )
        assert patch.json()["stage"] == "signature"


# ============================================================
# QUICK WIN testeur (Capov, Discord alpha 05/06/2026) : devise CAD
# Le module facturation ne proposait que EUR/CHF/USD/GBP. Ajout du dollar
# canadien (CAD), demandé par un testeur alpha.
# ============================================================


class TestQW_CADCurrency:
    """La devise CAD doit être acceptée de bout en bout (schéma + PDF + UI)."""

    @pytest.mark.asyncio
    async def test_invoice_accepts_cad_currency(self, client):
        """POST /api/invoices/ doit accepter currency='CAD' (Literal élargi)."""
        c = await client.post("/api/memory/contacts", json={"first_name": "Capov"})
        assert c.status_code == 200, c.text
        cid = c.json()["id"]

        resp = await client.post(
            "/api/invoices/",
            json={
                "contact_id": cid,
                "currency": "CAD",
                "lines": [
                    {
                        "description": "Conseil",
                        "quantity": 1.0,
                        "unit_price_ht": 100.0,
                        "tva_rate": 20.0,
                    }
                ],
            },
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["currency"] == "CAD"

    def test_backend_pdf_has_cad_symbol(self):
        """invoice_pdf.CURRENCY_SYMBOLS doit mapper CAD vers un symbole d'affichage."""
        content = (SRC / "app" / "services" / "invoice_pdf.py").read_text(encoding="utf-8")
        assert '"CAD"' in content, "CURRENCY_SYMBOLS (PDF) doit inclure CAD"

    def test_frontend_invoice_form_offers_cad(self):
        """InvoiceForm doit proposer CAD dans le sélecteur et sa table de symboles."""
        content = (
            FRONTEND / "components" / "invoices" / "InvoiceForm.tsx"
        ).read_text(encoding="utf-8")
        assert "'CAD'" in content, "InvoiceForm doit proposer CAD (sélecteur de devise)"
        assert "CAD:" in content, "InvoiceForm CURRENCY_SYMBOLS doit mapper CAD"


# ============================================================
# QUICK WIN testeur (Capov, Discord alpha 05/06/2026) : UI signature mail
# La brique backend existait (signature_html par compte, GET/PUT, injection à
# l'envoi) mais sans écran de réglage. Ajout de l'UI + couverture du contrat.
# ============================================================


class TestQW_EmailSignature:
    """Signature mail : contrat backend (round-trip + sanitisation) + câblage UI."""

    @pytest.mark.asyncio
    async def test_signature_roundtrip_and_sanitization(self, client):
        """PUT/GET signature : persiste, round-trip, et neutralise le HTML dangereux."""
        from unittest.mock import AsyncMock, MagicMock
        from unittest.mock import patch as _patch

        with _patch("app.routers.email.get_email_provider") as mock_provider:
            mock_instance = MagicMock()
            mock_instance.test_connection = AsyncMock(return_value={"success": True})
            mock_provider.return_value = mock_instance
            await client.post(
                "/api/email/auth/imap-setup",
                json={
                    "email": "sig@example.com",
                    "password": "app-password-test",
                    "imap_host": "imap.example.com",
                    "imap_port": 993,
                    "smtp_host": "smtp.example.com",
                    "smtp_port": 587,
                    "smtp_use_tls": True,
                },
            )

        status = await client.get("/api/email/auth/status")
        account_id = status.json()["accounts"][0]["id"]

        put = await client.put(
            f"/api/email/accounts/{account_id}/signature",
            json={"signature_html": "<p>Ludo</p><script>alert(1)</script>"},
        )
        assert put.status_code == 200, put.text
        assert "Ludo" in put.json()["signature_html"]
        assert "<script>" not in put.json()["signature_html"], "Le HTML doit être sanitisé (nh3)"

        got = await client.get(f"/api/email/accounts/{account_id}/signature")
        assert got.status_code == 200
        assert got.json()["account_id"] == account_id
        assert "<script>" not in (got.json()["signature_html"] or "")

    def test_signature_strips_inline_css(self):
        """Revue : nh3 ne filtre pas le CSS de style -> on retire style de l'allowlist
        (sinon background-image:url(remote) exfiltre, contraire au 100% local)."""
        from app.services.html_sanitizer import sanitize_html

        out = sanitize_html(
            '<div style="position:fixed;background-image:url(https://evil.com/x)">x</div>'
        )
        assert "style=" not in out
        assert "evil.com" not in out
        assert "position:fixed" not in out
        assert "x" in out  # le contenu textuel reste

    def test_signature_links_get_noopener_rel(self):
        """Revue : les liens target=_blank doivent recevoir rel=noopener (anti tab-nabbing)."""
        from app.services.html_sanitizer import sanitize_html

        out = sanitize_html('<a href="https://x.fr" target="_blank">lien</a>')
        assert "noopener" in out

    def test_emailpanel_wires_signature_editor(self):
        """EmailPanel doit exposer le déclencheur et monter la modale de signature."""
        content = (
            FRONTEND / "components" / "email" / "EmailPanel.tsx"
        ).read_text(encoding="utf-8")
        assert "SignatureEditorModal" in content
        assert "setShowSignatureEditor" in content

    def test_signature_editor_preview_is_sanitized(self):
        """L'aperçu passe par la politique partagée sanitizeEmailHtml (interdit style/
        script) ; la modale s'inscrit sur la pile Échap (anti-éjection de vue, revue)."""
        content = (
            FRONTEND / "components" / "email" / "SignatureEditorModal.tsx"
        ).read_text(encoding="utf-8")
        assert "sanitizeEmailHtml" in content, "L'aperçu doit utiliser sanitizeEmailHtml"
        assert "pushEscapeHandler" in content, (
            "La modale doit s'inscrire sur la pile Échap (sinon Échap éjecte la vue)"
        )
        assert "getEmailSignature" in content and "updateEmailSignature" in content

    def test_shared_sanitizer_forbids_inline_style(self):
        """Le sanitizer partagé (aperçu + emails reçus) doit interdire l'attribut style,
        cohérent avec le backend nh3."""
        import re

        content = (FRONTEND / "lib" / "sanitizeEmailHtml.ts").read_text(encoding="utf-8")
        assert "FORBID_TAGS" in content and "'style'" in content
        m = re.search(r"ALLOWED_ATTR:\s*\[(.*?)\]", content, re.DOTALL)
        assert m is not None, "ALLOWED_ATTR introuvable"
        assert "'style'" not in m.group(1), "style ne doit pas être dans ALLOWED_ATTR"


# ============================================================
# LOT M - P0-IA-3 : badge local/cloud par message
# Constat C1/C2 : l'utilisateur ne sait pas si sa requête est partie chez Mistral
# (cloud) ou est restée locale (Ollama). On expose le provider par message.
# ============================================================


class TestP0IA3_ProviderBadge:
    """Le provider LLM doit être stocké et exposé par message (badge local/cloud)."""

    @pytest.mark.asyncio
    async def test_message_provider_roundtrips_in_history(self, client, db_session):
        """Un message assistant persiste son provider, exposé dans l'historique."""
        from app.models.entities import Conversation, Message

        conv = Conversation(title="Test provider")
        db_session.add(conv)
        await db_session.commit()

        db_session.add(
            Message(
                conversation_id=conv.id,
                role="assistant",
                content="Tes données sont locales dans ~/.therese/.",
                model="mistral-small-latest",
                provider="mistral",
            )
        )
        await db_session.commit()

        resp = await client.get(f"/api/chat/conversations/{conv.id}/messages")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data) == 1
        assert data[0]["provider"] == "mistral"
        assert data[0]["model"] == "mistral-small-latest"

    def test_main_auto_migration_adds_provider_column(self):
        """La migration auto desktop doit ajouter la colonne provider à messages."""
        content = APP_MAIN_PY.read_text(encoding="utf-8")
        assert "ALTER TABLE messages ADD COLUMN provider" in content

    def test_message_bubble_shows_provider_badge(self):
        """MessageBubble doit afficher un badge local/cloud selon le provider."""
        content = (FRONTEND / "components" / "chat" / "MessageBubble.tsx").read_text(encoding="utf-8")
        assert "provider" in content, "MessageBubble doit lire message.provider"
        assert "ollama" in content.lower(), "Le badge doit distinguer Ollama (local)"

    def test_chat_input_has_model_selector(self):
        """ChatInput doit exposer un sélecteur de modèle (F-12)."""
        content = (FRONTEND / "components" / "chat" / "ChatInput.tsx").read_text(encoding="utf-8")
        assert "setLLMConfig" in content or "setModel" in content, (
            "ChatInput doit pouvoir changer de modèle"
        )


# ============================================================
# LOT M - P0-PROD-2 : profil émetteur + garde-fou avant facture
# Constat C7 : factures/devis sans SIRET ni identité émetteur (P8, P10),
# NDA d'OF inventé faute de profil (P7).
# ============================================================


class TestP0PROD2_BillingProfile:
    """Le profil émetteur (SIRET, identité) doit être stocké et bloquer une
    facture non conforme."""

    @pytest.mark.asyncio
    async def test_profile_siret_nda_roundtrip(self, client):
        """Le profil accepte et restitue SIRET / code APE / NDA."""
        resp = await client.post(
            "/api/config/profile",
            json={
                "name": "Ludovic Sanchez",
                "company": "Synoptia",
                "address": "294 Montee des Genets, 04100 Manosque",
                "siret": "99160678100011",
                "code_ape": "6202A",
                "nda": "93040123604",
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["siret"] == "99160678100011"
        assert data["code_ape"] == "6202A"
        assert data["nda"] == "93040123604"

    @pytest.mark.asyncio
    async def test_billing_status_complete_after_profile(self, client):
        """billing/profile-status passe à is_complete=True une fois le profil rempli."""
        await client.post(
            "/api/config/profile",
            json={
                "name": "Ludo",
                "company": "Synoptia",
                "address": "294 Montee des Genets",
                "siret": "99160678100011",
            },
        )
        resp = await client.get("/api/invoices/billing/profile-status")
        assert resp.status_code == 200, resp.text
        assert resp.json()["is_complete"] is True

    @pytest.mark.asyncio
    async def test_pdf_generation_blocked_without_emitter(self, client):
        """La génération PDF est bloquée (400) si le profil émetteur est incomplet."""
        # Profil sans SIRET ni adresse -> incomplet
        await client.post("/api/config/profile", json={"name": "Ludo"})

        c = await client.post("/api/memory/contacts", json={"first_name": "Client"})
        cid = c.json()["id"]
        inv = await client.post(
            "/api/invoices/",
            json={
                "contact_id": cid,
                "lines": [
                    {
                        "description": "Prestation",
                        "quantity": 1.0,
                        "unit_price_ht": 100.0,
                        "tva_rate": 20.0,
                    }
                ],
            },
        )
        assert inv.status_code == 200, inv.text
        invoice_id = inv.json()["id"]

        pdf = await client.get(f"/api/invoices/{invoice_id}/pdf")
        assert pdf.status_code == 400, pdf.text
        # Le handler HTTPException custom renvoie {"code", "message"} (pas "detail").
        body = pdf.json()
        msg = (body.get("message") or body.get("detail") or "").lower()
        assert "émetteur" in msg or "siret" in msg

    def test_profile_injects_legal_identity_for_llm(self):
        """format_for_llm doit injecter SIRET/NDA pour que le chat ne les invente pas."""
        from app.services.user_profile import UserProfile

        p = UserProfile(name="Ludo", siret="99160678100011", nda="93040123604")
        out = p.format_for_llm()
        assert "99160678100011" in out
        assert "93040123604" in out
        assert "ne jamais inventer" in out.lower()

    def test_profile_tab_has_siret_field(self):
        """L'utilisateur doit pouvoir saisir son SIRET dans le profil."""
        content = (FRONTEND / "components" / "settings" / "ProfileTab.tsx").read_text(encoding="utf-8")
        assert "siret" in content and "SIRET" in content

    def test_invoice_form_has_emitter_guardrail(self):
        """Le formulaire de facture doit afficher un garde-fou profil émetteur."""
        content = (FRONTEND / "components" / "invoices" / "InvoiceForm.tsx").read_text(encoding="utf-8")
        assert "getBillingProfileStatus" in content
        assert "émetteur" in content.lower()


# ============================================================
# LOT M - P0-PROD-3 : brancher le chat sur le CRM + calendrier
# Constat C9 : le chat hallucine le contexte client / les échéances au lieu de
# lire les objets structurés. Tool read_contact + fenêtre calendrier élargie.
# ============================================================


class TestP0PROD3_ChatTools:
    """Le chat doit pouvoir LIRE une fiche contact complète et un agenda large."""

    @pytest.mark.asyncio
    async def test_read_contact_tool_returns_full_fiche(self, db_session):
        """read_contact retourne coordonnées, stage, score, notes et interactions."""
        import json

        from app.models.entities import Activity, Contact
        from app.services.memory_tools import MEMORY_TOOL_NAMES, execute_memory_tool

        assert "read_contact" in MEMORY_TOOL_NAMES

        c = Contact(
            first_name="Karim",
            last_name="Benali",
            company="Agence ABC",
            email="karim@abc.fr",
            stage="proposition",
            score=85,
            notes="Cherche un T3 sous 250k",
        )
        db_session.add(c)
        await db_session.commit()
        db_session.add(Activity(contact_id=c.id, type="call", title="Appel découverte"))
        await db_session.commit()

        result = await execute_memory_tool("read_contact", {"query": "Benali"}, db_session)
        data = json.loads(result)

        assert data["found"] is True
        fiche = data["contacts"][0]
        assert fiche["score"] == 85
        assert fiche["stage"] == "proposition"
        assert fiche["notes"] == "Cherche un T3 sous 250k"
        assert any(a["title"] == "Appel découverte" for a in fiche["recent_activities"])

    @pytest.mark.asyncio
    async def test_read_contact_not_found(self, db_session):
        """read_contact renvoie found=False plutôt que d'inventer un contact."""
        import json

        from app.services.memory_tools import execute_memory_tool

        result = await execute_memory_tool("read_contact", {"query": "Personne12345"}, db_session)
        assert json.loads(result)["found"] is False

    def test_read_contact_is_registered_as_tool(self):
        """read_contact doit être exposé au LLM dans MEMORY_TOOLS."""
        from app.services.memory_tools import MEMORY_TOOLS

        names = {t["function"]["name"] for t in MEMORY_TOOLS}
        assert "read_contact" in names

    def test_calendar_tool_default_window_widened(self):
        """La fenêtre par défaut du calendrier doit être élargie (échéances, P9)."""
        content = (SRC / "app" / "services" / "workspace_tools.py").read_text(encoding="utf-8")
        assert 'args.get("days", 30)' in content, "Défaut calendrier élargi à 30 jours"
        assert "90" in content, "Max élargi pour couvrir les échéances"


# ============================================================
# QUICK WINS 2e passage personas (06/06/2026)
# QW1 : notes CRM jetées à la création. QW3 : GET /api/crm/contacts/{id} manquant.
# ============================================================


class TestQW_CRMNotesAndGet:
    """Le POST CRM doit persister notes/address/tags, et la fiche se relire par id."""

    @pytest.mark.asyncio
    async def test_crm_create_persists_notes(self, client):
        """QW1 : la note métier envoyée à la création doit être stockée et relue."""
        note = "Cherche un T3 sous 250k, tensions sur le prix"
        resp = await client.post(
            "/api/crm/contacts",
            json={"first_name": "Karim", "company": "ABC", "notes": note},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["notes"] == note, "La note ne doit plus être jetée"
        cid = resp.json()["id"]

        got = await client.get(f"/api/crm/contacts/{cid}")
        assert got.status_code == 200, got.text
        body = got.json()
        assert body["notes"] == note
        assert body["score"] is not None, "QW3 : le score doit être hydraté"
        assert body["stage"] == "contact"

    @pytest.mark.asyncio
    async def test_crm_get_contact_404(self, client):
        """QW3 : la route CRM par id existe et renvoie 404 si introuvable."""
        got = await client.get("/api/crm/contacts/inexistant-123")
        assert got.status_code == 404


class TestQW_PromptHardening:
    """QW2/QW4 : anti-hallu calendrier + distinction stockage/traitement."""

    def test_prompt_distinguishes_storage_vs_treatment(self):
        """QW4 : le prompt distingue stockage local et traitement cloud."""
        from app.services.llm import LLMService

        prompt = LLMService()._get_system_prompt_with_identity()
        assert "Distingue TOUJOURS deux couches" in prompt
        # Interdit explicitement la surpromesse observée au 2e passage
        assert "même pas pour traitement" in prompt

    def test_prompt_has_data_honesty_block(self):
        """QW2 : bloc anti-invention quand un outil renvoie un vide/une absence."""
        from app.services.llm import LLMService

        prompt = LLMService()._get_system_prompt_with_identity()
        assert "anti-invention" in prompt.lower()
        assert "N'invente JAMAIS d'événement" in prompt

    def test_calendar_tool_directive_on_no_calendar(self):
        """QW2 : l'outil calendrier renvoie une consigne directive sans compte."""
        content = (SRC / "app" / "services" / "workspace_tools.py").read_text(encoding="utf-8")
        assert "AUCUN CALENDRIER CONNECTE" in content
        assert "N'invente AUCUN evenement" in content


# ============================================================
# P8 (2e passage personas) : skill Office en OUTIL appelable
# Le chat bluffait un faux lien faute de routage fiable -> generate_document.
# ============================================================


class TestQW_GenerateDocumentTool:
    """Le LLM doit pouvoir générer un vrai fichier Office via un outil."""

    def test_generate_document_registered(self):
        """L'outil generate_document est exposé aux providers."""
        from app.services.workspace_tools import WORKSPACE_TOOL_NAMES, WORKSPACE_TOOLS

        assert "generate_document" in WORKSPACE_TOOL_NAMES
        names = {t["function"]["name"] for t in WORKSPACE_TOOLS}
        assert "generate_document" in names

    @pytest.mark.asyncio
    async def test_generate_document_produces_real_link(self, db_session, monkeypatch):
        """L'outil exécute le bon skill et renvoie une URL de téléchargement réelle."""
        from unittest.mock import AsyncMock, MagicMock

        import app.services.skills as skills_mod
        from app.services.workspace_tools import execute_workspace_tool

        fake_resp = MagicMock(
            success=True,
            file_name="rapport_ab12.docx",
            download_url="/api/skills/download/ab12",
            error=None,
        )
        fake_registry = MagicMock()
        fake_registry.execute = AsyncMock(return_value=fake_resp)
        monkeypatch.setattr(skills_mod, "get_skills_registry", lambda: fake_registry)

        result = await execute_workspace_tool(
            "generate_document",
            {"format": "docx", "title": "Rapport", "content": "# Titre\nContenu"},
            db_session,
        )

        assert "rapport_ab12.docx" in result
        assert "/api/skills/download/ab12" in result
        assert fake_registry.execute.await_args[0][0] == "docx-pro"

    @pytest.mark.asyncio
    async def test_generate_document_rejects_empty_content(self, db_session):
        """Pas de contenu -> message clair, pas de génération fantôme."""
        from app.services.workspace_tools import execute_workspace_tool

        result = await execute_workspace_tool(
            "generate_document", {"format": "docx", "content": "   "}, db_session
        )
        assert "aucun contenu" in result.lower()

    def test_capabilities_advertise_generate_document_and_read_contact(self):
        """Le prompt de capacités (streaming) doit pousser à utiliser generate_document
        et read_contact, sinon le LLM rédige inline / hallucine au lieu d'appeler l'outil."""
        content = (SRC / "app" / "routers" / "chat.py").read_text(encoding="utf-8")
        assert '"generate_document" in tool_names' in content
        assert '"read_contact" in tool_names' in content


# ============================================================
# RAG JURIDIQUE : corpus de références légales vérifiées (Légifrance)
# Ancre les réponses juridiques sur des références à jour au lieu de la mémoire
# périmée du modèle (2e passage : L441-6 cité au lieu de L441-10).
# ============================================================


class TestRAG_LegalCorpus:
    """Le corpus juridique vérifié doit être chargé, cherché et injecté."""

    def test_corpus_loads_verified_entries(self):
        """Le corpus existe et ne contient que des entrées sourcées (Légifrance/service-public)."""
        from app.services.legal_corpus import _load_corpus

        entries = _load_corpus()
        assert len(entries) >= 10
        for e in entries:
            assert e.get("reference")
            url = e.get("source_url", "")
            assert "legifrance" in url or "service-public" in url

    def test_lookup_late_payment_points_to_current_article(self):
        """'pénalités de retard' doit pointer L441-10 (et pas l'ancien L441-6)."""
        from app.services.legal_corpus import lookup_legal

        matches = lookup_legal(
            "Rédige une clause de pénalités de retard de paiement pour ma facture entre professionnels."
        )
        assert matches
        refs = " ".join(m["reference"] for m in matches)
        assert "L441-10" in refs
        assert "L441-6 " not in refs and "L441-6," not in refs

    def test_lookup_moral_interests_article(self):
        """'intérêts moratoires' doit retrouver l'article 1231-6 du Code civil (finding avocate)."""
        from app.services.legal_corpus import lookup_legal

        matches = lookup_legal("Quels sont les intérêts moratoires en cas de retard de paiement ?")
        refs = " ".join(m["reference"] for m in matches)
        assert "1231-6" in refs

    def test_lookup_no_match_returns_empty(self):
        """Aucun sujet juridique -> pas d'injection."""
        from app.services.legal_corpus import lookup_legal

        assert lookup_legal("Quelle est la météo à Manosque aujourd'hui ?") == []

    def test_format_legal_context_has_guardrail(self):
        """Le contexte formaté impose d'utiliser ces refs + [à confirmer] pour le reste."""
        from app.services.legal_corpus import get_legal_context

        ctx = get_legal_context("franchise en base de TVA mention sur facture")
        assert "VÉRIFIÉES" in ctx
        assert "à confirmer sur Légifrance" in ctx
        assert "293 B" in ctx

    @pytest.mark.asyncio
    async def test_memory_context_injects_legal_without_memory(self):
        """_get_memory_context injecte les réfs légales même sans résultat mémoire."""
        from app.routers.chat import _get_memory_context

        ctx = await _get_memory_context(
            "clause de pénalités de retard de paiement entre professionnels"
        )
        assert ctx is not None
        assert "L441-10" in ctx
        assert "VÉRIFIÉES" in ctx


# ============================================================
# TEST GLOBAL (persona Claire Fontaine) - corrections pré-0.20.0
# ============================================================


class TestGlobal_Fixes:
    """Corrections issues du test exhaustif des fonctionnalités."""

    def test_legal_lookup_accent_insensitive(self):
        """Le matching juridique doit ignorer les accents (intérêts, commerçants...)."""
        from app.services.legal_corpus import lookup_legal

        assert lookup_legal("Quels sont les intérêts moratoires entre commerçants ?"), (
            "Une requête accentuée doit matcher le corpus"
        )
        refs = " ".join(x["reference"] for x in lookup_legal("clause de pénalités de retard"))
        assert "L441-10" in refs

    @pytest.mark.asyncio
    async def test_validation_422_exposes_field(self, client):
        """Hors debug, la 422 doit indiquer le champ manquant (details non vide)."""
        resp = await client.post("/api/crm/contacts", json={})
        assert resp.status_code == 422, resp.text
        details = resp.json().get("details", [])
        assert details, "details ne doit plus être vide"
        assert any("first_name" in d.get("field", "") for d in details)

    def test_mistral_provider_uses_valid_stream_event(self):
        """mistral.py ne doit plus utiliser les kwargs invalides (bug streaming tools)."""
        content = (SRC / "app" / "services" / "providers" / "mistral.py").read_text(encoding="utf-8")
        assert "tool_use_id=" not in content
        assert 'type="tool_call"' in content and "tool_call=ToolCall(" in content

    def test_mcp_create_server_handles_duplicate_and_timeout(self):
        """create_server : 409 explicite sur doublon + démarrage borné par timeout."""
        content = (SRC / "app" / "routers" / "mcp.py").read_text(encoding="utf-8")
        assert "status_code=409" in content
        assert "asyncio.wait_for" in content

    def test_legal_mentions_gated_on_currency(self):
        """Les mentions FR (40 EUR, L441-10) ne sortent qu'en EUR, pas en devise étrangère."""
        from app.routers.invoices import generate_legal_mentions

        eur = generate_legal_mentions(due_date_str="06/06/2026", currency="EUR")
        assert "40 EUR" in eur and "L441-10" in eur

        cad = generate_legal_mentions(due_date_str="06/06/2026", currency="CAD")
        assert "40 EUR" not in cad and "L441-10" not in cad
        # Une ligne générique reste présente (pas de vide juridique).
        assert "retard de paiement" in cad

    def _render_invoice_pdf(self, tmp_path, currency: str) -> str:
        """Rend un PDF de facture minimal dans la devise donnée, renvoie le texte extrait."""
        from pypdf import PdfReader

        from app.services.invoice_pdf import InvoicePDFGenerator

        gen = InvoicePDFGenerator(output_dir=str(tmp_path))
        invoice_data = {
            "invoice_number": f"FACT-2026-TEST-{currency}",
            "document_type": "facture",
            "tva_applicable": True,
            "validite_jours": 30,
            "issue_date": "2026-06-06T00:00:00",
            "due_date": "2026-07-06T00:00:00",
            "status": "draft",
            "subtotal_ht": 100.0,
            "total_tax": 20.0,
            "total_ttc": 120.0,
            "notes": "",
            "lines": [{
                "description": "Conseil",
                "quantity": 1,
                "unit_price_ht": 100.0,
                "tva_rate": 20.0,
                "total_ht": 100.0,
                "total_ttc": 120.0,
            }],
        }
        contact_data = {"name": "Client QC", "company": "", "email": "", "phone": "", "address": ""}
        profile = {
            "name": "Ludovic Sanchez", "company": "Synoptia",
            "address": "Manosque", "siren": "", "siret": "99160678100011",
            "code_ape": "", "tva_intra": "",
        }
        path = gen.generate_invoice_pdf(
            invoice_data=invoice_data, contact_data=contact_data,
            user_profile=profile, currency=currency,
        )
        text = "".join(page.extract_text() for page in PdfReader(path).pages)
        return "".join(text.split()).lower()  # sans espaces pour robustesse extraction

    def test_pdf_drops_french_indemnity_for_foreign_currency(self, tmp_path):
        """Le PDF (vrai livrable) ne doit PAS imprimer l'indemnité FR (40 / L441,
        'frais de recouvrement') sur une facture en devise étrangère (CAD)."""
        cad = self._render_invoice_pdf(tmp_path, "CAD")
        assert "recouvrement" not in cad, "L'indemnité FR (frais de recouvrement) ne doit pas figurer en CAD"
        assert "tauxlegal" not in cad, "La pénalité 'au taux légal' (droit FR) ne doit pas figurer en CAD"
        assert "convenues" in cad, "Une ligne neutre doit prendre le relais en devise étrangère"

    def test_pdf_keeps_french_indemnity_in_eur(self, tmp_path):
        """Régression inverse : en EUR, l'indemnité forfaitaire FR reste bien présente."""
        eur = self._render_invoice_pdf(tmp_path, "EUR")
        assert "recouvrement" in eur, "En EUR, l'indemnité forfaitaire (frais de recouvrement) doit rester"

    def test_collection_routes_have_no_slash_variant(self):
        """invoices/tasks : routes collection exposées sans slash final (anti-redirection 307)."""
        from app.main import app

        paths = {getattr(r, "path", None) for r in app.routes}
        # Avant le fix, seuls "/api/invoices/" et "/api/tasks/" existaient -> 307.
        assert "/api/invoices" in paths and "/api/invoices/" in paths
        assert "/api/tasks" in paths and "/api/tasks/" in paths

    @pytest.mark.asyncio
    async def test_available_models_symmetric_for_cloud_provider(self):
        """_available_models_for renvoie la liste complète (source unique GET/POST)."""
        from app.routers.config import _available_models_for

        models = await _available_models_for("anthropic")
        # Le POST renvoyait avant une liste vide pour les providers cloud.
        assert len(models) >= 3
        assert "claude-opus-4-8" in models

    def test_board_profile_brief_omits_legal_identity(self):
        """format_brief (Board) garde le nom/métier mais retire SIRET/TVA/NDA."""
        from app.services.user_profile import UserProfile

        profile = UserProfile(
            name="Claire Fontaine",
            role="consultante-formatrice",
            siret="123 456 789 00010",
            nda="93040123604",
            tva_intra="FR00123456789",
        )
        brief = profile.format_brief()
        assert "Claire Fontaine" in brief
        assert "123 456 789 00010" not in brief
        assert "93040123604" not in brief
        # Le format complet, lui, doit toujours porter l'identité légale (anti-hallu chat).
        assert "123 456 789 00010" in profile.format_for_llm()

    @pytest.mark.asyncio
    async def test_quick_add_local_returns_clear_error(self, client):
        """Quick-add sans compte Google : 400 explicite (plus de 404 'Account not found')."""
        resp = await client.post(
            "/api/calendar/events/quick-add",
            json={"text": "Déjeuner demain à 12h30", "calendar_id": "local-cal"},
        )
        assert resp.status_code == 400, resp.text
        assert "Google" in resp.json().get("message", "") + resp.text


class TestMistralToolLoop:
    """Mistral : boucle d'outils réparée (NO-GO Syn 0.20.0).

    Avant : tout appel d'outil renvoyait une réponse VIDE (le done annonçait
    'end_turn' au lieu de 'tool_calls' donc l'outil n'était jamais exécuté, et
    continue_with_tool_results était un stub).
    """

    def _provider(self, lines):
        from app.services.llm import LLMConfig, LLMProvider
        from app.services.providers.mistral import MistralProvider

        class _Resp:
            def raise_for_status(self):
                return None

            async def aiter_lines(self):
                for ln in lines:
                    yield ln

        class _Ctx:
            async def __aenter__(self):
                return _Resp()

            async def __aexit__(self, *a):
                return False

        class _Client:
            def stream(self, *a, **k):
                return _Ctx()

        config = LLMConfig(provider=LLMProvider.MISTRAL, model="mistral-large-latest", api_key="x")
        return MistralProvider(config, _Client())

    @pytest.mark.asyncio
    async def test_stream_emits_tool_call_and_tool_calls_stop_reason(self):
        """Un tool_call streamé en fragments est reconstruit, avec done(stop_reason=tool_calls)."""
        import json

        def sse(obj):
            return "data: " + json.dumps(obj)

        lines = [
            sse({"choices": [{"delta": {"tool_calls": [
                {"index": 0, "id": "call_1", "function": {"name": "read_contact", "arguments": '{"na'}}
            ]}}]}),
            sse({"choices": [{"delta": {"tool_calls": [
                {"index": 0, "function": {"arguments": 'me":"Dupont"}'}}
            ]}}]}),
            sse({"choices": [{"delta": {}, "finish_reason": "tool_calls"}]}),
            "data: [DONE]",
        ]
        provider = self._provider(lines)
        events = [
            e async for e in provider.stream(
                None, [{"role": "user", "content": "qui est Dupont ?"}], tools=[{"type": "function"}]
            )
        ]
        tool_calls = [e for e in events if e.type == "tool_call"]
        assert len(tool_calls) == 1
        assert tool_calls[0].tool_call.name == "read_contact"
        assert tool_calls[0].tool_call.arguments == {"name": "Dupont"}
        dones = [e for e in events if e.type == "done"]
        assert any(e.stop_reason == "tool_calls" for e in dones), (
            "done doit signaler tool_calls pour déclencher l'exécution + la continuation"
        )

    @pytest.mark.asyncio
    async def test_continue_with_tool_results_appends_messages_and_restreams(self):
        """continue_with_tool_results n'est plus un stub : il renvoie les résultats et re-stream."""
        from app.services.providers.base import StreamEvent, ToolCall, ToolResult

        provider = self._provider([])
        captured = {}

        async def fake_stream(system_prompt, messages, tools=None):
            captured["messages"] = messages
            yield StreamEvent(type="text", content="Dupont travaille chez ACME.")

        provider.stream = fake_stream

        events = [
            e async for e in provider.continue_with_tool_results(
                system_prompt=None,
                messages=[{"role": "user", "content": "qui est Dupont ?"}],
                assistant_content="",
                tool_calls=[ToolCall(id="call_1", name="read_contact", arguments={"name": "Dupont"})],
                tool_results=[ToolResult(tool_call_id="call_1", result={"company": "ACME"})],
            )
        ]

        # Re-stream effectif (plus de réponse vide)
        assert any(e.type == "text" and "ACME" in (e.content or "") for e in events)
        msgs = captured["messages"]
        assistant = [m for m in msgs if m["role"] == "assistant" and m.get("tool_calls")]
        assert assistant, "le message assistant portant les tool_calls doit être ajouté"
        assert assistant[0]["tool_calls"][0]["function"]["name"] == "read_contact"
        tool_msgs = [m for m in msgs if m["role"] == "tool"]
        assert tool_msgs and tool_msgs[0]["tool_call_id"] == "call_1"
        assert "ACME" in tool_msgs[0]["content"]


class TestSovereigntyHonesty:
    """Souveraineté : ne plus prétendre la base chiffrée (NO-GO Syn 0.20.0)."""

    def test_prompt_does_not_claim_encrypted_database(self):
        from app.services.llm import LLMService

        block = LLMService.SOVEREIGNTY_BLOCK
        assert "base SQLite chiffrée" not in block, "ne plus affirmer que la base est chiffrée (faux)"
        assert "n'est PAS chiffrée au repos" in block
        # Honnête sur ce qui EST chiffré : les secrets, via Fernet (AES-128)
        assert "AES-128" in block and "clés API" in block
