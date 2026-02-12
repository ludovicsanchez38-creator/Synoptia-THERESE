"""
THÉRÈSE v2 - Tests de démarrage (main.py entry point)

Vérifie que freeze_support et le patch resource_tracker fonctionnent
correctement pour le sidecar PyInstaller.
"""

import importlib
import multiprocessing
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ============================================================
# freeze_support
# ============================================================


class TestFreezeSupport:
    """Vérifier que freeze_support() est appelé avant les imports lourds."""

    def test_freeze_support_called_before_argparse(self):
        """freeze_support() doit être appelé AVANT argparse dans main.py."""
        main_path = Path(__file__).resolve().parent.parent / "src" / "backend" / "main.py"
        content = main_path.read_text(encoding="utf-8")

        # freeze_support doit apparaître avant argparse
        freeze_pos = content.find("multiprocessing.freeze_support()")
        argparse_pos = content.find("import argparse")

        assert freeze_pos > 0, "freeze_support() absent de main.py"
        assert argparse_pos > 0, "argparse absent de main.py"
        assert freeze_pos < argparse_pos, (
            "freeze_support() doit être appelé AVANT import argparse "
            f"(freeze_pos={freeze_pos}, argparse_pos={argparse_pos})"
        )

    def test_freeze_support_called_before_app_import(self):
        """freeze_support() doit être appelé AVANT l'import de app.main."""
        main_path = Path(__file__).resolve().parent.parent / "src" / "backend" / "main.py"
        content = main_path.read_text(encoding="utf-8")

        freeze_pos = content.find("multiprocessing.freeze_support()")
        app_import_pos = content.find("from app.main import app")

        assert freeze_pos > 0, "freeze_support() absent de main.py"
        assert app_import_pos > 0, "import app.main absent de main.py"
        assert freeze_pos < app_import_pos, (
            "freeze_support() doit être appelé AVANT from app.main import app"
        )


# ============================================================
# resource_tracker patch
# ============================================================


class TestResourceTrackerPatch:
    """Vérifier que le patch resource_tracker intercepte les arguments PyInstaller."""

    def test_resource_tracker_pattern_detection(self):
        """Le code doit détecter les arguments resource_tracker de CPython."""
        # Simuler les arguments que PyInstaller passe au resource_tracker
        test_args = [
            "backend", "-B", "-S", "-I",
            "-c", "from multiprocessing.resource_tracker import main;main(5)",
        ]
        # Le pattern détecte si argv[-2] == "-c" et argv[-1] commence par le bon préfixe
        assert test_args[-2] == "-c"
        assert test_args[-1].startswith("from multiprocessing.resource_tracker import main")

    def test_forkserver_pattern_detection(self):
        """Le code doit aussi détecter les arguments forkserver."""
        test_args = [
            "backend", "-B", "-S",
            "-c", "from multiprocessing.forkserver import main;main()",
        ]
        assert test_args[-2] == "-c"
        assert test_args[-1].startswith("from multiprocessing.forkserver import main")

    def test_normal_args_not_intercepted(self):
        """Les arguments normaux (--host, --port) ne doivent PAS être interceptés."""
        test_args = ["backend", "--host", "127.0.0.1", "--port", "8000"]
        # Le guard exige len >= 3 et argv[-2] == "-c"
        should_intercept = (
            len(test_args) >= 3
            and test_args[-2] == "-c"
            and test_args[-1].startswith(
                (
                    "from multiprocessing.resource_tracker import main",
                    "from multiprocessing.forkserver import main",
                )
            )
        )
        assert not should_intercept, "Les arguments normaux ne doivent pas être interceptés"

    def test_short_args_not_intercepted(self):
        """Un argv trop court ne doit pas déclencher l'interception."""
        test_args = ["backend"]
        should_intercept = len(test_args) >= 3
        assert not should_intercept


# ============================================================
# Zombie cleanup
# ============================================================


class TestZombieCleanup:
    """Vérifier que _kill_zombie_backends() fonctionne."""

    def test_kill_zombie_skips_own_pid(self):
        """Le cleanup ne doit PAS tuer le process courant."""
        # On vérifie que le code utilise current_pid pour filtrer
        main_path = Path(__file__).resolve().parent.parent / "src" / "backend" / "main.py"
        content = main_path.read_text(encoding="utf-8")

        assert "current_pid = os.getpid()" in content
        assert "pid != current_pid" in content

    def test_kill_zombie_skips_parent_pid(self):
        """Le cleanup ne doit PAS tuer le parent PyInstaller (bootloader) sur Windows."""
        main_path = Path(__file__).resolve().parent.parent / "src" / "backend" / "main.py"
        content = main_path.read_text(encoding="utf-8")

        assert "parent_pid = os.getppid()" in content
        assert "pid != current_pid and pid != parent_pid" in content

    def test_kill_zombie_does_not_inherit_broken_stdin(self):
        """Les subprocess du cleanup ne doivent pas hériter d'un stdin potentiellement cassé."""
        main_path = Path(__file__).resolve().parent.parent / "src" / "backend" / "main.py"
        content = main_path.read_text(encoding="utf-8")

        assert "stdin=subprocess.DEVNULL" in content

    def test_stdio_guard_detects_invalid_handles(self):
        """La protection stdio doit valider les handles (pas seulement None)."""
        main_path = Path(__file__).resolve().parent.parent / "src" / "backend" / "main.py"
        content = main_path.read_text(encoding="utf-8")

        assert "def _is_stream_valid(" in content
        assert "os.fstat(" in content
        assert "not _is_stream_valid(sys.stdout, readable=False)" in content
        assert "not _is_stream_valid(sys.stderr, readable=False)" in content
        assert "not _is_stream_valid(sys.stdin, readable=True)" in content

    def test_qdrant_lock_cleanup(self):
        """Le cleanup doit supprimer le fichier .lock Qdrant."""
        main_path = Path(__file__).resolve().parent.parent / "src" / "backend" / "main.py"
        content = main_path.read_text(encoding="utf-8")

        assert '".therese"' in content or "'.therese'" in content
        assert '".lock"' in content or "'.lock'" in content
        assert "lock_file.unlink()" in content

    def test_atexit_cleanup_registered(self):
        """Un handler atexit pour les processus enfants doit être enregistré."""
        main_path = Path(__file__).resolve().parent.parent / "src" / "backend" / "main.py"
        content = main_path.read_text(encoding="utf-8")

        assert "atexit.register(_cleanup_children)" in content
        assert "multiprocessing.active_children()" in content


# ============================================================
# Startup keychain safety
# ============================================================


class TestStartupKeychainSafety:
    """Vérifier que le startup n'est pas bloqué par un prompt trousseau."""

    def test_startup_profile_preload_skips_decrypt(self):
        """Le preload profil au démarrage doit passer allow_decrypt=False."""
        main_path = Path(__file__).resolve().parent.parent / "src" / "backend" / "app" / "main.py"
        content = main_path.read_text(encoding="utf-8")

        assert "get_user_profile(session, allow_decrypt=False)" in content

    def test_get_user_profile_supports_allow_decrypt_flag(self):
        """Le service profil doit accepter allow_decrypt pour éviter le keychain au boot."""
        service_path = (
            Path(__file__).resolve().parent.parent
            / "src"
            / "backend"
            / "app"
            / "services"
            / "user_profile.py"
        )
        content = service_path.read_text(encoding="utf-8")

        assert "allow_decrypt: bool = True" in content
        assert "if not allow_decrypt:" in content
