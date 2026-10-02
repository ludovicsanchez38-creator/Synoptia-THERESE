"""B-1686 : chemin de finalisation de l'archive de sécurité, mémoire seulement.

On lit l'AST du vrai finally, les deux handlers du retour arrière et l'appel
normal au finaliseur. Aucun import produit, HTTP, archive réelle, DB, clé,
trousseau ou passphrase. Les objets archive/finaliseur sont des témoins mémoire.
"""
from __future__ import annotations

import ast
import asyncio
import copy
import hashlib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "src/backend/app/routers/data.py"
SOURCE_BYTES = SOURCE.read_bytes()
SOURCE_SHA = hashlib.sha256(SOURCE_BYTES).hexdigest()
TREE = ast.parse(SOURCE_BYTES.decode())
RESTORE = next(n for n in TREE.body if isinstance(n, ast.AsyncFunctionDef)
               and n.name == "restore_backup")


def calls_named(node, name):
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == name for n in ast.walk(node))


MAIN = next(n for n in RESTORE.body if isinstance(n, ast.Try) and n.finalbody
            and any(calls_named(x, "_rouvrir_la_base_apres_restauration")
                    for x in n.finalbody))
INNER = next(n for n in MAIN.body if isinstance(n, ast.Try) and n.handlers
             and isinstance(n.handlers[0].type, ast.Name)
             and n.handlers[0].type.id == "HTTPException")
# Conserver les initialisations et l'ordre du produit, avant ou après le fix.
INITIALIZATIONS = [n for n in RESTORE.body if isinstance(n, ast.Assign)
                   and RESTORE.body.index(n) < RESTORE.body.index(MAIN)
                   and any(isinstance(t, ast.Name) and t.id in
                           {"safety_finalized", "safety_kept"} for t in n.targets)]
NORMAL_AFTER = [n for n in RESTORE.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "safety_kept"
                        for t in n.targets)
                and calls_named(n, "_finalize_safety_archive")]



class RemoveProductImports(ast.NodeTransformer):
    def visit_ImportFrom(self, node):
        if (node.module or "").startswith("app."):
            return None
        return node


# Précondition synthétique : l'archive de sécurité a déjà été créée. Seule la
# restauration centrale est simulée. Les handlers, finally et l'appel normal
# restent ceux du produit, dans leur ordre de contrôle réel.
simulated_restore = ast.Expr(value=ast.Await(value=ast.Call(
    func=ast.Name(id="simuler_restauration", ctx=ast.Load()), args=[], keywords=[])))
inner = ast.Try(body=[simulated_restore], handlers=copy.deepcopy(INNER.handlers),
                orelse=[], finalbody=[])
main = ast.Try(body=[inner], handlers=[], orelse=[],
               finalbody=copy.deepcopy(MAIN.finalbody))
function = ast.AsyncFunctionDef(
    name="chemin_finalisation_reel",
    args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
    body=[*copy.deepcopy(INITIALIZATIONS), main, *copy.deepcopy(NORMAL_AFTER),
          ast.Return(value=ast.Name(id="safety_kept", ctx=ast.Load()))],
    decorator_list=[], returns=None,
)
module = RemoveProductImports().visit(ast.Module(body=[function], type_ignores=[]))
module = ast.fix_missing_locations(module)
assert not any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(module))
COMPILED = compile(module, str(SOURCE), "exec")


class MemoryHTTPError(Exception):
    """Témoin de l'exception produit, sans bibliothèque HTTP."""
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def isolated_path(cancel_at=None, error=None, kept=True):
    state = SimpleNamespace(safety_plain_present=True, decrypted_temp_present=True,
                            chat_suspended=True, maintenance_active=True,
                            safety_encrypted_present=False)
    reopen = AsyncMock(side_effect=asyncio.CancelledError if cancel_at == "reopen" else None)
    reload_mcp = AsyncMock(side_effect=asyncio.CancelledError if cancel_at == "mcp" else None)
    restore = AsyncMock(side_effect=error)
    archive = object()  # Pas un Path ; aucune méthode de fichier n'est disponible.
    included = ["temoin-synthetique"]

    def finalize(backup_dir, name, plain_archive, password, contents):
        assert plain_archive is archive
        assert password is None
        assert contents is included
        state.safety_plain_present = False
        state.safety_encrypted_present = kept
        return kept

    def resume():
        state.chat_suspended = False

    def end():
        state.maintenance_active = False

    def unlink(*, missing_ok):
        assert missing_ok is True
        state.decrypted_temp_present = False

    finalizer = Mock(side_effect=finalize)
    resume_mock = Mock(side_effect=resume)
    end_mock = Mock(side_effect=end)
    unlink_mock = Mock(side_effect=unlink)
    ns = {
        "simuler_restauration": restore,
        "_rouvrir_la_base_apres_restauration": reopen,
        "get_mcp_service": lambda: SimpleNamespace(recharger_la_configuration=reload_mcp),
        "reprendre_les_creations_du_chat": resume_mock,
        "maintenance_mode": SimpleNamespace(end=end_mock),
        "decrypted_temp": SimpleNamespace(unlink=unlink_mock),
        "_finalize_safety_archive": finalizer,
        "_rollback": Mock(return_value=True),
        "backup_dir": object(), "current_backup_name": "archive-simulee",
        "safety_archive": archive, "password": None, "safety_included": included,
        "HTTPException": MemoryHTTPError,
        "message_pour_ecran": lambda exc, *, ou: f"Erreur simulée {exc} {ou}",
        "logger": Mock(),
    }
    for n in TREE.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            if n.targets[0].id in {"DONNEES_INTACTES", "RETOUR_ARRIERE_REUSSI", "ECHEC_DU_RETOUR_ARRIERE"}:
                ns[n.targets[0].id] = ast.literal_eval(n.value)
    exec(COMPILED, ns)
    return ns["chemin_finalisation_reel"], state, finalizer, (reopen, reload_mcp)


class TestSafetyMemory(unittest.IsolatedAsyncioTestCase):
    def assert_finalized_once(self, label, state, finalizer, awaits):
        observed = {"finalizer_calls": finalizer.call_count,
                    "safety_plain_present": state.safety_plain_present,
                    "safety_encrypted_present": state.safety_encrypted_present,
                    "decrypted_temp_present": state.decrypted_temp_present,
                    "chat_suspended": state.chat_suspended,
                    "maintenance_active": state.maintenance_active,
                    "reopen_awaited": awaits[0].await_count,
                    "mcp_awaited": awaits[1].await_count}
        print(label, observed, flush=True)
        self.assertFalse(state.decrypted_temp_present)
        self.assertFalse(state.chat_suspended)
        self.assertFalse(state.maintenance_active)
        self.assertEqual(finalizer.call_count, 1,
                         "Le finaliseur de l'archive de sécurité doit être appelé une seule fois")
        self.assertFalse(state.safety_plain_present)

    async def test_succes_finalise_une_fois_et_conserve_le_resultat(self):
        path, state, finalizer, awaits = isolated_path(kept=True)
        self.assertTrue(await path())
        self.assert_finalized_once("success_kept", state, finalizer, awaits)
        self.assertTrue(state.safety_encrypted_present)

    async def test_succes_finalise_une_fois_et_supprime_le_temoin(self):
        path, state, finalizer, awaits = isolated_path(kept=False)
        self.assertFalse(await path())
        self.assert_finalized_once("success_deleted", state, finalizer, awaits)
        self.assertFalse(state.safety_encrypted_present)

    async def test_erreur_http_finalise_une_fois_avant_le_finally(self):
        error = MemoryHTTPError(409, "Refus simulé")
        path, state, finalizer, awaits = isolated_path(error=error)
        with self.assertRaises(MemoryHTTPError) as caught:
            await path()
        self.assertIs(caught.exception, error)
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(caught.exception.detail,
                         "Refus simulé L'état d'avant tentative est conservé en "
                         "sauvegarde chiffrée avec la passphrase saisie.")
        self.assert_finalized_once("error_http", state, finalizer, awaits)

    async def test_erreur_standard_finalise_une_fois_avant_le_finally(self):
        path, state, finalizer, awaits = isolated_path(error=RuntimeError("incident"))
        with self.assertRaises(MemoryHTTPError) as caught:
            await path()
        self.assertEqual(caught.exception.status_code, 500)
        self.assertEqual(caught.exception.detail,
                         "Erreur simulée incident pendant la restauration "
                         "Données restaurées à l'état précédent. "
                         "L'état d'avant tentative est conservé en sauvegarde chiffrée "
                         "avec la passphrase saisie.")
        self.assert_finalized_once("error_standard", state, finalizer, awaits)

    async def test_erreur_deja_finalisee_puis_annulation_ne_double_pas(self):
        path, state, finalizer, awaits = isolated_path(
            cancel_at="reopen", error=MemoryHTTPError(409, "Refus simulé"))
        with self.assertRaises(asyncio.CancelledError):
            await path()
        self.assert_finalized_once("error_then_cancel", state, finalizer, awaits)

    async def test_annulation_reouverture_finalise_archive_de_securite(self):
        path, state, finalizer, awaits = isolated_path(cancel_at="reopen")
        with self.assertRaises(asyncio.CancelledError):
            await path()
        self.assert_finalized_once("cancel_at_reopen", state, finalizer, awaits)

    async def test_annulation_mcp_finalise_archive_de_securite(self):
        path, state, finalizer, awaits = isolated_path(cancel_at="mcp")
        with self.assertRaises(asyncio.CancelledError):
            await path()
        self.assert_finalized_once("cancel_at_mcp", state, finalizer, awaits)


if __name__ == "__main__":
    print("source_sha256", SOURCE_SHA, flush=True)
    print("main_try_finally", MAIN.lineno, MAIN.end_lineno, flush=True)
    print("rollback_handlers", [(h.lineno, h.end_lineno) for h in INNER.handlers], flush=True)
    print("normal_finalizers_after_try", [(n.lineno, n.end_lineno) for n in NORMAL_AFTER], flush=True)
    print("scope mémoire/AST uniquement ; aucun import produit ni HTTP", flush=True)
    unittest.main(verbosity=2)
