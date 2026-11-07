"""La recette .deb s'authentifie avec son fichier privé, sans HTTP anonyme."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.name != "posix", reason="La recette .deb utilise les exécutables POSIX.")


def _jouer_amorcage(tmp_path, contenu_jeton):
    donnees = tmp_path / "donnees"
    donnees.mkdir()
    if contenu_jeton is not None:
        jeton = donnees / ".session_token"
        jeton.write_text(contenu_jeton, encoding="utf-8")
        jeton.chmod(0o600)
    binaires = tmp_path / "bin"
    binaires.mkdir()
    appels = tmp_path / "appels.jsonl"
    faux_curl = binaires / "curl"
    faux_curl.write_text(
        f"#!{sys.executable}\n" + '''
import json
import os
import sys
from pathlib import Path

with Path(os.environ["APPELS_FACTICES"]).open("a", encoding="utf-8") as fichier:
    fichier.write(json.dumps(sys.argv[1:]) + "\\n")
autorise = "X-Therese-Token: jeton-prive-factice" in sys.argv
print(json.dumps({"id": "document-factice"} if autorise else {"code": "UNAUTHORIZED"}))
''',
        encoding="utf-8",
    )
    faux_curl.chmod(0o700)
    racine = Path(__file__).resolve().parents[1]
    texte = (racine / "scripts" / "recette-deb.sh").read_text(encoding="utf-8")
    # Exécuter le vrai amorçage et le premier appel métier, sans extraire de paquet.
    debut = texte.index("# 3. DOCX")
    fin = texte.index('sec="$(', debut)
    resultat = subprocess.run(
        ["bash", "-c", 'set -uo pipefail\nko() { echo "[ÉCHEC] $*"; }\n'
         + texte[debut:fin] + '\nprintf "%s" "$doc"\n'],
        cwd=racine,
        env={**os.environ, "PATH": str(binaires) + os.pathsep + os.defpath,
             "DONNEES": str(donnees), "PORT": "17593", "APPELS_FACTICES": str(appels)},
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=10,
        check=False,
    )
    requetes = [json.loads(ligne) for ligne in appels.read_text(encoding="utf-8").splitlines()] if appels.exists() else []
    return resultat, requetes


def test_la_recette_deb_lit_son_fichier_prive_pour_creer_un_document(tmp_path):
    resultat, requetes = _jouer_amorcage(tmp_path, "jeton-prive-factice")
    assert resultat.returncode == 0, resultat.stderr
    assert resultat.stdout == "document-factice"
    assert len(requetes) == 1
    assert "http://127.0.0.1:17593/api/documents" in requetes[0]
    assert "X-Therese-Token: jeton-prive-factice" in requetes[0]


@pytest.mark.parametrize("contenu_jeton", [None, ""], ids=["absent", "vide"])
def test_la_recette_deb_refuse_un_jeton_absent_ou_vide_avant_tout_appel(tmp_path, contenu_jeton):
    resultat, requetes = _jouer_amorcage(tmp_path, contenu_jeton)
    assert resultat.returncode != 0
    assert "jeton de session" in resultat.stdout.lower()
    assert requetes == []
