"""Codec RPC fichiers. Aucun G1, processus ou socket ; fichiers ≠ identité d'écrivain."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat

PROTOCOL = "exclusive-pending-fsync-hardlink-v1"
CONTEXT_SCHEMA = "c17-g5-root-rpc-context-v1"
DESCRIPTOR_SCHEMA = "c17-g5-root-rpc-descriptor-v1"
REQUEST_SCHEMA = "c17-g5-root-rpc-request-v1"
ACK_SCHEMA = "c17-g5-root-rpc-ack-v1"
CAPTURE_SECONDS = 5
CLEANUP_SECONDS = 8
MAX_MESSAGE_BYTES = 1_048_576
MAX_ARTIFACT_BYTES = 67_108_864
IDENTITY_FIELDS = ("pid", "start_sec", "start_usec", "ppid", "uid", "pgid")
SITE_SPECS = {}
for _index, _label in enumerate(("all-test_runner", "all-logs", "all-runtime_ui-visual_capture-network_capture", "all-screen_coverage")):
    SITE_SPECS[_label] = ("calibrate", _index, "web", 700)
for _index, _label in enumerate(("test-pytest-positive", "test-pytest-negative", "test-vitest-positive", "test-vitest-negative")):
    SITE_SPECS[_label] = ("rpc-all-test_runner", _index, "web", 90)
for _index, _label in enumerate(("screen-negative", "screen-positive-visual", "screen-positive-network", "screen-restored")):
    SITE_SPECS[_label] = ("rpc-all-screen_coverage", _index, "web", 180)
for _label, _requester in (("sql-b1753", "B1753"), ("sql-b1760", "B1760"), ("sql-b1753-power", "B1753-power")):
    SITE_SPECS[_label] = (_requester, 0, "sql", 240)
DESCRIPTOR_FIELDS = {"schema", "id", "context_id", "requester_id", "logical_parent_id", "index", "nonce",
    "source_refs", "argv", "cwd", "environment", "stdout_path", "stderr_path", "timeout_seconds", "mode",
    "label", "stage_name", "role"}
PAYLOAD_FIELDS = ("argv", "cwd", "environment", "stdout_path", "stderr_path", "timeout_seconds", "label", "source_refs")


class RpcInstrumentError(RuntimeError):
    """Transport/identité/timeout : jamais un résultat métier réussi."""


class RpcTimeout(RpcInstrumentError, TimeoutError):
    pass


class RpcPrelaunchRefused(RpcInstrumentError):
    """Adapter atteste un refus AVANT tout handle/Popen, pas un enfant nettoyé."""


class RpcCleanupUncertain(RpcInstrumentError):
    """Un handle peut exister : aucun ACK tant que sa fermeture n'est prouvée."""
    def __init__(self, message, token=None):
        super().__init__(message)
        self.token = token


def require(condition, reason):
    if not condition:
        raise RpcInstrumentError(reason)


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def same(left, right):
    return encoded(left) == encoded(right)


def identity(value):
    require(isinstance(value, dict) and all(type(value.get(k)) is int for k in IDENTITY_FIELDS), "RPC identity fields")
    require(value["pid"] > 0 and value["ppid"] > 0 and value["pgid"] > 0 and value["uid"] >= 0
            and value["start_sec"] > 0 and 0 <= value["start_usec"] < 1_000_000, "RPC identity values")
    return {k: value[k] for k in IDENTITY_FIELDS}


def same_identity(left, right):
    require(same(identity(left), identity(right)), "RPC real birth/UID/PGID mismatch")


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def canonical_root(root):
    root = Path(root)
    require(root.is_absolute() and root.parent == Path("/private/tmp") and not root.is_symlink()
            and root.resolve(strict=True) == root and root.is_dir(), "RPC QA root canonical")
    return root


def inside(root, path, *, absent=False):
    path = Path(path)
    require(path.is_absolute() and not path.is_symlink() and path != root and path.is_relative_to(root)
            and path.parent.resolve(strict=True) == path.parent, "RPC artifact path canonical inside QA")
    if absent:
        require(not path.exists() and not path.is_symlink(), "RPC exclusive destination exists")
    else:
        require(path.resolve(strict=True) == path, "RPC existing artifact canonical")
    return path


def reference(path):
    data = Path(path).read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def read_reference(ref, *, root=None, limit=MAX_ARTIFACT_BYTES):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256", "bytes"}, "RPC exact reference shape")
    path = Path(ref["path"])
    require(path.is_absolute() and not path.is_symlink() and path.resolve(strict=True) == path, "RPC reference canonical")
    if root is not None:
        inside(root, path)
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                and 0 <= info.st_size <= limit, "RPC reference regular/owner/bound")
        raw = stream.read(limit + 1)
    require(type(ref["bytes"]) is int and len(raw) == info.st_size == ref["bytes"]
            and hashlib.sha256(raw).hexdigest() == ref["sha256"], "RPC reference SHA/bytes changed")
    return raw


def checked_json(ref, *, root=None):
    value = json.loads(read_reference(ref, root=root, limit=MAX_MESSAGE_BYTES))
    require(isinstance(value, dict), "RPC referenced JSON object")
    return value


def publish(root, path, value):
    path = inside(root, path, absent=True)
    require(value.get("publication_protocol") == PROTOCOL, "RPC publication protocol")
    payload = encoded(value)
    require(len(payload) <= MAX_MESSAGE_BYTES, "RPC message bound")
    pending = Path(str(path) + ".pending")
    inside(root, pending, absent=True)
    with os.fdopen(os.open(pending, os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_WRONLY, 0o600), "wb") as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    os.link(pending, path, follow_symlinks=False)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return reference(path)


def read_committed(root, path):
    path = inside(root, path)
    pending = inside(root, Path(str(path) + ".pending"))
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as left:
        with os.fdopen(os.open(pending, os.O_RDONLY | os.O_NOFOLLOW), "rb") as right:
            a, b = os.fstat(left.fileno()), os.fstat(right.fileno())
            require(stat.S_ISREG(a.st_mode) and stat.S_ISREG(b.st_mode)
                and (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino) and a.st_nlink == b.st_nlink == 2
                and a.st_uid == b.st_uid == os.getuid() and a.st_size == b.st_size
                and 0 < a.st_size <= MAX_MESSAGE_BYTES, "RPC exact pending hardlink")
            raw = left.read(MAX_MESSAGE_BYTES + 1)
            require(len(raw) == a.st_size, "RPC committed stable bytes")
    value = json.loads(raw)
    require(isinstance(value, dict) and value.get("publication_protocol") == PROTOCOL, "RPC committed object")
    return value


def validate_context(context, root):
    require(context.get("schema") == CONTEXT_SCHEMA and context.get("root") == str(root), "RPC context schema/root")
    for name in ("actor", "round_id"):
        require(isinstance(context.get(name), str) and bool(context[name]), "RPC context " + name)
    require(re.fullmatch(r"[a-f0-9]{40}", context.get("head", "")) is not None
            and re.fullmatch(r"[a-f0-9]{32}", context.get("context_id", "")) is not None, "RPC HEAD/context id")
    require(finite(context.get("deadline_monotonic")) and context["deadline_monotonic"] > 0, "RPC outer deadline")
    identity(context["owner_identity"])


def validate_descriptor(row, context, root):
    require(isinstance(row, dict) and set(row) == DESCRIPTOR_FIELDS, "RPC closed descriptor fields")
    require(row["schema"] == DESCRIPTOR_SCHEMA and row["context_id"] == context["context_id"], "RPC descriptor schema/context")
    require(row["label"] in SITE_SPECS, "RPC five-site closed label")
    requester, index, mode, timeout = SITE_SPECS[row["label"]]
    require(row["requester_id"] == row["logical_parent_id"] == requester
            and type(row["index"]) is int and row["index"] == index
            and row["mode"] == mode and type(row["timeout_seconds"]) is int and row["timeout_seconds"] == timeout,
            "RPC requester/index/mode/bound closed")
    require(row["id"] == row["stage_name"] == "rpc-" + row["label"]
            and row["role"] == "stage-" + row["stage_name"]
            and re.fullmatch(r"[a-f0-9]{32}", row["nonce"]) is not None, "RPC id/role/nonce")
    require(isinstance(row["argv"], list) and row["argv"] and all(isinstance(a, str) and a and "\x00" not in a for a in row["argv"]), "RPC exact argv")
    require(Path(row["argv"][0]).is_absolute(), "RPC argv executable absolute")
    require(isinstance(row["environment"], dict) and all(isinstance(k, str) and k and "=" not in k and "\x00" not in k
            and isinstance(v, str) and "\x00" not in v for k, v in row["environment"].items()), "RPC full environment")
    require(Path(row["cwd"]).is_absolute(), "RPC cwd absolute")
    require(isinstance(row["source_refs"], list) and row["source_refs"], "RPC pinned sources absent")
    for ref in row["source_refs"]:
        require(isinstance(ref, dict) and set(ref) == {"path", "sha256", "bytes"}
                and re.fullmatch(r"[a-f0-9]{64}", ref.get("sha256", "")) is not None
                and type(ref.get("bytes")) is int and ref["bytes"] >= 0, "RPC source ref")
    for name in ("stdout_path", "stderr_path"):
        path = Path(row[name])
        require(path.is_absolute() and path != root and path.is_relative_to(root), "RPC declared QA sink")
    require(row["stdout_path"] != row["stderr_path"], "RPC distinct stdout/stderr")


def closed_payload(row):
    return {k: row[k] for k in PAYLOAD_FIELDS}


def event_path(root, row, kind):
    require(kind in {"request", "ack", "cancel"}, "RPC event kind")
    return root / "session-rpc" / kind / (row["id"] + "-" + row["nonce"] + ".json")


def common(context):
    return {k: context[k] for k in ("actor", "round_id", "head", "context_id")}


def validate_request(value, row, context, enrollment, now):
    expected_fields = {"schema", "publication_protocol", "id", "descriptor_digest", "requester_id",
        "logical_parent_id", "index", "nonce", "requester_identity", "created_monotonic", "payload"} | set(common(context))
    require(isinstance(value, dict) and set(value) == expected_fields, "RPC exact request fields")
    require(value.get("schema") == REQUEST_SCHEMA and value.get("publication_protocol") == PROTOCOL, "RPC request schema")
    for key, expected in common(context).items():
        require(value.get(key) == expected, "RPC request context " + key)
    require(value.get("descriptor_digest") == digest(row) and value.get("id") == row["id"]
        and value.get("requester_id") == row["requester_id"] and value.get("logical_parent_id") == row["logical_parent_id"]
        and type(value.get("index")) is int and value["index"] == row["index"]
        and value.get("nonce") == row["nonce"] and same(value.get("payload"), closed_payload(row)),
        "RPC immutable descriptor/request mismatch")
    same_identity(value.get("requester_identity"), enrollment["identity"])
    require(finite(value.get("created_monotonic")) and 0 < value["created_monotonic"] <= now
            <= value["created_monotonic"] + CAPTURE_SECONDS, "RPC fresh request")


def fresh_budget(now, row, context, enrollment):
    deadline = min(context["deadline_monotonic"], enrollment["parent_deadline_monotonic"])
    require(finite(now) and finite(deadline) and now + row["timeout_seconds"] + CAPTURE_SECONDS + CLEANUP_SECONDS < deadline,
            "RPC remaining parent budget insufficient before launch")
    return deadline
