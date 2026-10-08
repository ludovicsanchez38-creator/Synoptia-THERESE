"""Contrôles de la configuration réelle des journaux sur un profil jetable."""
from __future__ import annotations

import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from common import REPO, environment, head, manifest, new_run, save, sha


def main() -> None:
    out = new_run("logs")
    current_head = head()
    data = manifest()
    data_dir = Path(data["temporary_root"]) / out.name
    data_dir.mkdir()
    # Tous les imports produit viennent après le dossier explicite et la garde.
    clean = environment(data_dir)
    os.chdir(data["temporary_root"])
    os.environ.clear()
    os.environ.update(clean)
    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(REPO / "src/backend"))
    from tests.couverture.backend_offline import installer_garde_socket
    installer_garde_socket()
    from app.config import settings
    from app.core.logging_config import dossier_des_journaux, setup_logging
    if Path(settings.data_dir).resolve() != data_dir.resolve():
        raise RuntimeError("Configuration de journal non jetable")
    log_path = dossier_des_journaux() / "therese.log"
    if not log_path.resolve().is_relative_to(data_dir.resolve()):
        raise RuntimeError("Le journal sort du profil jetable")
    setup_logging()
    logger = logging.getLogger("calibration.cycle17.reprise")
    run_id = out.name
    logger.info("TEMOIN-C17-SAIN", extra={"calibration_run": run_id})
    before = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    healthy = [line for line in before if line.get("message") == "TEMOIN-C17-SAIN"
               and line.get("extra", {}).get("calibration_run") == run_id and line["level"] == "INFO"]
    negative_ok = len(healthy) == 1 and not any(line["level"] == "ERROR" for line in before)
    logger.error("TEMOIN-C17-ERREUR-INJECTEE", extra={"calibration_run": run_id})
    after = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    errors = [line for line in after if line.get("message") == "TEMOIN-C17-ERREUR-INJECTEE"
              and line.get("extra", {}).get("calibration_run") == run_id and line["level"] == "ERROR"]
    positive_ok = len(errors) == 1 and bool(healthy) and datetime.fromisoformat(healthy[0]["timestamp"]) <= datetime.fromisoformat(errors[0]["timestamp"])
    logging.shutdown()
    raw = out / "therese-temoin.log"
    shutil.copy2(log_path, raw)
    save(out / "logs-controls.json", {"instrument": "logs", "cycle": 17,
        "status": "passed" if positive_ok and negative_ok else "failed", "head": current_head,
        "tool": "app.core.logging_config.setup_logging", "data_dir": str(data_dir),
        "raw_log": str(raw), "raw_log_sha256": sha(raw), "run_id": run_id,
        "negative_control": {"pass": negative_ok, "healthy_markers": len(healthy), "records": len(before)},
        "positive_control": {"pass": positive_ok, "correlated_errors": len(errors), "records": len(after)}})
    print(json.dumps({"status": "passed" if positive_ok and negative_ok else "failed", "proof": str(out / "logs-controls.json")}))
    raise SystemExit(0 if positive_ok and negative_ok else 1)


if __name__ == "__main__":
    main()
