"""B-1858 : refuser une publication Windows sans signature active."""

import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MESSAGE = "Signature Windows inactive : secrets Microsoft absents ou incomplets, publication refusée"


def test_la_publication_windows_exige_une_signature_sauf_a_blanc():
    workflow = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8"))
    etapes = workflow["jobs"]["build"]["steps"]
    preparation = next(i for i, etape in enumerate(etapes) if etape.get("id") == "windows-signing")
    garde = next((etape for etape in etapes if etape.get("name") == "Exiger la signature Windows"), None)
    assert garde is not None, "La publication Windows ne refuse pas une signature inactive"
    publication = next(i for i, etape in enumerate(etapes) if etape.get("name") == "Publier les artefacts vérifiés")
    assert preparation < etapes.index(garde) < publication
    assert "Windows" in garde.get("if", "")
    assert garde.get("shell") == "bash"
    assert not garde.get("continue-on-error")

    commande = garde["run"]
    for signature, a_blanc, code in (("false", "false", 1), ("", "", 1), ("false", "true", 0),
                                     ("true", "false", 0), ("true", "true", 0)):
        script = commande.replace("${{ steps.windows-signing.outputs.enabled }}", signature)
        script = script.replace("${{ inputs.dry_run }}", a_blanc)
        assert "${{" not in script
        resultat = subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=False)
        assert resultat.returncode == code
        if signature != "true" and a_blanc != "true":
            assert MESSAGE in resultat.stdout
        if signature == "false" and a_blanc == "true":
            assert "à blanc" in resultat.stdout and "signature Windows inactive" in resultat.stdout
