"""Barrière avant workload ; aucune source produit ni ancien résultat."""
import json
import os
from pathlib import Path
import re
import stat
import sys
import time

root = Path(os.environ["QA_ROOT"])
preparation = Path(os.environ["C17_RUNTIME_MODULE_DIR"])
assert root.resolve(strict=True) == root and root.parent == Path("/private/tmp") and not root.is_symlink()
if os.environ.get("C17_G1_CANARY_ONLY") == "1":
    assert re.fullmatch(r"therese-c17-g1-canary-(positive|timeout)-[a-z0-9_]{8,64}", root.name)
elif os.environ.get("C17_RPC_CANARY_ONLY") == "1":
    assert re.fullmatch(r"therese-c17-rpc-canary-(positive|timeout)-[a-z0-9_]{8,64}", root.name)
elif os.environ.get("C17_SESSION_ROUND_NAME") == "WRAPPER_CANARY":
    assert re.fullmatch(r"therese-c17-wrapper-canary-[a-z0-9_]{8,64}", root.name)
else:
    assert re.fullmatch(r"therese-c17-direct-round-[ab]-[a-z0-9-]{8,64}", root.name)
assert preparation.resolve(strict=True) == preparation == Path(__file__).resolve().parent
sys.path.insert(0, str(preparation))
from runtime_session import load_admission
actor, round_id = os.environ["C17_SESSION_ACTOR"], os.environ["C17_SESSION_ROUND_ID"]
head, stage = os.environ["C17_SESSION_HEAD"], os.environ["C17_SESSION_STAGE"]
decision_id, binding_sha = os.environ["C17_SESSION_DECISION_ID"], os.environ["C17_SESSION_BINDING_SHA256"]
assert re.fullmatch(r"[a-f0-9]{40}", head) and actor != "/root/cycle17_gate_review"
if os.environ["C17_SESSION_ROUND_NAME"] != "WRAPPER_CANARY":
    assert head == "542cc6f7b7ef764a7730a9b99918df5ac02d54f2"
assert re.fullmatch(r"[a-f0-9]{64}", binding_sha)
decision, binding = load_admission(root, actor=actor, round_id=round_id,
    round_name=os.environ["C17_SESSION_ROUND_NAME"],
    decision_ref=json.loads(os.environ["C17_SESSION_DECISION_REF"]),
    binding_ref=json.loads(os.environ["C17_SESSION_BINDING_REF"]))
assert decision["decision_id"] == decision_id
assert head == decision["head"] == binding["head"]
assert json.loads(os.environ["C17_SESSION_BINDING_REF"])["sha256"] == binding_sha
destination = Path(sys.argv[1])
command = sys.argv[2:]
assert destination.parent.resolve(strict=True).is_relative_to(root)
assert command[0] == "/usr/bin/sandbox-exec"
protocol = "exclusive-pending-fsync-hardlink-v1"
pending = destination.with_name(destination.name + ".pending")
fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
value = {"pid": os.getpid(), "ppid": os.getppid(), "uid": os.getuid(), "pgid": os.getpgrp(),
         "command": command, "qa_root": str(root), "publication_protocol": protocol,
         "actor": actor, "round_id": round_id, "head": head, "stage": stage,
         "decision_id": decision_id, "binding_sha256": binding_sha}
with os.fdopen(fd, "w") as handle:
    json.dump(value, handle)
    handle.flush()
    os.fsync(handle.fileno())
os.link(pending, destination, follow_symlinks=False)
# Pending fermé conservé ; visibilité atomique du hardlink, jamais overwrite.
release = destination.with_name(destination.name + ".release")
deadline = time.monotonic() + 5
while True:
    if time.monotonic() >= deadline:
        raise SystemExit("barrier_autonomous_timeout_no_workload")
    try:
        fd = os.open(release, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        time.sleep(0.01)
        continue
    with os.fdopen(fd) as handle:
        release_pending = release.with_name(release.name + ".pending")
        assert release.resolve(strict=True) == release
        assert release_pending.resolve(strict=True) == release_pending
        assert release_pending.parent.resolve(strict=True).is_relative_to(root)
        with os.fdopen(os.open(release_pending, os.O_RDONLY | os.O_NOFOLLOW)) as staged:
            a, b = os.fstat(handle.fileno()), os.fstat(staged.fileno())
            assert stat.S_ISREG(a.st_mode) and stat.S_ISREG(b.st_mode)
            assert (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino) and a.st_nlink == b.st_nlink == 2
            assert a.st_uid == b.st_uid == os.getuid() and a.st_size == b.st_size
        approved = json.load(handle)
    assert approved["publication_protocol"] == protocol
    assert approved["gate"] == value and approved["identity"]["pid"] == os.getpid()
    assert approved["identity"]["ppid"] == os.getppid() and approved["identity"]["uid"] == os.getuid()
    assert approved["identity"]["pgid"] == os.getpgrp() and approved["identity"]["start_sec"] > 0
    assert 0 <= approved["identity"]["start_usec"] < 1_000_000
    if time.monotonic() >= deadline:
        raise SystemExit("barrier_autonomous_timeout_no_workload")
    break
os.execve(command[0], command, os.environ)
