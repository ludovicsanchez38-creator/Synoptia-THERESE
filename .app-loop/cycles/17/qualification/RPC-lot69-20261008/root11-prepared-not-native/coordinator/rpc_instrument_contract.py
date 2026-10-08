"""Contrat pur des cinq ports RPC et de leur préémission root acyclique.

Ce module ne lance, n'admet et ne qualifie aucun workload. L'identité du
superviseur et le deadline monotonic sont fournis par le coordinateur vivant,
jamais par le constructeur des copies QA.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re


INPUTS = frozenset({
    "runtime/calibrate-all.py",
    "runtime/calibrate-test-runner.py",
    "runtime/calibrate-screen.py",
    "complements/instruments/preparer-et-executer-harness-root-stack.py",
    "complements/instruments/preparer-harness-b1753-power.py",
})
FOLDERS = ("runtime", "complements/instruments")
DEPENDENCIES = frozenset({"rpc_client.py", "rpc_protocol.py"})
HELPERS = frozenset({folder + "/nested_capture.py" for folder in FOLDERS})
OUTPUTS = INPUTS | HELPERS | frozenset({folder + "/" + name
    for folder in FOLDERS for name in DEPENDENCIES})
REQUESTERS = frozenset({"calibrate", "rpc-all-test_runner", "rpc-all-screen_coverage",
    "B1753", "B1760", "B1753-power"})
DIRECT_PARENTS = frozenset({"calibrate", "B1753", "B1760", "B1753-power"})
ALLOCATIONS = frozenset({"all", "test-runner", "screen", "sql-b1753-output",
    "sql-b1753-profile", "sql-b1760-output", "sql-b1760-profile",
    "sql-b1753-power-output", "sql-b1753-power-profile"})
ENVELOPE_SCHEMA = "c17-g5-root-rpc-enrollment-context-v2"
PLAN_SCHEMA = "c17-g5-root-rpc-plan-v1"
RENDER_SCHEMA = "c17-g5-root-rpc-request-v1"
SITE_SPECS = {}
for _index, _label in enumerate(("all-test_runner", "all-logs",
                                  "all-runtime_ui-visual_capture-network_capture",
                                  "all-screen_coverage")):
    SITE_SPECS[_label] = ("calibrate", _index, "web", 700)
for _index, _label in enumerate(("test-pytest-positive", "test-pytest-negative",
                                  "test-vitest-positive", "test-vitest-negative")):
    SITE_SPECS[_label] = ("rpc-all-test_runner", _index, "web", 90)
for _index, _label in enumerate(("screen-negative", "screen-positive-visual",
                                  "screen-positive-network", "screen-restored")):
    SITE_SPECS[_label] = ("rpc-all-screen_coverage", _index, "web", 180)
for _label, _requester in (("sql-b1753", "B1753"), ("sql-b1760", "B1760"),
                           ("sql-b1753-power", "B1753-power")):
    SITE_SPECS[_label] = (_requester, 0, "sql", 240)


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def exact_ref(protocol, path: Path, value: dict) -> dict:
    raw = protocol.encoded(value)
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def expected_allocations(root: Path) -> dict[str, str]:
    """Chemins attendus par les cinq wrappers, pas un nouveau dossier libre."""
    values = {label: str(root / "runtime/calibration" / (label + "-rpc"))
              for label in ("all", "test-runner", "screen")}
    for group, label in (("B1753", "sql-b1753"), ("B1760", "sql-b1760"),
                         ("B1753-power", "sql-b1753-power")):
        output = root / "complements/runs" / group
        values[label + "-output"] = str(output)
        values[label + "-profile"] = str(output / "profile")
    return values


def render_instruments(renderer, definitions: dict[str, str], *, qa_source: str,
                       head: str, helper_text: str, dependencies: dict[str, str],
                       expected_source_refs: dict[str, str], protocol) -> dict[str, str]:
    """Rend les 11 textes exacts. Les références d'origine viennent du GO root."""
    need(set(definitions) == INPUTS and set(expected_source_refs) == INPUTS
         and all(type(value) is str and sha_text(value) == expected_source_refs[name]
                 for name, value in definitions.items()), "Cinq définitions/pins d'origine divergents")
    need(set(dependencies) == DEPENDENCIES
         and all(type(value) is str and value for value in dependencies.values()),
         "Client et protocole RPC exacts absents")
    need(type(helper_text) is str and helper_text ==
         "from rpc_client import capture_nested, session_child_env, reserved_path\n",
         "Helper RPC doit seulement importer les trois primitives du client épinglé")
    need(re.fullmatch(r"[0-9a-f]{40}", head or "") is not None,
         "HEAD documentaire exact absent")
    need(protocol.REQUEST_SCHEMA == RENDER_SCHEMA and protocol.SITE_SPECS == SITE_SPECS,
         "Table quinze sites/protocole RPC divergent")
    source = Path(qa_source)
    need(source.is_absolute() and source.is_relative_to(Path("/private/tmp"))
         and ".." not in source.parts, "Source QA hors racine privée")
    dependency_refs = {name: sha_text(value) for name, value in dependencies.items()}
    context = {"source_refs": expected_source_refs, "qa_source": qa_source, "head": head,
        "rpc_helper_text": helper_text, "rpc_helper_sha256": sha_text(helper_text),
        "rpc_dependency_texts": dependencies, "rpc_dependency_sha256": dependency_refs,
        "rpc_protocol_schema": RENDER_SCHEMA,
        "rpc_protocol_sha256": dependency_refs["rpc_protocol.py"]}
    outputs = renderer.render_ports(definitions, context)
    need(type(outputs) is dict and set(outputs) == OUTPUTS
         and all(type(value) is str and value for value in outputs.values()),
         "Renderer RPC doit livrer exactement cinq ports, deux helpers et quatre dépendances")
    need(all(outputs[name] == helper_text for name in HELPERS), "Deux helpers RPC différents")
    for folder in FOLDERS:
        for name in DEPENDENCIES:
            need(outputs[folder + "/" + name] == dependencies[name],
                 "Dépendance RPC générée différente : " + folder + "/" + name)
    return outputs


def draft_context_envelopes(protocol, *, root: Path, scope: str, actor: str,
                            round_id: str, head: str, context_id: str,
                            owner_identity: dict, deadline_monotonic: float,
                            allocations: dict[str, str]) -> dict:
    """Gabarit sans I/O ; l'owner réel sera observé par root avant tout Popen."""
    root = Path(root)
    # A/B restent fermées : cette version ne prépare que le lot instrument.
    allowed = {"WRAPPER_CANARY": "therese-c17-wrapper-canary-"}
    need(scope in allowed and root.is_absolute() and root.parent == Path("/private/tmp")
         and root.name.startswith(allowed[scope]) and root.name != allowed[scope],
         "Portée/racine QA exacte absente")
    need(type(actor) is str and actor and type(round_id) is str and round_id
         and re.fullmatch(r"[0-9a-f]{40}", head or "") is not None
         and re.fullmatch(r"[0-9a-f]{32}", context_id or "") is not None,
         "Acteur/ronde/HEAD/contexte incomplet")
    need(type(deadline_monotonic) in (int, float) and math.isfinite(deadline_monotonic)
         and deadline_monotonic > 0, "Deadline owner absent")
    need(type(allocations) is dict and allocations == expected_allocations(root)
         and set(allocations) == ALLOCATIONS,
         "Neuf allocations exactes des vrais wrappers requises")
    context = {"schema": protocol.CONTEXT_SCHEMA, "root": str(root), "actor": actor,
        "round_id": round_id, "head": head, "context_id": context_id,
        "deadline_monotonic": deadline_monotonic,
        "owner_identity": {key: owner_identity[key] for key in protocol.IDENTITY_FIELDS},
        "allocations": allocations}
    protocol.validate_context(context, root)
    context_path = root / "session-rpc/context.json"
    envelopes = {}
    for requester in sorted(REQUESTERS):
        path = root / "session-rpc/envelope" / (requester + ".json")
        body = {"schema": ENVELOPE_SCHEMA, "context": context,
            "requester_id": requester,
            "descriptor_plan_path": str(root / "session-rpc/plan.json"),
            "enrollment_path": str(root / "session-rpc/enrollment" / (requester + ".json"))}
        envelopes[requester] = {"path": str(path), "body": body,
            "ref": exact_ref(protocol, path, body)}
    return {"scope": scope, "root": str(root), "context": context,
            "context_ref": exact_ref(protocol, context_path, context),
            "envelopes": envelopes, "plan": None,
            "status": "draft_owner_supplied_not_published_not_admitted"}


def seal_plan(protocol, draft: dict, descriptors: list[dict],
              parent_commands: dict[str, dict]) -> dict:
    """Contrôle la table 15 et les refs enveloppe ; aucune décision n'est créée."""
    root = Path(draft["root"])
    context = draft["context"]
    need(protocol.REQUEST_SCHEMA == RENDER_SCHEMA and protocol.SITE_SPECS == SITE_SPECS,
         "Table quinze sites/protocole RPC divergent")
    need(draft.get("status") == "draft_owner_supplied_not_published_not_admitted"
         and draft.get("plan") is None and set(draft["envelopes"]) == REQUESTERS,
         "Gabarit RPC réutilisé ou incomplet")
    need(draft.get("context_ref") == exact_ref(protocol, root / "session-rpc/context.json", context),
         "Contexte owner modifié après brouillon")
    for requester in REQUESTERS:
        item = draft["envelopes"][requester]
        path = root / "session-rpc/envelope" / (requester + ".json")
        need(item == {"path": str(path), "body": {"schema": ENVELOPE_SCHEMA,
             "context": context, "requester_id": requester,
             "descriptor_plan_path": str(root / "session-rpc/plan.json"),
             "enrollment_path": str(root / "session-rpc/enrollment" / (requester + ".json"))},
             "ref": exact_ref(protocol, path, item["body"])},
             "Enveloppe owner modifiée après brouillon")
    expected = {"rpc-" + label for label in protocol.SITE_SPECS}
    need(type(descriptors) is list and len(descriptors) == len(expected) == 15
         and {row.get("id") for row in descriptors if isinstance(row, dict)} == expected,
         "Table RPC quinze commandes exactes absente")
    need(len({row.get("nonce") for row in descriptors}) == 15,
         "Nonce RPC réutilisé entre enfants")
    ordered = sorted(descriptors, key=lambda row: list(protocol.SITE_SPECS).index(row["label"]))
    need([row["label"] for row in ordered] == list(protocol.SITE_SPECS),
         "Ordre/labels des quinze appels RPC différents")
    for row in ordered:
        protocol.validate_descriptor(row, context, root)
        for reference in row["source_refs"]:
            source = Path(reference["path"])
            need(source.is_absolute() and not source.is_relative_to(root / "session-rpc")
                 and not any(source.is_relative_to(Path(path))
                             for path in expected_allocations(root).values()),
                 "Source RPC future ou événement pris pour source initiale")
        actual = row["environment"].get("C17_RPC_CONTEXT_REF")
        if row["id"] in {"rpc-all-test_runner", "rpc-all-screen_coverage"}:
            envelope = draft["envelopes"].get(row["id"])
            need(envelope is not None, "Enveloppe du helper absent")
            need(actual == json.dumps(envelope["ref"], sort_keys=True),
                 "Helper imbriqué sans enveloppe owner exacte")
        else:
            need(actual is None, "Contexte helper injecté à un enfant feuille")
    need(type(parent_commands) is dict and set(parent_commands) == DIRECT_PARENTS,
         "Quatre demandeurs directs instrument manquants")
    for requester, command in parent_commands.items():
        envelope = draft["envelopes"][requester]
        need(type(command) is dict and type(command.get("env")) is dict
             and command["env"].get("C17_RPC_CONTEXT_REF") == json.dumps(envelope["ref"], sort_keys=True),
             "Demandeur direct sans enveloppe owner exacte")
    plan = {"schema": PLAN_SCHEMA, "publication_protocol": protocol.PROTOCOL,
        "actor": context["actor"], "round_id": context["round_id"],
        "head": context["head"], "context_id": context["context_id"],
        "descriptors": ordered}
    path = root / "session-rpc/plan.json"
    result = dict(draft)
    result.update({"plan": {"path": str(path), "body": plan,
                           "ref": exact_ref(protocol, path, plan)},
                   "status": "sealed_prelaunch_not_published_not_admitted"})
    return result


def exclusive_json(protocol, root: Path, path: Path, value: dict) -> dict:
    """Émission O_EXCL/fsync des cinq champs envelope v2, comme le runner mesuré.

    Les enveloppes et le contexte n'ont pas de hardlink ; le plan seul utilise
    protocol.publish. Leur référence SHA/bytes est contrôlée après écriture.
    """
    path = protocol.inside(root, path, absent=True)
    payload = protocol.encoded(value)
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return protocol.reference(path)


def publish_prelaunch(protocol, sealed: dict, *, exclusive_writer=None) -> dict:
    """À appeler seulement par le superviseur réel avant Popen, après GO exact.

    Contexte et six envelopes sont exclusifs/fsync ; le plan seul est publié
    pending/fsync/hardlink. La décision/binding externes doivent ensuite
    épingler ces références ; ce code ne s'auto-autorise jamais.
    """
    need(sealed.get("status") == "sealed_prelaunch_not_published_not_admitted",
         "Préémission sans table scellée")
    root = protocol.canonical_root(sealed["root"])
    need(sealed.get("context_ref") == exact_ref(protocol, root / "session-rpc/context.json", sealed["context"]),
         "Contexte préémis non lié au plan scellé")
    need(isinstance(sealed.get("plan"), dict)
         and sealed["plan"].get("ref") == exact_ref(protocol, root / "session-rpc/plan.json", sealed["plan"]["body"]),
         "Plan préémis non lié à sa référence scellée")
    writer = exclusive_writer or (lambda path, body: exclusive_json(protocol, root, path, body))
    context_path = root / "session-rpc/context.json"
    context_ref = writer(context_path, sealed["context"])
    need(context_ref == sealed["context_ref"], "Contexte publié différent du brouillon root")
    for requester in sorted(REQUESTERS):
        item = sealed["envelopes"][requester]
        actual = writer(Path(item["path"]), item["body"])
        need(actual == item["ref"], "Enveloppe publiée différente du brouillon root")
    plan = sealed["plan"]
    actual = protocol.publish(root, Path(plan["path"]), plan["body"])
    need(actual == plan["ref"], "Plan RPC publié différent du brouillon root")
    return {"context_ref": context_ref, "plan_ref": actual, "envelope_refs": {
        requester: sealed["envelopes"][requester]["ref"] for requester in sorted(REQUESTERS)},
        "status": "published_not_admitted_requires_external_root_binding_and_go"}
