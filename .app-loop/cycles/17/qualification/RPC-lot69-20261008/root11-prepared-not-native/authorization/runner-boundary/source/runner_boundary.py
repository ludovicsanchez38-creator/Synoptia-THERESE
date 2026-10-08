"""Deux dérivations préparatoires fermées ; aucun I/O, lancement ou admission.

Appliquer à l'overlay avant son émission et au blueprint avant la dérivation
SQL de la racine fraîche. Le manifeste initial des onze copies reste intact.
"""
from __future__ import annotations

import ast
import copy
import hashlib
from pathlib import Path

RUNNER_SHA = "8150bae5865dea1a27179b2ae65bbcbbc7710d44825b3a0da93b14edc6d54d76"
BLUEPRINT_SHA = "f55bd3522a22207195070d14c84be67e420e848d43ed34ec98f5ceafc72e60ad"
RUNNER_PATH = "runtime/calibrate-test-runner.py"
ROOTDIR_BEFORE = 'command = ([str(PYTHON), "-m", "pytest", "--noconftest", str(pytest_source),'
ROOTDIR_AFTER = 'command = ([str(PYTHON), "-m", "pytest", "--noconftest", f"--rootdir={out}", str(pytest_source),'
HOST_BEFORE = '}, test: {{globals:'
HOST_AFTER = '}, server: {{host: "127.0.0.1"}}, test: {{globals:'
BLUEPRINT_BEFORE = ('argv = [str(QA_PYTHON), "-m", "pytest", "--noconftest",\n'
                    '                        str(test_out / "test_temoin_c17.py")')
BLUEPRINT_AFTER = ('argv = [str(QA_PYTHON), "-m", "pytest", "--noconftest",\n'
                   '                        "--rootdir=" + str(test_out), str(test_out / "test_temoin_c17.py")')


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def once(source: str, before: str, after: str) -> str:
    need(source.count(before) == 1, "Ancre exacte unique requise")
    return source.replace(before, after, 1)


def derive_runner(source: str) -> str:
    need(type(source) is str and sha(source.encode()) == RUNNER_SHA, "Préimage runner SHA différente")
    result = once(once(source, ROOTDIR_BEFORE, ROOTDIR_AFTER), HOST_BEFORE, HOST_AFTER)
    restored = once(once(result, ROOTDIR_AFTER, ROOTDIR_BEFORE), HOST_AFTER, HOST_BEFORE)
    need(restored == source, "Delta runner hors des deux ancres")
    ast.parse(result)
    return result


def derive_blueprint(source: str) -> str:
    need(type(source) is str and sha(source.encode()) == BLUEPRINT_SHA, "Préimage blueprint SHA différente")
    result = once(source, BLUEPRINT_BEFORE, BLUEPRINT_AFTER)
    need(once(result, BLUEPRINT_AFTER, BLUEPRINT_BEFORE) == source, "Delta blueprint hors argv pytest")
    ast.parse(result)
    return result


def planned_ref(path: str, raw: bytes) -> dict:
    return {"path": path, "sha256": sha(raw), "bytes": len(raw)}


def derive_overlay(plan: dict) -> dict:
    """Recalculer les deux refs de la copie modifiée, pas seulement son payload.

Le constructeur précédent a fourni une table26 pure, non encore émise. Aucun
autre payload, contexte Chrome, metadata/env ou entrée du manifeste11 ne bouge.
"""
    need(type(plan) is dict and plan.get("schema") == "c17-wrapper-auxiliary-additive-plan-v1"
         and plan.get("scope") == "WRAPPER_CANARY" and plan.get("emitted") is False
         and plan.get("admission") is False and plan.get("OS_qualified") is False,
         "Overlay fermé et non émis requis")
    root = Path(plan["root"])
    need(root.parent == Path("/private/tmp") and root.name.startswith("therese-c17-wrapper-canary-"),
         "Racine WRAPPER fermée requise")
    path = str(root / "auxiliary-ports" / RUNNER_PATH)
    need(len(plan["payloads"]) == len(plan["outputs"]) == 26
         and len(plan["script_outputs"]) == 17, "Table overlay26/17 différente")
    raw = plan["payloads"][path]
    need(type(raw) is bytes and plan["outputs"][path] == planned_ref(path, raw)
         and plan["script_outputs"][RUNNER_PATH] == plan["outputs"][path],
         "Payload/ref runner préalable divergent")
    result = copy.deepcopy(plan)
    updated = derive_runner(raw.decode()).encode()
    result["payloads"][path] = updated
    reference = planned_ref(path, updated)
    result["outputs"][path] = reference
    result["script_outputs"][RUNNER_PATH] = reference
    # Aucun fichier écrit et aucune preuve observée n'est créée ici.
    return result
