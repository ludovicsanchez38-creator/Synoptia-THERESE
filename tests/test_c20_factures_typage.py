"""Les fonctions de facturation, sauvegarde et coûts restent typées sous mypy."""

import ast
import os
import re
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
FONCTIONS = {
    "src/backend/app/routers/invoices.py": {
        "_dernier_apercu_pdf", "_empreinte_donnees_pdf", "_verifier_preuve_pdf",
        "_verifier_archive_pdf", "_enregistrer_preuve_pdf", "_numero_pdf_pour_statut",
        "_verifier_edition_pdf", "_publier_pdf_atteste", "_generer_edition_pdf",
    },
    "src/backend/app/routers/data.py": {
        "_lien_de_publication_sur", "_lien_de_compagnon_sur", "_membres_a_extraire",
    },
    "src/backend/app/routers/escalation.py": {"_avec_montants_usd"},
}


def test_les_fonctions_des_archives_sont_typees():
    plages = {}
    for fichier, noms in FONCTIONS.items():
        arbre = ast.parse((RACINE / fichier).read_text(encoding="utf-8"))
        fonctions = {
            noeud.name: (noeud.lineno, noeud.end_lineno)
            for noeud in arbre.body if isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert noms <= fonctions.keys()
        plages[fichier] = [fonctions[nom] for nom in noms]

    resultat = subprocess.run(
        [
            sys.executable, "-m", "mypy", *FONCTIONS,
            "--follow-imports=skip", "--ignore-missing-imports", "--no-error-summary",
            f"--cache-dir={os.devnull}",
        ],
        cwd=RACINE,
        env={**os.environ, "MYPYPATH": str(RACINE / "src" / "backend")},
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert resultat.returncode in (0, 1), resultat.stdout + resultat.stderr
    assert "INTERNAL ERROR" not in resultat.stdout + resultat.stderr
    assert resultat.returncode == 0 or " error:" in resultat.stdout
    erreurs = []
    for ligne in resultat.stdout.splitlines():
        diagnostic = re.match(r"^(.+?):(\d+): error:", ligne)
        if diagnostic:
            fichier, numero = diagnostic.group(1).replace("\\", "/"), int(diagnostic.group(2))
            if any(debut <= numero <= fin for debut, fin in plages.get(fichier, [])):
                erreurs.append(ligne)
    assert not erreurs, f"{len(erreurs)} erreur(s) mypy dans les fonctions concernées :\n" + "\n".join(erreurs)
