"""US-017 : contrôle automatisé des accents dans les messages utilisateur.

Scanne les routers backend et détecte, dans les chaînes ``detail="..."``
des HTTPException, des mots français courants écrits SANS accent alors
qu'ils devraient en porter un (« Echec » au lieu de « Échec », « non
trouve » au lieu de « non trouvé », etc.).

Le test échoue avec la liste ``fichier:ligne`` des occurrences pour que
la correction soit immédiate. La liste de motifs est volontairement
ciblée (zéro faux positif) : ne pas y ajouter de motif sans avoir
vérifié qu'il ne matche aucune chaîne légitime (mots anglais, noms de
variables, chaînes déjà accentuées).
"""

import re
from pathlib import Path

ROUTERS_DIR = Path("src/backend/app/routers")

# Extraction du contenu des chaînes detail="..." / detail=f"..." (mono-ligne).
DETAIL_STRING_RE = re.compile(r'detail=f?"([^"]*)"')

# Motifs interdits : mots français courants sans leur accent.
# NB : les limites de mot \b sont Unicode en Python -> « non trouve\b » ne
# matche PAS « non trouvé » (é est un caractère de mot, pas une frontière).
FORBIDDEN_PATTERNS = [
    (re.compile(r"\bEchec\b"), "Echec -> Échec"),
    (re.compile(r"\bnon trouvee?s?\b"), "non trouve -> non trouvé"),
    (re.compile(r"\bnon autorisee?s?\b"), "non autorise -> non autorisé"),
    (re.compile(r"\bsont autorises\b"), "autorises -> autorisés"),
    (re.compile(r"\bcaracteres\b"), "caracteres -> caractères"),
    (re.compile(r"\bDonnees\b"), "Donnees -> Données"),
    (re.compile(r"\bprecedente?s?\b"), "precedent -> précédent"),
    (re.compile(r"\bGeneration\b"), "Generation -> Génération"),
    (re.compile(r"\btelecharge\w*\b"), "telecharge -> télécharge"),
    (re.compile(r"\bdemarrage\b"), "demarrage -> démarrage"),
    (re.compile(r"\blancees?\b"), "lancee -> lancée"),
    (re.compile(r"\bcreees?\b"), "creee -> créée"),
]


def test_detail_messages_routers_sans_mot_desaccentue():
    """Aucune chaîne detail="..." des routers ne doit contenir un mot
    français courant privé de son accent (messages visibles utilisateur)."""
    assert ROUTERS_DIR.is_dir(), f"Dossier routers introuvable : {ROUTERS_DIR}"

    violations: list[str] = []
    for py_file in sorted(ROUTERS_DIR.glob("*.py")):
        source = py_file.read_text(encoding="utf-8")
        for lineno, line in enumerate(source.splitlines(), start=1):
            for match in DETAIL_STRING_RE.finditer(line):
                content = match.group(1)
                for pattern, hint in FORBIDDEN_PATTERNS:
                    if pattern.search(content):
                        violations.append(
                            f"{py_file}:{lineno} [{hint}] {content!r}"
                        )

    assert not violations, (
        "Mots sans accent détectés dans des messages utilisateur "
        "(detail=...) :\n" + "\n".join(violations)
    )
