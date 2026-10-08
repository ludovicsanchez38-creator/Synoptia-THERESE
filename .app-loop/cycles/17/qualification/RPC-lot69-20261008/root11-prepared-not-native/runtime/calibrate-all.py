"""Exécute les six instruments séquentiellement et conserve tous les retours."""
from __future__ import annotations

import json
import subprocess
from nested_capture import capture_nested, session_child_env, reserved_path

from common import NODE, OUT, PYTHON, REPO, environment, head, manifest, new_run, save


if __name__ == "__main__":
    if manifest()["status"] != "running":
        raise SystemExit("Démarrer et vérifier la pile après l'intégration finale")
    out = reserved_path("all")
    results = []
    for name, command in (
        ("test_runner", [str(PYTHON), str(OUT / "calibrate-test-runner.py")]),
        ("logs", [str(PYTHON), str(OUT / "calibrate-logs.py")]),
        ("runtime_ui-visual_capture-network_capture", [str(NODE), str(OUT / "calibrate-browser.mjs")]),
        ("screen_coverage", [str(PYTHON), str(OUT / "calibrate-screen.py")]),
    ):
        result = capture_nested(command, cwd=manifest()["temporary_root"], env=session_child_env(environment()), timeout=700,
                                stdout_path=out / f"{name}.stdout", stderr_path=out / f"{name}.stderr",
                                label=f"all-{name}")
        path = out / f"{name}.log"
        with path.open("x", encoding="utf-8") as stream:
            stream.write(result.stdout + result.stderr)
        results.append({"instruments": name, "exit_code": result.returncode, "log": str(path)})
        print(json.dumps(results[-1]), flush=True)
    status = "passed" if all(result["exit_code"] == 0 for result in results) else "failed"
    save(out / "calibration-summary.json", {"cycle": 17, "status": status, "head": head(), "repo": str(REPO), "results": results})
    print(json.dumps({"status": status, "summary": str(out / "calibration-summary.json")}))
    raise SystemExit(0 if status == "passed" else 1)
