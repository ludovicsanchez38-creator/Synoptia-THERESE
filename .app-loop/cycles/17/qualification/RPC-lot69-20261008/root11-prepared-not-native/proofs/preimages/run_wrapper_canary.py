#!/usr/bin/env python3
"""Coordinateur réel WRAPPER_CANARY, fermé à quatre parents instrument.

Cette CLI est destinée à la seule copie QA root. Le GO humain et le slot G1
exact sont fournis et revus par root ; aucun JSON créé ici ne les authentifie.
Les quinze RPC sont démarrés exclusivement par la Session lors des cinq vrais
wrappers. Ce fichier n'admet ni FULL, ni 78 recettes, ni profil utilisateur.
"""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import traceback
import urllib.request

import rpc_instrument_contract as contract
import wrapper_blueprint as blueprint


GO_SCHEMA = "c17-wrapper-canary-root-go-v1"
AUX_SCHEMA = "c17-wrapper-canary-auxiliary-physical-v1"
SOURCE_REFS_SCHEMA = "c17-wrapper-canary-source-refs-v1"
RESULT_SCHEMA = "c17-wrapper-canary-instrument-result-v1"
CHROME_JOBS = ("rpc-all-runtime_ui-visual_capture-network_capture",
               "rpc-screen-negative", "rpc-screen-positive-visual",
               "rpc-screen-positive-network", "rpc-screen-restored")
STAGES = ("calibrate", "B1753", "B1760", "B1753-power")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def now() -> str:
    return datetime.now(UTC).isoformat()


def exclusive_json(path: Path, value: dict) -> None:
    payload = (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()
    with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_WRONLY, 0o600), "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def same_ref(protocol, ref: dict, path: Path) -> bool:
    return (isinstance(ref, dict) and set(ref) == {"path", "sha256", "bytes"}
            and ref.get("path") == str(path) and protocol.reference(path) == ref)


def read_inputs(protocol, root: Path, go_sha256: str) -> tuple[dict, dict, list[dict], dict, dict]:
    """Entrées root exactes avant toute préémission ou Popen."""
    root = blueprint.exact_root(root)
    require(re.fullmatch(r"[a-f0-9]{64}", go_sha256 or "") is not None,
            "SHA du GO root obligatoire sur la CLI")
    go_path = root / "authorization/root-go.json"
    require(go_path.resolve(strict=True) == go_path and not go_path.is_symlink(),
            "GO root hors QA ou non canonique")
    go_ref = protocol.reference(go_path)
    require(go_ref["sha256"] == go_sha256, "GO root différent du SHA fourni par l'exécuteur")
    go = protocol.checked_json(go_ref, root=root)
    require(go.get("schema") == GO_SCHEMA and go.get("root") == str(root)
            and go.get("actor") == "/root" and go.get("head") == blueprint.HEAD
            and go.get("scope") == "WRAPPER_CANARY"
            and go.get("root_tool_authorization_verified") is True,
            "GO externe root non exact ; le JSON seul n'authentifie pas l'autorisation")
    checkout_ref = go.get("source_checkout_ref")
    refs_ref = go.get("source_refs_ref")
    auxiliary_ref = go.get("auxiliary_ref")
    require(all(isinstance(ref, dict) and ref.get("path") == str(root / "authorization" / name)
                for ref, name in ((checkout_ref, "source-checkout.json"),
                                  (refs_ref, "source-refs.json"),
                                  (auxiliary_ref, "auxiliary-physical.json"))),
            "Refs source/aux root hors chemins exacts")
    checkout = protocol.checked_json(checkout_ref, root=root)
    refs_data = protocol.checked_json(refs_ref, root=root)
    auxiliary = protocol.checked_json(auxiliary_ref, root=root)
    require(checkout.get("schema") == "c17-wrapper-canary-source-checkout-v1"
            and checkout.get("head") == blueprint.HEAD
            and checkout.get("product_source_root") == str(blueprint.QA_SOURCE),
            "Attestation checkout frais absente")
    refs = refs_data.get("source_refs")
    require(refs_data.get("schema") == SOURCE_REFS_SCHEMA and type(refs) is list
            and len(refs) >= 26 and len({item.get("path") for item in refs if isinstance(item, dict)}) == len(refs),
            "Références instrument26 absentes/doublonnées")
    for ref in refs:
        path = Path(ref["path"])
        require(path.is_absolute() and path.resolve(strict=True) == path
                and (path.is_relative_to(root) or path.is_relative_to(blueprint.QA_SOURCE))
                and same_ref(protocol, ref, path), "Source instrument modifiée avant préémission")
    require(auxiliary.get("schema") == AUX_SCHEMA and auxiliary.get("root") == str(root)
            and auxiliary.get("head") == blueprint.HEAD
            and set(auxiliary.get("auxiliary_context_refs", {})) == set(CHROME_JOBS)
            and isinstance(auxiliary.get("auxiliary_descriptors"), dict)
            and set(auxiliary["auxiliary_descriptors"]) == set(CHROME_JOBS),
            "Overlay/5 Chrome réels absents ; aucun fallback")
    git_ref = auxiliary.get("git_snapshot_ref")
    require(same_ref(protocol, git_ref, root / "auxiliary/git/snapshot.json"),
            "Snapshot Git physique absent/différent")
    expected_metadata = blueprint.auxiliary_metadata(root, git_ref=git_ref,
        chrome_context_refs=auxiliary["auxiliary_context_refs"])
    require(auxiliary.get("metadata_by_job") == expected_metadata,
            "Métadonnées auxiliaires différentes des huit vrais enfants")
    for job, ref in auxiliary["auxiliary_context_refs"].items():
        path = root / "auxiliary" / ("aux-chrome-" + job) / "context.json"
        require(same_ref(protocol, ref, path), "Contexte Chrome modifié/hors QA")
    require(isinstance(auxiliary.get("chrome_files_ref"), dict)
            and same_ref(protocol, auxiliary["chrome_files_ref"],
                         root / "authorization/chrome-files.json"),
            "Dossier Chrome/profil QA non pincé")
    return go_ref, checkout_ref, refs, auxiliary, go


def prepare_qa_directories(root: Path) -> None:
    """Seulement les parents de sorties QA ; jamais les neuf allocations futures."""
    root = blueprint.exact_root(root)
    require(root.resolve(strict=True) == root and root.is_dir() and not root.is_symlink(),
            "Root QA physique absent")
    paths = blueprint.paths(root)
    for folder in (root / "session-rpc", root / "output", root / "runtime/calibration",
                   paths["profile"], paths["home"], paths["tmp"], paths["data"],
                   paths["test_data"], paths["logs_data"], paths["vite_cache"]):
        require(folder == root or folder.is_relative_to(root), "Création hors QA")
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    for name in ("request", "ack", "cancel", "enrollment", "envelope"):
        (root / "session-rpc" / name).mkdir(mode=0o700, exist_ok=False)
    for path in (root / "session-rpc/context.json", root / "session-rpc/plan.json",
                 root / "binding.json", root / "decision.json", root / "runtime/pile-reprise.json",
                 root / "wrapper-canary-result.json"):
        require(not path.exists() and not path.is_symlink(), "Préémission/état QA déjà présent : " + str(path))


def compose_26_commands(root: Path, base21: dict[str, dict],
                        auxiliary_descriptors: dict[str, dict]) -> dict[str, dict]:
    require(type(base21) is dict and len(base21) == 21
            and type(auxiliary_descriptors) is dict and set(auxiliary_descriptors) == set(CHROME_JOBS),
            "Table 21+5 absente")
    commands = dict(base21)
    for job in CHROME_JOBS:
        row = auxiliary_descriptors[job]
        name = "aux-chrome-" + job
        require(isinstance(row, dict) and row.get("name") == name
                and row.get("role") == "auxiliary-" + name
                and row.get("deadline") == 50 and row.get("cwd") in (str(root), str(blueprint.QA_SOURCE))
                and type(row.get("argv")) is list and type(row.get("env")) is dict,
                "Descriptor Chrome root non exact : " + job)
        commands[name] = {"argv": row["argv"], "role": row["role"], "mode": "chrome",
            "timeout_seconds": 50, "env": row["env"], "cwd": row["cwd"],
            "stdout_path": row["stdout"], "stderr_path": row["stderr"],
            "combine_stderr": False, "derived_deadline": "start_monotonic_plus_exact_timeout"}
    require(len(commands) == 26, "Table exacte 21+5 non composée")
    return commands


def publish_and_bind(protocol, g1, root: Path, *, owner_identity: dict,
                     go_ref: dict, checkout_ref: dict, refs: list[dict], auxiliary: dict) -> tuple[dict, dict, dict]:
    """Owner vivant → plan exact → binding/décision root déjà autorisés hors fichier."""
    planned = blueprint.build_plan(protocol, root, owner_identity=owner_identity,
        deadline_monotonic=time.monotonic() + 2700, source_refs=refs,
        git_ref=auxiliary["git_snapshot_ref"],
        chrome_context_refs=auxiliary["auxiliary_context_refs"])
    published = contract.publish_prelaunch(protocol, planned["sealed"])
    st = root.stat()
    common = {"actor": "/root", "round_id": root.name, "round_name": "WRAPPER_CANARY",
              "qa_root": str(root), "head": blueprint.HEAD}
    commands = compose_26_commands(root, planned["commands"], auxiliary["auxiliary_descriptors"])
    binding = common | {"schema": "c17-g1-real-wrappers-canary-binding-v1",
        "decision_plan": {"path": str(root / "decision.json"), "decision_id": root.name},
        "root_identity": {"dev": st.st_dev, "ino": st.st_ino, "uid": st.st_uid,
                          "birthtime": st.st_birthtime},
        "product_source_root": str(blueprint.QA_SOURCE), "qa_python": str(blueprint.QA_PYTHON),
        "source_checkout_ref": checkout_ref, "source_refs": refs,
        "commands": commands,
        "rpc_descriptors": {row["id"]: row for row in planned["descriptors"]},
        "rpc_context_ref": published["context_ref"], "rpc_plan_ref": published["plan_ref"],
        "auxiliary_descriptors": auxiliary["auxiliary_descriptors"],
        "chrome_files_ref": auxiliary["chrome_files_ref"],
        "git_snapshot_ref": auxiliary["git_snapshot_ref"]}
    exclusive_json(root / "binding.json", binding)
    binding_ref = protocol.reference(root / "binding.json")
    decision = common | {"schema": "c17-g1-real-wrappers-canary-decision-v1",
        "scope": "g1_rpc_real_instrument_wrappers_canary_only", "supplied_by": "/root",
        "decision_id": root.name, "binding": binding_ref, "source_checkout_ref": checkout_ref,
        "root_tool_authorization_verified": True, "root_authorization_origin": go_ref,
        "instruments": refs}
    exclusive_json(root / "decision.json", decision)
    decision_ref = protocol.reference(root / "decision.json")
    # Le loader relit slot root, GO, checkout, sources, plan et toutes commandes.
    admitted_decision, admitted_binding = g1.load_wrapper_canary_admission(root,
        actor="/root", round_id=root.name, round_name="WRAPPER_CANARY",
        decision_ref=decision_ref, binding_ref=binding_ref)
    require(admitted_decision == decision and admitted_binding == binding,
            "G1 n'a pas admis les octets root préémis")
    return decision_ref, binding_ref, planned


def start_exact(session, name: str):
    spec = session.binding["commands"].get(name)
    require(type(spec) is dict, "Commande directe root absente : " + name)
    return session.start(name, spec["role"], spec["argv"], mode=spec["mode"],
        timeout=spec["timeout_seconds"], env=spec["env"], cwd=Path(spec["cwd"]),
        stdout_path=Path(spec["stdout_path"]), stderr_path=Path(spec["stderr_path"]),
        combine_stderr=spec["combine_stderr"])


def request_loopback(path: str, *, token: str | None = None, method: str = "GET") -> dict:
    require(path in ("/__couverture/offline", "/api/auth/token", "/api/config/stats",
                     "/api/config/onboarding-complete"), "Route HTTP QA hors liste")
    require(method == ("POST" if path == "/api/config/onboarding-complete" else "GET"),
            "Méthode HTTP QA hors liste")
    headers = {"X-Therese-Token": token} if token else {}
    request = urllib.request.Request("http://127.0.0.1:17593" + path,
                                     method=method, headers=headers)
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=3) as response:
        require(response.status == 200, "Backend QA ne répond pas 200")
        return json.load(response)


def ensure_readiness(session, g1, root: Path, *, request_json=request_loopback,
                     vite_open=None) -> dict:
    """Pas de healthcheck avant l'attribution globale des deux ports."""
    journal = root / "ownership-traces.jsonl"
    deadline = time.monotonic() + 50
    pending = {17593, 5173}
    observations = []
    while pending and time.monotonic() < deadline:
        for port in tuple(sorted(pending)):
            raw = session._capture_listener("calibrate", port, journal)
            observations.append(raw["receipt"])
            if raw["result"]["status"] == "owned":
                pending.remove(port)
            else:
                require(raw["result"]["status"] == "absent", "Listener QA étranger/incertain")
        if pending:
            require(all(session.handles[name]["process"].poll() is None for name in ("backend", "vite")),
                    "Service QA mort avant readiness")
            time.sleep(0.25)
    require(not pending, "Les deux listeners QA ne sont pas possédés dans 50 s")
    owned = session.observe_owned_listeners("calibrate", [17593, 5173], journal)
    # Le dernier scan possédé précède les requêtes. Aucun proxy ni destination externe.
    offline = request_json("/__couverture/offline")
    require(offline == {"version": 1, "network_policy": "loopback-only", "offline": True},
            "Identité offline du backend QA incorrecte")
    token = request_json("/api/auth/token").get("token")
    require(isinstance(token, str) and token, "Jeton de session QA absent")
    stats = request_json("/api/config/stats", token=token)
    data = blueprint.paths(root)["data"]
    require(Path(stats.get("data_dir", "")).resolve(strict=True) == data
            and Path(stats.get("db_path", "")).resolve(strict=True).is_relative_to(data),
            "Backend branché à une base hors profil QA")
    request_json("/api/config/onboarding-complete", token=token, method="POST")
    require(session.handles["backend"]["process"].poll() is None
            and session.handles["vite"]["process"].poll() is None,
            "Service mort pendant onboarding QA")
    vite_request = urllib.request.Request("http://127.0.0.1:5173/")
    open_vite = vite_open or urllib.request.build_opener(urllib.request.ProxyHandler({})).open
    with open_vite(vite_request, timeout=3) as response:
        require(response.status == 200, "Vite QA ne sert pas le frontend")
    final_owned = session.observe_owned_listeners("calibrate", [17593, 5173], journal)
    return {"schema": "c17-wrapper-canary-readiness-v1", "owned_listener_refs": owned["observations"],
            "post_http_owned_listener_refs": final_owned["observations"],
            "earlier_listener_refs": observations, "offline_identity": offline,
            "verified_data_dir": stats["data_dir"], "verified_db_path": stats["db_path"],
            "onboarding_completed": True, "vite_http_status": 200, "at": now()}


def stage_is_clean(protocol, root: Path, stage: str, stage_ref: dict) -> bool:
    receipt = protocol.checked_json(stage_ref, root=root)
    cleanup = receipt.get("cleanup") or {}
    return (receipt.get("stage_id") == stage and receipt.get("exit_code") == 0
            and receipt.get("instrument_error") is None
            and receipt.get("termination_proved") is True
            and receipt.get("log_stability_proved") is True
            and receipt.get("cleanup_deadline_met") is True
            and type(receipt.get("cleanup_elapsed_seconds")) in (int, float)
            and math.isfinite(receipt["cleanup_elapsed_seconds"])
            and 0 <= receipt["cleanup_elapsed_seconds"] <= 8
            and cleanup.get("clean") is True)


def audit_fifteen_rpc(protocol, root: Path, dispatcher) -> dict:
    """Quinze ACK normaux physiques, avec les codes métier négatifs inchangés."""
    expected = {"rpc-" + label for label in contract.SITE_SPECS}
    jobs = getattr(dispatcher, "jobs", {}) if dispatcher is not None else {}
    result = {"expected": 15, "observed": len(jobs), "jobs": {}, "passed": False}
    if set(jobs) != expected or getattr(dispatcher, "errors", []):
        return result
    for name in sorted(expected):
        job = jobs[name]
        ref = job.get("ack_ref")
        if job.get("state") != "complete" or not isinstance(ref, dict):
            return result
        ack = protocol.read_committed(root, Path(ref["path"]))
        if protocol.reference(Path(ref["path"])) != ref:
            return result
        exit_code = ack.get("exit_code")
        expected_code = (1 if name in {"rpc-test-pytest-positive", "rpc-test-vitest-positive",
                                       "rpc-sql-b1753-power"} else None if name ==
                         "rpc-screen-positive-network" else 0)
        code_ok = (type(exit_code) is int and exit_code != 0 if expected_code is None
                   else exit_code == expected_code)
        required_refs = ("receipt_ref", "cleanup_ref", "stdout_ref", "stderr_ref")
        refs_ok = all(isinstance(ack.get(key), dict)
                      and protocol.reference(Path(ack[key]["path"])) == ack[key]
                      for key in required_refs)
        ok = (ack.get("id") == name and ack.get("state") == "complete"
              and ack.get("instrument_error") is None
              and ack.get("synthetic_authentication") is False
              and ack.get("termination_proved") is True
              and ack.get("log_stability_proved") is True
              and ack.get("cleanup_deadline_met") is True
              and ack.get("signals") == [] and ack.get("tainted") is False
              and code_ok and refs_ok)
        result["jobs"][name] = {"ack_ref": ref, "exit_code": exit_code,
                                "expected_code": "nonzero" if expected_code is None else expected_code,
                                "passed": ok}
        if not ok:
            return result
    result["passed"] = len(result["jobs"]) == 15
    return result


def run(root: Path, *, go_sha256: str) -> int:
    root = blueprint.exact_root(root)
    require(Path(__file__).resolve(strict=True) == root / "coordinator/run_wrapper_canary.py",
            "Exécuter seulement la copie coordinateur QA épinglée")
    require(os.environ.get("C17_WRAPPER_CANARY_ONLY") == "1"
            and os.environ.get("C17_RPC_CANARY_ONLY") != "1", "Flag WRAPPER distinct absent")
    sys.path.insert(0, str(root / "g1"))
    sys.path.insert(0, str(root / "source"))
    import rpc_protocol as protocol
    import runtime_session as g1
    import session_rpc_adapter
    import rpc_dispatcher
    import rpc_unix
    go_ref, checkout_ref, refs, auxiliary, _go = read_inputs(protocol, root, go_sha256)
    require(g1.HERE == root / "g1" and g1.NODE_ROOT == blueprint.NODE_ROOT
            and g1.WRAPPER_SCOPE == "g1_rpc_real_instrument_wrappers_canary_only"
            and g1.WRAPPER_ADMISSION_TABLE, "G1 WRAPPER exact/root slot fermé")
    for path in (blueprint.paths(root)["vite_config"], blueprint.paths(root)["vite_canonical"]):
        require(path.is_file() and not path.is_symlink()
                and any(item == protocol.reference(path) for item in refs),
                "Config Vite QA préémise/épinglée absente")
    session = server = None
    stage_refs = {}
    service_stop_ref = stop_ref = None
    error = None
    readiness = None
    readiness_ref = None
    transport_final = None
    rpc_audit = None
    return_code = 86
    try:
        prepare_qa_directories(root)
        owner = g1.DarwinLedger().owner
        decision_ref, binding_ref, plan = publish_and_bind(protocol, g1, root,
            owner_identity=owner, go_ref=go_ref, checkout_ref=checkout_ref,
            refs=refs, auxiliary=auxiliary)
        session = g1.Session(root, actor="/root", round_id=root.name,
                             round_name="WRAPPER_CANARY",
                             decision_ref=decision_ref, binding_ref=binding_ref)
        protocol.same_identity(session.ledger.owner, plan["sealed"]["context"]["owner_identity"])
        api = {name: getattr(g1, name) for name in ("RPC_REQUESTERS", "RPC_CHILDREN", "SOURCE", "HERE",
            "reference", "read_published_json", "checked_json_ref", "save")}
        api["_ACTIVE_SESSION"] = g1._ACTIVE_SESSION
        adapter = session_rpc_adapter.SessionRpcAdapter(session, api, protocol=protocol,
            context=plan["sealed"]["context"], enrollments={})
        dispatcher = rpc_dispatcher.RpcDispatcher(root, plan["sealed"]["context"],
            plan["descriptors"], {}, adapter)
        server = rpc_unix.create_server(root, plan["sealed"]["context"],
                                        plan["descriptors"], session.ledger)
        dispatcher.attach_transport(server)
        session.attach_rpc_dispatcher(dispatcher)
        before = session._record_ports_absence("before-services")
        require(before["result"]["ports_absence_proved"] is True,
                "Port QA occupé avant démarrage ; aucun service n'est lancé")
        exclusive_json(root / "runtime/pile-preparation.json", blueprint.prepared_stack(root, prepared_at=now()))
        start_exact(session, "backend")
        start_exact(session, "vite")
        readiness = ensure_readiness(session, g1, root)
        exclusive_json(root / "runtime/readiness.json", readiness)
        readiness_ref = protocol.reference(root / "runtime/readiness.json")
        services = session.services_receipt()
        exclusive_json(root / "runtime/services-running.json", services)
        stack = blueprint.prepared_stack(root, prepared_at=now())
        stack.update({"status": "running", "head_at_start": blueprint.HEAD,
            "offline_factory_sha256": protocol.reference(blueprint.QA_SOURCE / "tests/couverture/backend_offline.py")["sha256"],
            "verified_data_dir": readiness["verified_data_dir"],
            "verified_db_path": readiness["verified_db_path"],
            "onboarding_completed": True, "started_at": now(),
            "owned_services": services, "readiness_ref": readiness_ref})
        for name in ("backend", "vite"):
            stack[name]["pid"] = session.handles[name]["root_identity"]["pid"]
            stack[name]["command"] = session.binding["commands"][name]["argv"]
        exclusive_json(root / "runtime/pile-reprise.json", stack)
        for stage in STAGES:
            entry = start_exact(session, stage)
            stage_refs[stage] = session.wait(entry)
            require(stage_is_clean(protocol, root, stage, stage_refs[stage]),
                    "Étape instrument non verte : " + stage)
        return_code = 0
    except BaseException as exc:
        error = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    finally:
        if session is not None:
            if any(name in session.handles for name in ("backend", "vite")) and not session.services_stopped:
                try:
                    service_stop_ref = session.stop_services()
                except BaseException as exc:
                    error = error or {"type": type(exc).__name__, "message": str(exc),
                                      "traceback": traceback.format_exc()}
                    return_code = 86
            if not session.closed:
                try:
                    stop_ref = session.stop()
                except BaseException as exc:
                    error = error or {"type": type(exc).__name__, "message": str(exc),
                                      "traceback": traceback.format_exc()}
                    return_code = 86
        if server is not None:
            try:
                deadline = time.monotonic() + 5
                while True:
                    transport_final = server.pump()
                    if transport_final["errors"] or transport_final["active"] == 0:
                        break
                    require(time.monotonic() < deadline, "EOF Unix après ACK non observé dans 5s")
                    time.sleep(0.01)
            except BaseException as exc:
                error = error or {"type": type(exc).__name__, "message": str(exc),
                                  "traceback": traceback.format_exc()}
                return_code = 86
            try:
                server.close()
            except BaseException as exc:
                error = error or {"type": type(exc).__name__, "message": str(exc),
                                  "traceback": traceback.format_exc()}
                return_code = 86
        stop_ok = False
        try:
            if session is not None and service_stop_ref and stop_ref:
                services_closed = protocol.checked_json(service_stop_ref, root=root)
                stopped = protocol.checked_json(stop_ref, root=root)
                stop_ok = (services_closed.get("services_stopped") is True
                           and services_closed.get("ports_absence_proved") is True
                           and stopped.get("session_closed") is True
                           and stopped.get("ports_absence_proved") is True
                           and stopped.get("ports_absent") == [17593, 5173]
                           and stopped.get("log_stability_proved") is True)
        except BaseException as exc:
            error = error or {"type": type(exc).__name__, "message": str(exc),
                              "phase": "read_shutdown_receipts"}
        all_stages_present = set(stage_refs) == set(STAGES)
        all_stages_clean = False
        try:
            all_stages_clean = all_stages_present and all(
                stage_is_clean(protocol, root, stage, stage_refs[stage]) for stage in STAGES)
        except BaseException as exc:
            error = error or {"type": type(exc).__name__, "message": str(exc),
                              "phase": "read_stage_receipts"}
        transport_ok = (server is not None and not server.errors and transport_final is not None
                        and transport_final["active"] == 0 and not transport_final["errors"])
        try:
            rpc_audit = audit_fifteen_rpc(protocol, root,
                None if session is None else session._rpc_dispatcher)
        except BaseException as exc:
            error = error or {"type": type(exc).__name__, "message": str(exc),
                              "phase": "read_fifteen_rpc_ack"}
        source_unchanged = False
        try:
            source_unchanged = all(protocol.reference(Path(ref["path"])) == ref for ref in refs)
        except BaseException as exc:
            error = error or {"type": type(exc).__name__, "message": str(exc),
                              "phase": "rehash_sources_after"}
        passed = bool(return_code == 0 and error is None and all_stages_clean
                      and stop_ok and transport_ok and source_unchanged
                      and rpc_audit is not None and rpc_audit["passed"])
        if not passed:
            return_code = 86
        result = {"schema": RESULT_SCHEMA, "scope": "WRAPPER_CANARY", "head": blueprint.HEAD,
            "actor": "/root", "round_id": root.name, "qa_root": str(root),
            "stage_refs": stage_refs, "service_stop_ref": service_stop_ref,
            "session_stop_ref": stop_ref, "readiness_ref": readiness_ref,
            "transport_final": transport_final, "transport_errors": [] if server is None else server.errors,
            "rpc_audit": rpc_audit,
            "error": error, "source_unchanged": source_unchanged,
            "all_four_parent_receipts_present": all_stages_present,
            "all_four_parent_receipts_clean": all_stages_clean,
            "owned_shutdown_proved": stop_ok, "rpc_transport_closed": transport_ok,
            "classification": "instrument_only_completed_not_FULL_not_78" if passed else
                "instrument_error_or_incomplete_not_product_bug",
            "passed": passed, "FULL": False, "round_A_or_B": False,
            "density_or_78": False, "runner_exit": return_code}
        try:
            exclusive_json(root / "wrapper-canary-result.json", result)
        except BaseException:
            return_code = 86
    return return_code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--go-sha256", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    require(args.execute, "Aucun lancement sans --execute et GO SHA root exact")
    return run(args.root, go_sha256=args.go_sha256)


if __name__ == "__main__":
    raise SystemExit(main())
