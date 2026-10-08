"""Bornes explicites proposées par root, pas des durées mesurées ni une admission."""
from __future__ import annotations
import math

STAGE_BOUNDS = {
    "backend": 50, "vite": 50, "prepare-runtime": 120, "start-runtime": 120,
    "calibrate": 1200, "recipe-general": 360, "recipe-invoices": 360, "recipe-crm": 360,
    "B1713": 360, "P157-800": 360, "P157-1440": 360, "B1755": 360, "P162": 360,
    "B1753": 360, "B1753-power": 360, "B1760": 360, "coverage": 1500,
    "build-calibrations-v3": 120, "density": 1500, "bind-current-context-contract": 120,
    "eight-logs-review": 120, "mapping78": 120, "package78": 120,
    "rpc-all-test_runner": 700, "rpc-all-logs": 700,
    "rpc-all-runtime_ui-visual_capture-network_capture": 700,
    "rpc-all-screen_coverage": 700,
    "rpc-test-pytest-positive": 90, "rpc-test-pytest-negative": 90,
    "rpc-test-vitest-positive": 90, "rpc-test-vitest-negative": 90,
    "rpc-screen-negative": 180, "rpc-screen-positive-visual": 180,
    "rpc-screen-positive-network": 180, "rpc-screen-restored": 180,
    "rpc-sql-b1753": 240, "rpc-sql-b1760": 240,
    "rpc-sql-b1753-power": 240,
}
WAIT_BOUNDS = {"contract-review-wait": 120, "independent-review-wait": 120, "stage-binding-wait": 120}
START_SEQUENCE = ("prepare-runtime", "backend", "vite", "start-runtime", "calibrate",
    "build-calibrations-v3", "recipe-general", "recipe-invoices", "recipe-crm", "density",
    "bind-current-context-contract", "B1713", "P157-800", "P157-1440", "B1755", "P162",
    "B1753", "B1753-power", "B1760", "coverage", "eight-logs-review", "mapping78", "package78")
ROOT_REVIEW_SEQUENCE = ("contract-review", "independent-review", "independent-review",
                        "independent-review", "package-review")
SERVICE_NAMES = frozenset(("backend", "vite"))
CLEANUP_SECONDS = 8


def exact_bound(name: str, value: float, *, wait: bool = False) -> float:
    table = WAIT_BOUNDS if wait else STAGE_BOUNDS
    if (name not in table or type(value) not in (int, float) or not math.isfinite(value)
        or value != table[name] or not 0 < value <= 1500):
        raise ValueError("Borne explicite différente/manquante : " + name)
    return value


def round_ceiling_proposal() -> dict:
    # Plafond conservateur, après canaris frais et avant la première étape.
    # Au maximum chaque start reçoit son binding tardif exact ; cinq revues root.
    # Chaque wait non-service, stop_services et stop final garde cleanup8.
    components = {
        "workload_and_service_startup": sum(STAGE_BOUNDS[name] for name in START_SEQUENCE),
        "late_binding_waits_upper": len(START_SEQUENCE) * WAIT_BOUNDS["stage-binding-wait"],
        "root_review_waits": len(ROOT_REVIEW_SEQUENCE) * WAIT_BOUNDS["independent-review-wait"],
        "in_process_copy_and_service_stop": 2 * 120,
        "cleanup_upper": (len(START_SEQUENCE) - len(SERVICE_NAMES) + 2) * CLEANUP_SECONDS,
    }
    return {"components": components, "seconds": sum(components.values()),
            "measured": False, "admitted": False, "round_watchdog_implemented": False,
            "service_50s_is_startup_gate_only_not_lifetime": True,
            "services_closed_only_by_owned_stop": True}
