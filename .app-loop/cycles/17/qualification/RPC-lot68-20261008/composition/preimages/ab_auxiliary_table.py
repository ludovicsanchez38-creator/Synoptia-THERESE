"""Closed A/B Chrome invocation table; preparation only, never an admission.

The five RPC children are a subset of the fourteen browser invocations.  This
table does not claim that the candidate Seatbelt profile passed a native test.
"""
from __future__ import annotations

from pathlib import Path
import re


ROOT_RE = re.compile(r"therese-(c17-direct-round-([ab])-[0-9a-f]{12})\Z")
RPC_JOBS = (
    "rpc-all-runtime_ui-visual_capture-network_capture",
    "rpc-screen-negative", "rpc-screen-positive-visual",
    "rpc-screen-positive-network", "rpc-screen-restored",
)
DIRECT_SITES = (
    ("recipe-general", "runtime/recette-c17.mjs"),
    ("recipe-invoices", "runtime/recette-facturation-p160-v2.mjs"),
    ("recipe-crm", "runtime/recette-crm-focus.mjs"),
    ("B1713", "complements/instruments/b1713-clavier-v3.mjs"),
    ("P157-800", "complements/instruments/p157-pipeline-root-oracle.mjs"),
    ("P157-1440", "complements/instruments/p157-pipeline-root-oracle.mjs"),
    ("B1755", "complements/instruments/b1755-garde-v3.mjs"),
    ("P162", "complements/instruments/p162-colonnes-v3.mjs"),
    ("coverage", "runtime/couverture-ecran-c17.mjs"),
)
JOBS = RPC_JOBS + tuple(name for name, _ in DIRECT_SITES)
NAMES = {job: "aux-chrome-" + job for job in JOBS}
ROLES = frozenset("auxiliary-" + name for name in NAMES.values())
DISABLED_ARGS = ["--disable-background-networking", "--disable-component-update", "--disable-sync"]
CHROME_CANDIDATE_SHA256 = "5266a6b026b5eb8192e030b5c27cc0001b65fce97d5840a9979e16a0d4ac151d"
CHROME_CANDIDATE_BYTES = 1914


def scope(root: Path, round_name: str) -> bool:
    match = ROOT_RE.fullmatch(root.name)
    return (root.parent == Path("/private/tmp") and match is not None
            and round_name in ("A", "B") and round_name == match.group(2).upper())


def expected_row(root: Path, job: str) -> dict:
    if job not in JOBS:
        raise ValueError("Auxiliary job outside fourteen exact A/B invocations")
    name = NAMES[job]
    folder = root / "auxiliary" / name
    options = {"headless": False, "channel": "chrome", "chromiumSandbox": True}
    if job != RPC_JOBS[0]:
        options["args"] = DISABLED_ARGS.copy()
    return {
        "job": job, "name": name, "role": "auxiliary-" + name,
        "logical_parent": "calibrate" if job in RPC_JOBS else job,
        "port": 17594,
        "executable": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "profile": str(folder / "profile"), "stdout": str(folder / "stdout.log"),
        "stderr": str(folder / "stderr.log"), "start_path": str(folder / "start.json"),
        "services_path": str(folder / "services.json"), "stop_path": str(folder / "stop.json"),
        "original_options": options, "source_script": dict(DIRECT_SITES).get(job),
    }


def required_metadata(job: str) -> frozenset[str]:
    if job in JOBS:
        return (frozenset(("C17_AUX_CONTEXT_REF", "C17_AUX_GIT_SNAPSHOT_REF"))
                if job == RPC_JOBS[0] or job not in RPC_JOBS
                else frozenset(("C17_AUX_CONTEXT_REF",)))
    if job == "rpc-all-logs":
        return frozenset(("C17_AUX_GIT_SNAPSHOT_REF", "C17_AUX_LOGS_RUN"))
    if job in ("rpc-all-test_runner", "rpc-all-screen_coverage"):
        return frozenset(("C17_AUX_GIT_SNAPSHOT_REF",))
    return frozenset()
