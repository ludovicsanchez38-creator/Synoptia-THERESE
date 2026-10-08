"""Calibre une copie de l'instrument écran ; aucune source produit n'est écrite."""
from __future__ import annotations

import json
import subprocess
from nested_capture import capture_nested, reserved_path
from pathlib import Path

from common import BASE, NODE, OUT, REPO, assert_unchanged, environment, head, immutable_snapshot, manifest, new_run, save, sha


INJECTION = '''
  // Témoin réservé à cette copie de calibration ; le fichier suivi reste intact.
  if (process.env.C17_SCREEN_WITNESS === 'visual') {
    await page.evaluate(() => {
      const wrapper = document.createElement('div');
      Object.assign(wrapper.style, {position: 'fixed', right: '0', bottom: '0', width: '100px', height: '24px', overflow: 'hidden', zIndex: '99999', background: '#e11d8d', border: '2px solid #000'});
      const overflow = document.createElement('div'); Object.assign(overflow.style, {width: '4000px', height: '20px'}); wrapper.appendChild(overflow);
      const button = document.createElement('button'); Object.assign(button.style, {position: 'fixed', right: '0', bottom: '28px', width: '20px', height: '20px', zIndex: '99999', background: '#e11d8d', border: '2px solid #000'});
      document.body.append(wrapper, button);
    });
  } else if (process.env.C17_SCREEN_WITNESS === 'network') {
    await page.evaluate(() => {const script = document.createElement('script'); script.src = 'https://calibration.invalid/probe?jeton=temoin'; document.body.appendChild(script);});
    await page.waitForTimeout(150);
  }
'''


def main() -> None:
    out = reserved_path("screen")
    snapshot = immutable_snapshot()
    source = OUT / "couverture-ecran-c17.mjs"
    original = source.read_text(encoding="utf-8")
    anchor = "  await ouvrirLEcran(page, base, action);\n  if (journal.portReel)"
    if original.count(anchor) != 1:
        raise RuntimeError("Ancre d'injection écran modifiée ; relire l'instrument")
    copy = out / "couverture-ecran-calibree.mjs"
    copy.write_text(original.replace(anchor, "  await ouvrirLEcran(page, base, action);\n" + INJECTION + "  if (journal.portReel)"), encoding="utf-8")
    evidence = {"instrument": "screen_coverage", "cycle": 17, "head": head(), "status": "running",
        "source": str(source), "source_sha256": sha(source), "calibrated_copy": str(copy),
        "copy_sha256": sha(copy), "stack": {"base": BASE, "data_dir": manifest()["data_dir"]},
        "note": "Injection DOM dans une copie ignorée de l'instrument ; aucun index.html ni verrou modifié."}

    def run(label: str, witness: str | None = None) -> tuple[int, Path]:
        target = out / label
        env = environment()
        if witness:
            env["C17_SCREEN_WITNESS"] = witness
        command = [str(NODE), str(copy), "--base", BASE, "--expected-data-dir", manifest()["data_dir"],
                   "--sortie", str(target), "--ecrans", "accueil", "--largeurs", "1440", "--themes", "light"]
        result = capture_nested(command, cwd=REPO, env=env, timeout=180,
                                stdout_path=out / f"{label}.stdout", stderr_path=out / f"{label}.stderr",
                                label=f"screen-{label}")
        with (out / f"{label}.log").open("x", encoding="utf-8") as stream:
            stream.write(result.stdout + result.stderr)
        print(json.dumps({"control": label, "exit": result.returncode, "folder": str(target)}), flush=True)
        return result.returncode, target

    def healthy(label: str) -> dict:
        code, folder = run(label)
        report_path = folder / "rapport.json"
        report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
        ok = code == 0 and "anomalies" in report and not report["anomalies"] and not any(report["garde"].get(name) for name in ("bloquees", "websockets_bloques", "telechargements", "popups", "portReel"))
        return {"exit_code": code, "pass": ok, "path": str(report_path),
                "sha256": sha(report_path) if report_path.exists() else None, "anomalies": report.get("anomalies")}

    try:
        evidence["negative"] = healthy("negative")
        code, folder = run("positive-visual", "visual")
        path = folder / "rapport.json"
        report = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        types = sorted({anomaly["type"] for anomaly in report.get("anomalies", [])})
        evidence["positive_visual"] = {"exit_code": code, "pass": code == 0 and {"contenu-rogne", "nom-accessible-vide"}.issubset(types),
            "types": types, "path": str(path), "sha256": sha(path) if path.exists() else None}
        code, folder = run("positive-network", "network")
        path = folder / "interruption.json"
        interruption = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        blocked = interruption.get("garde", {}).get("bloquees", [])
        redacted = path.exists() and "jeton=temoin" not in path.read_text(encoding="utf-8")
        evidence["positive_network"] = {"exit_code": code, "pass": code != 0 and any(item["url"] == "https://calibration.invalid/probe" for item in blocked) and redacted,
            "path": str(path), "sha256": sha(path) if path.exists() else None, "blocked": blocked, "query_redacted": redacted}
        evidence["restored"] = healthy("restored")
        evidence["status"] = "passed" if all(evidence[name]["pass"] for name in ("negative", "positive_visual", "positive_network", "restored")) else "failed"
    except BaseException as error:
        evidence["status"] = "blocked"
        evidence["error"] = str(error)
        raise
    finally:
        assert_unchanged(snapshot)
        evidence["sources_preserved"] = snapshot
        save(out / "screen-controls.json", evidence)
    print(json.dumps({"status": evidence["status"], "proof": str(out / "screen-controls.json")}))
    raise SystemExit(0 if evidence["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
