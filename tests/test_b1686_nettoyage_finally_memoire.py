"""B-1686 : témoins mémoire du vrai finally de restore_backup.

Lecture AST uniquement du fichier produit ; aucun import produit, HTTP,
serveur, archive, base, clé, trousseau ou passphrase. Les seules créations
de fichiers sont celles de l'exécuteur qui capture les résultats du test.
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
source_bytes = SOURCE.read_bytes()
tree = ast.parse(source_bytes.decode())
restore = next(x for x in tree.body if isinstance(x, ast.AsyncFunctionDef) and x.name == "restore_backup")
matches = [
    x for x in restore.body if isinstance(x, ast.Try) and x.finalbody
    and any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "_rouvrir_la_base_apres_restauration"
            for s in x.finalbody for n in ast.walk(s))
]
assert len(matches) == 1
finally_source = matches[0].finalbody


class RemoveProductImports(ast.NodeTransformer):
    def visit_ImportFrom(self, node):
        if (node.module or "").startswith("app."):
            return None
        return node


body = [RemoveProductImports().visit(copy.deepcopy(x)) for x in finally_source]
function = ast.AsyncFunctionDef(
    name="vrai_finally", args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[],
        kw_defaults=[], defaults=[]), body=body, decorator_list=[], returns=None,
)
module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
assert not any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(module))
compiled_finally = compile(module, str(SOURCE), "exec")


def isolated_finally(cancel_at: str | None):
    state = SimpleNamespace(chat_suspended=True, maintenance_active=True,
        plaintext_present=True, unlink_missing_ok=None)
    reopen = AsyncMock(side_effect=asyncio.CancelledError if cancel_at == "reopen" else None)
    reload_mcp = AsyncMock(side_effect=asyncio.CancelledError if cancel_at == "mcp" else None)

    def resume_chat():
        state.chat_suspended = False

    def end_maintenance():
        state.maintenance_active = False

    def unlink_temporary(*, missing_ok):
        state.plaintext_present = False
        state.unlink_missing_ok = missing_ok

    resume = Mock(side_effect=resume_chat)
    end = Mock(side_effect=end_maintenance)
    unlink = Mock(side_effect=unlink_temporary)
    ns = {
        # Ce contrôle vise les trois nettoyages ; l’archive est déjà finalisée.
        "safety_finalized": True,
        "_rouvrir_la_base_apres_restauration": reopen,
        "get_mcp_service": lambda: SimpleNamespace(recharger_la_configuration=reload_mcp),
        "reprendre_les_creations_du_chat": resume,
        "maintenance_mode": SimpleNamespace(end=end),
        "decrypted_temp": SimpleNamespace(unlink=unlink),
        "logger": Mock(),
    }
    exec(compiled_finally, ns)
    return ns["vrai_finally"], state, (reopen, reload_mcp, resume, end, unlink)


class TestFinallyMemoire(unittest.IsolatedAsyncioTestCase):
    def require_cleanup(self, state, calls, case):
        reopen, reload_mcp, resume, end, unlink = calls
        observed = {"reopen_awaited": reopen.await_count,
                    "mcp_awaited": reload_mcp.await_count,
                    "chat_suspended": state.chat_suspended,
                    "maintenance_active": state.maintenance_active,
                    "plaintext_present": state.plaintext_present,
                    "resume_calls": resume.call_count,
                    "end_calls": end.call_count,
                    "unlink_calls": unlink.call_count}
        print(case, observed, flush=True)
        self.assertEqual(
            {"chat_suspended": state.chat_suspended,
             "maintenance_active": state.maintenance_active,
             "plaintext_present": state.plaintext_present},
            {"chat_suspended": False, "maintenance_active": False,
             "plaintext_present": False},
            "L'annulation se propage, mais le nettoyage local doit avoir lieu",
        )
        self.assertEqual(resume.call_count, 1)
        self.assertEqual(end.call_count, 1)
        unlink.assert_called_once_with(missing_ok=True)

    async def test_temoin_sain_execute_les_trois_gestes(self):
        block, state, calls = isolated_finally(None)
        await block()
        self.require_cleanup(state, calls, "healthy")

    async def test_annulation_reouverture_garde_nettoyage(self):
        block, state, calls = isolated_finally("reopen")
        with self.assertRaises(asyncio.CancelledError):
            await block()
        self.require_cleanup(state, calls, "cancel_at_reopen")

    async def test_annulation_mcp_garde_nettoyage(self):
        block, state, calls = isolated_finally("mcp")
        with self.assertRaises(asyncio.CancelledError):
            await block()
        self.require_cleanup(state, calls, "cancel_at_mcp")


if __name__ == "__main__":
    print("source", SOURCE, flush=True)
    print("source_sha256", hashlib.sha256(source_bytes).hexdigest(), flush=True)
    print("finally_statement_lines", finally_source[0].lineno,
          finally_source[-1].end_lineno, flush=True)
    print("scope mémoire uniquement; aucun import produit ni HTTP", flush=True)
    unittest.main(verbosity=2)
