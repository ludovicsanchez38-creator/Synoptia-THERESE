"""B-1855 : une release manuelle doit construire la référence du tag demandé."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_le_tag_manuel_designe_le_commit_valide_par_la_ci():
    workflow = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8"))
    refs = {}
    for nom in ("sources-copyleft", "build"):
        etapes = workflow["jobs"][nom]["steps"]
        checkout = next(e for e in etapes if e.get("uses", "").startswith("actions/checkout@"))
        refs[nom] = checkout.get("with", {}).get("ref")
    preflight = workflow["jobs"]["preflight"]["steps"]
    gardes = [e for e in preflight if "git rev-parse" in e.get("run", "")
              and ("GITHUB_SHA" in e["run"] or "github.sha" in e["run"])
              and "tag" in str(e).lower()]
    assert gardes, (
        f"aucune comparaison du commit du tag manuel à celui de la CI ; refs checkout : {refs}"
    )
