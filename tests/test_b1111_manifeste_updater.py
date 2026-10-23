"""B-1111 : un .deb ne doit jamais être une mise à jour Linux générique."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parents[1]
SCRIPT = RACINE / "scripts" / "nettoyer_latest_json.py"


def _nettoyer(manifeste):
    spec = importlib.util.spec_from_file_location("nettoyer_latest_json", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.nettoyer_manifeste(manifeste)


def test_le_deb_perd_la_cible_generique_et_garde_la_cible_deb():
    paquet = {"url": "https://exemple.test/THERESE_0.79.0_amd64.deb", "signature": "signature-factice"}
    resultat = _nettoyer({"version": "0.79.0", "platforms": {"linux-x86_64": paquet, "linux-x86_64-deb": paquet}})
    assert resultat["platforms"] == {"linux-x86_64-deb": paquet}


def test_un_generique_non_appimage_fait_echouer_sans_ecrire(tmp_path):
    chemin = tmp_path / "latest.json"
    contenu = json.dumps({"platforms": {"linux-aarch64": {"url": "https://exemple.test/update.rpm"}}})
    chemin.write_text(contenu, encoding="utf-8")
    retour = subprocess.run([sys.executable, str(SCRIPT), str(chemin)], capture_output=True, text=True)
    assert retour.returncode != 0
    assert "AppImage" in retour.stderr
    assert chemin.read_text(encoding="utf-8") == contenu


def test_workflow_nettoie_avant_de_publier():
    workflow = yaml.safe_load((RACINE / ".github/workflows/release.yml").read_text(encoding="utf-8"))
    construction = workflow["jobs"]["build"]
    action = next(e for e in construction["steps"] if e.get("uses", "").startswith("tauri-apps/tauri-action@"))
    # La matrice ne doit jamais publier un manifeste dangereux, même provisoire.
    assert action["with"].get("includeUpdaterJson") is False
    publication = workflow["jobs"]["manifeste-updater"]
    assert "build" in publication["needs"]
    commandes = "\n".join(e.get("run", "") for e in publication["steps"])
    assert commandes.index("nettoyer_latest_json.py") < commandes.index("gh release upload")


# Entrées inventées après le correctif : dix variantes indépendantes.
@pytest.mark.parametrize("cible,url,sort", [
    ("linux-x86_64", "https://exemple.test/app.deb?download=1", "retire"),
    ("linux-aarch64", "https://exemple.test/app.DEB", "retire"),
    ("linux-armv7", "https://exemple.test/app%2Edeb", "retire"),
    ("linux-x86_64", "https://exemple.test/app.AppImage", "garde"),
    ("linux-aarch64", "https://exemple.test/app.APPIMAGE?miroir=2", "garde"),
    ("linux-x86_64", "https://exemple.test/app.rpm", "refuse"),
    ("linux-aarch64", "https://exemple.test/app.tar.gz", "refuse"),
    ("linux-armv7", "https://exemple.test/app.AppImage.sig", "refuse"),
    ("linux-x86_64-deb", "https://exemple.test/app.deb", "garde"),
    ("windows-x86_64", "https://exemple.test/app.msi", "garde"),
])
def test_rejeu_dix_manifestes(cible, url, sort):
    source = {"version": "1.2.3", "notes": "Notes à conserver", "platforms": {cible: {"url": url, "signature": "factice"}}}
    avant = json.dumps(source)
    if sort == "refuse":
        with pytest.raises(ValueError, match="AppImage"):
            _nettoyer(source)
    else:
        resultat = _nettoyer(source)
        assert (cible in resultat["platforms"]) == (sort == "garde")
        assert resultat["notes"] == source["notes"]
        assert _nettoyer(resultat) == resultat
    assert json.dumps(source) == avant


def _release_et_signatures(dossier):
    assets = []
    for nom in ["THERESE_aarch64.app.tar.gz", "THERESE_x64-setup.exe", "THERESE_x64.msi", "THERESE_amd64.deb"]:
        assets.append({"name": nom, "url": f"https://github.com/exemple/app/releases/download/untagged-123/{nom}"})
        assets.append({"name": nom + ".sig", "url": f"https://exemple.test/{nom}.sig"})
        (dossier / (nom + ".sig")).write_text("signature-factice\n", encoding="utf-8")
    return {"tagName": "v1.2.3-alpha", "body": "Notes", "publishedAt": "2026-10-23T00:00:00Z", "assets": assets}


def test_assemblage_ci_conserve_les_trois_os_et_les_signatures(tmp_path):
    release = tmp_path / "release.json"
    release.write_text(json.dumps(_release_et_signatures(tmp_path)), encoding="utf-8")
    manifeste = tmp_path / "latest.json"
    retour = subprocess.run([
        sys.executable, str(SCRIPT), str(manifeste), "--release-assets", str(release),
        "--signatures", str(tmp_path), "--version", "1.2.3",
    ], capture_output=True, text=True)
    assert retour.returncode == 0, retour.stderr
    resultat = json.loads(manifeste.read_text(encoding="utf-8"))
    assert resultat["version"] == "1.2.3"
    assert set(resultat["platforms"]) == {
        "darwin-aarch64", "darwin-aarch64-app", "windows-x86_64", "windows-x86_64-msi",
        "windows-x86_64-nsis", "linux-x86_64-deb",
    }
    assert resultat["platforms"]["windows-x86_64"]["url"].endswith(".msi")
    assert all("untagged" not in p["url"] and "v1.2.3-alpha" in p["url"] and p["signature"] == "signature-factice" for p in resultat["platforms"].values())


def test_signature_absente_bloque_la_creation_du_manifeste(tmp_path):
    release = _release_et_signatures(tmp_path)
    release["assets"] = [a for a in release["assets"] if not a["name"].endswith(".deb.sig")]
    donnees = tmp_path / "release.json"
    donnees.write_text(json.dumps(release), encoding="utf-8")
    manifeste = tmp_path / "latest.json"
    retour = subprocess.run([
        sys.executable, str(SCRIPT), str(manifeste), "--release-assets", str(donnees),
        "--signatures", str(tmp_path), "--version", "1.2.3",
    ], capture_output=True, text=True)
    assert retour.returncode != 0
    assert not manifeste.exists()


def test_les_architectures_du_constructeur_correspondent_a_la_matrice():
    workflow = yaml.safe_load((RACINE / ".github/workflows/release.yml").read_text(encoding="utf-8"))
    cibles = workflow["jobs"]["build"]["strategy"]["matrix"]["platform"]
    assert {c["target"] for c in cibles} == {
        "aarch64-apple-darwin", "x86_64-pc-windows-msvc", "x86_64-unknown-linux-gnu",
    }
