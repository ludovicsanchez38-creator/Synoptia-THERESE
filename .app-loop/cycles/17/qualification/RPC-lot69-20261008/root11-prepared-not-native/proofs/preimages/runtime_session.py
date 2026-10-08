#!/usr/bin/env python3
"""G1 C17 : définition runtime séparée. Admissions fermées, aucun GO auteur."""
from __future__ import annotations

import argparse
import ctypes
from datetime import UTC, datetime
import errno
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import threading
import time


HERE = Path(__file__).resolve().parent
HEAD = "542cc6f7b7ef764a7730a9b99918df5ac02d54f2"
PYTHON = Path("/private/tmp/therese-c17-full-suite-ps_tgzy5/source/.venv-conforme/bin/python")
SOURCE = Path("/private/tmp/therese-c17-full-suite-ps_tgzy5/source")
NODE_ROOT = Path("/Users/synoptia/.nvm/versions/node/v22.19.0")
PYTHON_ALIAS = Path("/Users/synoptia/.local/share/uv/python/cpython-3.13-macos-aarch64-none")
PYTHON_ROOT = Path("/Users/synoptia/.local/share/uv/python/cpython-3.13.5-macos-aarch64-none")
RPC_CANARY_PYTHON = PYTHON_ROOT / "bin/python3.13"  # stdlib, no product QA venv/site-packages.
PORTS = (17593, 5173)
CHROME_JOBS = ("rpc-all-runtime_ui-visual_capture-network_capture", "rpc-screen-negative",
               "rpc-screen-positive-visual", "rpc-screen-positive-network", "rpc-screen-restored")
AUXILIARY_NAMES = {job: "aux-chrome-" + job for job in CHROME_JOBS}
AUXILIARY_ROLES = frozenset("auxiliary-" + name for name in AUXILIARY_NAMES.values())
AUXILIARY_PORT = 17594  # politique proposée distincte, aucune qualification native.
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
PERSISTENT = frozenset(("persistent-backend", "persistent-vite"))
PUBLICATION_PROTOCOL = "exclusive-pending-fsync-hardlink-v1"
API_SCHEMA = "c17-runtime78-session-api-v1"
RUNTIME_ENABLED = False
OS_STARTUP_QUALIFIED = False
CAPABILITIES = {"owned_listener_rpc": False, "nested_normal_completion_stable_fd": False,
                "nested_timeout_handshake": False, "ports_absence_proof": False}
# A renseigner seulement après nouveau gel + revue/root GO : paths/ids/acteur/
# ronde, PAS de hash de décision dans le module (aucun cycle de SHA).
ADMISSION_TABLE: dict[str, dict] = {}
# Instrument seul : le root devra émettre un slot après revue du nouveau gel.
# Paths/id/HEAD seulement, jamais hash futur de décision (pas de cycle).
WRAPPER_ADMISSION_TABLE: dict[str, dict] = {}
WRAPPER_SCOPE = "g1_rpc_real_instrument_wrappers_canary_only"
WRAPPER_PARENTS = frozenset(("calibrate", "B1753", "B1760", "B1753-power"))
WRAPPER_STAGES = WRAPPER_PARENTS | frozenset(("backend", "vite"))
WRAPPER_PATTERN = re.compile(r"therese-c17-wrapper-canary-[a-z0-9_]{8,64}\Z")
DECISION_ROOT = Path("/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex/.app-loop/cycles/17/qualification")
STAGE_TIMEOUTS = {
    "backend": 50, "vite": 50, "prepare-runtime": 120, "start-runtime": 120,
    "calibrate": 1200, "recipe-general": 360, "recipe-invoices": 360, "recipe-crm": 360,
    "B1713": 360, "P157-800": 360, "P157-1440": 360, "B1755": 360,
    "P162": 360, "B1753": 360, "B1760": 360, "coverage": 1500,
    "build-calibrations-v3": 120, "density": 1500, "bind-current-context-contract": 120,
    "B1753-power": 360, "eight-logs-review": 120, "mapping78": 120, "package78": 120,
    "canary-positive": 30, "canary-timeout": 30,
}
# Exact direct children of the five reviewed G5 call sites.  These are not
# runnable from a request alone: the root-issued binding must contain the
# complete command, environment, cwd and two exclusive sinks for each name.
RPC_CHILDREN = {
    "rpc-all-test_runner": ("calibrate", 700, "web"),
    "rpc-all-logs": ("calibrate", 700, "web"),
    "rpc-all-runtime_ui-visual_capture-network_capture": ("calibrate", 700, "web"),
    "rpc-all-screen_coverage": ("calibrate", 700, "web"),
    "rpc-test-pytest-positive": ("rpc-all-test_runner", 90, "web"),
    "rpc-test-pytest-negative": ("rpc-all-test_runner", 90, "web"),
    "rpc-test-vitest-positive": ("rpc-all-test_runner", 90, "web"),
    "rpc-test-vitest-negative": ("rpc-all-test_runner", 90, "web"),
    "rpc-screen-negative": ("rpc-all-screen_coverage", 180, "web"),
    "rpc-screen-positive-visual": ("rpc-all-screen_coverage", 180, "web"),
    "rpc-screen-positive-network": ("rpc-all-screen_coverage", 180, "web"),
    "rpc-screen-restored": ("rpc-all-screen_coverage", 180, "web"),
    "rpc-sql-b1753": ("B1753", 240, "sql"),
    "rpc-sql-b1760": ("B1760", 240, "sql"),
    "rpc-sql-b1753-power": ("B1753-power", 240, "sql"),
}
STAGE_TIMEOUTS.update({name: row[1] for name, row in RPC_CHILDREN.items()})
STAGE_TIMEOUTS.update({name: 50 for name in AUXILIARY_NAMES.values()})
RPC_REQUESTERS = frozenset(parent for parent, _, _ in RPC_CHILDREN.values())
ENV_CONSTANTS = {
    "__CF_USER_TEXT_ENCODING": f"0x{os.getuid():X}:0:0",
    "PATH": str(NODE_ROOT / "bin") + ":/usr/bin:/bin:/usr/sbin:/sbin",
    "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8", "PYTHONNOUSERSITE": "1",
    "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1",
    "PYTHONPATH": str(SOURCE) + ":" + str(SOURCE / "src/backend"),
    "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
    "PYTHON_KEYRING_BACKEND": "keyring.backends.null.Keyring", "THERESE_SKIP_SERVICES": "1",
    "THERESE_SONDE_CATALOGUE": "off", "OLLAMA_BASE_URL": "http://127.0.0.1:9",
    "PORT": "17593", "HOST": "127.0.0.1", "VITE_THERESE_BACKEND_PORT": "17593",
}
ENV_PATHS = frozenset(("HOME", "CFFIXED_USER_HOME", "TMPDIR", "XDG_CACHE_HOME", "THERESE_DATA_DIR",
                      "DATA_DIR", "DB_PATH", "QDRANT_PATH", "C16_ACTION_TRACE", "C16_OUT",
                      "PLAYWRIGHT_BROWSERS_PATH"))
ENV_CONTEXT = frozenset(("C16_ACTOR", "C16_ROUND_ID", "C16_REVIEWED_SHA256", "C16_WIDTH", "THERESE_DB_PLAINTEXT",
                         "C17_G1_CANARY_ONLY", "C17_RPC_CANARY_ONLY", "C17_RPC_CONTEXT_REF"))
REQUIRED_ENV = frozenset(("PATH", "HOME", "CFFIXED_USER_HOME", "TMPDIR", "LANG", "LC_ALL",
                          "PYTHONNOUSERSITE", "PYTHONDONTWRITEBYTECODE", "PYTHONPATH",
                          "__CF_USER_TEXT_ENCODING"))
ROUND_PATTERN = re.compile(r"therese-c17-direct-round-([ab])-([a-z0-9-]{8,64})\Z")
_ACTIVE_SESSION: Session | None = None


class InstrumentError(RuntimeError):
    """Instrumentation incertaine : aucune assertion produit admissible."""


class ListenerNotReady(OSError):
    """Seule absence fraîche, non ambiguë, réessayable avant readiness."""


class ListenerScanError(InstrumentError):
    def __init__(self, message: str, raw: dict) -> None:
        self.raw = raw
        super().__init__(message)



class IdentityReadError(InstrumentError):
    def __init__(self, pid: int, error_number: int) -> None:
        self.pid, self.error_number = pid, error_number
        super().__init__(f"Identité Darwin illisible pid={pid} errno={error_number} ; pas une absence")


class ControllerInterrupted(BaseException):
    """Ne doit jamais être avalé par un except OSError de disponibilité réseau."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InstrumentError(message)


def now() -> str:
    return datetime.now(UTC).isoformat()


def reference(path: Path) -> dict:
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size}


def _load_exact_relay_definition(name: str, expected_sha: str):
    path = HERE / name
    require(path.resolve(strict=True) == path and not path.is_symlink()
            and path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha,
            "Dépendance relais exacte SHA absente/changée : " + name)
    spec = importlib.util.spec_from_file_location("_c17_exact_" + name.removesuffix(".py"), path)
    require(spec is not None and spec.loader is not None, "Chargeur relais absent")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha, "Relais changé pendant import")
    return module


_relay_protocol = _load_exact_relay_definition("relay_protocol.py", "f9dacee7194967f825219e631d3ef42aaba2bca6091d4a79cc9bfa73aad23dd0")
runtime_bounds = _load_exact_relay_definition("runtime_bounds.py", "e1ef6aae69448fcbcb79c9dbba0ded2fef832f98a0244fe863cdeffba58371f5")
root_stage_relay = _load_exact_relay_definition("root_stage_relay.py", "7837e2c5f7cdc86ae57edd60b47248de71ab88150bd56555697c4d29ca43555b")
root_stage_relay.protocol = _relay_protocol
root_stage_relay.bounds = runtime_bounds

def child_path(root: Path, path: Path, *, existing: bool = False) -> Path:
    resolved = path.resolve(strict=existing)
    require(resolved.is_relative_to(root) and resolved != root, "Chemin hors QA ou racine entière")
    return resolved


def exclusive(path: Path):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        return os.fdopen(fd, "wb", buffering=0)
    except BaseException:
        os.close(fd)
        raise


def save(root: Path, path: Path, value: dict) -> None:
    child_path(root, path)
    with exclusive(path) as handle:
        handle.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())
        handle.flush()
        os.fsync(handle.fileno())


def publish_json(root: Path, path: Path, value: dict) -> None:
    """Publication visible seulement après fermeture/fsync, jamais overwrite."""
    require(value.get("publication_protocol") == PUBLICATION_PROTOCOL, "Protocole publication absent")
    child_path(root, path)
    pending = path.with_name(path.name + ".pending")
    child_path(root, pending)
    payload = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    with exclusive(pending) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.link(pending, path, follow_symlinks=False)  # EEXIST si destination existe.
    # Le pending fermé reste une preuve brute. Aucun unlink/rename/overwrite.


def read_published_json(root: Path, path: Path) -> dict:
    """Lire seulement un objet publié par le protocole hardlink exact."""
    require(child_path(root, path, existing=True) == path, "Objet publié non canonique")
    pending = path.with_name(path.name + ".pending")
    require(child_path(root, pending, existing=True) == pending, "Pending non canonique")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as committed:
        with os.fdopen(os.open(pending, os.O_RDONLY | os.O_NOFOLLOW), "rb") as staged:
            a, b = os.fstat(committed.fileno()), os.fstat(staged.fileno())
            require(stat.S_ISREG(a.st_mode) and stat.S_ISREG(b.st_mode)
                    and (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino) and a.st_nlink == b.st_nlink == 2
                    and a.st_uid == b.st_uid == os.getuid() and a.st_size == b.st_size,
                    "Publication sans pending fermé/hardlink exclusif exact")
            payload = committed.read()
            require(len(payload) == a.st_size, "Objet publié taille différente")
    value = json.loads(payload)
    require(isinstance(value, dict) and value.get("publication_protocol") == PUBLICATION_PROTOCOL,
            "Objet publié sous autre protocole")
    return value


class BSDInfo(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in
                ("flags", "status", "xstatus", "pid", "ppid", "uid", "gid", "ruid", "rgid", "svuid", "svgid", "reserved")]
    _fields_ += [("comm", ctypes.c_char * 16), ("name", ctypes.c_char * 32)]
    _fields_ += [(name, ctypes.c_uint32) for name in ("nfiles", "pgid", "jobc", "tdev", "tpgid")]
    _fields_ += [("nice", ctypes.c_int32), ("start_sec", ctypes.c_uint64), ("start_usec", ctypes.c_uint64)]


class DarwinLedger:
    def __init__(self) -> None:
        require(sys.platform == "darwin", "Darwin requis")
        self.lib = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        self.lib.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
        self.lib.proc_pidinfo.restype = ctypes.c_int
        self.lib.proc_listallpids.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.lib.proc_listallpids.restype = ctypes.c_int
        self.lib.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
        self.lib.proc_pidpath.restype = ctypes.c_int
        self.records: dict[tuple[int, int, int], dict] = {}
        self.events: list[dict] = []
        self.ambiguous: list[dict] = []
        self.attribution_errors: list[dict] = []
        self.snapshot_audits: list[dict] = []
        self.snapshot_totals = {"snapshots": 0, "listed": 0, "read": 0, "ESRCH": 0, "unattributed_permission_refusals": 0}
        own = self.info(os.getpid())
        require(own is not None and own["ppid"] == os.getppid() and own["uid"] == os.getuid()
                and own["pgid"] == os.getpgrp() and own["start_sec"] > 0
                and 0 <= own["start_usec"] < 1_000_000, "ABI/identité parent non confirmée")
        self.owner = own

    @staticmethod
    def key(row: dict) -> tuple[int, int, int]:
        return row["pid"], row["start_sec"], row["start_usec"]

    def info(self, pid: int) -> dict | None:
        value = BSDInfo()
        ctypes.set_errno(0)
        count = self.lib.proc_pidinfo(pid, 3, 0, ctypes.byref(value), ctypes.sizeof(value))
        error_number = ctypes.get_errno()
        if count == 0:
            if error_number == errno.ESRCH:
                return None
            raise IdentityReadError(pid, error_number)
        require(count == ctypes.sizeof(value) and value.pid == pid and error_number == 0, "Lecture BSD incomplète/incertaine")
        return {name: getattr(value, name) for name in
                ("pid", "ppid", "uid", "pgid", "status", "start_sec", "start_usec")}

    def executable(self, pid: int) -> str | None:
        buffer = ctypes.create_string_buffer(4096)
        count = self.lib.proc_pidpath(pid, buffer, len(buffer))
        if count <= 0:
            return None
        return os.fsdecode(buffer.value)

    def snapshot(self) -> dict[int, dict]:
        ctypes.set_errno(0)
        count = self.lib.proc_listallpids(None, 0)
        require(0 < count <= 16_384, "Inventaire Darwin indisponible/hors borne")
        buffer = (ctypes.c_int * (count + 1024))()
        ctypes.set_errno(0)
        actual = self.lib.proc_listallpids(buffer, ctypes.sizeof(buffer))
        require(0 < actual < len(buffer), "Inventaire tronqué")
        rows = {}
        known = {self.owner["pid"], *(row["pid"] for row in self.records.values())}
        listed = {pid for pid in buffer[:actual] if pid > 0}
        audit = {"at": now(), "listed": len(listed), "read": 0, "ESRCH": 0,
                 "unattributed_permission_refusals": 0, "unattributed_refusal_sample": [], "error": None,
                 "supplemental_known_pids": sorted(known - listed), "scope": "observed_attribution_not_hostile_exhaustiveness"}
        try:
            for pid in sorted(listed | known):
                try:
                    row = self.info(pid)
                except IdentityReadError as error:
                    if pid in known or error.error_number not in (errno.EPERM, errno.EACCES):
                        raise  # connu/incertain : jamais assimilé à disparu.
                    audit["unattributed_permission_refusals"] += 1
                    if len(audit["unattributed_refusal_sample"]) < 16:
                        audit["unattributed_refusal_sample"].append({"pid": pid, "errno": error.error_number})
                    continue  # non attribué, non adopté, non signalable ; pas une absence.
                if row is None:
                    audit["ESRCH"] += 1
                else:
                    rows[pid] = row
                    audit["read"] += 1
        except InstrumentError as error:
            audit["error"] = str(error)
            raise
        finally:
            self.snapshot_audits.append(audit)
            self.snapshot_audits = self.snapshot_audits[-64:]
            self.snapshot_totals["snapshots"] += 1
            for key in ("listed", "read", "ESRCH", "unattributed_permission_refusals"):
                self.snapshot_totals[key] += audit[key]
        return rows

    def unchanged(self, old: dict, current: dict | None) -> bool:
        return (current is not None and self.key(old) == self.key(current)
                and current["uid"] == old["uid"] and current["pgid"] == old["pgid"])

    def admit_root(self, pid: int, role: str) -> dict:
        require(self.unchanged(self.owner, self.info(self.owner["pid"])), "Parent contrôleur changé")
        row = self.info(pid)
        require(row is not None and row["ppid"] == self.owner["pid"] and row["uid"] == self.owner["uid"]
                and row["pgid"] == pid and row["status"] != 5, "Racine Popen non attribuable")
        entry = row | {"role": role, "parent_birth": list(self.key(self.owner)),
                       "attribution": "popen_child_before_workload", "captured_at": now()}
        self.records[self.key(row)] = entry
        return entry

    def attribute(self) -> None:
        try:
            self._attribute()
        except InstrumentError as error:
            self.attribution_errors.append({"at": now(), "error": str(error)})
            raise

    def _attribute(self) -> None:
        rows = self.snapshot()
        require(self.unchanged(self.owner, rows.get(self.owner["pid"])), "Parent contrôleur absent/changé")
        by_pid = {row["pid"]: row for row in self.records.values()
                  if self.unchanged(row, rows.get(row["pid"])) and rows[row["pid"]]["status"] != 5}
        changed = True
        while changed:
            changed = False
            for pid, row in rows.items():
                if self.key(row) in self.records or row["uid"] != self.owner["uid"]:
                    continue
                parent = by_pid.get(row["ppid"])
                if parent is None:
                    continue
                require((row["start_sec"], row["start_usec"]) >= (parent["start_sec"], parent["start_usec"]),
                        "Naissance enfant antérieure au parent")
                # Aucune adoption par seul PGID. Le parent de même birth doit
                # être vivant dans ce snapshot ; un setsid observé reste borné.
                if row["pgid"] not in (parent["pgid"], row["pid"]):
                    self.ambiguous.append(row | {"reason": "pgid_transition_not_reviewed"})
                    raise InstrumentError("PGID descendant non admis")
                entry = row | {"role": parent["role"], "parent_birth": list(self.key(parent)),
                               "attribution": "live_exact_parent_uid_pgid", "captured_at": now()}
                self.records[self.key(row)] = entry
                by_pid[pid] = entry
                changed = True
        # Un membre du groupe propre n'est PAS adopté sans parent vivant.
        # Sa présence est une ambiguïté qui refuse le nettoyage vert, jamais
        # une autorisation de lui envoyer un signal.
        roots = [r for r in self.records.values() if r["attribution"] == "popen_child_before_workload"]
        for row in rows.values():
            if self.key(row) in self.records or row["uid"] != self.owner["uid"] or row["status"] == 5:
                continue
            for root in roots:
                if (row["pgid"] == root["pgid"] and (row["start_sec"], row["start_usec"])
                        >= (root["start_sec"], root["start_usec"])):
                    ambiguity = row | {"reason": "unattributed_member_of_owned_group", "root_birth": list(self.key(root))}
                    if ambiguity not in self.ambiguous:
                        self.ambiguous.append(ambiguity)
                    raise InstrumentError("Membre de groupe non attribué ; aucun signal")

    def live(self, roles: frozenset[str] | set[str] | None = None) -> list[dict]:
        result = []
        for old in self.records.values():
            if roles is not None and old["role"] not in roles:
                continue
            try:
                row = self.info(old["pid"])
            except InstrumentError as error:
                self.ambiguous.append({"expected": old, "reason": "identity_read_failed", "error": str(error)})
                continue
            if row is None or self.key(row) != self.key(old) or row["status"] == 5:
                continue
            if not self.unchanged(old, row):
                ambiguity = row | {"expected": old, "reason": "uid_or_pgid_changed"}
                if ambiguity not in self.ambiguous:
                    self.ambiguous.append(ambiguity)
                continue  # rouge conservé, autres identités exactes encore nettoyables.
            result.append(old)
        return result

    def residuals(self, roles: set[str]) -> list[dict]:
        """Toute birth connue encore vivante, même UID/PGID devenu ambigu.

        C'est une preuve de résidu, PAS une liste de cibles à signaler.
        """
        result = []
        for old in self.records.values():
            if old["role"] not in roles:
                continue
            try:
                current = self.info(old["pid"])
            except InstrumentError as error:
                result.append({"expected": old, "identity_unreadable": str(error)})
                continue
            if current is not None and self.key(current) == self.key(old) and current["status"] != 5:
                result.append(current | {"expected": old, "exact_signal_candidate": self.unchanged(old, current)})
        return result

    def verify_signal_candidate(self, row: dict, allowed_roles: set[str] | frozenset[str], current: dict | None) -> bool:
        """Garde pure : copies négatives admises comme sondes, jamais ciblées."""
        canonical = self.records.get(self.key(row))
        fields = ("pid", "start_sec", "start_usec", "uid", "ppid", "pgid", "role", "parent_birth", "attribution")
        require(canonical is not None and row["role"] in allowed_roles
                and all(row.get(field) == canonical.get(field) for field in fields),
                "Cible birth/UID/PGID/filiation/rôle non canonique")
        if current is None or self.key(current) != self.key(row) or current["status"] == 5:
            return False
        require(self.unchanged(row, current), "UID/PGID changé ; signal refusé")
        return True

    def send(self, row: dict, sig: signal.Signals, allowed_roles: set[str] | frozenset[str]) -> None:
        # Valider d'abord la copie canonique sans diagnostic PID étranger.
        self.verify_signal_candidate(row, allowed_roles, None)
        current = self.info(row["pid"])
        if not self.verify_signal_candidate(row, allowed_roles, current):
            return
        # Aucun killpg : lecture libproc immédiatement avant le signal PID.
        # Darwin n'expose pas ici un kill atomique conditionné à start_usec.
        try:
            os.kill(row["pid"], sig)
        except ProcessLookupError:
            return
        self.events.append({"identity": list(self.key(row)), "uid": row["uid"], "pgid": row["pgid"],
                            "role": row["role"], "signal": sig.name, "at": now()})

    def cleanup(self, roles: set[str], processes: list[subprocess.Popen]) -> dict:
        event_start = len(self.events)
        errors = []
        def scan():
            try:
                self.attribute()
            except InstrumentError as error:
                errors.append({"phase": "attribute", "error": str(error)})
        def send_all(sig):
            # Les ambiguïtés ne sont pas adoptées, mais ne bloquent pas le
            # nettoyage des AUTRES identités exactement connues et relues.
            for row in self.live(roles):
                try:
                    self.send(row, sig, roles)
                except (InstrumentError, OSError) as error:
                    errors.append({"phase": sig.name, "identity": list(self.key(row)), "error": str(error)})
        scan()
        # Geler uniquement les branches de ce lot, jamais les services lors
        # d'un nettoyage d'étape. Trois scans capturent les derniers forks.
        for _ in range(3):
            send_all(signal.SIGSTOP)
            scan()
        send_all(signal.SIGTERM)
        send_all(signal.SIGCONT)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and self.live(roles):
            for process in processes:
                process.poll()
            scan()
            time.sleep(0.02)
        send_all(signal.SIGKILL)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and self.live(roles):
            for process in processes:
                process.poll()
            time.sleep(0.02)
        for process in processes:
            if process.poll() is None:
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
        remaining = self.residuals(roles)
        return {"roles": sorted(roles), "signals": self.events[event_start:],
                "remaining_attributed": remaining, "termination_of_exact_targets_proved": not remaining,
                "clean": not remaining and not self.ambiguous and not errors,
                "ambiguities": list(self.ambiguous), "errors": errors,
                "snapshot_totals": dict(self.snapshot_totals), "snapshot_audits_tail": list(self.snapshot_audits)}


def checked_json_ref(ref: dict, allowed_root: Path) -> dict:
    require(isinstance(ref, dict) and isinstance(ref.get("path"), str)
            and re.fullmatch(r"[a-f0-9]{64}", ref.get("sha256", "")) is not None, "Référence immuable invalide")
    path = Path(ref["path"])
    require(path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink()
            and path.is_relative_to(allowed_root), "Référence hors périmètre canonique")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as handle:
        st = os.fstat(handle.fileno())
        require(stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid() and 0 < st.st_size <= 4_000_000,
                "Référence non régulière / mauvais owner / taille")
        payload = handle.read()
    require(len(payload) == st.st_size and hashlib.sha256(payload).hexdigest() == ref["sha256"]
            and ("bytes" not in ref or ref["bytes"] == len(payload)), "Référence SHA/taille différente")
    value = json.loads(payload)
    require(isinstance(value, dict), "Référence JSON pas un objet")
    return value


def load_canary_admission(root: Path, *, actor: str, round_id: str, round_name: str,
                          decision_ref: dict, binding_ref: dict) -> tuple[dict, dict]:
    """Canari inerte isolé ; n'authentifie pas root et n'ouvre aucune ronde FULL."""
    require(not RUNTIME_ENABLED and not OS_STARTUP_QUALIFIED and not any(CAPABILITIES.values()),
            "Canari distinct impossible si une porte FULL est ouverte")
    require(root.parent == Path("/private/tmp") and root.resolve(strict=True) == root and not root.is_symlink(),
            "Racine canari non canonique")
    match = re.fullmatch(r"therese-c17-g1-canary-(positive|timeout)-([a-z0-9_]{8,64})", root.name)
    require(match is not None and round_name == "CANARY" and round_id == root.name and actor == "/root",
            "Identité/racine du canari inerte différente")
    variant = match[1]
    stage = "canary-" + variant
    decision = checked_json_ref(decision_ref, root)
    binding = checked_json_ref(binding_ref, root)
    require(decision_ref["path"] == str(root / "decision.json")
            and binding_ref["path"] == str(root / "binding.json"), "Références canari hors paths exclusifs")
    require(decision.get("schema") == "c17-g1-inert-canary-decision-v1"
            and decision.get("scope") == "g1_inert_lifecycle_canary_only"
            and decision.get("provenance") == "self_generated_not_root_authorization"
            and decision.get("binding") == binding_ref
            and decision.get("decision_id") == round_id
            and decision.get("canary_variant") == variant,
            "Décision canari auto-déclarée non exactement bornée")
    require(binding.get("schema") == "c17-g1-inert-canary-binding-v1"
            and binding.get("decision_plan") == {"path": decision_ref["path"], "decision_id": round_id}
            and binding.get("canary_variant") == variant,
            "Binding canari différent")
    for item in (decision, binding):
        require(all(item.get(k) == v for k, v in {"actor": actor, "round_id": round_id,
            "round_name": round_name, "qa_root": str(root), "head": HEAD}.items()),
            "Contexte canari différent")
    st = root.stat()
    require(st.st_uid == os.getuid() and binding.get("root_identity") == {
        "dev": st.st_dev, "ino": st.st_ino, "uid": st.st_uid, "birthtime": st.st_birthtime},
        "Racine canari réutilisée/changée")
    instruments = ["runtime_session.py", "runtime_launch_gate.py", "sql.sb", "canary_workload.py",
                   "nested_capture.py", "joint_protocol.py", "joint_owner.py", "child_gate.py",
                   "fixture_child.py", "joint-contract.json", "run_joint.py"]
    refs = [reference(HERE / name) for name in instruments]
    require(decision.get("instruments") == refs and binding.get("source_refs") == refs,
            "Sources/profil du canari changés")
    expected_argv = [str(PYTHON), "-I", "-B", str(HERE / "canary_workload.py"), variant]
    spec = binding.get("commands", {}).get(stage)
    require(binding.get("commands") == {stage: spec} and isinstance(spec, dict)
            and spec.get("argv") == expected_argv and spec.get("role") == "stage-" + stage
            and spec.get("mode") == "sql" and spec.get("timeout_seconds") == STAGE_TIMEOUTS[stage]
            and spec.get("cwd") == str(root)
            and spec.get("stdout_path") == str(root / "output" / "stdout")
            and spec.get("stderr_path") == str(root / "output" / "stderr")
            and spec.get("combine_stderr") is False
            and spec.get("derived_deadline") == "start_monotonic_plus_exact_timeout"
            and isinstance(spec.get("env"), dict)
            and spec["env"].get("C17_G1_CANARY_ONLY") == "1",
            "Commande canari non inerte/exacte")
    return decision, binding


RPC_CANARY_PARENTS = {"B1753": "sql-b1753", "B1760": "sql-b1760",
                      "B1753-power": "sql-b1753-power"}
RPC_CANARY_REQUIRED_SOURCES = (
    "g1/runtime_session.py", "g1/runtime_bounds.py", "g1/relay_protocol.py",
    "g1/root_stage_relay.py", "g1/runtime_launch_gate.py", "g1/sql.sb",
    "g1/rpc_canary_parent.py", "g1/rpc_canary_child.py", "g1/rpc_canary_node.mjs",
    "g1/run_rpc_canary.py",
    "source/session_rpc_adapter.py", "source/rpc_protocol.py", "source/rpc_client.py",
    "source/rpc_dispatcher.py", "source/rpc_peer.py", "source/rpc_unix.py",
)
RPC_CANARY_ENV_KEYS = frozenset((
    "PATH", "HOME", "CFFIXED_USER_HOME", "TMPDIR", "THERESE_DATA_DIR", "DATA_DIR", "PYTHONPATH",
    "LANG", "LC_ALL", "PYTHONNOUSERSITE", "PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED",
    "__CF_USER_TEXT_ENCODING", "THERESE_SKIP_SERVICES", "PYTHON_KEYRING_BACKEND",
    "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "OLLAMA_BASE_URL", "THERESE_ENV",
    "THERESE_DB_KEY", "C16_ACTOR", "C16_ROUND_ID", "C17_RPC_CANARY_ONLY",
    "C17_RPC_CONTEXT_REF", "PORT", "HOST", "VITE_THERESE_BACKEND_PORT",
    "THERESE_DB_PLAINTEXT", "C17_TEST_RUNNER_DEFECT", "C17_SCREEN_WITNESS",
))


def load_rpc_canary_admission(root: Path, *, actor: str, round_id: str, round_name: str,
                              decision_ref: dict, binding_ref: dict) -> tuple[dict, dict]:
    """Inert SQL fixture only; never an alias for product/FULL admission."""
    require(not RUNTIME_ENABLED and not OS_STARTUP_QUALIFIED and not any(CAPABILITIES.values())
            and os.environ.get("C17_RPC_CANARY_ONLY") == "1"
            and os.environ.get("C17_G1_CANARY_ONLY") != "1", "Canari RPC hors porte fermée")
    require(root.parent == Path("/private/tmp") and root.resolve(strict=True) == root
            and not root.is_symlink(), "Racine canari RPC non canonique")
    match = re.fullmatch(r"therese-c17-rpc-canary-(positive|timeout)-([a-z0-9_]{8,64})", root.name)
    require(match is not None and round_name == "RPC_CANARY" and round_id == root.name
            and actor == "/root", "Scope/racine/acteur canari RPC différents")
    variant = match[1]
    require(decision_ref["path"] == str(root / "decision.json")
            and binding_ref["path"] == str(root / "binding.json"),
            "Décision/binding canari RPC hors paths exacts")
    decision = checked_json_ref(decision_ref, root)
    binding = checked_json_ref(binding_ref, root)
    require(decision.get("schema") == "c17-g1-rpc-inert-canary-decision-v1"
            and decision.get("scope") == "g1_rpc_inert_sql_canary_only"
            and decision.get("supplied_by") == "/root"
            and decision.get("decision_id") == round_id
            and decision.get("canary_variant") == variant
            and decision.get("binding") == binding_ref,
            "Décision canari RPC non bornée ; supplied_by n'authentifie pas un GO outil")
    require(binding.get("schema") == "c17-g1-rpc-inert-canary-binding-v1"
            and binding.get("decision_plan") == {"path": decision_ref["path"], "decision_id": round_id}
            and binding.get("canary_variant") == variant,
            "Binding canari RPC hors schéma/variant")
    for item in (decision, binding):
        require(all(item.get(key) == value for key, value in {
            "actor": actor, "round_id": round_id, "round_name": round_name,
            "qa_root": str(root), "head": HEAD}.items()),
            "Contexte canari RPC/HEAD non exact")
    st = root.stat()
    require(st.st_uid == os.getuid() and binding.get("root_identity") == {
        "dev": st.st_dev, "ino": st.st_ino, "uid": st.st_uid, "birthtime": st.st_birthtime},
        "Racine canari RPC réutilisée/changée")
    refs = binding.get("source_refs")
    required = {str(root / relative) for relative in RPC_CANARY_REQUIRED_SOURCES}
    require(isinstance(refs, list) and len(refs) == len(required)
            and {ref.get("path") for ref in refs if isinstance(ref, dict)} == required
            and decision.get("instruments") == refs
            and all(reference(Path(ref["path"])) == ref for ref in refs),
            "Instruments canari RPC non exclusivement QA/byte-exacts")
    require(HERE == root / "g1" and (root / "source").is_dir(),
            "Définitions G1/RPC canari non copiées au bon emplacement QA")
    probe = binding.get("network_probe")
    require(isinstance(probe, dict) and set(probe) == {"host", "tcp_port", "udp_port"}
            and probe["host"] == "127.0.0.1"
            and all(type(probe[key]) is int and 1024 < probe[key] <= 65535
                    for key in ("tcp_port", "udp_port")),
            "Contreparties réseau canari RPC non préliées en loopback")
    require(RPC_CANARY_PYTHON.resolve(strict=True) == RPC_CANARY_PYTHON
            and RPC_CANARY_PYTHON.is_file(), "Python canari physique non canonique")
    denied_path = root / "session-rpc" / "denied.sock"
    denied_stat = denied_path.lstat()
    require(stat.S_ISSOCK(denied_stat.st_mode) and denied_stat.st_uid == os.getuid()
            and denied_stat.st_mode & 0o077 == 0,
            "Counterpart Unix de refus canari absent/étranger/ouvert")
    parents = ("B1753", "B1760") if variant == "positive" else ("B1753-power",)
    commands = binding.get("commands")
    descriptors = binding.get("rpc_descriptors")
    require(isinstance(commands, dict) and isinstance(descriptors, dict)
            and set(descriptors) == set(RPC_CHILDREN)
            and set(commands) == set(RPC_CHILDREN) | set(parents),
            "Table quinze enfants/parents fixtures canari RPC non exacte")
    context_ref, plan_ref = binding.get("rpc_context_ref"), binding.get("rpc_plan_ref")
    require(isinstance(context_ref, dict) and isinstance(plan_ref, dict)
            and context_ref.get("path") == str(root / "session-rpc" / "context.json")
            and plan_ref.get("path") == str(root / "session-rpc" / "plan.json"),
            "Contexte/plan RPC canari non root-préémis")
    context, plan = checked_json_ref(context_ref, root), checked_json_ref(plan_ref, root)
    require(context.get("root") == str(root) and context.get("actor") == actor
            and context.get("round_id") == round_id and context.get("head") == HEAD
            and read_published_json(root, Path(plan_ref["path"])) == plan
            and isinstance(plan.get("descriptors"), list)
            and {row["id"]: row for row in plan["descriptors"]} == descriptors,
            "Contexte/table quinze RPC canari différents du binding")
    for stage in parents:
        label = RPC_CANARY_PARENTS[stage]
        spec = commands[stage]
        require(isinstance(spec, dict)
                and spec.get("argv") == [str(RPC_CANARY_PYTHON), "-I", "-B", str(HERE / "rpc_canary_parent.py"),
                                         variant, stage, label, str(probe["tcp_port"]), str(probe["udp_port"])]
                and spec.get("role") == "stage-" + stage and spec.get("mode") == "sql"
                and spec.get("timeout_seconds") == STAGE_TIMEOUTS[stage]
                and spec.get("cwd") == str(root) and spec.get("combine_stderr") is False
                and spec.get("derived_deadline") == "start_monotonic_plus_exact_timeout"
                and isinstance(spec.get("env"), dict)
                and spec["env"].get("C17_RPC_CANARY_ONLY") == "1"
                and set(spec["env"]) <= RPC_CANARY_ENV_KEYS,
                "Parent RPC canari non fixture SQL exacte")
        envelope = validate_rpc_context_ref(root, spec["env"]["C17_RPC_CONTEXT_REF"],
                                            stage, actor, round_id)
        require(envelope["context"] == context
                and envelope["descriptor_plan_path"] == plan_ref["path"],
                "Enveloppe parent canari RPC non liée au plan/contexte root")
    for name, row in descriptors.items():
        require(isinstance(row, dict) and row.get("id") == row.get("stage_name") == name
                and row.get("requester_id") == RPC_CHILDREN[name][0]
                and row.get("timeout_seconds") == RPC_CHILDREN[name][1]
                and row.get("mode") == RPC_CHILDREN[name][2]
                and row.get("cwd") == str(root)
                and row.get("source_refs") == refs
                and row.get("environment", {}).get("C17_RPC_CANARY_ONLY") == "1"
                and set(row["environment"]) <= RPC_CANARY_ENV_KEYS
                and isinstance(commands[name], dict),
                "Descriptor RPC canari hors table/source fixture")
        fixture_kind = {"rpc-sql-b1753": "exit1", "rpc-sql-b1760": "exit2",
                        "rpc-sql-b1753-power": "timeout"}.get(name, "inert")
        expected_argv = ([str(NODE_ROOT / "bin/node"), str(HERE / "rpc_canary_node.mjs"), fixture_kind]
                         if name == "rpc-sql-b1760" else
                         [str(RPC_CANARY_PYTHON), "-I", "-B", str(HERE / "rpc_canary_child.py"), fixture_kind])
        require(row.get("argv") == expected_argv
                and (name in {"rpc-sql-b1753", "rpc-sql-b1760", "rpc-sql-b1753-power"}
                     or fixture_kind == "inert")
                and commands[name] == {"argv": expected_argv, "role": "stage-" + name,
                    "mode": row["mode"], "timeout_seconds": row["timeout_seconds"],
                    "env": row["environment"], "cwd": row["cwd"],
                    "stdout_path": row["stdout_path"], "stderr_path": row["stderr_path"],
                    "combine_stderr": False, "derived_deadline": "start_monotonic_plus_exact_timeout",
                    "logical_parent_id": row["logical_parent_id"]},
                "Commande enfant canari différente de fixture inert exacte")
    return decision, binding


WRAPPER_INSTRUMENTS = (
    "g1/runtime_session.py", "g1/runtime_launch_gate.py", "g1/runtime_bounds.py",
    "g1/relay_protocol.py", "g1/root_stage_relay.py", "g1/sql.sb", "g1/web.sb", "g1/chrome.sb", "g1/lsof_gate.py",
    "source/git_snapshot.py", "source/chrome_contract.py",
    "source/session_rpc_adapter.py", "source/rpc_protocol.py", "source/rpc_client.py",
    "source/rpc_dispatcher.py", "source/rpc_peer.py", "source/rpc_unix.py",
)


def load_wrapper_canary_admission(root: Path, *, actor: str, round_id: str, round_name: str,
                                  decision_ref: dict, binding_ref: dict) -> tuple[dict, dict]:
    """Scope réel des instruments, pas une admission A/B ni un GO auto-authentifié.

    La table est vide dans ce gel. Seul root, après autorisation outil réelle,
    peut préparer sa copie/admission exacte. Les JSON seuls n'authentifient pas
    leur auteur : l'origine externe et sa revue restent obligatoires.
    """
    require(not RUNTIME_ENABLED and not OS_STARTUP_QUALIFIED and not any(CAPABILITIES.values())
            and not ADMISSION_TABLE and bool(WRAPPER_ADMISSION_TABLE),
            "WRAPPER_CANARY fermé : slot root distinct absent ou portée FULL ouverte")
    require(root.parent == Path("/private/tmp") and root.resolve(strict=True) == root
            and not root.is_symlink() and WRAPPER_PATTERN.fullmatch(root.name)
            and round_name == "WRAPPER_CANARY" and round_id == root.name and actor == "/root",
            "Racine/acteur/ronde WRAPPER_CANARY non exacts")
    require(decision_ref.get("path") == str(root / "decision.json")
            and binding_ref.get("path") == str(root / "binding.json"),
            "Décision/binding wrappers hors paths QA exacts")
    decision = checked_json_ref(decision_ref, root)
    binding = checked_json_ref(binding_ref, root)
    slot = WRAPPER_ADMISSION_TABLE.get(decision.get("decision_id"))
    head = binding.get("head")
    source_text, python_text = binding.get("product_source_root"), binding.get("qa_python")
    require(isinstance(head, str) and re.fullmatch(r"[a-f0-9]{40}", head)
            and slot == {"decision_path": decision_ref["path"], "binding_path": binding_ref["path"],
                         "actor": actor, "round_id": round_id, "round_name": round_name,
                         "qa_root": str(root), "head": head,
                         "product_source_root": source_text, "qa_python": python_text},
            "Slot wrappers root/HEAD/paths différent")
    require(decision.get("schema") == "c17-g1-real-wrappers-canary-decision-v1"
            and decision.get("scope") == WRAPPER_SCOPE and decision.get("supplied_by") == "/root"
            and decision.get("decision_id") == round_id and decision.get("binding") == binding_ref
            and decision.get("root_tool_authorization_verified") is True,
            "GO wrappers instrument non exact ; JSON n'authentifie pas root")
    checked_json_ref(decision.get("root_authorization_origin"), root)
    require(binding.get("schema") == "c17-g1-real-wrappers-canary-binding-v1"
            and binding.get("decision_plan") == {"path": decision_ref["path"], "decision_id": round_id}
            and all(item.get(key) == value for item in (decision, binding) for key, value in {
                "actor": actor, "round_id": round_id, "round_name": round_name,
                "qa_root": str(root), "head": head}.items()), "Contexte wrappers différent")
    st = root.stat()
    require(st.st_uid == os.getuid() and binding.get("root_identity") == {
        "dev": st.st_dev, "ino": st.st_ino, "uid": st.st_uid, "birthtime": st.st_birthtime},
        "Racine wrappers réutilisée/changée")
    require(isinstance(source_text, str) and isinstance(python_text, str), "Chemins SOURCE/Python absents")
    product_source, qa_python = Path(source_text), Path(python_text)
    require(product_source.parent.parent == Path("/private/tmp") and product_source.name == "source"
            and re.fullmatch(r"therese-c17-wrapper-source-[A-Za-z0-9_-]{8,64}", product_source.parent.name)
            and product_source.resolve(strict=True) == product_source and product_source.is_dir()
            and not product_source.is_symlink() and HERE == root / "g1",
            "Checkout neuf/module wrappers hors QA exact")
    require(qa_python == product_source / ".venv-conforme/bin/python"
            and qa_python.resolve(strict=True) == RPC_CANARY_PYTHON,
            "Python QA hors SOURCE neuve/binaire physique exact")
    checkout_ref = binding.get("source_checkout_ref")
    checkout = checked_json_ref(checkout_ref, root)
    require(checkout.get("schema") == "c17-wrapper-canary-source-checkout-v1"
            and checkout.get("head") == head and checkout.get("product_source_root") == str(product_source)
            and checkout.get("git_head") == head and checkout.get("git_tree_verified") is True,
            "Checkout/HEAD frais non vérifié par root")
    git_head = product_source / ".git/HEAD"
    require(git_head.resolve(strict=True) == git_head and not git_head.is_symlink()
            and checkout.get("git_head_ref") == reference(git_head)
            and git_head.read_text().strip() == head,
            "HEAD Git physique/détaché ne correspond pas au contexte wrappers")
    manifest_ref = checkout.get("source_manifest_ref")
    manifest = checked_json_ref(manifest_ref, root)
    verify_wrapper_git(root, binding, product_source, manifest)
    require(manifest.get("head") == head and isinstance(manifest.get("files"), list)
            and bool(manifest["files"]), "Manifeste checkout sources vide/ancien")
    seen = set()
    for ref in manifest["files"]:
        require(isinstance(ref, dict) and set(ref) == {"path", "sha256", "bytes", "git_blob"},
                "Source checkout sans identité SHA/blob exacte")
        path = Path(ref["path"])
        require(path.is_absolute() and path.resolve(strict=True) == path
                and path.is_relative_to(product_source) and not path.is_symlink()
                and str(path) not in seen and re.fullmatch(r"[a-f0-9]{40}", ref["git_blob"]),
                "Manifeste checkout hors racine/doublon/blob")
        require(reference(path) == {key: ref[key] for key in ("path", "sha256", "bytes")},
                "Fichier checkout différent du manifeste courant")
        content = path.read_bytes()
        require(hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
                == ref["git_blob"], "Blob checkout ne correspond pas aux bytes exécutables")
        seen.add(str(path))
    refs = binding.get("source_refs")
    require(isinstance(refs, list) and len(refs) == len({ref.get("path") for ref in refs if isinstance(ref, dict)})
            and {str(root / rel) for rel in WRAPPER_INSTRUMENTS} <= {ref.get("path") for ref in refs}
            and decision.get("instruments") == refs, "Instruments wrappers manquants/doublons")
    for ref in refs:
        require(isinstance(ref, dict) and set(ref) == {"path", "sha256", "bytes"}, "Référence source incomplète")
        path = Path(ref["path"])
        require(path.resolve(strict=True) == path
                and (path.is_relative_to(root) or path.is_relative_to(product_source))
                and not path.is_symlink() and reference(path) == ref, "Source wrapper hors QA/SHA exacte")
    commands, descriptors = binding.get("commands"), binding.get("rpc_descriptors")
    require(isinstance(commands, dict) and isinstance(descriptors, dict)
            and set(commands) == set(RPC_CHILDREN) | WRAPPER_STAGES | set(AUXILIARY_NAMES.values())
            and set(descriptors) == set(RPC_CHILDREN), "Table wrappers 26 commandes/15 RPC non exacte")
    context_ref, plan_ref = binding.get("rpc_context_ref"), binding.get("rpc_plan_ref")
    require(isinstance(context_ref, dict) and isinstance(plan_ref, dict)
            and context_ref.get("path") == str(root / "session-rpc/context.json")
            and plan_ref.get("path") == str(root / "session-rpc/plan.json"), "Plan/contexte wrappers non préémis")
    context, plan = checked_json_ref(context_ref, root), checked_json_ref(plan_ref, root)
    require(context.get("root") == str(root) and context.get("actor") == actor
            and context.get("round_id") == round_id and context.get("head") == head
            and read_published_json(root, Path(plan_ref["path"])) == plan
            and isinstance(plan.get("descriptors"), list) and len(plan["descriptors"]) == 15
            and {row["id"]: row for row in plan["descriptors"]} == descriptors,
            "Plan/enveloppes wrappers différents du binding root")
    for name, (parent, bound, mode) in RPC_CHILDREN.items():
        row = descriptors[name]
        require(isinstance(row, dict) and row.get("id") == row.get("stage_name") == name
                and row.get("requester_id") == row.get("logical_parent_id") == parent
                and row.get("role") == "stage-" + name and row.get("mode") == mode
                and row.get("timeout_seconds") == bound,
                "Descriptor wrappers hors table immuable")
        require(commands[name] == {"argv": row["argv"], "role": row["role"], "mode": mode,
                "timeout_seconds": bound, "env": row["environment"], "cwd": row["cwd"],
                "stdout_path": row["stdout_path"], "stderr_path": row["stderr_path"],
                "combine_stderr": False, "derived_deadline": "start_monotonic_plus_exact_timeout",
                "logical_parent_id": parent}, "Commande RPC différente de son descriptor wrappers")
    validate_auxiliary_binding(root, binding, head, product_source)
    for name in WRAPPER_STAGES:
        spec = commands[name]
        service = name in ("backend", "vite")
        require(isinstance(spec, dict) and spec.get("role") == ("persistent-" if service else "stage-") + name
                and spec.get("mode") == ("web" if service or name == "calibrate" else "sql")
                and spec.get("timeout_seconds") == STAGE_TIMEOUTS[name]
                and spec.get("combine_stderr") is service
                and spec.get("derived_deadline") == "start_monotonic_plus_exact_timeout",
                "Service/parent wrappers hors table de bornes/rôles")
    for name in RPC_REQUESTERS:
        spec = commands[name]
        envelope = validate_rpc_context_ref(root, spec["env"].get("C17_RPC_CONTEXT_REF"),
                                            name, actor, round_id, expected_head=head)
        require(envelope["context"] == context and envelope["descriptor_plan_path"] == plan_ref["path"],
                "Helper wrappers sans enveloppe préémise root exacte")
    return decision, binding



def load_wrapper_helper(root: Path, binding: dict, name: str):
    require(name in ("git_snapshot.py", "chrome_contract.py"), "Helper auxiliaire hors noms exacts")
    path = root / "source" / name
    ref = reference(path)
    require(path.resolve(strict=True) == path and not path.is_symlink()
            and ref in binding["source_refs"], "Helper root non pinné/canonique")
    spec = importlib.util.spec_from_file_location("_c17_wrapper_" + name.removesuffix(".py"), path)
    require(spec is not None and spec.loader is not None, "Chargeur helper absent")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(reference(path) == ref, "Helper changé pendant import définition pure")
    return module


def verify_wrapper_git(root: Path, binding: dict, product_source: Path, manifest: dict) -> None:
    # Root remet une copie du snapshot/rawtree/commit sous QA ; aucune commande Git.
    module = load_wrapper_helper(root, binding, "git_snapshot.py")
    snapshot_ref = binding.get("git_snapshot_ref")
    require(isinstance(snapshot_ref, dict) and Path(snapshot_ref["path"]).is_relative_to(root),
            "Snapshot Git hors root préémis")
    snapshot = module.GitSnapshot(snapshot_ref, product_source)
    observed = snapshot.verify_worktree()  # tree reconstruit/commit/HEAD/blobs/modes réels, pas booléen seul.
    require(snapshot.recheck() == binding["head"] and manifest.get("head") == binding["head"]
            and isinstance(manifest.get("modes"), dict) and manifest.get("symlinks") == [],
            "Manifestes HEAD/modes/liens courant absents")
    files = manifest.get("files")
    require(isinstance(files, list) and len(files) == len(observed), "Source manifest incomplet ou en trop")
    expected = {str(product_source / relative): record for relative, record in observed.items()}
    require(set(manifest["modes"]) == set(expected), "Modes source manifest incomplets")
    for ref in files:
        record = expected.get(ref.get("path"))
        require(record is not None and ref["sha256"] == record["sha256"] and ref["git_blob"] == record["git_blob"]
                and manifest["modes"][ref["path"]] == record["mode"], "Manifest autre tree/blob/mode actuel")


def validate_auxiliary_binding(root: Path, binding: dict, head: str, product_source: Path) -> None:
    helper = load_wrapper_helper(root, binding, "chrome_contract.py")
    definition = helper.plan(root)
    rows = binding.get("auxiliary_descriptors")
    require(isinstance(rows, dict) and set(rows) == set(CHROME_JOBS), "Cinq descriptors Chrome absents/en trop")
    for job, row in rows.items():
        expected = definition["jobs"][job]
        require(isinstance(row, dict) and set(row) == set(expected), "Champs descriptor Chrome divergents")
        for key in expected.keys() - {"launch_defaults_ref", "argv", "env", "cwd", "deadline"}:
            require(row[key] == expected[key], "Descriptor Chrome autre nom/port/profil/options : " + key)
        defaults = checked_json_ref(row["launch_defaults_ref"], root)
        require(defaults.get("schema") == "c17-wrapper-chrome-launch-defaults-v1"
                and defaults.get("original_options") == row["original_options"]
                and defaults.get("argv") == row["argv"] and defaults.get("executable") == str(CHROME),
                "Arguments Chrome ne conservent pas options/defaults physiquement relus")
        require(isinstance(row["argv"], list) and row["argv"] and row["argv"][0] == str(CHROME)
                and "--user-data-dir=" + row["profile"] in row["argv"]
                and "--remote-debugging-port=17594" in row["argv"]
                and "--remote-debugging-address=127.0.0.1" in row["argv"]
                and "--no-sandbox" not in row["argv"] and "--remote-debugging-pipe" not in row["argv"]
                and not any(arg.startswith("--headless") for arg in row["argv"])
                and row["deadline"] == 50 and row["cwd"] in (str(root), str(product_source)),
                "Commande Chrome hors canal CDP/profil/borne originals")
        spec = binding["commands"][row["name"]]
        require(spec == {"argv": row["argv"], "role": row["role"], "mode": "chrome", "timeout_seconds": 50,
                "env": row["env"], "cwd": row["cwd"], "stdout_path": row["stdout"], "stderr_path": row["stderr"],
                "combine_stderr": False, "derived_deadline": "start_monotonic_plus_exact_timeout"},
                "Commande Chrome non égale au descriptor préémis")
        validate_environment(root, row["env"], "chrome", binding["actor"], binding["round_id"],
                              source_root=product_source, stage=row["name"])
    files_ref = binding.get("chrome_files_ref")
    manifest = checked_json_ref(files_ref, root)
    bundle = Path("/Applications/Google Chrome.app")
    require(manifest.get("schema") == "c17-wrapper-chrome-bundle-files-v1"
            and manifest.get("bundle_root") == str(bundle) and isinstance(manifest.get("files"), list)
            and len(manifest["files"]) >= 2, "Binaire/frameworks Chrome non physiquement pinnés")
    paths = set()
    for ref in manifest["files"]:
        path = Path(ref["path"])
        require(path.resolve(strict=True) == path and path.is_relative_to(bundle) and not path.is_symlink()
                and reference(path) == ref and str(path) not in paths, "Binaire/ressource Chrome changé/hors bundle")
        paths.add(str(path))
    require(str(CHROME) in paths and any(path.endswith("/Google Chrome Framework") for path in paths),
            "Binaire/framework physique Chrome requis")


def observe_auxiliary_port(ledger: DarwinLedger, handles: dict, job: str, *, qa_python: Path) -> dict:
    require(job in CHROME_JOBS, "Listener Chrome autre job")
    name = AUXILIARY_NAMES[job]
    handle = handles.get(name)
    require(handle is not None and handle["role"] == "auxiliary-" + name and handle["released"] is True
            and isinstance(handle.get("root_identity"), dict), "Chrome non lancé/admis réellement")
    root = handle["root_identity"]
    require(ledger.records.get(ledger.key(root)) == root, "Chrome birth hors ledger")
    ledger.attribute()
    first = listener_pids(AUXILIARY_PORT, ledger, qa_python=qa_python)
    ledger.attribute()
    second = listener_pids(AUXILIARY_PORT, ledger, qa_python=qa_python)
    require(first["pids"] == second["pids"], "CDP changé entre scans globaux")
    if not first["pids"]:
        return {"status": "absent", "port": AUXILIARY_PORT, "scans": [first, second], "observed_at": now()}
    require(len(first["pids"]) == 1, "CDP occupé par plusieurs PID")
    current = ledger.info(first["pids"][0])
    require(current is not None and current["status"] != 5, "CDP PID disparu/zombie")
    recorded = ledger.records.get(ledger.key(current))
    require(recorded is not None and ledger.unchanged(recorded, current), "CDP PID étranger/changé")
    root_live = ledger.info(root["pid"])
    require(ledger.unchanged(root, root_live) and root_live["status"] != 5, "Chrome root mort/changé")
    chain = service_chain(ledger, recorded, root, handle["role"])
    return {"status": "owned", "port": AUXILIARY_PORT, "pid": current["pid"], "identity": recorded,
            "root_identity": root, "chain": chain, "scans": [first, second], "owner": ledger.owner, "observed_at": now()}


def fetch_cdp_version() -> dict:
    # Aucun proxy/env hérité, cible exacte déjà attribuée par le parent.
    import urllib.request
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request("http://127.0.0.1:17594/json/version", method="GET")
    with opener.open(request, timeout=1) as response:
        require(response.status == 200, "CDP metadata HTTP non200")
        payload = response.read(100_001)
    require(len(payload) <= 100_000, "CDP metadata hors borne")
    result = json.loads(payload)
    require(isinstance(result, dict), "CDP metadata autre JSON")
    return result


def validate_wrapper_child_metadata(root: Path, env: dict, name: str, head: str, source_root: Path) -> None:
    if "C17_AUX_LOGS_RUN" in env:
        require(name == "rpc-all-logs" and env["C17_AUX_LOGS_RUN"] == str(root / "runtime/calibration/logs-rpc"),
                "Allocation logs metadata autre étape/path")
    if name == "rpc-all-logs":
        require(env.get("C17_AUX_LOGS_RUN") == str(root / "runtime/calibration/logs-rpc")
                and env.get("PYTHONPATH") == f"{root / 'auxiliary-ports/runtime'}:{source_root}:{source_root / 'src/backend'}",
                "Logs helper/source path exact absent")
    if "C17_AUX_CONTEXT_REF" in env or name in CHROME_JOBS:
        require(name in CHROME_JOBS and isinstance(env.get("C17_AUX_CONTEXT_REF"), str), "Chrome context metadata autre étape/absent")
        context = checked_json_ref(json.loads(env["C17_AUX_CONTEXT_REF"]), root)
        require(context.get("schema") == "c17-wrapper-auxiliary-context-v1" and context.get("scope") == "WRAPPER_CANARY"
                and context.get("root") == str(root) and context.get("stage") == name and context.get("head") == head,
                "Chrome context autre root/job/HEAD")
    if "C17_AUX_GIT_SNAPSHOT_REF" in env:
        snapshot = checked_json_ref(json.loads(env["C17_AUX_GIT_SNAPSHOT_REF"]), root)
        require(snapshot.get("schema") == "c17-wrapper-physical-git-snapshot-v1" and snapshot.get("head") == head,
                "Snapshot metadata Git autre HEAD/schéma")



def load_admission(root: Path, *, actor: str, round_id: str, round_name: str,
                   decision_ref: dict, binding_ref: dict) -> tuple[dict, dict]:
    if round_name == "WRAPPER_CANARY":
        return load_wrapper_canary_admission(root, actor=actor, round_id=round_id, round_name=round_name,
                                              decision_ref=decision_ref, binding_ref=binding_ref)
    if os.environ.get("C17_RPC_CANARY_ONLY") == "1":
        return load_rpc_canary_admission(root, actor=actor, round_id=round_id, round_name=round_name,
                                         decision_ref=decision_ref, binding_ref=binding_ref)
    if os.environ.get("C17_G1_CANARY_ONLY") == "1":
        return load_canary_admission(root, actor=actor, round_id=round_id, round_name=round_name,
                                     decision_ref=decision_ref, binding_ref=binding_ref)
    # Cette barrière précède allocation de journal, DarwinLedger et tout Popen.
    require(RUNTIME_ENABLED and OS_STARTUP_QUALIFIED and bool(ADMISSION_TABLE), "G1 preparation_only : admission/startup OS non qualifiés")
    require(root.parent == Path("/private/tmp") and root.resolve(strict=True) == root and not root.is_symlink(),
            "Racine de ronde non canonique")
    match = ROUND_PATTERN.fullmatch(root.name)
    require(match is not None and round_name in ("A", "B") and match[1] == round_name.lower(), "Root/ronde A-B différente")
    decision = checked_json_ref(decision_ref, DECISION_ROOT)
    slot = ADMISSION_TABLE.get(decision.get("decision_id"))
    require(isinstance(slot, dict) and slot == {
        "decision_path": decision_ref["path"], "binding_path": binding_ref["path"],
        "actor": actor, "round_id": round_id, "round_name": round_name, "qa_root": str(root)},
        "Décision sans slot exact actor/round/path/binding root")
    require(actor != "/root/cycle17_gate_review" and isinstance(round_id, str)
            and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{7,127}", round_id) is not None,
            "Auteur ne peut autoriser sa campagne / round_id invalide")
    require(decision.get("schema") == "c17-runtime78-session-root-go-v1"
            and decision.get("supplied_by") == "/root" and decision.get("scope") == "runtime78_exact_round"
            and decision.get("actor") == actor and decision.get("round_id") == round_id
            and decision.get("round_name") == round_name and decision.get("head") == HEAD
            and decision.get("qa_root") == str(root) and decision.get("binding") == binding_ref
            and decision.get("api_schema") == API_SCHEMA, "GO root hors exact acteur/ronde/HEAD/portée")
    require(decision.get("root_tool_authorization_verified") is True
            and decision.get("canaries_qualified") is True, "Autorité outil/canaris réels non vérifiés par root")
    # Ce booléen n'authentifie pas root : l'origine outil reste une obligation
    # externe de sa revue, liée à des références vraies (jamais créée ici).
    for field in ("root_authorization_origin", "identity_registry", "actor_origin", "canary_qualification"):
        checked_json_ref(decision[field], DECISION_ROOT)
    for name in ("runtime_session.py", "runtime_launch_gate.py", "web.sb", "sql.sb", "api-contract.json",
                 "root_stage_relay.py", "relay_protocol.py", "runtime_bounds.py"):
        require(decision.get("instruments", {}).get(name) == reference(HERE / name), "Instrument/profil/API non revu exact")
    binding = checked_json_ref(binding_ref, DECISION_ROOT)
    require(binding.get("schema") == "c17-runtime78-session-binding-v1"
            and all(binding.get(k) == v for k, v in {"actor": actor, "round_id": round_id,
                "round_name": round_name, "qa_root": str(root), "head": HEAD}.items()), "Binding acteur/round/root/HEAD non exact")
    st = root.stat()
    require(binding.get("root_identity") == {"dev": st.st_dev, "ino": st.st_ino,
            "uid": st.st_uid, "birthtime": st.st_birthtime} and st.st_uid == os.getuid(), "Root frais différent du binding")
    if round_name == "B":
        prior = checked_json_ref(decision["prior_A_shutdown"], DECISION_ROOT)
        require(prior.get("termination_proved") is True and prior.get("log_stability_proved") is True
                and prior.get("ports_absent") == [17593, 5173] and prior.get("actor") != actor,
                "B exige arrêt réel A et exécutant distinct")
    require(isinstance(binding.get("commands"), dict) and bool(binding.get("commands")), "Table commandes vide")
    require(isinstance(binding.get("source_refs"), list) and bool(binding["source_refs"]), "Snapshot source/instruments vide")
    return decision, binding


def validate_environment(root: Path, env: dict[str, str], mode: str, actor: str, round_id: str,
                         *, source_root: Path = SOURCE, stage: str | None = None) -> dict[str, str]:
    require(isinstance(env, dict) and REQUIRED_ENV <= env.keys()
            and set(env) <= ENV_CONSTANTS.keys() | ENV_PATHS | ENV_CONTEXT | ({"C17_AUX_GIT_SNAPSHOT_REF"} if WRAPPER_PATTERN.fullmatch(root.name) else set()), "Env manquant/hors allowlist (aucun héritage)")
    require(all(isinstance(k, str) and isinstance(v, str) and "\x00" not in k + v for k, v in env.items()), "Env invalide")
    for key, value in env.items():
        if key in ENV_CONSTANTS:
            expected = (str(root / "source") + ":" + str(root / "g1")
                        if key == "PYTHONPATH" and env.get("C17_RPC_CANARY_ONLY") == "1"
                        else str(source_root) + ":" + str(source_root / "src/backend")
                        if key == "PYTHONPATH" else ENV_CONSTANTS[key])
            require(value == expected, "Valeur env constante différente : " + key)
        elif key in ENV_PATHS:
            path = Path(value)
            require(path.is_absolute() and child_path(root, path) == path, "Env chemin non QA exact : " + key)
    require(env["HOME"] == env["CFFIXED_USER_HOME"], "HOME/CFHOME doivent même profil QA")
    if "THERESE_DATA_DIR" in env or "DATA_DIR" in env:
        require(env.get("THERESE_DATA_DIR") == env.get("DATA_DIR"), "Data dirs différentes")
    require("THERESE_DB_PLAINTEXT" not in env or mode in ("web", "chrome") and env["THERESE_DB_PLAINTEXT"] == "1",
            "SQL ne peut hériter mode plaintext")
    if "C16_ACTOR" in env:
        require(env["C16_ACTOR"] == actor and env.get("C16_ROUND_ID") == round_id, "Env acteur/round fictif")
    require("C16_ROUND_ID" not in env or env.get("C16_ACTOR") == actor and env["C16_ROUND_ID"] == round_id,
            "Env round sans acteur exact")
    require("C16_WIDTH" not in env or env["C16_WIDTH"] in ("800", "1440"), "Largeur hors définition")
    require("C16_REVIEWED_SHA256" not in env or re.fullmatch(r"[a-f0-9]{64}", env["C16_REVIEWED_SHA256"]) is not None,
            "SHA contexte invalide")
    require("C17_G1_CANARY_ONLY" not in env or env["C17_G1_CANARY_ONLY"] == "1"
            and os.environ.get("C17_G1_CANARY_ONLY") == "1", "Flag canari différent du parent")
    require("C17_RPC_CANARY_ONLY" not in env or env["C17_RPC_CANARY_ONLY"] == "1"
            and os.environ.get("C17_RPC_CANARY_ONLY") == "1"
            and root.name.startswith("therese-c17-rpc-canary-"),
            "Flag canari RPC différent du parent/racine")
    return dict(env)


def validate_rpc_environment(root: Path, env: dict[str, str], mode: str, name: str,
                             actor: str, round_id: str, *, expected_head: str = HEAD,
                             source_root: Path = SOURCE) -> dict[str, str]:
    """Validate the source-specific, *prebound* child environment.

    The root binding's byte-for-byte command equality remains mandatory in
    ``Session.start``.  This check closes the QA/profile boundary without
    forcing the older five scripts into the unrelated top-level env allowlist.
    No inherited ``C17_SESSION_*`` is accepted: G1 injects fresh child context.
    """
    require(name in RPC_CHILDREN and mode == RPC_CHILDREN[name][2]
            and isinstance(env, dict) and bool(env)
            and all(isinstance(k, str) and isinstance(v, str) and "\x00" not in k + v
                    for k, v in env.items()), "Environnement enfant RPC invalide")
    require(not any(key.startswith("C17_SESSION_") for key in env),
            "Contexte G1 parent transmis comme environnement enfant")
    if root.name.startswith("therese-c17-rpc-canary-"):
        require(env.get("C17_RPC_CANARY_ONLY") == "1"
                and os.environ.get("C17_RPC_CANARY_ONLY") == "1"
                and set(env) <= RPC_CANARY_ENV_KEYS
                and env.get("PYTHONPATH") == str(root / "source") + ":" + str(root / "g1"),
                "Environnement enfant canari RPC hors source QA")
    else:
        require("C17_RPC_CANARY_ONLY" not in env, "Flag canari RPC sur vraie ronde")
    if WRAPPER_PATTERN.fullmatch(root.name):
        validate_wrapper_child_metadata(root, env, name, expected_head, source_root)
    context_ref = env.get("C17_RPC_CONTEXT_REF")
    require((context_ref is not None) == (name in RPC_REQUESTERS),
            "Enveloppe RPC absente chez helper ou présente chez feuille")
    if context_ref is not None:
        validate_rpc_context_ref(root, context_ref, name, actor, round_id, expected_head=expected_head)
    for key in ("HOME", "TMPDIR", "THERESE_DATA_DIR"):
        path = Path(env.get(key, ""))
        require(path.is_absolute() and path.resolve() == path
                and (path == root or child_path(root, path) == path),
                "Profil enfant RPC hors racine QA : " + key)
    require(env.get("PATH") in (ENV_CONSTANTS["PATH"],
            ENV_CONSTANTS["PATH"] + ":/opt/homebrew/bin",
            "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin")
            and env.get("THERESE_SKIP_SERVICES") == "1"
            and env.get("PYTHON_KEYRING_BACKEND") == "keyring.backends.null.Keyring"
            and env.get("HF_HUB_OFFLINE") == "1"
            and env.get("TRANSFORMERS_OFFLINE") == "1"
            and env.get("OLLAMA_BASE_URL") == "http://127.0.0.1:9",
            "Environnement enfant RPC non isolé/offline")
    if "__CF_USER_TEXT_ENCODING" in env:
        require(env["__CF_USER_TEXT_ENCODING"] == ENV_CONSTANTS["__CF_USER_TEXT_ENCODING"],
                "Encodage utilisateur enfant RPC différent")
    if mode == "sql":
        require(env.get("THERESE_ENV") == "test" and env.get("THERESE_DB_KEY") == "ad" * 32
                and "THERESE_DB_PLAINTEXT" not in env
                and env.get("C16_ACTOR") == actor and env.get("C16_ROUND_ID") == round_id,
                "Profil SQL enfant RPC non exact")
    else:
        require(env.get("CFFIXED_USER_HOME") == env["HOME"]
                and env.get("PORT") == "17593" and env.get("HOST") == "127.0.0.1"
                and env.get("VITE_THERESE_BACKEND_PORT") == "17593"
                and env.get("THERESE_DB_PLAINTEXT") == "1",
                "Profil web enfant RPC non exact")
        defect = name in ("rpc-test-pytest-positive", "rpc-test-vitest-positive")
        require((env.get("C17_TEST_RUNNER_DEFECT") == "1") == defect
                and ("C17_TEST_RUNNER_DEFECT" not in env or defect),
                "Témoin test-runner RPC non exact")
        witness = {"rpc-screen-positive-visual": "visual",
                   "rpc-screen-positive-network": "network"}.get(name)
        require(env.get("C17_SCREEN_WITNESS") == witness,
                "Témoin écran RPC non exact")
    return dict(env)


def validate_rpc_context_ref(root: Path, ref_text: str, requester: str,
                             actor: str, round_id: str, *, expected_head: str = HEAD) -> dict:
    """Check a preissued envelope, never an invented requester PID or birth."""
    require(requester in RPC_REQUESTERS and isinstance(ref_text, str),
            "Demandeur/enveloppe RPC absent")
    try:
        envelope_ref = json.loads(ref_text)
        require(set(envelope_ref) == {"path", "sha256", "bytes"},
                "Référence enveloppe RPC non exacte")
        envelope_path = Path(envelope_ref["path"])
        require(envelope_path.is_absolute() and child_path(root, envelope_path) == envelope_path,
                "Enveloppe RPC hors QA")
        envelope = checked_json_ref(envelope_ref, root)
        enrollment_path = root / "session-rpc" / "enrollment" / (requester + ".json")
        plan_path = root / "session-rpc" / "plan.json"
        require(set(envelope) == {"schema", "context", "requester_id", "descriptor_plan_path", "enrollment_path"}
                and envelope["schema"] == "c17-g5-root-rpc-enrollment-context-v2"
                and envelope["requester_id"] == requester
                and envelope["enrollment_path"] == str(enrollment_path)
                and envelope["descriptor_plan_path"] == str(plan_path)
                and isinstance(envelope["context"], dict)
                and envelope["context"].get("root") == str(root)
                and envelope["context"].get("actor") == actor
                and envelope["context"].get("round_id") == round_id
                and envelope["context"].get("head") == expected_head
                and isinstance(read_published_json(root, plan_path), dict),
                "Contexte/plan/enrollment RPC non préémis exactement")
    except (OSError, ValueError, TypeError, KeyError, InstrumentError) as error:
        raise InstrumentError("Enveloppe RPC non vérifiable") from error
    return envelope


def sandbox(root: Path, mode: str, command: list[str], *, source_root: Path = SOURCE,
            qa_python: Path = PYTHON, chrome_context: dict | None = None) -> list[str]:
    require(mode in ("web", "sql", "chrome"), "Profil non admis")
    require(command and all(isinstance(x, str) and "\x00" not in x for x in command), "Argv invalide")
    rpc_canary = root.name.startswith("therese-c17-rpc-canary-")
    require(PYTHON_ROOT.resolve(strict=True) == PYTHON_ROOT and not PYTHON_ROOT.is_symlink()
            and RPC_CANARY_PYTHON.resolve(strict=True) == RPC_CANARY_PYTHON,
            "Racine/interpréteur Python physique différent")
    if not rpc_canary:
        require(PYTHON_ALIAS.resolve(strict=True) == PYTHON_ROOT
                and qa_python.resolve(strict=True) == RPC_CANARY_PYTHON,
                "Alias/venv Python historique différent")
    source_root = root if rpc_canary else source_root
    require(source_root.resolve(strict=True) == source_root and NODE_ROOT.resolve(strict=True) == NODE_ROOT,
            "Source ou racine Node non canonique")
    extra = []
    if mode == "chrome":
        require(isinstance(chrome_context, dict) and set(chrome_context) == {"AUXILIARY_ROOT", "HOME_ROOT", "TMP_ROOT"}, "Params Chrome manquants")
        for key, value in chrome_context.items():
            path = Path(value)
            require(path.resolve(strict=True) == path and child_path(root, path) == path, "Param Chrome hors QA exact")
            extra.extend(["-D", key + "=" + value])
    else:
        require(chrome_context is None, "Params Chrome sur profil ordinaire")
    return ["/usr/bin/sandbox-exec", *extra, "-D", "QA_ROOT=" + str(root),
            "-D", "SOURCE_ROOT=" + str(source_root), "-D", "PREPARATION_ROOT=" + str(HERE),
            "-D", "NODE_ROOT=" + str(NODE_ROOT), "-D", "PYTHON_ROOT=" + str(PYTHON_ROOT),
            "-f", str(HERE / (mode + ".sb")), *command]


def listener_pids(port: int, ledger: DarwinLedger, *, qa_python: Path = PYTHON) -> dict:
    """Lsof global après birth gate admise ; timeout nettoyé par ledger seul."""
    require(type(port) is int and port in (*PORTS, AUXILIARY_PORT), "Port hors QA")
    argv = ["/usr/sbin/lsof", "-nP", "-iTCP:" + str(port), "-sTCP:LISTEN", "-F", "p"]
    launch = [str(qa_python), "-I", "-B", str(HERE / "lsof_gate.py"), str(port)]
    started = time.monotonic()
    raw = {"port": port, "argv": argv, "launch": launch, "identity": None,
           "returncode": None, "stdout": "", "stderr": "", "cleanup": None}
    process = subprocess.Popen(launch, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, close_fds=True, start_new_session=True,
                               env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "C", "LC_ALL": "C"})
    try:
        raw["identity"] = ledger.admit_root(process.pid, "diagnostic-lsof")
    except BaseException as error:
        if process.stdin and not process.stdin.closed:
            process.stdin.close()  # gate non libéré, sort seul à EOF/5s ; aucun PID inconnu signalé.
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            raw["unattributed_gate_still_alive"] = process.pid
        raw["returncode"] = process.poll()
        raw["elapsed_seconds"] = time.monotonic() - started
        raise ListenerScanError("Birth du gate lsof non attribuée", raw) from error
    try:
        stdout, stderr = process.communicate(input=b"GO", timeout=2)
    except ControllerInterrupted as error:
        raw["interruption"] = str(error)
        try:
            raw["cleanup"] = ledger.cleanup({"diagnostic-lsof"}, [process])
        except BaseException as cleanup_error:
            raw["cleanup_error"] = {"type": type(cleanup_error).__name__, "message": str(cleanup_error)}
        raw["returncode"] = process.poll()
        raw["elapsed_seconds"] = time.monotonic() - started
        raise ListenerScanError("lsof interrompu ; cleanup birth exact requis, jamais absence", raw) from error
    except subprocess.TimeoutExpired as error:
        raw["stdout"] = (error.stdout or b"").decode("utf-8", "replace")
        raw["stderr"] = (error.stderr or b"").decode("utf-8", "replace")
        try:
            raw["cleanup"] = ledger.cleanup({"diagnostic-lsof"}, [process])
        except BaseException as cleanup_error:
            raw["cleanup_error"] = {"type": type(cleanup_error).__name__, "message": str(cleanup_error)}
        raw["returncode"] = process.poll()
        raw["elapsed_seconds"] = time.monotonic() - started
        raise ListenerScanError("lsof expiré ; cleanup birth exact requis, jamais absence", raw) from error
    raw["returncode"] = process.returncode
    raw["stdout"] = stdout.decode("utf-8", "strict")
    raw["stderr"] = stderr.decode("utf-8", "strict")
    raw["elapsed_seconds"] = time.monotonic() - started
    try:
        require(ledger.residuals({"diagnostic-lsof"}) == [], "Gate lsof encore vivant après communicate")
    except InstrumentError as error:
        raise ListenerScanError(str(error), raw) from error
    try:
        pids = parse_listener_output(process.returncode, raw["stdout"], raw["stderr"])
    except InstrumentError as error:
        raise ListenerScanError(str(error), raw) from error
    return raw | {"pids": pids, "observed_at": now()}


def parse_listener_output(returncode: int, stdout: str, stderr: str) -> list[int]:
    """Grammaire lsof -F p : process set p suivi de file set(s) f obligatoires."""
    require(type(returncode) is int and isinstance(stdout, str) and isinstance(stderr, str)
            and not stderr and returncode in (0, 1), "lsof erreur ou sortie non fiable")
    if returncode == 1:
        require(stdout == "", "lsof rc1 avec données")
        return []
    require(stdout.endswith("\n") and "\x00" not in stdout, "lsof -F p sans terminateur NL exact")
    lines = stdout[:-1].split("\n")
    require(2 <= len(lines) <= 64, "lsof -F p nombre de champs hors borne")
    pids: list[int] = []
    current_pid: int | None = None
    file_descriptors: set[int] = set()
    for line in lines:
        if re.fullmatch(r"p[1-9][0-9]*", line):
            require(current_pid is None or bool(file_descriptors),
                    "lsof process set sans file set")
            current_pid = int(line[1:])
            require(current_pid not in pids, "lsof PID process set dupliqué")
            pids.append(current_pid)
            file_descriptors = set()
        elif re.fullmatch(r"f(?:0|[1-9][0-9]*)", line):
            require(current_pid is not None, "lsof file set avant process set")
            fd = int(line[1:])
            require(fd not in file_descriptors, "lsof FD dupliqué dans process set")
            file_descriptors.add(fd)
        else:
            raise InstrumentError("lsof champ p/f inattendu ou mal formé")
    require(current_pid is not None and bool(file_descriptors), "lsof dernier process set sans file set")
    return sorted(pids)


def service_chain(ledger: DarwinLedger, listener: dict, root: dict, role: str) -> list[dict]:
    """Chaque birth a été admise par filiation vivante, jamais par PGID seul."""
    chain = []
    current = listener
    for _ in range(64):
        require(current["role"] == role and current["uid"] == root["uid"],
                "Rôle/UID du listener hors service")
        chain.append(current)
        if ledger.key(current) == ledger.key(root):
            require(current == root and current["attribution"] == "popen_child_before_workload",
                    "Racine service non canonique")
            return chain
        parent_key = tuple(current["parent_birth"])
        parent = ledger.records.get(parent_key)
        require(parent is not None and current["ppid"] == parent["pid"]
                and current["pgid"] in (parent["pgid"], current["pid"]),
                "Filiation/PGID du listener non prouvés")
        current = parent
    raise InstrumentError("Chaîne de filiation listener hors borne")


def observe_owned_port(ledger: DarwinLedger, handles: dict[str, dict], port: int,
                       *, qa_python: Path = PYTHON) -> dict:
    """Deux scans globaux et identité libproc canonique, sans signal ni cache."""
    require(type(port) is int and port in PORTS, "Port hors QA")
    name = {17593: "backend", 5173: "vite"}[port]
    handle = handles.get(name)
    require(isinstance(handle, dict) and handle.get("released") is True
            and handle.get("role") == "persistent-" + name
            and isinstance(handle.get("root_identity"), dict)
            and isinstance(handle.get("service_start_receipt"), dict),
            "Service canonique non lancé/admis")
    root = handle["root_identity"]
    require(ledger.records.get(ledger.key(root)) == root, "Birth racine service hors ledger")
    ledger.attribute()
    first = listener_pids(port, ledger, qa_python=qa_python)
    ledger.attribute()
    second = listener_pids(port, ledger, qa_python=qa_python)
    require(first["pids"] == second["pids"], "Listener changé entre deux scans globaux")
    if not first["pids"]:
        return {"status": "absent", "port": port, "scans": [first, second],
                "owner": ledger.owner, "observed_at": now()}
    require(len(first["pids"]) == 1, "Plusieurs PID listener globaux")
    pid = first["pids"][0]
    current = ledger.info(pid)
    require(current is not None and current["status"] != 5, "Listener disparu ou zombie")
    recorded = ledger.records.get(ledger.key(current))
    require(recorded is not None and ledger.unchanged(recorded, current),
            "Listener étranger, non attribué ou birth/UID/PGID changés")
    root_live = ledger.info(root["pid"])
    require(ledger.unchanged(root, root_live) and root_live["status"] != 5,
            "Racine service changée ou morte")
    chain = service_chain(ledger, recorded, root, handle["role"])
    return {"status": "owned", "port": port, "pid": pid, "identity": recorded,
            "root_identity": root, "chain": chain, "scans": [first, second],
            "owner": ledger.owner, "observed_at": now()}


def prove_ports_absent(ledger: DarwinLedger, *, qa_python: Path = PYTHON) -> dict:
    """Port libre GLOBAL + aucune birth service encore vivante ; pas de PID filtré."""
    ledger.attribute()
    first = [listener_pids(port, ledger, qa_python=qa_python) for port in (*PORTS, AUXILIARY_PORT)]
    ledger.attribute()
    second = [listener_pids(port, ledger, qa_python=qa_python) for port in (*PORTS, AUXILIARY_PORT)]
    require(all(a["pids"] == b["pids"] == [] for a, b in zip(first, second)),
            "Port QA encore occupé, instable ou inconnu")
    residuals = ledger.residuals(set(PERSISTENT | AUXILIARY_ROLES))
    require(not residuals and not ledger.ambiguous and not ledger.attribution_errors,
            "Birth service résiduelle ou attribution ambiguë")
    return {"schema": "c17-runtime78-ports-absence-v1", "ports_absent": list(PORTS), "auxiliary_ports_absent": [AUXILIARY_PORT],
            "ports_absence_proved": True, "scans": [first, second], "residuals": residuals,
            "ambiguities": list(ledger.ambiguous), "attribution_errors": list(ledger.attribution_errors),
            "owner": ledger.owner, "observed_at": now()}


def append_listener_journal(root: Path, journal: Path, value: dict) -> None:
    require(journal in (root / "ownership-traces.jsonl", root / "ownership-density.jsonl")
            and child_path(root, journal) == journal, "Journal listener hors QA exact")
    payload = (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode()
    require(len(payload) <= 100_000, "Entrée journal hors borne")
    fd = os.open(journal, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        st = os.fstat(fd)
        require(stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid() and st.st_nlink == 1
                and st.st_size <= 20_000_000, "Journal non régulier/owner/taille")
        require(os.write(fd, payload) == len(payload), "Écriture journal partielle")
        os.fsync(fd)
    finally:
        os.close(fd)



class Session:
    """Un seul parent vivant pour services et étapes ; pas d'API shell."""
    def __init__(self, root: Path, *, actor: str, round_id: str, round_name: str,
                 decision_ref: dict, binding_ref: dict) -> None:
        decision, binding = load_admission(root, actor=actor, round_id=round_id, round_name=round_name,
                                           decision_ref=decision_ref, binding_ref=binding_ref)
        self.root = root
        self.actor, self.round_id, self.round_name = actor, round_id, round_name
        self.decision_ref, self.binding_ref = dict(decision_ref), dict(binding_ref)
        self.decision, self.binding = decision, binding
        self.head = binding["head"]
        self.product_source_root = Path(binding["product_source_root"]) if round_name == "WRAPPER_CANARY" else SOURCE
        self.qa_python = Path(binding["qa_python"]) if round_name == "WRAPPER_CANARY" else PYTHON
        self.validate_sources()
        require(threading.current_thread() is threading.main_thread(), "Session G1 exige le thread principal pour SIGINT/SIGTERM")
        global _ACTIVE_SESSION
        require(_ACTIVE_SESSION is None, "Une autre Session G1 possède déjà les interruptions")
        self.ledger = DarwinLedger()
        ledger_root = child_path(root, root / "ledger")
        ledger_root.mkdir(mode=0o700, exist_ok=True)  # après admission, source et owner libproc.
        self.handles: dict[str, dict] = {}
        self.closed = False
        self.log_stability_tainted = False
        self.services_stopped = False
        self.service_stop_attempts = 0
        self.close_attempts = 0
        self.events_seen: set[str] = set()
        self.listener_observation_count = 0
        self.port_absence_count = 0
        self._relay_requests: list[dict] = []
        self._relay_deliveries: dict[str, dict] = {}
        self._stage_admissions: dict[str, dict] = {}
        self._root_review_cursor = 0
        self._rpc_dispatcher = None
        self.prelaunch_errors: list[dict] = []
        self._interruptions: list[dict] = []
        self._defer_interrupts = False
        self._handlers_restored = False
        self._previous_signal_handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
        try:
            for sig in self._previous_signal_handlers:
                signal.signal(sig, self._handle_interrupt)
        except BaseException:
            for sig, handler in self._previous_signal_handlers.items():
                signal.signal(sig, handler)
            raise
        _ACTIVE_SESSION = self

    def _handle_interrupt(self, signum, _frame) -> None:
        self._interruptions.append({"signal": signal.Signals(signum).name, "at": now()})
        self.log_stability_tainted = True
        if not self._defer_interrupts:
            raise ControllerInterrupted(signal.Signals(signum).name)

    def _raise_deferred_interrupt(self) -> None:
        if self._interruptions:
            raise ControllerInterrupted(self._interruptions[-1]["signal"])

    def _restore_interrupt_handlers_if_quiescent(self, cleanup: dict | None) -> bool:
        if cleanup is None or cleanup.get("remaining_attributed") != [] or not cleanup.get("clean"):
            return False
        if any(h["process"] is not None and h["process"].poll() is None for h in self.handles.values()):
            return False
        if self._handlers_restored:
            return True  # reçu final refusé auparavant : restauration déjà faite, retry sans faux échec.
        global _ACTIVE_SESSION
        if _ACTIVE_SESSION is not self:
            return False
        for sig, handler in self._previous_signal_handlers.items():
            signal.signal(sig, handler)
        _ACTIVE_SESSION = None
        self._handlers_restored = True
        return True

    def validate_sources(self) -> None:
        for ref in self.binding["source_refs"]:
            path = Path(ref["path"])
            require(path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink()
                    and any(path.is_relative_to(base) for base in (self.product_source_root, HERE, self.root)),
                    "Source hors QA/definition/import explicitement revus")
            if self.round_name == "RPC_CANARY":
                require(path.is_relative_to(self.root), "Source produit/hôte interdite au canari RPC")
            require(reference(path) == ref, "Source/instrument/lock changé : " + str(path))

    def verify_rpc_plan(self) -> dict:
        """Rehash root plan and its hardlink; a helper path grants no authority."""
        ref = self.binding.get("rpc_plan_ref")
        path = self.root / "session-rpc" / "plan.json"
        require(isinstance(ref, dict) and ref.get("path") == str(path)
                and reference(path) == ref, "Plan RPC root SHA absent/changé")
        plan = read_published_json(self.root, path)
        require(isinstance(plan.get("descriptors"), list)
                and {row["id"]: row for row in plan["descriptors"]}
                    == self.binding.get("rpc_descriptors"),
                "Plan RPC hardlink différent du binding root")
        if self._rpc_dispatcher is not None:
            require(plan["descriptors"] == self._rpc_dispatcher.descriptors,
                    "Plan RPC différent du dispatcher root")
        return plan

    def attach_rpc_dispatcher(self, dispatcher) -> None:
        """Install only the root-prebound, pinned dispatcher before a RPC parent.

        This is an integration seam, not evidence that the observer of a Unix
        peer or any nested capability has passed an OS calibration.
        """
        require(self._rpc_dispatcher is None and not self.handles and not self.closed
                and _ACTIVE_SESSION is self, "Dispatcher RPC tardif/étranger")
        require(getattr(dispatcher, "root", None) == self.root
                and getattr(getattr(dispatcher, "adapter", None), "session", None) is self
                and getattr(dispatcher.adapter, "context", None) == getattr(dispatcher, "context", None)
                and getattr(dispatcher.adapter, "enrollments", None) is getattr(dispatcher, "enrollments", None)
                and callable(getattr(dispatcher, "poll", None))
                and callable(getattr(dispatcher, "abort_parent", None))
                and callable(getattr(dispatcher, "parent_quiescent", None))
                and callable(getattr(dispatcher, "enroll_requester", None))
                and getattr(dispatcher, "auth_observer", None) is not None,
                "Dispatcher RPC sans Session/observateur séparé exact")
        module = sys.modules.get(type(dispatcher).__module__)
        path = Path(getattr(module, "__file__", ""))
        require(path.is_absolute() and path.resolve(strict=True) == path
                and path.is_relative_to(self.root) and reference(path) in self.binding["source_refs"],
                "Source dispatcher RPC non épinglée dans la ronde")
        adapter_module = sys.modules.get(type(dispatcher.adapter).__module__)
        adapter_path = Path(getattr(adapter_module, "__file__", ""))
        require(adapter_path.is_absolute() and adapter_path.resolve(strict=True) == adapter_path
                and adapter_path.is_relative_to(self.root)
                and reference(adapter_path) in self.binding["source_refs"],
                "Source adapter RPC non épinglée dans la ronde")
        protocol = getattr(dispatcher.adapter, "protocol", None)
        protocol_path = Path(getattr(protocol, "__file__", ""))
        require(protocol is not None and getattr(module, "p", None) is protocol
                and protocol_path.is_absolute() and protocol_path.resolve(strict=True) == protocol_path
                and protocol_path.is_relative_to(self.root)
                and reference(protocol_path) in self.binding["source_refs"],
                "Protocole RPC partagé non épinglé dans la ronde")
        descriptors = self.binding.get("rpc_descriptors")
        self.verify_rpc_plan()
        require(isinstance(descriptors, dict) and set(descriptors) == set(RPC_CHILDREN)
                and all(name in self.binding["commands"] for name in RPC_CHILDREN)
                and {row["id"]: row for row in dispatcher.descriptors} == descriptors,
                "Table des quinze enfants RPC non émise avant lancement")
        nonces = []
        for name, (parent, bound, mode) in RPC_CHILDREN.items():
            row = descriptors[name]
            protocol.validate_descriptor(row, dispatcher.context, self.root)
            require(isinstance(row, dict) and row.get("schema") == "c17-g5-root-rpc-descriptor-v1"
                    and row.get("id") == row.get("stage_name") == name
                    and row.get("requester_id") == row.get("logical_parent_id") == parent
                    and row.get("timeout_seconds") == bound and row.get("mode") == mode
                    and row.get("role") == "stage-" + name
                    and isinstance(row.get("nonce"), str)
                    and re.fullmatch(r"[a-f0-9]{32}", row["nonce"]) is not None,
                    "Ligne RPC root préliée incomplète")
            require(self.binding["commands"][name] == dispatcher.adapter._command_spec(row),
                    "Commande enfant RPC différente du descriptor fermé")
            nonces.append(row["nonce"])
        require(len(set(nonces)) == len(RPC_CHILDREN), "Nonce RPC réutilisé dans la table root")
        self.validate_sources()
        self._rpc_dispatcher = dispatcher

    def publish_rpc_enrollment(self, entry: dict, gate_ref: dict) -> dict:
        """Bind an actually admitted/live parent before the gate is released."""
        name = entry["name"]
        require(name in RPC_REQUESTERS and self._rpc_dispatcher is not None
                and entry["released"] is False and entry["root_identity"] is not None
                and entry["verified_before_release"] is not None,
                "Enrollment RPC hors gate parent encore fermé")
        envelope = validate_rpc_context_ref(self.root, entry["environment"]["C17_RPC_CONTEXT_REF"],
                                            name, self.actor, self.round_id, expected_head=self.head)
        dispatcher = self._rpc_dispatcher
        require(envelope["context"] == dispatcher.context,
                "Contexte RPC du helper différent du dispatcher root")
        plan = self.verify_rpc_plan()
        require(isinstance(plan.get("descriptors"), list)
                and plan["descriptors"] == dispatcher.descriptors
                and {row["id"]: row for row in plan["descriptors"]} == self.binding["rpc_descriptors"],
                "Plan des quinze RPC différent du binding root")
        self.ledger.attribute()
        identity = entry["root_identity"]
        current = self.ledger.info(identity["pid"])
        require(self.ledger.unchanged(identity, current) and current["status"] != 5
                and entry["process"].poll() is None,
                "Parent RPC mort/changé avant enrollment")
        path = Path(envelope["enrollment_path"])
        require(path.parent == self.root / "session-rpc" / "enrollment"
                and path.name == name + ".json" and path.parent.is_dir()
                and not path.exists(), "Destination enrollment RPC non exclusive")
        enrollment = {"schema": "c17-g5-root-rpc-enrollment-v1",
                      "publication_protocol": PUBLICATION_PROTOCOL,
                      "actor": self.actor, "round_id": self.round_id, "head": self.head,
                      "context_id": dispatcher.context["context_id"],
                      "requester_id": name, "logical_parent_id": name,
                      "parent_stage": name, "identity": {k: identity[k] for k in
                          ("pid", "start_sec", "start_usec", "ppid", "uid", "pgid")},
                      "gate_ref": gate_ref, "plan_ref": self.binding["rpc_plan_ref"],
                      "source_refs": list(self.binding["source_refs"]),
                      "parent_deadline_monotonic": entry["outer_deadline_monotonic"],
                      "enrollment_path": str(path)}
        publish_json(self.root, path, enrollment)
        require(read_published_json(self.root, path) == enrollment,
                "Enrollment RPC publié mais illisible")
        dispatcher.enroll_requester(enrollment)
        entry["rpc_enrollment_ref"] = reference(path)
        entry["rpc_enrollment_pending_ref"] = reference(path.with_name(path.name + ".pending"))
        return entry["rpc_enrollment_ref"]

    def start(self, name: str, role: str, command: list[str], *, mode: str, timeout: float,
              env: dict[str, str], cwd: Path, stdout_path: Path, stderr_path: Path | None,
              combine_stderr: bool = False, logical_parent_id: str | None = None,
              rpc_request_ref: dict | None = None,
              rpc_observed_requester: dict | None = None) -> dict:
        decision, binding = load_admission(self.root, actor=self.actor, round_id=self.round_id, round_name=self.round_name,
                                           decision_ref=self.decision_ref, binding_ref=self.binding_ref)
        require(decision == self.decision and binding == self.binding, "Admission mutable")
        require(not self.closed and not self._handlers_restored and self.close_attempts == 0
                and name not in self.handles and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", name),
                "Session/nom non admis")
        if self.round_name == "RPC_CANARY":
            variant = self.decision["canary_variant"]
            parents = {"B1753", "B1760"} if variant == "positive" else {"B1753-power"}
            children = {"rpc-" + RPC_CANARY_PARENTS[stage] for stage in parents}
            require(name in parents | children, "Canari RPC ne lance aucune autre commande des quinze lignes")
        elif self.round_name == "WRAPPER_CANARY":
            require(name in WRAPPER_STAGES | set(RPC_CHILDREN) | set(AUXILIARY_NAMES.values()), "Scope wrappers interdit aux autres 27 étapes")
        expected_role = ({"backend": "persistent-backend", "vite": "persistent-vite"} | {n: "auxiliary-" + n for n in AUXILIARY_NAMES.values()}).get(name, "stage-" + name)
        require(role == expected_role and (role not in PERSISTENT or not self.services_stopped), "Rôle non exact/réemploi services")
        require(all(h["role"] != role for h in self.handles.values()), "Rôle déjà attribué")
        require(name in STAGE_TIMEOUTS and STAGE_TIMEOUTS[name] is not None
                and timeout == STAGE_TIMEOUTS[name] and 0 < timeout <= 1500, "Borne manquante/différente de table exacte")
        require(mode in ("web", "sql", "chrome") and isinstance(combine_stderr, bool), "Mode/capture invalide")
        rpc_child = name in RPC_CHILDREN
        if rpc_child:
            parent_name, child_bound, child_mode = RPC_CHILDREN[name]
            self.verify_rpc_plan()
            require(logical_parent_id == parent_name and timeout == child_bound and mode == child_mode
                    and self._rpc_dispatcher is not None, "Enfant RPC hors table/parent/superviseur exact")
            parent = self.handles.get(parent_name)
            require(parent is not None and parent["role"].startswith("stage-")
                    and self._released_birth(parent) and parent["process"].poll() is None,
                    "Parent logique RPC non lancé/vivant")
            self.ledger.attribute()
            current_parent = self.ledger.info(parent["root_identity"]["pid"])
            require(self.ledger.unchanged(parent["root_identity"], current_parent)
                    and current_parent["status"] != 5,
                    "Birth parent logique RPC changée")
            fields = ("pid", "start_sec", "start_usec", "ppid", "uid", "pgid")
            require(isinstance(rpc_observed_requester, dict)
                    and all(rpc_observed_requester.get(key) == parent["root_identity"].get(key)
                            == current_parent.get(key) for key in fields),
                    "Demandeur observé hors payload absent/différent de la birth parent")
            require(isinstance(rpc_request_ref, dict) and isinstance(rpc_request_ref.get("path"), str),
                    "Requête RPC publiée absente")
            request_path = Path(rpc_request_ref["path"])
            require(request_path.is_relative_to(self.root / "session-rpc" / "request")
                    and reference(request_path) == rpc_request_ref,
                    "Requête RPC non canonique/SHA différent")
            read_published_json(self.root, request_path)
            descriptor = self.binding.get("rpc_descriptors", {}).get(name)
            require(isinstance(descriptor, dict) and descriptor.get("id") == name
                    and descriptor.get("stage_name") == name
                    and descriptor.get("requester_id") == parent_name
                    and descriptor.get("logical_parent_id") == parent_name
                    and descriptor.get("role") == role
                    and descriptor.get("timeout_seconds") == timeout
                    and descriptor.get("mode") == mode,
                    "Descriptor RPC root fermé absent/différent")
            require(request_path == self.root / "session-rpc" / "request" / (
                    name + "-" + str(descriptor.get("nonce")) + ".json"),
                    "Requête RPC hors emplacement nonce root préémis")
            require(name not in self._stage_admissions,
                    "Enfant RPC ne peut être admis par relais tardif implicite")
        else:
            require(logical_parent_id is None and rpc_request_ref is None
                    and rpc_observed_requester is None,
                    "Parent/requête RPC sur étape ordinaire")
        require(command and command[0] in (str(self.qa_python), str(NODE_ROOT / "bin/node"),
                    str(self.product_source_root / "src/frontend/node_modules/.bin/vite"))
                or self.round_name == "WRAPPER_CANARY" and name in AUXILIARY_NAMES.values()
                and command and command[0] == str(CHROME)
                or self.round_name == "RPC_CANARY" and command and command[0] == str(RPC_CANARY_PYTHON)
                or rpc_child and name in ("rpc-test-vitest-positive", "rpc-test-vitest-negative")
                and command and command[0] == str(self.product_source_root / "src/frontend/node_modules/.bin/vitest"),
                "Exécutable direct hors allowlist ; aucun shell")
        require(not any(x.endswith("runtime.py") for x in command) or command[-1] not in ("start", "stop"),
                "Ancien runtime.py start/stop interdit")
        if name in ("calibrate", "B1753", "B1753-power", "B1760"):
            require(self.round_name == "RPC_CANARY" and name in RPC_CANARY_PARENTS
                    or self.round_name == "WRAPPER_CANARY" and name in WRAPPER_PARENTS
                    or CAPABILITIES["nested_timeout_handshake"] and CAPABILITIES["nested_normal_completion_stable_fd"],
                    "Nested completion/timeout capabilities non implémentées/non admises")
        if name in RPC_REQUESTERS:
            require(self._rpc_dispatcher is not None,
                    "Étape lançant des enfants RPC sans dispatcher possédé")
            self.verify_rpc_plan()
        require(cwd.is_absolute() and cwd.resolve(strict=True) == cwd
                and any(cwd == base or cwd.is_relative_to(base) for base in (self.product_source_root, self.root)), "cwd non QA exact")
        require(stdout_path.is_absolute() and child_path(self.root, stdout_path) == stdout_path, "Stdout non QA canonique")
        if combine_stderr:
            require(name in ("backend", "vite") and stdout_path == self.root / "runtime" / (name + "-runtime.log")
                    and stderr_path in (None, stdout_path), "Seuls les deux services ont un vrai log combiné")
            stderr_path = stdout_path
        else:
            require(name not in ("backend", "vite") and isinstance(stderr_path, Path)
                    and stderr_path.is_absolute() and child_path(self.root, stderr_path) == stderr_path
                    and stderr_path != stdout_path, "Deux canaux exclusifs distincts obligatoires")
        environment = (validate_rpc_environment(self.root, env, mode, name, self.actor, self.round_id,
                                                expected_head=self.head, source_root=self.product_source_root)
                       if rpc_child else validate_environment(self.root, env, mode, self.actor, self.round_id,
                                                                source_root=self.product_source_root, stage=name))
        if not rpc_child:
            require((name in RPC_REQUESTERS) == ("C17_RPC_CONTEXT_REF" in environment),
                    "Enveloppe RPC absente du parent ou présente sur étape non RPC")
            if name in RPC_REQUESTERS:
                validate_rpc_context_ref(self.root, environment["C17_RPC_CONTEXT_REF"],
                                         name, self.actor, self.round_id, expected_head=self.head)
        if self.round_name == "WRAPPER_CANARY" and "C17_AUX_GIT_SNAPSHOT_REF" in environment:
            require(json.loads(environment["C17_AUX_GIT_SNAPSHOT_REF"]) == binding["git_snapshot_ref"], "Snapshot env autre root binding")
        actual = {"argv": command, "role": role, "mode": mode, "timeout_seconds": timeout, "env": environment,
                  "cwd": str(cwd), "stdout_path": str(stdout_path), "stderr_path": str(stderr_path),
                  "combine_stderr": combine_stderr, "derived_deadline": "start_monotonic_plus_exact_timeout"}
        if rpc_child:
            actual["logical_parent_id"] = logical_parent_id
        stage_record = self._stage_admissions.get(name)
        if stage_record is not None:
            root_stage_relay.guard(self, globals())
            for key in ("stage_binding", "stage_decision", "stage_origin", "registration"):
                root_stage_relay.exact_ref(self, globals(), stage_record[key])
            expected = stage_record["command"]
        else:
            expected = binding["commands"].get(name)
        require(expected == actual, "Commande/env/cwd/sinks non exactement revus")
        if rpc_child:
            require(descriptor["argv"] == command and descriptor["cwd"] == str(cwd)
                    and descriptor["environment"] == environment
                    and descriptor["stdout_path"] == str(stdout_path)
                    and descriptor["stderr_path"] == str(stderr_path)
                    and descriptor["role"] == role and descriptor["mode"] == mode,
                    "Descriptor RPC et commande root préliée différents")
        self.validate_sources()
        if self.round_name == "WRAPPER_CANARY" and name in CHROME_JOBS:
            self.start_auxiliary_for_job(name)  # Chrome gate/ownedCDP avant toute allocation/Popen Node.
        wrapped = sandbox(self.root, mode, command, source_root=self.product_source_root,
                          qa_python=self.qa_python, chrome_context=({"AUXILIARY_ROOT": str(self.root / "auxiliary" / name),
                            "HOME_ROOT": environment["HOME"], "TMP_ROOT": environment["TMPDIR"]} if mode == "chrome" else None))  # validation AVANT ouverture des FD.
        self._defer_interrupts = True  # avant mkdir/FD, jusqu'à l'enregistrement et la birth.
        out = None
        err = None
        try:
            folder = child_path(self.root, self.root / "ledger" / name)
            folder.mkdir(mode=0o700, parents=True, exist_ok=False)
            require(stdout_path.parent.is_dir() and stderr_path.parent.is_dir(), "Parents sinks manquants (pas fallback)")
            out = exclusive(stdout_path)
            err = out if combine_stderr else exclusive(stderr_path)
            started_monotonic = time.monotonic()
            environment |= {"QA_ROOT": str(self.root), "C17_RUNTIME_MODULE_DIR": str(HERE),
                            "C17_SESSION_ACTOR": self.actor, "C17_SESSION_ROUND_ID": self.round_id,
                            "C17_SESSION_HEAD": self.head, "C17_SESSION_STAGE": name,
                            "C17_SESSION_ROOT": str(self.root), "C17_SESSION_EVENTS": str(self.root / "session-events"),
                            "C17_SESSION_DECISION_ID": self.decision["decision_id"],
                            "C17_SESSION_BINDING_SHA256": self.binding_ref["sha256"],
                            "C17_SESSION_ROUND_NAME": self.round_name,
                            "C17_SESSION_DECISION_REF": json.dumps(self.decision_ref, sort_keys=True),
                            "C17_SESSION_BINDING_REF": json.dumps(self.binding_ref, sort_keys=True),
                            "C17_SESSION_OUTER_DEADLINE_MONOTONIC": str(started_monotonic + timeout)}
            gate_python = RPC_CANARY_PYTHON if self.round_name == "RPC_CANARY" else self.qa_python
            launch = [str(gate_python), "-I", "-B", str(HERE / "runtime_launch_gate.py"), str(folder / "gate.json"), *wrapped]
            entry = {"name": name, "role": role, "command": wrapped, "launch_command": launch,
                     "workload_command": command, "environment": environment, "cwd": str(cwd), "started_at": now(),
                     "timeout_seconds": timeout, "started_monotonic": started_monotonic,
                     "outer_deadline_monotonic": started_monotonic + timeout,
                     "deadline_scope": "startup_admission_only_not_service_lifetime" if role in AUXILIARY_ROLES
                                       else "stage_lifetime" if role.startswith("stage-") else "persistent_service_no_lifetime_claim",
                     "stdout_path": str(stdout_path), "stderr_path": str(stderr_path), "combine_stderr": combine_stderr,
                     "stdout_handle": out, "stderr_handle": err, "folder": folder, "process": None,
                     "root_identity": None, "released": False, "launch_attempted": False,
                     "launch_error": None, "interruption": None, "timed_out": False,
                     "output_archived": False, "termination_proved": False,
                     "terminal_receipt_ref": None, "receipt_paths": []}
            if rpc_child:
                entry["logical_parent_id"] = logical_parent_id
                entry["logical_parent_identity"] = dict(parent["root_identity"])
                entry["rpc_request_ref"] = dict(rpc_request_ref)
                entry["rpc_observed_requester"] = dict(rpc_observed_requester)
            self.handles[name] = entry  # avant Popen : même le défaut d'admission sera archivé.
            if stage_record is not None:
                entry.update({key: stage_record[key] for key in ("stage_binding", "stage_decision", "stage_origin")})
        except BaseException as error:
            close_errors = []
            for stream in (err, out):
                if stream is not None and not stream.closed:
                    try:
                        stream.close()
                    except OSError as close_error:
                        close_errors.append(str(close_error))
            self.prelaunch_errors.append({"stage": name, "phase": "allocate_or_register_before_popen",
                                          "type": type(error).__name__, "message": str(error),
                                          "stdout_path": str(stdout_path), "stderr_path": str(stderr_path),
                                          "close_errors": close_errors, "at": now()})
            self.log_stability_tainted = True
            self._defer_interrupts = False
            raise
        try:
            self._raise_deferred_interrupt()  # aucun Popen si SIGINT/SIGTERM est arrivé avant registration.
            entry["launch_attempted"] = True
            process = subprocess.Popen(launch, cwd=cwd, env=entry["environment"], stdin=subprocess.DEVNULL,
                                       stdout=out, stderr=err, close_fds=True, start_new_session=True)
            entry["process"] = process
            identity = self.ledger.admit_root(process.pid, role)
            entry["root_identity"] = identity
        except BaseException as error:
            entry["launch_error"] = {"type": type(error).__name__, "message": str(error)}
            self.log_stability_tainted = True
            raise
        finally:
            self._defer_interrupts = False
        self._raise_deferred_interrupt()
        deadline = time.monotonic() + min(timeout, 5)
        try:
            while True:
                self.ledger.attribute()
                current = self.ledger.info(process.pid)
                gate = folder / "gate.json"
                if gate.is_file() and current and current["status"] != 5:
                    require(self.ledger.unchanged(identity, current), "Birth barrière changé")
                    value = read_published_json(self.root, gate)
                    require(value["pid"] == identity["pid"] and value["ppid"] == os.getpid()
                            and value["uid"] == identity["uid"] and value["pgid"] == identity["pgid"]
                            and value["command"] == wrapped and value["qa_root"] == str(self.root)
                            and value["actor"] == self.actor and value["round_id"] == self.round_id
                            and value["head"] == self.head and value["stage"] == name
                            and value["decision_id"] == self.decision["decision_id"]
                            and value["binding_sha256"] == self.binding_ref["sha256"], "Barrière runtime non liée")
                    require(self.ledger.executable(process.pid) == str(gate_python.resolve(strict=True)),
                            "Exécutable de barrière non exact")
                    before_release = self.ledger.info(process.pid)
                    require(self.ledger.unchanged(identity, before_release) and before_release["ppid"] == os.getpid()
                            and before_release["pgid"] == process.pid, "Identité finale avant release différente")
                    entry["verified_before_release"] = before_release
                    release = gate.with_name(gate.name + ".release")
                    entry["gate_ref"] = reference(gate)
                    entry["gate_pending_ref"] = reference(gate.with_name(gate.name + ".pending"))
                    if name in RPC_REQUESTERS:
                        self.publish_rpc_enrollment(entry, entry["gate_ref"])
                    publish_json(self.root, release, {"publication_protocol": PUBLICATION_PROTOCOL,
                                                     "gate": value, "identity": identity})
                    entry["release_ref"] = reference(release)
                    entry["release_pending_ref"] = reference(release.with_name(release.name + ".pending"))
                    entry["released"] = True
                    entry["released_monotonic"] = time.monotonic()
                    if role in PERSISTENT or role in AUXILIARY_ROLES:
                        start_receipt = folder / "service-start.json"
                        save(self.root, start_receipt, {"schema": "c17-runtime78-owned-service-start-v1",
                            "actor": self.actor, "round_id": self.round_id, "head": self.head, "qa_root": str(self.root),
                            "stage_id": name, "argv": command, "cwd": str(cwd), "environment": environment,
                            "root_identity": identity, "owner": self.ledger.owner, "admission": self.decision_ref,
                            "binding": self.binding_ref, "gate": entry["gate_ref"], "release": entry["release_ref"],
                            "started_at": entry["started_at"], "admitted_at": now(),
                            "deadline_scope": entry["deadline_scope"], "timeout_seconds": timeout,
                            "stdout_path": str(stdout_path), "stderr_path": str(stderr_path),
                            "log_stability_proved": False, "service_readiness_proved": False})
                        entry["service_start_receipt"] = reference(start_receipt)
                    return entry
                require(process.poll() is None and time.monotonic() < deadline, "Barrière non confirmée")
                time.sleep(0.01)
        except BaseException as error:
            entry["interruption"] = {"type": type(error).__name__, "message": str(error)}
            self.log_stability_tainted = True
            raise

    def wait(self, entry: dict) -> dict:
        require(self.handles.get(entry["name"]) is entry and entry["role"].startswith("stage-")
                and entry["released"] and entry["name"] not in RPC_CHILDREN,
                "Étape non canonique/lancée ou enfant RPC : wait récursif interdit")
        rpc_parent = entry["name"] in RPC_REQUESTERS
        if rpc_parent:
            require(self._rpc_dispatcher is not None, "Dispatcher RPC absent pendant wait parent")
        try:
            while True:
                self.ledger.attribute()
                self._serve_listener_requests(entry)
                if rpc_parent:
                    self._rpc_dispatcher.poll()  # no Session.wait(child), no workload-blocking communicate.
                require(self.services_stopped or all(h["process"].poll() is None for h in self.handles.values()
                            if h["role"] in PERSISTENT), "Service persistant mort pendant l'étape")
                if entry["process"].poll() is not None:
                    break
                if not rpc_parent and self.consume_nested_timeout(entry):
                    entry["timed_out"] = True
                    self.log_stability_tainted = True
                    break
                if time.monotonic() >= entry["outer_deadline_monotonic"]:
                    entry["timed_out"] = True
                    self.log_stability_tainted = True
                    break
                time.sleep(0.01)
        except BaseException as error:
            entry["interruption"] = {"type": type(error).__name__, "message": str(error)}
            self.log_stability_tainted = True
            raise
        finally:
            if rpc_parent and not self._rpc_dispatcher.parent_quiescent(entry["name"]):
                self.log_stability_tainted = True
                self._rpc_dispatcher.abort_parent(entry["name"], "parent_exited_or_interrupted")
                cleanup_deadline = time.monotonic() + 8
                while (not self._rpc_dispatcher.parent_quiescent(entry["name"])
                       and time.monotonic() < cleanup_deadline):
                    self._rpc_dispatcher.poll()
                    time.sleep(0.01)
            if rpc_parent:
                require(self._rpc_dispatcher.parent_quiescent(entry["name"]),
                        "Descendant RPC encore actif/incertain : Session.stop doit nettoyer avant parent")
            self.finish({entry["role"]})
        if rpc_parent:
            require(self._rpc_dispatcher.parent_quiescent(entry["name"]),
                    "Enfants RPC encore actifs après parent")
        result = json.loads(Path(entry["receipt_paths"][-1]).read_text())
        require(result["termination_proved"] and result["output_archived"] and not result["output_archive_errors"]
                and result["cleanup"] is not None and result["cleanup"]["clean"],
                "Nettoyage étape non qualifié, fermeture session requise")
        require(not result["timed_out"] and result["interruption"] is None and not result["log_stability_tainted"],
                "Timeout/interruption/source/ambiguïté instrument : pas un rouge causal")
        return reference(Path(entry["receipt_paths"][-1]))

    def consume_nested_timeout(self, entry: dict) -> bool:
        """Définition de handshake fermé : marker ne peut attribuer un PID."""
        events = child_path(self.root, self.root / "session-events")
        if not events.is_dir():
            return False
        for path in sorted(events.glob("nested-timeout-" + entry["name"] + "-*.json")):
            if str(path) in self.events_seen:
                continue
            value = read_published_json(self.root, path)
            require(value.get("schema") == "c17-runtime78-nested-timeout-handshake-v1"
                    and value.get("actor") == self.actor and value.get("round_id") == self.round_id
                    and value.get("head") == self.head and value.get("stage") == entry["name"]
                    and value.get("capture_seconds") == 5 and value.get("cleanup_seconds") == 8,
                    "Marqueur nested hors contexte/borne exacte")
            require(self.decision.get("nested_timeout_handshake_admitted") is True,
                    "Handshake nested non admis par root")
            require(CAPABILITIES["nested_timeout_handshake"], "Cap nested timeout proposée mais fermée")
            request_time = value.get("request_monotonic")
            require(isinstance(request_time, (float, int)) and 0 < request_time <= time.monotonic()
                    <= request_time + 5, "Capture nested hors délai5s : aucun faux accusé")
            self.ledger.attribute()  # familles observées pendant parents vivants.
            pair = []
            for label in ("helper_identity", "child_identity"):
                declared = value[label]
                actual = self.ledger.records.get(self.ledger.key(declared))
                current = self.ledger.info(declared["pid"]) if actual is not None else None
                require(actual is not None and actual["role"] == entry["role"]
                        and all(declared.get(k) == actual.get(k) for k in ("pid", "start_sec", "start_usec", "ppid", "uid", "pgid"))
                        and self.ledger.unchanged(actual, current) and current["status"] != 5,
                        "Marker helper/child absent, mort ou non réellement attribué")
                pair.append(actual)
            require(pair[1]["parent_birth"] == list(self.ledger.key(pair[0])), "Child nested sans parent helper vivant exact")
            entry["nested_timeout"] = {"marker": reference(path), "captured_at": now(),
                                       "captured_monotonic": time.monotonic(),
                                       "captured_births": pair, "classification": "instrument_timeout_never_causal"}
            self.events_seen.add(str(path))
            return True
        return False

    def _released_birth(self, handle: dict) -> bool:
        row, process = handle["root_identity"], handle["process"]
        if process is None or not isinstance(row, dict) or handle["released"] is not True or not handle.get("release_ref"):
            return False
        try:
            return process.pid == row["pid"] and self.ledger.records.get(self.ledger.key(row)) == row
        except (KeyError, TypeError):
            return False

    def _launch_summary(self) -> dict:
        # Ces listes décrivent uniquement les handles enregistrés. Elles ne
        # prouvent ni couverture du plan, ni terminaison, ni ports absents.
        launched = []
        for name in ("backend", "vite"):
            handle = self.handles.get(name)
            if (handle is not None and handle.get("name") == name
                    and handle.get("role") == "persistent-" + name
                    and handle.get("launch_attempted") is True and self._released_birth(handle)
                    and isinstance(handle.get("service_start_receipt"), dict)):
                launched.append(name)
        unlaunched = [stage_name for stage_name, handle in sorted(self.handles.items())
                      if handle.get("name") != stage_name or handle.get("launch_attempted") is not True
                      or not self._released_birth(handle)]
        return {"launched_services": launched, "unlaunched_handles": unlaunched}

    def _execution_scope(self) -> str:
        require(self.round_name in ("CANARY", "LISTENER_CANARY", "RPC_CANARY", "WRAPPER_CANARY", "A", "B"), "Portée Session inconnue")
        if self.round_name in ("A", "B"):
            require(RUNTIME_ENABLED and OS_STARTUP_QUALIFIED and bool(ADMISSION_TABLE),
                    "Portée runtime A/B sans admission")
        else:
            require(not RUNTIME_ENABLED and not OS_STARTUP_QUALIFIED and not any(CAPABILITIES.values()),
                    "Portée canari incompatible avec portes runtime ouvertes")
        decision, binding = load_admission(self.root, actor=self.actor, round_id=self.round_id,
            round_name=self.round_name, decision_ref=self.decision_ref, binding_ref=self.binding_ref)
        require(decision == self.decision and binding == self.binding, "Portée admission initiale mutée")
        # Chaque scope exige son loader exact ; LISTENER_CANARY reste fermé.
        return {"CANARY": "g1_g5_joint_inert_canary_only",
                "LISTENER_CANARY": "inert_loopback_listener_session_canary_only",
                "RPC_CANARY": "g1_rpc_inert_sql_canary_only",
                "WRAPPER_CANARY": "g1_rpc_real_instrument_wrappers_canary_only",
                "A": "runtime78_exact_round", "B": "runtime78_exact_round"}[self.round_name]

    def _finish_owned_roles(self, roles: set[str]) -> dict:
        targets = [h for h in self.handles.values() if h["role"] in roles
                   and (not h["termination_proved"] or not h["output_archived"]
                        or h.get("terminal_receipt_ref") is None)]
        for h in targets:
            h["terminal_receipt_ref"] = None  # une preuve antérieure n'est pas le reçu de ce nouvel état.
        previous_defer = self._defer_interrupts
        self._defer_interrupts = True  # enregistrer tout signal, ne jamais l'ignorer pendant nettoyage.
        cleanup = None
        failure = None
        cleanup_started_monotonic = time.monotonic()
        try:
            cleanup = self.ledger.cleanup(roles, [h["process"] for h in targets if h["process"] is not None])
            self.validate_sources()  # refus/taint, sans empêcher les nettoyages déjà tentés.
            for h in targets:
                if h["root_identity"] is None and h["process"] is not None and not h["released"]:
                    # Barrière non admise : pas de nouveau signal. Son attente
                    # autonome est bornée à 5 s ; waitpid porte notre enfant,
                    # pas une cible déduite d'un PID/nom extérieur.
                    try:
                        h["process"].wait(timeout=6)
                    except subprocess.TimeoutExpired:
                        failure = {"type": "UnattributedBarrierStillAlive", "message": "auto-expiration non observée"}
        except BaseException as error:
            failure = {"type": type(error).__name__, "message": str(error)}
        finally:
            try:
                if (failure is not None or cleanup is None or cleanup.get("clean") is not True
                        or self.ledger.ambiguous or self.ledger.attribution_errors or self._interruptions):
                    self.log_stability_tainted = True  # une erreur antérieure ne disparaît pas au réessai.
                for h in targets:
                    archive_errors = []
                    if not h["output_archived"]:
                        for channel in ("stdout", "stderr"):
                            handle = h[channel + "_handle"]
                            if handle.closed:
                                continue
                            try:
                                handle.flush()
                                os.fsync(handle.fileno())
                            except OSError as error:
                                archive_errors.append({"channel": channel, "error": str(error)})
                            finally:
                                try:
                                    handle.close()
                                except OSError as error:
                                    archive_errors.append({"channel": channel, "close_error": str(error)})
                        h["output_archived"] = all(h[k + "_handle"].closed for k in ("stdout", "stderr"))
                    h.setdefault("output_archive_errors", []).extend(archive_errors)
                    if h["output_archive_errors"]:
                        self.log_stability_tainted = True
                    # Archivage ne signifie pas terminaison. En échec, garder
                    # une branche réessayable sans réécrire le premier reçu.
                    process = h["process"]
                    try:
                        own_live = self.ledger.residuals({h["role"]})
                    except BaseException as error:
                        own_live = [{"identity_read_error": str(error)}]
                        failure = failure or {"type": type(error).__name__, "message": str(error)}
                    h["termination_proved"] = (self._released_birth(h) and not own_live
                                                and process.poll() is not None)
                    if not self._released_birth(h) or h["launch_error"] or h["interruption"] or h["timed_out"]:
                        self.log_stability_tainted = True
                    if h.get("nested_timeout") and not h.get("nested_timeout_ack"):
                        elapsed = time.monotonic() - h["nested_timeout"]["captured_monotonic"]
                        h["nested_cleanup_elapsed_seconds"] = elapsed
                        h["nested_cleanup_deadline8_met"] = elapsed <= 8
                        self.log_stability_tainted = True  # timeout n'est jamais un rouge causal.
                try:
                    execution_scope = self._execution_scope()
                except BaseException as error:
                    execution_scope = "unverified_session_scope"
                    failure = failure or {"type": type(error).__name__, "message": str(error)}
                    self.log_stability_tainted = True
                cleanup_finished_monotonic = time.monotonic()
                cleanup_elapsed_seconds = cleanup_finished_monotonic - cleanup_started_monotonic
                cleanup_deadline_met = cleanup_elapsed_seconds <= 8
                cleanup_taint: list[str] = []
                if failure is not None:
                    cleanup_taint.append("cleanup_or_source_error")
                if cleanup is None or cleanup.get("clean") is not True:
                    cleanup_taint.append("cleanup_not_proved_clean")
                if self.ledger.ambiguous or self.ledger.attribution_errors:
                    cleanup_taint.append("identity_or_attribution_ambiguous")
                if self._interruptions or self.prelaunch_errors:
                    cleanup_taint.append("interruption_or_prelaunch_error")
                if not cleanup_deadline_met:
                    cleanup_taint.append("cleanup_deadline_8s_exceeded")
                for h in targets:
                    if h["output_archive_errors"] or not h["output_archived"]:
                        cleanup_taint.append(h["name"] + ":output_archive_incomplete")
                    if not self._released_birth(h) or not h["termination_proved"]:
                        cleanup_taint.append(h["name"] + ":released_birth_or_termination_unproved")
                    if h["launch_error"] or h["interruption"] or h["timed_out"]:
                        cleanup_taint.append(h["name"] + ":launch_interruption_or_timeout")
                if self.log_stability_tainted:
                    cleanup_taint.append("session_tainted_before_receipts")
                if cleanup_taint:
                    self.log_stability_tainted = True
                for h in targets:
                    h["cleanup_started_monotonic"] = cleanup_started_monotonic
                    h["cleanup_finished_monotonic"] = cleanup_finished_monotonic
                    h["cleanup_elapsed_seconds"] = cleanup_elapsed_seconds
                    h["cleanup_deadline_met"] = cleanup_deadline_met
                    h["cleanup_taint"] = list(cleanup_taint)
                # Tous les sinks, births, erreurs et taints sont figés avant le premier reçu.
                for h in targets:
                    try:
                        attempt = len(h["receipt_paths"]) + 1
                        receipt_path = h["folder"] / ("receipt.json" if attempt == 1 else "receipt-attempt-" + str(attempt) + ".json")
                        h["receipt_paths"].append(str(receipt_path))
                        raw = {k: v for k, v in h.items() if k not in
                               ("stdout_handle", "stderr_handle", "process", "folder", "released_monotonic",
                                "terminal_receipt_ref")}
                        completed = now()
                        raw |= {"finished_at": completed, "completed_at": completed,
                                "stage_id": h["name"], "argv": h["workload_command"],
                                "exit_code": h["process"].returncode if h["process"] else None,
                                "cleanup": cleanup, "cleanup_error": failure,
                                "schema": "c17-runtime78-owned-stage-receipt-v1",
                                "stdout": reference(Path(h["stdout_path"])), "stderr": reference(Path(h["stderr_path"])),
                                "attributed": list(self.ledger.records.values()), "owner": self.ledger.owner,
                                "execution_scope": execution_scope, "round_name": self.round_name,
                                "cycle": 17, "round_id": self.round_id,
                                "actor": self.actor, "head": self.head, "qa_root": str(self.root),
                                "admission": self.decision_ref, "binding": self.binding_ref,
                                "cleanup_attempt": attempt, "attribution_errors": list(self.ledger.attribution_errors),
                                "interruptions": list(self._interruptions),
                                "log_stability_tainted": self.log_stability_tainted,
                                "log_stability_proved": h["termination_proved"] and h["output_archived"]
                                    and not h["output_archive_errors"] and not self.log_stability_tainted
                                    and h["cleanup_deadline_met"] and not h["cleanup_taint"]
                                    and failure is None and cleanup is not None and cleanup.get("clean") is True}
                        raw["instrument_error"] = (failure or h["launch_error"] or h["interruption"]
                                                   or ({"type": "instrument_timeout"} if h["timed_out"] else None))
                        if raw["instrument_error"] is None and (cleanup is None or not cleanup["clean"] or self.log_stability_tainted):
                            raw["instrument_error"] = {"type": "instrument_guard_or_cleanup_taint"}
                        raw["raw_stable"] = raw["log_stability_proved"]
                        save(self.root, receipt_path, raw)
                        h["terminal_receipt_ref"] = reference(receipt_path)
                        if h.get("nested_timeout") and not h.get("nested_timeout_ack"):
                            cleanup_elapsed = h["nested_cleanup_elapsed_seconds"]
                            cleanup_deadline_met = h["nested_cleanup_deadline8_met"]
                            ack = Path(h["nested_timeout"]["marker"]["path"]).with_name(Path(h["nested_timeout"]["marker"]["path"]).name + ".cleanup-ack")
                            publish_json(self.root, ack, {"publication_protocol": PUBLICATION_PROTOCOL,
                                "schema": "c17-runtime78-nested-cleanup-ack-v1", "actor": self.actor, "round_id": self.round_id,
                                "head": self.head, "stage": h["name"], "marker": h["nested_timeout"]["marker"],
                                "captured_births": h["nested_timeout"]["captured_births"], "receipt": reference(receipt_path),
                                "termination_proved": h["termination_proved"], "cleanup": cleanup,
                                "cleanup_elapsed_seconds": cleanup_elapsed, "cleanup_deadline8_met": cleanup_deadline_met,
                                "helper_survival_or_read_claimed": False, "classified_as": "instrument_timeout_never_causal"})
                            h["nested_timeout_ack"] = reference(ack)
                    except BaseException:
                        h["terminal_receipt_ref"] = None
                        self.log_stability_tainted = True
                        raise
            finally:
                self._defer_interrupts = previous_defer
        return {"execution_scope": execution_scope, "round_name": self.round_name,
                "cleanup": cleanup, "cleanup_error": failure, "clean": failure is None and cleanup is not None
                and cleanup["clean"] and cleanup_deadline_met and not cleanup_taint
                and not self.log_stability_tainted
                and all(h["termination_proved"] and h["output_archived"]
                        and h["terminal_receipt_ref"] is not None
                        and not h["output_archive_errors"] for h in targets),
                "remaining_handles": [h["name"] for h in targets if not h["termination_proved"]],
                "log_stability_tainted": self.log_stability_tainted,
                "cleanup_elapsed_seconds": cleanup_elapsed_seconds,
                "cleanup_deadline_met": cleanup_deadline_met,
                "cleanup_taint": list(cleanup_taint),
                "interruptions": list(self._interruptions),
                "attribution_errors": list(self.ledger.attribution_errors)}

    def stop(self) -> dict:
        require(not self.closed, "Session déjà fermée")
        phase_started_monotonic = time.monotonic()
        previous_defer = self._defer_interrupts
        self._defer_interrupts = True
        try:
            result = self.finish({h["role"] for h in self.handles.values()
                                  if not h["termination_proved"] or not h["output_archived"]
                                  or h.get("terminal_receipt_ref") is None})
            result |= self._launch_summary()
            if self.round_name == "WRAPPER_CANARY":
                ports = self._record_ports_absence("session-stop")
                result |= {"ports_absent": ports["result"]["ports_absent"],
                           "auxiliary_ports_absent": ports["result"].get("auxiliary_ports_absent"),
                           "ports_absence_proved": ports["result"]["ports_absence_proved"],
                           "ports_absence_receipt": ports["receipt"],
                           "port_absence_elapsed_seconds": ports["result"]["port_absence_elapsed_seconds"],
                           "session_stop_pre_receipt_elapsed_seconds": time.monotonic() - phase_started_monotonic,
                           "cleanup_elapsed_scope": "finish_only_excludes_post_cleanup_port_scan_and_receipt_publication",
                           "phase_elapsed_scope": "finish_plus_port_scan_before_final_receipt_write"}
                result["clean"] = result["clean"] and ports["result"]["ports_absence_proved"]
            else:
                result |= {"ports_absent": None, "ports_absence_proved": False}
            result["log_stability_tainted"] = self.log_stability_tainted
            candidate_closed = bool(self.handles) and all(
                self._released_birth(h) and h["termination_proved"] and h["output_archived"]
                and h["terminal_receipt_ref"] is not None and not h["output_archive_errors"]
                for h in self.handles.values())
            if self.round_name == "WRAPPER_CANARY":
                candidate_closed = candidate_closed and result["ports_absence_proved"]
            self.close_attempts += 1
            pre_path = self.root / "ledger" / ("session-close-" + str(self.close_attempts) + ".pre-restore.json")
            pre = result | {"schema": "c17-runtime78-owned-session-close-pre-restore-v1",
                            "actor": self.actor, "round_id": self.round_id, "head": self.head,
                            "qa_root": str(self.root), "attempt": self.close_attempts,
                            "owned_processes_closed_candidate": candidate_closed,
                            "session_closed": False, "interrupt_handlers_restored": False,
                            "log_stability_proved": False, "interruptions": list(self._interruptions),
                            "prelaunch_errors": list(self.prelaunch_errors)}
            try:
                save(self.root, pre_path, pre)
                pre_ref = reference(pre_path)
            except BaseException:
                self.log_stability_tainted = True
                raise
            restore_error = None
            try:
                restored = self._restore_interrupt_handlers_if_quiescent(result["cleanup"])
            except BaseException as error:
                restored = False
                restore_error = {"type": type(error).__name__, "message": str(error)}
            if not restored:
                self.log_stability_tainted = True
            candidate_final_closed = candidate_closed and restored
            result |= {"schema": "c17-runtime78-owned-session-close-v1", "cycle": 17, "actor": self.actor,
                       "round_id": self.round_id, "head": self.head, "qa_root": str(self.root),
                       "admission": self.decision_ref, "binding": self.binding_ref, "call": "Session.stop",
                       "kind": "actual_in_process_owned_controller_phase", "actual_coordinator_argv": list(sys.argv),
                       "attempt": self.close_attempts,
                       "pre_restore_receipt": pre_ref, "interruptions": list(self._interruptions),
                       "prelaunch_errors": list(self.prelaunch_errors),
                       "interrupt_handlers_restored": restored, "interrupt_restore_error": restore_error,
                       "session_closed": candidate_final_closed,
                       "log_stability_proved": candidate_final_closed and not self.log_stability_tainted and result["clean"]}
            path = self.root / "ledger" / ("session-close-" + str(self.close_attempts) + ".json")
            try:
                save(self.root, path, result)
                receipt_ref = reference(path)
            except BaseException:
                self.log_stability_tainted = True
                raise
            self.closed = candidate_final_closed
            return receipt_ref
        finally:
            self._defer_interrupts = previous_defer

    def stop_services(self) -> dict:
        require(not self.closed and not self.services_stopped, "Services déjà arrêtés/session fermée")
        phase_started_monotonic = time.monotonic()
        result = self.finish(set(PERSISTENT))
        result |= self._launch_summary()
        if self.round_name == "WRAPPER_CANARY":
            ports = self._record_ports_absence("services-stop")
            result |= {"ports_absent": ports["result"]["ports_absent"],
                       "auxiliary_ports_absent": ports["result"].get("auxiliary_ports_absent"),
                       "ports_absence_proved": ports["result"]["ports_absence_proved"],
                       "ports_absence_receipt": ports["receipt"],
                       "port_absence_elapsed_seconds": ports["result"]["port_absence_elapsed_seconds"],
                       "service_stop_pre_receipt_elapsed_seconds": time.monotonic() - phase_started_monotonic,
                       "cleanup_elapsed_scope": "finish_only_excludes_post_cleanup_port_scan_and_receipt_publication",
                       "phase_elapsed_scope": "finish_plus_port_scan_before_final_receipt_write"}
            result["clean"] = result["clean"] and ports["result"]["ports_absence_proved"]
        else:
            result |= {"ports_absent": None, "ports_absence_proved": False}
        result["log_stability_tainted"] = self.log_stability_tainted
        started_roles = {h["role"] for h in self.handles.values() if h["role"] in PERSISTENT}
        candidate_services_stopped = started_roles == PERSISTENT and all(
            self._released_birth(h) and h.get("service_start_receipt") is not None
            and h["termination_proved"] and h["output_archived"] and h["terminal_receipt_ref"] is not None
            and not h["output_archive_errors"]
            for h in self.handles.values() if h["role"] in PERSISTENT)
        try:
            service_receipts = [reference(Path(h["receipt_paths"][-1])) for h in self.handles.values()
                                if h["role"] in PERSISTENT and h["receipt_paths"]]
        except BaseException:
            self.log_stability_tainted = True
            raise
        result |= {"schema": "c17-runtime78-owned-service-stop-v1", "cycle": 17,
                   "actor": self.actor, "round_id": self.round_id, "head": self.head, "qa_root": str(self.root),
                   "kind": "actual_in_process_owned_controller_phase", "actual_coordinator_argv": list(sys.argv),
                   "call": "Session.stop_services", "services_stopped": candidate_services_stopped,
                   "log_stability_proved": candidate_services_stopped and not self.log_stability_tainted and result["clean"],
                   "port_diagnostics_required_before_runtime78_qualification": True,
                   "admission": self.decision_ref, "binding": self.binding_ref,
                   "service_receipts": service_receipts}
        if self.round_name == "WRAPPER_CANARY":
            candidate_services_stopped = candidate_services_stopped and result["ports_absence_proved"]
            result["services_stopped"] = candidate_services_stopped
            result["log_stability_proved"] = candidate_services_stopped and not self.log_stability_tainted and result["clean"]
            result["port_diagnostics_required_before_runtime78_qualification"] = not result["ports_absence_proved"]
        self.service_stop_attempts += 1
        path = self.root / "ledger" / ("session-stop-services-" + str(self.service_stop_attempts) + ".json")
        try:
            save(self.root, path, result)
            receipt_ref = reference(path)
        except BaseException:
            self.log_stability_tainted = True
            raise
        self.services_stopped = candidate_services_stopped
        return receipt_ref

    def services_receipt(self) -> dict:
        execution_scope = self._execution_scope()
        self.ledger.attribute()
        result = {"schema": "c17-runtime78-owned-services-observation-v1", "actor": self.actor,
                  "execution_scope": execution_scope, "round_name": self.round_name,
                  "round_id": self.round_id, "head": self.head, "qa_root": str(self.root),
                  "admission": self.decision_ref, "binding": self.binding_ref,
                  "owner": self.parent_phase_identity(), "observed_at": now()}
        for name in ("backend", "vite"):
            h = self.handles.get(name)
            require(h is not None and h["released"] and h["role"] in PERSISTENT, "Service non lancé réellement")
            current = self.ledger.info(h["root_identity"]["pid"])
            require(self.ledger.unchanged(h["root_identity"], current) and current["status"] != 5,
                    "Service absent/changé : aucun manifeste running admis")
            result[name] = {"identity": h["root_identity"], "start_receipt": h["service_start_receipt"]}
        return result

    def parent_phase_identity(self) -> dict:
        current = self.ledger.info(self.ledger.owner["pid"])
        require(self.ledger.unchanged(self.ledger.owner, current)
                and current["ppid"] == self.ledger.owner["ppid"], "Parent coordinateur changé")
        return dict(current)

    def start_auxiliary_for_job(self, job: str) -> dict:
        require(self.round_name == "WRAPPER_CANARY" and job in CHROME_JOBS, "Auxiliaire hors cinq jobs WRAPPER")
        self._execution_scope()
        row = self.binding["auxiliary_descriptors"][job]
        name = row["name"]
        require(name not in self.handles and all(h.get("termination_proved") is True
                for n, h in self.handles.items() if n in AUXILIARY_NAMES.values()),
                "CDP partagé : Chrome précédent encore vivant/incertain")
        folder = self.root / "auxiliary" / name
        require(folder.resolve(strict=True) == folder and folder.is_dir()
                and Path(row["profile"]).resolve(strict=True) == Path(row["profile"])
                and Path(row["profile"]).is_dir(), "Profil/sinks auxiliaires non préparés canoniquement")
        spec = self.binding["commands"][name]
        handle = self.start(name, row["role"], list(spec["argv"]), mode="chrome", timeout=50,
            env=dict(spec["env"]), cwd=Path(spec["cwd"]), stdout_path=Path(spec["stdout_path"]),
            stderr_path=Path(spec["stderr_path"]), combine_stderr=False)
        handle["auxiliary_job"] = job
        handle["deadline_scope"] = "startup_admission_only_not_service_lifetime"
        expires = time.monotonic() + 5
        endpoint_observations = []
        try:
            while True:
                self.ledger.attribute()
                current = self.ledger.info(handle["root_identity"]["pid"])
                require(handle["process"].poll() is None and self.ledger.unchanged(handle["root_identity"], current)
                        and current["status"] != 5 and time.monotonic() < expires,
                        "Chrome absent/changé ou admission CDP hors délai5s")
                observed = observe_auxiliary_port(self.ledger, self.handles, job, qa_python=self.qa_python)
                if observed["status"] == "owned":
                    endpoint_observations.append(observed)
                    value = fetch_cdp_version()  # seulement après l'observation physique du port exact.
                    after = observe_auxiliary_port(self.ledger, self.handles, job, qa_python=self.qa_python)
                    require(after["status"] == "owned" and after["identity"] == observed["identity"]
                            and after["root_identity"] == observed["root_identity"] and time.monotonic() < expires,
                            "CDP changé ou lecture hors deadline")
                    endpoint_observations.append(after)
                    endpoint = value.get("webSocketDebuggerUrl")
                    require(isinstance(endpoint, str) and re.fullmatch(
                        r"ws://127\.0\.0\.1:17594/devtools/browser/[A-Za-z0-9-]{1,128}", endpoint),
                        "Endpoint CDP autre port/hôte/auth/chemin")
                    break
                time.sleep(0.01)
            startup_admitted = time.monotonic()
            require(startup_admitted <= handle["outer_deadline_monotonic"], "Chrome admission hors borne50s")
            start = {"schema": "c17-g1-auxiliary-start-v1", "scope": "WRAPPER_CANARY",
                "actor": self.actor, "round_id": self.round_id, "head": self.head, "stage": job,
                "name": name, "role": row["role"], "binding_sha256": self.binding_ref["sha256"],
                "decision_id": self.decision["decision_id"], "released": handle["released"],
                "root_identity": handle["root_identity"], "gate_ref": handle["gate_ref"],
                "release_ref": handle["release_ref"], "gated_command": handle["command"],
                "original_options": row["original_options"], "user_data_dir": row["profile"],
                "endpoint": endpoint, "endpoint_observations": endpoint_observations,
                "cdp_json_version": value, "stdout_path": handle["stdout_path"], "stderr_path": handle["stderr_path"],
                "startup_timeout_seconds": 50, "startup_deadline_scope": handle["deadline_scope"],
                "startup_deadline_met": startup_admitted <= handle["outer_deadline_monotonic"],
                "startup_admitted_monotonic": startup_admitted,
                "leaf_timeout_seconds": self.binding["commands"][job]["timeout_seconds"],
                "lifetime_absolute_50s_claimed": False,
                "admitted_at": now(), "log_stability_proved": False}
            path = Path(row["start_path"])
            save(self.root, path, start)
            handle["auxiliary_start_ref"] = reference(path)
            services = {}
            for service, port in (("backend", 17593), ("vite", 5173)):
                service_handle = self.handles.get(service)
                require(service_handle is not None and self._released_birth(service_handle)
                        and service_handle["process"].poll() is None, "Service web non lancé avant Chrome")
                current = self.ledger.info(service_handle["root_identity"]["pid"])
                require(self.ledger.unchanged(service_handle["root_identity"], current) and current["status"] != 5,
                        "Birth service web changée avant registre auxiliaire")
                services[service] = {"port": port, "birth_identity": service_handle["root_identity"]}
            services["chrome"] = {"port": AUXILIARY_PORT, "birth_identity": handle["root_identity"]}
            registry = {"schema": "c17-g1-auxiliary-services-v1", "publication_protocol": PUBLICATION_PROTOCOL,
                "scope": "WRAPPER_CANARY", "root": str(self.root), "stage": job, "actor": self.actor,
                "round_id": self.round_id, "head": self.head, "decision_id": self.decision["decision_id"],
                "binding_sha256": self.binding_ref["sha256"], "services": services,
                "chrome": {"name": name, "port": AUXILIARY_PORT, "profile": row["profile"],
                    "original_options": row["original_options"], "start_ref": handle["auxiliary_start_ref"],
                    "endpoint": endpoint}}
            publish_json(self.root, Path(row["services_path"]), registry)
            handle["auxiliary_services_ref"] = reference(Path(row["services_path"]))
            return handle
        except BaseException:
            self.log_stability_tainted = True
            # Start/ledger connus restent dans handles pour arrêt exact, sans signaux sur un PID inconnu.
            raise


    def close_auxiliary_for_job(self, job: str, leaf_receipt_ref: dict) -> dict:
        require(self.round_name == "WRAPPER_CANARY" and job in CHROME_JOBS, "Close auxiliaire hors scope")
        self._execution_scope()
        row = self.binding["auxiliary_descriptors"][job]
        handle = self.handles.get(row["name"])
        require(handle is not None and self._released_birth(handle), "Chrome sans vraie launch/birth/release")
        leaf = checked_json_ref(leaf_receipt_ref, self.root)
        require(leaf.get("stage_id") == job and leaf.get("root_identity") == self.handles[job]["root_identity"],
                "Leaf reçu d'un autre job/birth")
        result = self._finish_owned_roles({row["role"]})  # signaux Chrome dans ses propres bruts, pas ceux de la feuille.
        raw = checked_json_ref(handle["terminal_receipt_ref"], self.root)
        require(raw["termination_proved"] and raw["output_archived"] and not raw["output_archive_errors"]
                and raw["cleanup"] is not None and raw["cleanup"]["clean"]
                and raw["cleanup"]["remaining_attributed"] == []
                and raw["cleanup_deadline_met"] and type(raw["cleanup_elapsed_seconds"]) in (int, float)
                and 0 <= raw["cleanup_elapsed_seconds"] <= 8,
                "Chrome physique non terminé/archivé ou deadline8 dépassée")
        first = listener_pids(AUXILIARY_PORT, self.ledger, qa_python=self.qa_python)
        second = listener_pids(AUXILIARY_PORT, self.ledger, qa_python=self.qa_python)
        require(first["pids"] == second["pids"] == [] and not self.ledger.residuals({row["role"]}),
                "CDP pas globalement libre après arrêt Chrome")
        handle["auxiliary_close_attempt"] = handle.get("auxiliary_close_attempt", 0) + 1
        attempt = handle["auxiliary_close_attempt"]
        stop_path = Path(row["stop_path"]) if attempt == 1 else Path(row["stop_path"]).with_name("stop-attempt-" + str(attempt) + ".json")
        stop = {"schema": "c17-g1-auxiliary-stop-v1", "scope": "WRAPPER_CANARY", "stage": job,
            "name": row["name"], "role": row["role"], "actor": self.actor, "round_id": self.round_id,
            "head": self.head, "binding_sha256": self.binding_ref["sha256"], "root_identity": handle["root_identity"],
            "termination_proved": raw["termination_proved"], "output_archived": raw["output_archived"],
            "log_stability_proved": raw["log_stability_proved"], "raw_stable": raw["raw_stable"],
            "clean": raw["cleanup"]["clean"], "timed_out": raw["timed_out"], "taint": self.log_stability_tainted,
            "remaining_attributed": raw["cleanup"]["remaining_attributed"],
            "ambiguities": list(self.ledger.ambiguous), "errors": list(self.ledger.attribution_errors),
            "cleanup_elapsed_seconds": raw["cleanup_elapsed_seconds"], "cleanup_deadline_met": raw["cleanup_deadline_met"],
            "port_absent": AUXILIARY_PORT, "port_absence_scans": [first, second],
            "controller_signals_attributed": all(isinstance(event, dict)
                and isinstance(event.get("identity"), list) and len(event["identity"]) == 3
                and self.ledger.records.get(tuple(event["identity"])) is not None
                and all(event.get(key) == self.ledger.records[tuple(event["identity"])].get(key)
                        for key in ("uid", "pgid", "role"))
                and event.get("role") == row["role"] and event.get("signal") in ("SIGSTOP", "SIGTERM", "SIGCONT", "SIGKILL")
                for event in raw["cleanup"].get("signals", [])),
            "receipt_refs": [handle.get("auxiliary_start_ref"), handle["terminal_receipt_ref"], leaf_receipt_ref],
            "auxiliary_services_ref": handle.get("auxiliary_services_ref"), "leaf_exit_code": leaf["exit_code"]}
        require(all(isinstance(ref, dict) for ref in stop["receipt_refs"]), "Start/cleanup/leaf bruts auxiliaires incomplets")
        save(self.root, stop_path, stop)
        stop_ref = reference(stop_path)
        closure = {"schema": "c17-g1-rpc-auxiliary-closure-v1", "scope": "WRAPPER_CANARY", "job": job,
            "leaf_receipt_ref": leaf_receipt_ref, "start_ref": handle["auxiliary_start_ref"], "stop_ref": stop_ref,
            "actor": self.actor, "round_id": self.round_id, "head": self.head,
            "binding_sha256": self.binding_ref["sha256"], "root_identity": handle["root_identity"],
            "termination_proved": stop["termination_proved"], "output_archived": stop["output_archived"],
            "cleanup_clean": stop["clean"], "remaining_attributed": stop["remaining_attributed"],
            "ambiguities": stop["ambiguities"], "errors": stop["errors"], "cleanup_elapsed_seconds": stop["cleanup_elapsed_seconds"],
            "cleanup_deadline_met": stop["cleanup_deadline_met"], "log_stability_proved": stop["log_stability_proved"],
            "tainted": self.log_stability_tainted, "port_absent": AUXILIARY_PORT}
        closure_path = stop_path.with_name("closure.json" if attempt == 1 else "closure-attempt-" + str(attempt) + ".json")
        save(self.root, closure_path, closure)
        self.handles[job]["auxiliary_terminal_ref"] = reference(closure_path)
        return self.checked_auxiliary_terminal(job, leaf_receipt_ref)


    def checked_auxiliary_terminal(self, job: str, leaf_ref: dict) -> dict:
        require(job in CHROME_JOBS and self.round_name == "WRAPPER_CANARY", "Join auxiliaire hors scope")
        self._execution_scope()
        leaf_handle = self.handles[job]
        ref = leaf_handle.get("auxiliary_terminal_ref")
        closure = checked_json_ref(ref, self.root)
        leaf = checked_json_ref(leaf_ref, self.root)
        start = checked_json_ref(closure["start_ref"], self.root)
        stop = checked_json_ref(closure["stop_ref"], self.root)
        row = self.binding["auxiliary_descriptors"][job]
        aux_handle = self.handles[row["name"]]
        require(closure.get("schema") == "c17-g1-rpc-auxiliary-closure-v1" and closure.get("scope") == "WRAPPER_CANARY"
                and closure.get("job") == job and closure.get("leaf_receipt_ref") == leaf_ref
                and leaf_handle["terminal_receipt_ref"] == leaf_ref and leaf.get("stage_id") == job,
                "Join leaf/closure non causale")
        for raw in (start, stop, closure):
            require(all(raw.get(key) == value for key, value in {"actor": self.actor, "round_id": self.round_id,
                    "head": self.head, "binding_sha256": self.binding_ref["sha256"],
                    "root_identity": aux_handle["root_identity"]}.items()), "Join autre contexte/birth auxiliaire")
        require(start["name"] == stop["name"] == row["name"] and start["role"] == stop["role"] == row["role"]
                and start["released"] is True and closure["start_ref"] == aux_handle["auxiliary_start_ref"]
                and all(closure.get(key) is True for key in ("termination_proved", "output_archived", "cleanup_clean", "cleanup_deadline_met"))
                and closure["remaining_attributed"] == closure["ambiguities"] == closure["errors"] == []
                and type(closure["cleanup_elapsed_seconds"]) in (int, float) and 0 <= closure["cleanup_elapsed_seconds"] <= 8
                and closure["port_absent"] == AUXILIARY_PORT and stop["controller_signals_attributed"] is True,
                "Chrome non fermé/archivé/borné avant ACK")
        require(aux_handle["termination_proved"] and aux_handle["output_archived"]
                and not self.ledger.residuals({row["role"]}), "Handle auxiliaire non terminé effectivement")
        stable = leaf.get("raw_stable") is True and leaf.get("instrument_error") is None
        if stable:
            require(closure["log_stability_proved"] is True and closure["tainted"] is False
                    and stop["raw_stable"] is True and stop["taint"] is False,
                    "Auxiliaire rouge ne peut faire passer la feuille normale")
        else:
            require(closure["tainted"] is True and self.log_stability_tainted,
                    "Timeout/abort ne peut perdre son taint pendant fermeture physique")
        return {"reference": ref, "receipt": closure, "leaf_exit_code": leaf["exit_code"],
                "normal_success_claimed": stable, "OS_qualification_claimed": False}


    def finish(self, roles: set[str]) -> dict:
        # Même un stop global garde les signaux auxiliaires dans une phase distincte.
        auxiliary_roles = set(roles) & AUXILIARY_ROLES
        result = self._finish_owned_roles(set(roles) - auxiliary_roles)
        errors = []
        if self.round_name == "WRAPPER_CANARY":
            for job in CHROME_JOBS:
                if "stage-" + job in roles and job in self.handles:
                    leaf = self.handles[job]
                    try:
                        require(isinstance(leaf.get("terminal_receipt_ref"), dict), "Feuille sans reçu avant arrêt Chrome")
                        self.close_auxiliary_for_job(job, leaf["terminal_receipt_ref"])
                    except BaseException as error:
                        self.log_stability_tainted = True
                        errors.append({"job": job, "type": type(error).__name__, "message": str(error)})
        # Une branche ambiguë ne bloque pas le nettoyage borné des autres connus.
        fallback_roles = auxiliary_roles | {self.binding["auxiliary_descriptors"][item["job"]]["role"] for item in errors}
        remaining = {h["role"] for h in self.handles.values() if h["role"] in fallback_roles
                     and (not h["termination_proved"] or not h["output_archived"] or not h.get("terminal_receipt_ref"))}
        if remaining:
            self._finish_owned_roles(remaining)
        require(not errors, "Fermeture auxiliaire incomplète avant ACK : " + repr(errors))
        return result


    def await_root_review(self, phase: str, *, expected_refs: dict, timeout: float) -> dict:
        return root_stage_relay.await_root_review(self, globals(), phase, expected_refs=expected_refs, timeout=timeout)

    def await_stage_binding(self, name: str, *, expected_command: dict,
                            initial_binding_ref: dict, timeout: float) -> dict:
        return root_stage_relay.await_stage_binding(self, globals(), name,
            expected_command=expected_command, initial_binding_ref=initial_binding_ref, timeout=timeout)

    def admit_stage_binding(self, *, binding_ref: dict, decision_ref: dict, origin_ref: dict) -> None:
        root_stage_relay.admit_stage_binding(self, globals(), binding_ref=binding_ref,
            decision_ref=decision_ref, origin_ref=origin_ref)

    def _listener_scope_guard(self) -> None:
        # L'instrument nouveau possède un slot distinct ; jamais un cap FULL hérité.
        require(self.round_name == "WRAPPER_CANARY", "Listener intégré hors scope instrument distinct")
        self._execution_scope()  # relecture admission exacte avant tout diagnostic Popen.
        self.validate_sources()

    def _capture_listener(self, stage_id: str, port: int, journal: Path) -> dict:
        self._listener_scope_guard()
        self.listener_observation_count += 1
        path = self.root / "ledger" / ("listener-observation-" + str(self.listener_observation_count) + ".json")
        try:
            observed = (observe_auxiliary_port(self.ledger, self.handles, stage_id, qa_python=self.qa_python)
                if port == AUXILIARY_PORT else observe_owned_port(self.ledger, self.handles, port, qa_python=self.qa_python))
        except Exception as error:
            self.log_stability_tainted = True
            observed = {"status": "rejected", "port": port,
                        "error": {"type": type(error).__name__, "message": str(error),
                                  "raw_scan": error.raw if isinstance(error, ListenerScanError) else None}}
        raw = observed | {"schema": "c17-runtime78-owned-listener-observation-v1",
                          "actor": self.actor, "round_id": self.round_id, "head": self.head,
                          "stage": stage_id, "qa_root": str(self.root), "journal": str(journal),
                          "decision_id": self.decision["decision_id"],
                          "binding_sha256": self.binding_ref["sha256"]}
        try:
            append_listener_journal(self.root, journal, raw)
            save(self.root, path, raw)
            receipt = reference(path)
        except BaseException:
            self.log_stability_tainted = True
            raise
        if observed["status"] == "rejected":
            raise InstrumentError(observed["error"]["message"])
        return {"result": raw, "receipt": receipt}


    def observe_owned_listeners(self, stage_id: str, ports: list[int], journal: Path) -> dict:
        require(not self.closed and stage_id in STAGE_TIMEOUTS
                and isinstance(ports, list) and bool(ports) and len(ports) == len(set(ports))
                and all(type(port) is int and port in (*PORTS, AUXILIARY_PORT) for port in ports),
                "Demande listener hors stage/ports QA")
        observations = [self._capture_listener(stage_id, port, journal) for port in ports]
        if not all(item["result"]["status"] == "owned" for item in observations):
            self.log_stability_tainted = True
        require(all(item["result"]["status"] == "owned" for item in observations),
                "Listener QA absent : pas de readiness acquise")
        return {"schema": "c17-runtime78-owned-listeners-v1", "stage": stage_id,
                "observations": [item["receipt"] for item in observations]}


    def _serve_python_listener_requests(self, entry: dict) -> None:
        if self.round_name != "WRAPPER_CANARY" or entry["name"] not in ("start-runtime", "density", "listener-probe"):
            return  # les autres étapes sont contrôlées directement avant start.
        events = self.root / "session-events"
        require(events.resolve(strict=True) == events and events.is_dir(), "Dossier RPC changé")
        for path in sorted(events.glob("listener-request-" + entry["name"] + "-*.json")):
            if str(path) in self.events_seen:
                continue
            require(len(self.events_seen) < 512, "Nombre de requêtes RPC hors borne")
            request = read_published_json(self.root, path)
            port = request.get("port")
            name = {17593: "backend", 5173: "vite"}.get(port)
            service = self.handles.get(name) if name else None
            request_time = request.get("request_monotonic")
            require(request.get("schema") == "c17-runtime78-owned-listener-request-v1"
                    and request.get("actor") == self.actor and request.get("round_id") == self.round_id
                    and request.get("head") == self.head and request.get("qa_root") == str(self.root)
                    and request.get("stage") == entry["name"]
                    and request.get("decision_id") == self.decision["decision_id"]
                    and request.get("binding_sha256") == self.binding_ref["sha256"]
                    and request.get("deadline_seconds") == 5
                    and isinstance(request_time, (int, float)) and 0 < request_time <= time.monotonic()
                    <= request_time + 5
                    and service is not None and service.get("root_identity") == request.get("expected_root_identity")
                    and request.get("journal") in (str(self.root / "ownership-traces.jsonl"),
                                                    str(self.root / "ownership-density.jsonl")),
                    "RPC listener hors contexte, birth, fraîcheur ou port exact")
            current = self.ledger.info(entry["root_identity"]["pid"])
            require(self.ledger.unchanged(entry["root_identity"], current) and current["status"] != 5,
                    "Worker RPC sans birth vivante attribuée")
            observed = self._capture_listener(entry["name"], port, Path(request["journal"]))
            require(time.monotonic() <= request_time + 5, "Observation root listener hors délai5s")
            response_path = path.with_name(path.name + ".response")
            publish_json(self.root, response_path, {"publication_protocol": PUBLICATION_PROTOCOL,
                "schema": "c17-runtime78-owned-listener-response-v1", "actor": self.actor,
                "round_id": self.round_id, "head": self.head, "qa_root": str(self.root), "stage": entry["name"],
                "port": port, "request": reference(path), "observation": observed["receipt"],
                "status": observed["result"]["status"]})
            self.events_seen.add(str(path))

    def _serve_listener_requests(self, entry: dict) -> None:
        self._serve_python_listener_requests(entry)  # ABI Python historique inchangée, horloge Python seule.
        if self.round_name != "WRAPPER_CANARY":
            return  # les autres étapes sont contrôlées directement avant start.
        events = self.root / "session-events"
        require(events.resolve(strict=True) == events and events.is_dir(), "Dossier RPC changé")
        paths = []
        for job in CHROME_JOBS:
            if job in self.handles and self.handles[job].get("released") is True:
                paths.extend(events.glob("listener-request-" + job + "-*.json"))
        for path in sorted(paths):
            if str(path) in self.events_seen:
                continue
            require(len(self.events_seen) < 512, "Nombre de requêtes RPC hors borne")
            request = read_published_json(self.root, path)
            stage = request.get("stage")
            require(stage in CHROME_JOBS and re.fullmatch("listener-request-" + re.escape(stage) + r"-[0-9a-f]{32}\.json", path.name),
                    "Stage Node/request nonce path hors table")
            worker = self.handles.get(stage)
            require(worker is not None and worker.get("released") is True and worker["process"].poll() is None, "Worker Node non vivant/libéré")
            port = request.get("port")
            name = AUXILIARY_NAMES[stage] if port == AUXILIARY_PORT else {17593: "backend", 5173: "vite"}.get(port)
            service = self.handles.get(name) if name else None
            request_time = request.get("request_wall_time_unix")
            capture_started = time.monotonic()
            require(request.get("schema") == "c17-runtime78-owned-listener-node-request-v2"
                    and request.get("clock_domain") == "unix-wall-request+requester-local-hrtime-v1"
                    and type(request.get("requester_hrtime_seconds")) in (int, float)
                    and 0 < request["requester_hrtime_seconds"] < float("inf")
                    and request.get("actor") == self.actor and request.get("round_id") == self.round_id
                    and request.get("head") == self.head and request.get("qa_root") == str(self.root)
                    and request.get("stage") == stage
                    and request.get("decision_id") == self.decision["decision_id"]
                    and request.get("binding_sha256") == self.binding_ref["sha256"]
                    and request.get("deadline_seconds") == 5
                    and type(request_time) in (int, float) and 0 < request_time <= time.time()
                    <= request_time + 5
                    and service is not None and service.get("root_identity") == request.get("expected_root_identity")
                    and request.get("journal") in (str(self.root / "ownership-traces.jsonl"),
                                                    str(self.root / "ownership-density.jsonl")),
                    "RPC listener hors contexte, birth, fraîcheur ou port exact")
            current = self.ledger.info(worker["root_identity"]["pid"])
            require(self.ledger.unchanged(worker["root_identity"], current) and current["status"] != 5,
                    "Worker RPC sans birth vivante attribuée")
            observed = self._capture_listener(stage, port, Path(request["journal"]))
            require(time.monotonic() <= capture_started + 5 and request_time <= time.time() <= request_time + 5, "Observation Node/root hors fenêtres5s distinctes")
            response_path = path.with_name(path.name + ".response")
            publish_json(self.root, response_path, {"publication_protocol": PUBLICATION_PROTOCOL,
                "schema": "c17-runtime78-owned-listener-response-v1", "actor": self.actor,
                "round_id": self.round_id, "head": self.head, "qa_root": str(self.root), "stage": stage,
                "port": port, "request": reference(path), "observation": observed["receipt"],
                "status": observed["result"]["status"]})
            self.events_seen.add(str(path))


    def _record_ports_absence(self, phase: str) -> dict:
        self._listener_scope_guard()
        self.port_absence_count += 1
        path = self.root / "ledger" / ("ports-absence-" + str(self.port_absence_count) + ".json")
        scan_started_monotonic = time.monotonic()
        try:
            result = prove_ports_absent(self.ledger, qa_python=self.qa_python)
        except Exception as error:
            self.log_stability_tainted = True
            result = {"schema": "c17-runtime78-ports-absence-v1", "ports_absent": None,
                      "auxiliary_ports_absent": None,
                      "ports_absence_proved": False,
                      "error": {"type": type(error).__name__, "message": str(error),
                                "raw_scan": error.raw if isinstance(error, ListenerScanError) else None},
                      "observed_at": now()}
        result["port_absence_elapsed_seconds"] = time.monotonic() - scan_started_monotonic
        result |= {"actor": self.actor, "round_id": self.round_id, "head": self.head,
                   "qa_root": str(self.root), "phase": phase}
        try:
            save(self.root, path, result)
            ref = reference(path)
        except BaseException:
            self.log_stability_tainted = True
            raise
        return {"result": result, "receipt": ref}



def request_owned_listener_observation(root: Path, stack: dict, port: int, journal: Path,
                                       *, stage_id: str, deadline: int) -> dict:
    """Worker : demande au parent vivant ; aucun lsof/libproc ni repli local."""
    head = os.environ.get("C17_SESSION_HEAD")
    require(type(port) is int and port in PORTS and deadline == 5
            and stage_id == os.environ.get("C17_SESSION_STAGE")
            and str(root) == os.environ.get("C17_SESSION_ROOT")
            and str(root / "session-events") == os.environ.get("C17_SESSION_EVENTS")
            and isinstance(head, str) and re.fullmatch(r"[a-f0-9]{40}", head) is not None
            and os.environ.get("C17_SESSION_ROUND_NAME") == "WRAPPER_CANARY"
            and journal in (root / "ownership-traces.jsonl", root / "ownership-density.jsonl")
            and root.resolve(strict=True) == root, "Worker RPC hors contexte QA exact")
    decision, binding = load_admission(root, actor=os.environ.get("C17_SESSION_ACTOR"),
        round_id=os.environ.get("C17_SESSION_ROUND_ID"), round_name="WRAPPER_CANARY",
        decision_ref=json.loads(os.environ["C17_SESSION_DECISION_REF"]),
        binding_ref=json.loads(os.environ["C17_SESSION_BINDING_REF"]))
    require(head == decision["head"] == binding["head"], "Worker listener HEAD non lié au binding admis")
    name = {17593: "backend", 5173: "vite"}[port]
    expected = stack.get(name, {}).get("birth_identity")
    require(isinstance(expected, dict) and expected.get("pid") == stack.get(name, {}).get("pid"),
            "Worker sans birth service attendue")
    actor = os.environ.get("C17_SESSION_ACTOR")
    round_id = os.environ.get("C17_SESSION_ROUND_ID")
    decision_id = os.environ.get("C17_SESSION_DECISION_ID")
    binding_sha256 = os.environ.get("C17_SESSION_BINDING_SHA256")
    require(all(isinstance(x, str) and x for x in (actor, round_id, decision_id, binding_sha256)),
            "Worker sans identité de session")
    events = root / "session-events"
    require(events.resolve(strict=True) == events and events.is_dir(), "Canal RPC absent/changé")
    path = events / ("listener-request-" + stage_id + "-" + uuid.uuid4().hex + ".json")
    publish_json(root, path, {"publication_protocol": PUBLICATION_PROTOCOL,
        "schema": "c17-runtime78-owned-listener-request-v1", "actor": actor,
        "round_id": round_id, "head": head, "qa_root": str(root), "stage": stage_id,
        "decision_id": decision_id, "binding_sha256": binding_sha256,
        "port": port, "expected_root_identity": expected, "journal": str(journal),
        "deadline_seconds": deadline, "request_monotonic": time.monotonic()})
    request_ref = reference(path)
    response_path = path.with_name(path.name + ".response")
    expires = time.monotonic() + deadline
    while time.monotonic() < expires:
        if response_path.is_file():
            response = read_published_json(root, response_path)
            require(response.get("schema") == "c17-runtime78-owned-listener-response-v1"
                    and response.get("actor") == actor and response.get("round_id") == round_id
                    and response.get("head") == head and response.get("qa_root") == str(root)
                    and response.get("stage") == stage_id and response.get("port") == port
                    and response.get("request") == request_ref,
                    "Réponse RPC non liée à la demande exacte")
            observation_ref = response.get("observation")
            observation = checked_json_ref(observation_ref, root)
            require(observation.get("schema") == "c17-runtime78-owned-listener-observation-v1"
                    and observation.get("actor") == actor and observation.get("round_id") == round_id
                    and observation.get("head") == head and observation.get("qa_root") == str(root)
                    and observation.get("stage") == stage_id and observation.get("port") == port
                    and observation.get("journal") == str(journal)
                    and response.get("status") == observation.get("status"),
                    "Observation RPC différente de son reçu")
            require(time.monotonic() < expires, "Observation listener lue après délai5s")
            if observation["status"] == "absent":
                raise ListenerNotReady("Listener QA pas encore prêt ; nouvelle demande fraîche requise")
            require(observation["status"] == "owned" and observation.get("root_identity") == expected
                    and observation.get("pid") == observation.get("identity", {}).get("pid")
                    and all(scan.get("pids") == [observation["pid"]] for scan in observation.get("scans", []))
                    and len(observation.get("scans", [])) == 2,
                    "Réponse RPC sans listener global et birth attendue")
            return {"response": reference(response_path), "observation": observation_ref}
        time.sleep(0.01)
    raise InstrumentError("Parent RPC listener absent au délai5s ; aucune requête autonome")



def plan() -> dict:
    return {"schema": API_SCHEMA, "status": "preparation_only", "runtime_enabled": RUNTIME_ENABLED,
            "admission_slots": len(ADMISSION_TABLE), "head": HEAD, "round_id": None,
            "author": "/root/cycle17_gate_review", "runtime_execution_closed": True,
            "owned_listener_rpc_implemented": True, "ports_absence_proof_implemented": True,
            "wrapper_admission_slots": len(WRAPPER_ADMISSION_TABLE),
            "wrapper_scope": WRAPPER_SCOPE, "wrapper_scope_closed": not WRAPPER_ADMISSION_TABLE,
            "wrapper_commands": 26, "wrapper_rpc_children": 15, "wrapper_chrome_services": 5,
            "chrome_startup_timeout_seconds": 50, "chrome_lifetime_absolute_50s_claimed": False,
            "node_listener_clock_domain": "unix-wall-request+requester-local-hrtime-v1",
            "auxiliary_closure_before_RPC_ACK_implemented": True,
            "new_os_qualification": False,
            "limitations": ["lsof diagnostic PIPE", "cooperative polling not hard realtime",
                            "Git/Chrome indirect descendants not yet qualified", "no FULL admission"]}


if __name__ == "__main__":
    print(json.dumps({"status": "runtime_execution_closed", "api_schema": API_SCHEMA}))
    raise SystemExit(2)
