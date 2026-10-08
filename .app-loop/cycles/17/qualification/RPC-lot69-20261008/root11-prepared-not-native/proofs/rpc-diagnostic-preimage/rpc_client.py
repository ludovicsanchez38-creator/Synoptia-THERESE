"""Client G5 RPC : aucun Popen ; contexte helper distinct de l'env métier enfant."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import json
import os
from pathlib import Path
import socket
import stat
import struct
import subprocess
import time

import rpc_protocol as p

RpcInstrumentError = p.RpcInstrumentError
RpcTimeout = p.RpcTimeout
_TRANSPORT = ContextVar("c17_g5_rpc_transport", default=None)
_FILE_TRANSPORT = None


@contextmanager
def use_transport(transport):
    """Injection explicite pour vrais wrappers/doubles, pas un fallback OS."""
    token = _TRANSPORT.set(transport)
    try:
        yield transport
    finally:
        _TRANSPORT.reset(token)


def _transport():
    injected = _TRANSPORT.get()
    if injected is not None:
        return injected
    global _FILE_TRANSPORT
    ref_text = os.environ.get("C17_RPC_CONTEXT_REF")
    p.require(ref_text is not None, "RPC helper enrollment context absent; no local process fallback")
    if _FILE_TRANSPORT is None:
        ref = json.loads(ref_text)
        p.require(Path(ref["path"]).is_relative_to(Path("/private/tmp")), "RPC context reference outside QA")
        envelope = p.checked_json(ref)
        p.require(set(envelope) == {"schema", "context", "requester_id", "descriptor_plan_path", "enrollment_path"}
            and envelope.get("schema") == "c17-g5-root-rpc-enrollment-context-v2", "RPC enrollment envelope schema/fields")
        root = p.canonical_root(envelope["context"]["root"])
        context = envelope["context"]
        enrollment_path = Path(envelope["enrollment_path"])
        p.require(enrollment_path == root / "session-rpc/enrollment" / (envelope["requester_id"] + ".json"),
                  "RPC fixed root enrollment path")
        # G1 publie avant release. Une visibilité tardive reste bornée, jamais
        # remplacée par un PID déclaré ou un lancement helper local.
        until = time.monotonic() + p.CAPTURE_SECONDS
        while True:
            try:
                enrollment = p.read_committed(root, enrollment_path)
                p.require(time.monotonic() <= until, "RPC root enrollment read completed after 5s")
                break
            except FileNotFoundError:
                p.require(time.monotonic() < until, "RPC root enrollment not published within 5s")
                time.sleep(0.01)
        p.require(enrollment["requester_id"] == envelope["requester_id"], "RPC actual enrollment requester")
        plan_path = root / "session-rpc/plan.json"
        p.require(envelope["descriptor_plan_path"] == str(plan_path), "RPC fixed root descriptor plan path")
        plan = p.read_committed(root, plan_path)
        p.require(p.reference(plan_path) == enrollment.get("plan_ref"), "RPC plan differs from post-birth root enrollment pin")
        p.read_reference(enrollment["plan_ref"], root=root, limit=p.MAX_MESSAGE_BYTES)
        p.require(enrollment["identity"]["pid"] == os.getpid(), "RPC enrollment belongs to another process")
        _FILE_TRANSPORT = FileRpcTransport(root, context, plan["descriptors"], enrollment,
                                          exchange=UnixRpcExchange(root, context))
        _FILE_TRANSPORT.context_ref = ref
    p.require(_FILE_TRANSPORT.context_ref == json.loads(ref_text), "RPC helper context changed mid-run")
    return _FILE_TRANSPORT


def capture_nested(command, *, cwd, env, timeout, stdout_path, stderr_path, label):
    result = _transport().capture(command, cwd=cwd, env=env, timeout=timeout,
        stdout_path=stdout_path, stderr_path=stderr_path, label=label)
    p.require(isinstance(result, subprocess.CompletedProcess) and type(result.returncode) is int
        and isinstance(result.stdout, str) and isinstance(result.stderr, str), "RPC CompletedProcess shape")
    return result


def session_child_env(base):
    transport = _transport()
    method = getattr(transport, "child_environment", None)
    return method(base) if method is not None else dict(base)


def reserved_path(label, *, requested=None):
    method = getattr(_transport(), "reserve", None)
    p.require(callable(method), "RPC deterministic allocator absent")
    return Path(method(label, requested=requested))


class FileRpcTransport:
    """Fichiers bornés uniquement ; identité peer réelle exigée séparément par root."""
    def __init__(self, root, context, descriptors, enrollment, *, clock=time.monotonic, sleeper=time.sleep,
                 poll_hook=None, exchange=None):
        self.root = p.canonical_root(root)
        p.validate_context(context, self.root)
        self.context = json.loads(json.dumps(context))
        self.enrollment = json.loads(json.dumps(enrollment))
        p.identity(self.enrollment["identity"])
        self.rows = sorted((json.loads(json.dumps(row)) for row in descriptors
                            if row["requester_id"] == enrollment["requester_id"]), key=lambda r: r["index"])
        p.require(self.rows and [r["index"] for r in self.rows] == list(range(len(self.rows))), "RPC requester closed sequence")
        for row in self.rows:
            p.validate_descriptor(row, context, self.root)
        self.cursor, self.tainted, self.used_allocations = 0, False, set()
        self.clock, self.sleeper, self.poll_hook = clock, sleeper, poll_hook
        self.exchange = exchange
        self.context_ref = None
        self.last_ack = None

    def _next(self):
        p.require(not self.tainted and self.cursor < len(self.rows), "RPC requester terminal/replay")
        return self.rows[self.cursor]

    def child_environment(self, base):
        row = self._next()
        expected = row["environment"]
        p.require(all(key in expected and expected[key] == value for key, value in base.items()), "RPC business environment changed")
        additions = set(expected) - set(base)
        allowed = p.auxiliary_metadata_keys(row, self.root)
        p.require(additions <= allowed, "RPC arbitrary child environment overlay")
        if p.wrapper_scope(self.root):
            p.require(allowed <= set(expected), "RPC required WRAPPER metadata absent")
        return dict(expected)

    def reserve(self, label, *, requested=None):
        requester = self.enrollment["requester_id"]
        allowed = {"calibrate": {"all"}, "rpc-all-test_runner": {"test-runner"},
            "rpc-all-screen_coverage": {"screen"}, "B1753": {"sql-b1753-output", "sql-b1753-profile"},
            "B1760": {"sql-b1760-output", "sql-b1760-profile"},
            "B1753-power": {"sql-b1753-power-output", "sql-b1753-power-profile"}}
        p.require(not self.tainted and label in allowed.get(requester, set())
            and label not in self.used_allocations, "RPC allocator label/replay")
        path = Path(self.context.get("allocations", {}).get(label, ""))
        p.require(requested is None or str(requested) == str(path), "RPC allocator exact requested path")
        p.inside(self.root, path, absent=True)
        path.mkdir(mode=0o700)  # parent root-déclaré déjà présent ; aucune mkdir libre/récursive.
        self.used_allocations.add(label)
        return path

    def capture(self, command, *, cwd, env, timeout, stdout_path, stderr_path, label):
        row = self._next()
        supplied = {"argv": command, "cwd": str(cwd), "environment": env,
            "stdout_path": str(stdout_path), "stderr_path": str(stderr_path),
            "timeout_seconds": timeout, "label": label, "source_refs": row["source_refs"]}
        p.require(p.same(supplied, p.closed_payload(row)), "RPC client exact closed call mismatch")
        now = self.clock()
        parent_deadline = p.fresh_budget(now, row, self.context, self.enrollment)
        for ref in row["source_refs"]:
            p.read_reference(ref)
        for name in ("stdout_path", "stderr_path"):
            p.inside(self.root, row[name], absent=True)
        request = p.common(self.context) | {"schema": p.REQUEST_SCHEMA, "publication_protocol": p.PROTOCOL,
            "id": row["id"], "descriptor_digest": p.digest(row), "requester_id": row["requester_id"],
            "logical_parent_id": row["logical_parent_id"], "index": row["index"], "nonce": row["nonce"],
            "requester_identity": self.enrollment["identity"], "created_monotonic": now,
            "payload": supplied}
        request_ref = p.publish(self.root, p.event_path(self.root, row, "request"), request)
        ack_path = p.event_path(self.root, row, "ack")
        deadline = min(parent_deadline, now + timeout + p.CAPTURE_SECONDS + p.CLEANUP_SECONDS)
        try:
            if self.exchange is not None:
                self.exchange.submit(request_ref, row, deadline)
            while self.clock() <= deadline:
                if self.poll_hook is not None:
                    self.poll_hook()
                try:
                    ack = (self.exchange.read_ack(ack_path, deadline) if self.exchange is not None
                           else p.read_committed(self.root, ack_path))
                except FileNotFoundError:
                    self.sleeper(0.01)
                    continue
                p.require(self.clock() <= deadline, "RPC ACK arrived after outer bound")
                self._check_ack(ack, row, request_ref)
                self.last_ack = p.reference(ack_path)
                stdout = p.read_reference(ack["stdout_ref"], root=self.root).decode("utf-8")
                stderr = p.read_reference(ack["stderr_ref"], root=self.root).decode("utf-8")
                self.cursor += 1
                return subprocess.CompletedProcess(list(command), ack["exit_code"], stdout, stderr)
            p.publish(self.root, p.event_path(self.root, row, "cancel"), p.common(self.context) |
                {"publication_protocol": p.PROTOCOL, "schema": "c17-g5-root-rpc-cancel-v1",
                 "request_ref": request_ref, "id": row["id"], "nonce": row["nonce"],
                 "reason": "client_ack_deadline", "created_monotonic": self.clock()})
            raise RpcTimeout("RPC ACK deadline: instrument red, no returncode invented")
        except BaseException:
            self.tainted = True
            raise
        finally:
            if self.exchange is not None:
                self.exchange.close()

    def _check_ack(self, ack, row, request_ref):
        p.require(ack.get("schema") == p.ACK_SCHEMA and ack.get("request_ref") == request_ref
            and ack.get("descriptor_digest") == p.digest(row) and ack.get("id") == row["id"]
            and ack.get("index") == row["index"] and ack.get("nonce") == row["nonce"], "RPC ACK exact request")
        for key, value in p.common(self.context).items():
            p.require(ack.get(key) == value, "RPC ACK context " + key)
        if ack.get("state") != "complete":
            raise RpcInstrumentError("RPC instrument refused/timeout: " + str(ack.get("instrument_error")))
        p.require(type(ack.get("exit_code")) is int and ack.get("tainted") is False
            and ack.get("termination_proved") is True and ack.get("log_stability_proved") is True
            and ack.get("cleanup_deadline_met") is True and ack.get("signals") == [], "RPC normal closure unproved")
        p.identity(ack["child_identity"])
        raw = p.checked_json(ack["receipt_ref"], root=self.root)
        cleanup = p.checked_json(ack["cleanup_ref"], root=self.root)
        p.same_identity(raw["root_identity"], ack["child_identity"])
        p.same_identity(cleanup["child_identity"], ack["child_identity"])
        p.require(type(raw.get("exit_code")) is int and raw["exit_code"] == ack["exit_code"]
            and raw.get("raw_stable") is True and raw.get("timed_out") is False
            and raw.get("log_stability_tainted") is False and raw.get("instrument_error") is None
            and cleanup.get("clean") is True and cleanup.get("log_stability_proved") is True
            and cleanup.get("remaining_attributed") == cleanup.get("ambiguities") == cleanup.get("errors") == []
            and cleanup.get("signals") == [] and cleanup.get("receipt_ref") == ack["receipt_ref"],
            "RPC referenced normal receipt/cleanup contradicted")
        if p.wrapper_scope(self.root) and row['id'] in p.CHROME_JOBS:
            p.require(cleanup.get('auxiliary_terminal_ref') == ack.get('auxiliary_terminal_ref'),
                      'RPC auxiliary ACK/cleanup join')
            p.validate_auxiliary_terminal(ack.get('auxiliary_terminal_ref'), row, self.root,
                self.context, ack['receipt_ref'], normal=True,
                binding_sha256=os.environ.get('C17_SESSION_BINDING_SHA256'))


class UnixRpcExchange:
    """Helper : un seul Unix stream, exacts octets publiés, gardé jusqu'à ACK.

La factory socket est injectée dans les tests ; aucune socket à l'import.
Seul rpc_client/rpc_protocol est requis dans les deux répertoires des wrappers.
"""
    def __init__(self, root, context, *, socket_factory=socket.socket, clock=time.monotonic):
        self.root, self.context = p.canonical_root(root), context
        self.socket_factory, self.clock, self.connection = socket_factory, clock, None

    def _remaining(self, deadline):
        remaining = deadline - self.clock()
        if remaining <= 0:
            raise RpcTimeout("RPC Unix stream deadline, instrument red")
        self.connection.settimeout(remaining)

    def _owner_peer(self):
        p.require(self.connection.family == socket.AF_UNIX
            and self.connection.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) == socket.SOCK_STREAM
            and self.connection.getsockopt(0, 2) == self.context["owner_identity"]["pid"],
            "RPC connected Unix owner kernel PID mismatch")

    def submit(self, request_ref, row, deadline):
        p.require(self.connection is None and request_ref["path"] == str(p.event_path(self.root, row, "request")),
                  "RPC Unix exact root-derived request destination")
        raw = p.read_reference(request_ref, root=self.root, limit=p.MAX_MESSAGE_BYTES)
        path = p.inside(self.root, self.root / "session-rpc/peer.sock")
        info = path.lstat()
        p.require(stat.S_ISSOCK(info.st_mode) and info.st_uid == os.getuid()
            and info.st_mode & 0o077 == 0, "RPC Unix socket type/owner/private mode")
        self.connection = self.socket_factory(socket.AF_UNIX, socket.SOCK_STREAM)
        self._remaining(deadline)
        self.connection.connect(str(path))
        self._owner_peer()
        self.connection.sendall(struct.pack("!I", len(raw)) + raw)

    def _read_exact(self, count, deadline):
        result = bytearray()
        while len(result) < count:
            self._remaining(deadline)
            try:
                data = self.connection.recv(count - len(result))
            except TimeoutError as error:
                raise RpcTimeout("RPC Unix ACK socket deadline") from error
            p.require(bool(data), "RPC Unix EOF before complete ACK")
            result.extend(data)
        return bytes(result)

    def read_ack(self, path, deadline):
        size = struct.unpack("!I", self._read_exact(4, deadline))[0]
        p.require(0 < size <= p.MAX_MESSAGE_BYTES, "RPC Unix bounded ACK frame")
        raw = self._read_exact(size, deadline)
        self._owner_peer()
        value = p.read_committed(self.root, path)
        p.require(raw == p.read_reference(p.reference(path), root=self.root, limit=p.MAX_MESSAGE_BYTES),
                  "RPC Unix ACK bytes differ from root-derived committed artifact")
        p.require(self.clock() <= deadline, "RPC Unix ACK after deadline")
        return value

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
