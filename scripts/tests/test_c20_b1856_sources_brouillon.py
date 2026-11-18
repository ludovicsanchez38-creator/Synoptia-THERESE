"""B-1856 : les archives de sources ne remplacent pas une release publique."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_les_sources_verifient_le_statut_brouillon_avant_upload():
    workflow = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8"))
    etapes = workflow["jobs"]["sources-copyleft"]["steps"]
    publication = next(e for e in etapes if "gh release upload" in e.get("run", ""))
    avant_upload = publication["run"].split("gh release upload", 1)[0]
    assert "--clobber" in publication["run"]
    assert "isDraft" in avant_upload or ".draft" in avant_upload, (
        "la release existante est seulement recherchée, sans contrôle du statut brouillon"
    )
