"""Relais fichiers root/stage réel proposé, sous Session déjà admise seulement.

N'ouvre aucune porte. Le workload ne peut pas publier sous DECISION_ROOT.
Root doit y conserver une vraie origine outil et sa revue, après demande.
Les schémas et SHA ne sont pas présentés comme authentification humaine.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time

# Fournis uniquement par le chargeur G1 exact SHA, pas par sys.path global.
protocol = None
bounds = None


def context(session, api: dict) -> dict:
    return {"actor": session.actor, "round_id": session.round_id, "round_name": session.round_name,
            "head": api["HEAD"], "qa_root": str(session.root)}


def guard(session, api: dict) -> None:
    require = api["require"]
    require(session.round_name in ("A", "B") and api["RUNTIME_ENABLED"] and api["OS_STARTUP_QUALIFIED"]
            and bool(api["ADMISSION_TABLE"]), "Relais fermé : aucune admission runtime par cette API")
    require(api["_ACTIVE_SESSION"] is session and not session.closed and not session._handlers_restored
            and not session.log_stability_tainted, "Relais hors vraie Session active/non tainted")
    session._raise_deferred_interrupt()
    decision, binding = api["load_admission"](session.root, actor=session.actor, round_id=session.round_id,
        round_name=session.round_name, decision_ref=session.decision_ref, binding_ref=session.binding_ref)
    require(decision == session.decision and binding == session.binding, "Relais admission initiale mutée")
    session.validate_sources()
    owner = session.ledger.owner
    current = session.ledger.info(os.getpid())
    require(current is not None and current.get("status") != 5
            and all(current.get(k) == owner[k] for k in ("pid", "start_sec", "start_usec", "ppid", "uid", "pgid"))
            and owner["pid"] == os.getpid(), "Relais owner kernel/birth changé")


def exact_ref(session, api: dict, value: dict) -> Path:
    protocol.reference(value)
    path = Path(value["path"])
    api["require"](path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink()
        and any(path.is_relative_to(base) for base in (session.root, api["SOURCE"], api["HERE"], api["DECISION_ROOT"])),
        "Relais référence hors QA/origine root exacte")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as stream:
        st = os.fstat(stream.fileno())
        api["require"](stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid(), "Relais référence non régulière/owner")
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    api["require"](digest.hexdigest() == value["sha256"]
        and ("bytes" not in value or value["bytes"] == st.st_size), "Relais référence SHA/taille changée")
    return path


def ref_tree(session, api: dict, value) -> None:
    if isinstance(value, dict) and "path" in value:
        exact_ref(session, api, value)
    elif isinstance(value, dict) and value:
        for child in value.values():
            ref_tree(session, api, child)
    elif isinstance(value, list) and value:
        for child in value:
            ref_tree(session, api, child)
    else:
        raise ValueError("Relais références attendues non exactes")


def external_path(session, api: dict, text: str) -> Path:
    path = Path(text)
    api["require"](path.is_absolute() and path.resolve() == path
        and path.is_relative_to(api["DECISION_ROOT"]) and path != api["DECISION_ROOT"]
        and not path.is_symlink() and not path.is_relative_to(session.root),
        "Relais livraison doit rester root externe, jamais un fichier workload")
    return path


def exchange(session, api: dict, *, kind: str, label: str, expected: dict,
             plan: dict, timeout: float) -> tuple[dict, dict]:
    guard(session, api)
    api["require"](re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", label) is not None, "Relais label")
    for key in ("delivery_path", "decision_path", "origin_path", "tool_record_path"):
        external_path(session, api, plan[key])
    if kind == "stage-binding":
        external_path(session, api, plan["binding_path"])
    else:
        ref_tree(session, api, expected)
    serial = len(session._relay_requests) + 1
    folder = api["child_path"](session.root, session.root / "root-relay" / (str(serial) + "-" + label))
    folder.mkdir(mode=0o700, parents=True, exist_ok=False)
    request_path = folder / "request.json"
    request = context(session, api) | {"schema": "c17-runtime78-root-relay-request-v1",
        "publication_protocol": protocol.PROTOCOL, "kind": kind, "label": label,
        "initial_binding": session.binding_ref, "session_decision": session.decision_ref,
        "actual_owner_identity": dict(session.ledger.owner), "expected_refs": expected,
        "planned_delivery": dict(plan), "timeout_seconds": timeout, "requested_at": api["now"]()}
    api["publish_json"](session.root, request_path, request)
    request_ref = api["reference"](request_path)
    session._relay_requests.append(request_ref)
    packet_path = external_path(session, api, plan["delivery_path"])
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        guard(session, api)
        session.ledger.attribute()  # parent/services restent attribués pendant l'attente.
        if packet_path.exists() or packet_path.is_symlink():
            packet = api["read_published_json"](api["DECISION_ROOT"], packet_path)
            protocol.delivery(packet, context(session, api), plan, request_ref, stage=kind == "stage-binding")
            for key in ("decision", "origin") + (("binding",) if kind == "stage-binding" else ()):
                external_path(session, api, packet[key]["path"])
                exact_ref(session, api, packet[key])
            origin = api["checked_json_ref"](packet["origin"], api["DECISION_ROOT"])
            protocol.origin(origin, context(session, api), request_ref, expected, plan)
            external_path(session, api, origin["root_tool_record"]["path"])
            exact_ref(session, api, origin["root_tool_record"])
            if packet.get("review") is not None:
                exact_ref(session, api, packet["review"])
            api["require"](time.monotonic() < deadline, "Relais livré après deadline")
            session._relay_deliveries[request_ref["path"]] = {
                "request": request_ref, "packet": api["reference"](packet_path), "plan": dict(plan),
                "expected": json.loads(json.dumps(expected)), "delivery": json.loads(json.dumps(packet))}
            return packet, request_ref
        time.sleep(0.01)
    raise api["InstrumentError"]("Relais root deadline : bruts conservés, aucun GO inventé")


def await_root_review(session, api: dict, phase: str, *, expected_refs: dict, timeout: float) -> dict:
    try:
        bounds.exact_bound("contract-review-wait" if phase == "contract-review" else "independent-review-wait", timeout, wait=True)
        guard(session, api)
        ordinal = session._root_review_cursor
        plans = session.binding.get("root_review_plans")
        api["require"](isinstance(plans, list) and ordinal < len(plans), "Relais plan de revue immuable absent")
        plan = plans[ordinal]
        api["require"](phase in ("contract-review", "independent-review", "package-review")
            and plan.get("phase") == phase and plan.get("timeout_seconds") == timeout,
            "Relais revue hors séquence/borne")
        packet, _ = exchange(session, api, kind="root-review", label=phase,
                            expected=expected_refs, plan=plan, timeout=timeout)
        decision = api["checked_json_ref"](packet["decision"], api["DECISION_ROOT"])
        protocol.review_decision(decision, packet, context(session, api), phase, expected_refs, plan)
        if packet.get("review") is not None:
            api["require"](decision.get("actor") != api["checked_json_ref"](packet["review"], api["DECISION_ROOT"]).get("actor"),
                           "Revue indépendante par exécutant interdite")
        session._root_review_cursor += 1
        return {key: packet[key] for key in ("decision", "origin", "review") if key in packet}
    except BaseException:
        session.log_stability_tainted = True
        raise


def await_stage_binding(session, api: dict, name: str, *, expected_command: dict,
                        initial_binding_ref: dict, timeout: float) -> dict:
    try:
        bounds.exact_bound("stage-binding-wait", timeout, wait=True)
        bounds.exact_bound(name, expected_command.get("timeout_seconds"))
        guard(session, api)
        api["require"](initial_binding_ref == session.binding_ref and name not in session.handles
            and name not in session._stage_admissions and name not in session.binding["commands"],
            "Relais binding initial/étape déjà lancée ou admise")
        raw_plan = session.binding.get("stage_plans", {}).get(name)
        api["require"](isinstance(raw_plan, dict) and raw_plan.get("timeout_seconds") == expected_command["timeout_seconds"],
                       "Relais plan exact d’étape absent")
        plan = dict(raw_plan, decision_path=raw_plan["decision"]["path"])
        packet, _ = exchange(session, api, kind="stage-binding", label=name,
            expected={"command": expected_command, "initial_binding": initial_binding_ref}, plan=plan, timeout=timeout)
        binding = api["checked_json_ref"](packet["binding"], api["DECISION_ROOT"])
        decision = api["checked_json_ref"](packet["decision"], api["DECISION_ROOT"])
        protocol.stage_admission(binding, decision, packet, context(session, api), name,
                                 expected_command, initial_binding_ref, raw_plan)
        return {key: packet[key] for key in ("binding", "decision", "origin")}
    except BaseException:
        session.log_stability_tainted = True
        raise


def admit_stage_binding(session, api: dict, *, binding_ref: dict, decision_ref: dict, origin_ref: dict) -> None:
    try:
        guard(session, api)
        matches = [item for item in session._relay_deliveries.values() if
            all(item["delivery"].get(key) == value for key, value in
                (("binding", binding_ref), ("decision", decision_ref), ("origin", origin_ref)))]
        api["require"](len(matches) == 1, "Relais admission sans livraison réelle unique reçue")
        item = matches[0]
        api["require"](api["reference"](Path(item["packet"]["path"])) == item["packet"]
            and api["reference"](Path(item["request"]["path"])) == item["request"], "Relais demande/livraison changée")
        binding = api["checked_json_ref"](binding_ref, api["DECISION_ROOT"])
        decision = api["checked_json_ref"](decision_ref, api["DECISION_ROOT"])
        name = binding["stage_id"]
        api["require"](name not in session.handles and name not in session._stage_admissions,
                       "Relais admission d’étape réutilisée")
        plan = session.binding["stage_plans"][name]
        protocol.stage_admission(binding, decision, item["delivery"], context(session, api), name,
            item["expected"]["command"], session.binding_ref, plan)
        origin = api["checked_json_ref"](origin_ref, api["DECISION_ROOT"])
        protocol.origin(origin, context(session, api), item["request"], item["expected"], item["plan"])
        exact_ref(session, api, origin["root_tool_record"])
        record = {"schema": "c17-runtime78-session-stage-registration-v1", **context(session, api),
            "stage_id": name, "command": binding["command"], "stage_binding": binding_ref,
            "stage_decision": decision_ref, "stage_origin": origin_ref,
            "request": item["request"], "delivery": item["packet"], "registered_at": api["now"]()}
        folder = api["child_path"](session.root, session.root / "stage-admissions")
        folder.mkdir(mode=0o700, exist_ok=True)
        path = folder / (name + ".json")
        api["publish_json"](session.root, path, record | {"publication_protocol": protocol.PROTOCOL})
        record["registration"] = api["reference"](path)
        session._stage_admissions[name] = json.loads(json.dumps(record))
    except BaseException:
        session.log_stability_tainted = True
        raise
