"""Témoins rouges et verts dans des copies ignorées, sans fichier suivi modifié."""
from __future__ import annotations

import json
import subprocess
from nested_capture import capture_nested, reserved_path
import xml.etree.ElementTree as ET
from pathlib import Path

from common import FRONT, PYTHON, REPO, environment, head, manifest, new_run, save, sha


def counts(path: Path) -> dict[str, int]:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    return {name: sum(int(suite.attrib.get(name, "0")) for suite in suites)
            for name in ("tests", "failures", "errors", "skipped")}


def main() -> None:
    out = reserved_path("test-runner")
    pytest_source = out / "test_temoin_c17.py"
    pytest_source.write_text('import os\n\ndef test_temoin_c17():\n    assert (2 if os.environ.get("C17_TEST_RUNNER_DEFECT") == "1" else 1) == 1\n', encoding="utf-8")
    vitest_source = out / "calibrationC17.test.ts"
    vitest_source.write_text('it("détecte le défaut puis l’état sain", () => { expect(process.env.C17_TEST_RUNNER_DEFECT === "1" ? 2 : 1).toBe(1); });\n', encoding="utf-8")
    config = out / "vitest.runtime.config.mjs"
    vite_module = str((FRONT / "node_modules/vite/dist/node/index.js").resolve())
    config.write_text(f'import {{ defineConfig }} from {json.dumps(vite_module)};\nexport default defineConfig({{root: {json.dumps(str(out))}, server: {{host: "127.0.0.1"}}, test: {{globals: true, environment: "node", include: ["calibrationC17.test.ts"], cache: false}}}});\n', encoding="utf-8")
    data = manifest()
    proofs = {}
    for tool in ("pytest", "vitest"):
        for name, defect, expected in (("positive", True, 1), ("negative", False, 0)):
            xml = out / f"{tool}-{name}.xml"
            env = environment(Path(data["temporary_root"]) / "test-data")
            if defect:
                env["C17_TEST_RUNNER_DEFECT"] = "1"
            command = ([str(PYTHON), "-m", "pytest", "--noconftest", f"--rootdir={out}", str(pytest_source),
                        f"--junitxml={xml}", "-p", "no:cacheprovider"] if tool == "pytest"
                       else [str(FRONT / "node_modules/.bin/vitest"), "run", "--config", str(config),
                             "--reporter=junit", f"--outputFile={xml}"])
            result = capture_nested(command, env=env, cwd=REPO if tool == "pytest" else FRONT, timeout=90,
                                    stdout_path=out / f"{tool}-{name}.stdout",
                                    stderr_path=out / f"{tool}-{name}.stderr", label=f"test-{tool}-{name}")
            with (out / f"{tool}-{name}.log").open("x", encoding="utf-8") as stream:
                stream.write(result.stdout + result.stderr)
            tally = counts(xml) if xml.exists() else {}
            expected_counts = {"tests": 1, "failures": 1 if defect else 0, "errors": 0, "skipped": 0}
            proofs[f"{tool}-{name}"] = {"exit_code": result.returncode, "counts": tally,
                "xml": str(xml), "sha256": sha(xml) if xml.exists() else None,
                "pass": result.returncode == expected and tally == expected_counts}
    status = "passed" if all(value["pass"] for value in proofs.values()) else "failed"
    save(out / "test-runner-controls.json", {"instrument": "test_runner", "cycle": 17,
         "status": status, "head": head(), "repo": str(REPO), "controls": proofs,
         "witnesses": {str(path): sha(path) for path in (pytest_source, vitest_source, config)},
         "note": "Témoins conservés uniquement dans le dossier ignoré de preuves, aucun retrait de source."})
    print(json.dumps({"status": status, "proof": str(out / "test-runner-controls.json")}))
    raise SystemExit(0 if status == "passed" else 1)


if __name__ == "__main__":
    main()
