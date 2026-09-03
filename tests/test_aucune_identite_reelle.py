"""B-276 : l'identité réelle du mainteneur ne sert pas de texte d'exemple.

Le dépôt est privé, les binaires ne le sont pas : chaque alpha part en release
GitHub et sur la landing. Or les placeholders du formulaire de profil, la
signature d'e-mail et les commentaires de `user_profile.py` portaient le nom
civil, l'adresse du siège et les identifiants légaux d'une personne et d'une
entreprise réelles. Un testeur qui ouvre Paramètres > Profil lisait donc un
SIREN, une TVA, un SIRET, un code APE et un numéro de déclaration d'activité
qui désignent quelqu'un.

Cette garde balaie les fichiers SUIVIS PAR GIT sous `src/` - frontend, backend
et coque Tauri. Le suivi git est l'énumération : elle écarte d'elle-même
`node_modules/`, `target/` et `dist/` (ignorés, jamais versionnés, reconstruits
depuis les sources balayées ici) sans liste d'exclusion arbitraire.

Ce qu'elle NE refuse PAS, sciemment :
  - « Ludo Sanchez » de `src-tauri/Cargo.toml` : de la paternité d'auteur, pas
    un exemple ;
  - le nom de marque « Synoptïa », qui est l'éditeur de l'application ;
  - `tests/`, hors périmètre : un jeu de données de test ne part pas dans le
    binaire (le jeu fictif y est posé par le même lot).

Les motifs sont composés par morceaux : le fichier ne doit jamais contenir la
valeur réelle d'un seul tenant, sinon la garde se dénoncerait elle-même.
"""

import re
import subprocess
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PERIMETRE = "src"

#: Séparateurs tolérés entre les tranches d'un identifiant : « 123 456 789 »,
#: « 123456789 », « 123.456.789 » et « 123-456-789 » sont le même numéro. Le
#: motif est donc composé tranche par tranche, jamais écrit d'un seul tenant :
#: une garde qui recopie la valeur qu'elle interdit la republie.
SEP = r"[ .\xa0\u202f\u2009-]?"
ESPACE = r"\s+"

MOTIFS: dict[str, re.Pattern[str]] = {
    "SIREN/SIRET du mainteneur": re.compile(rf"991{SEP}606{SEP}781"),
    "TVA intracommunautaire du mainteneur": re.compile(
        rf"FR{SEP}08{SEP}991{SEP}606{SEP}781", re.IGNORECASE
    ),
    "numéro de déclaration d'activité du mainteneur": re.compile(
        rf"93{SEP}04{SEP}01236{SEP}04"
    ),
    "adresse du siège du mainteneur": re.compile(
        rf"Mont[ée]e{ESPACE}des{ESPACE}Gen[êe]ts", re.IGNORECASE
    ),
    "nom civil du mainteneur": re.compile(rf"Ludovic{ESPACE}Sanchez", re.IGNORECASE),
}

#: Rien à lire dans une police ou une icône, et leur décodage coûte pour rien.
BINAIRES = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".icns", ".webp", ".avif",
    ".woff", ".woff2", ".ttf", ".otf", ".eot", ".wasm", ".pdf", ".zip",
    ".gz", ".db", ".sqlite", ".bin", ".so", ".dylib", ".dll", ".node",
    ".mp3", ".mp4", ".mov", ".jar", ".pyc",
}


def _fichiers_du_perimetre() -> list[Path]:
    """Les fichiers versionnés sous `src/`, chemins absolus."""
    sortie = subprocess.run(
        ["git", "ls-files", "-z", PERIMETRE],
        cwd=RACINE,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [
        chemin
        for relatif in sortie.split("\0")
        if relatif
        and (chemin := RACINE / relatif).suffix.lower() not in BINAIRES
        # Un fichier indexé mais absent du répertoire de travail (suppression
        # non encore validée) ne doit pas faire tomber la garde sur une
        # FileNotFoundError : il n'a rien à dire.
        and chemin.is_file()
    ]


def _violations() -> tuple[list[str], int]:
    """(violations lisibles, nombre de fichiers réellement lus)."""
    violations: list[str] = []
    lus = 0
    for chemin in _fichiers_du_perimetre():
        try:
            texte = chemin.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        lus += 1
        for ligne_num, ligne in enumerate(texte.splitlines(), start=1):
            for quoi, motif in MOTIFS.items():
                trouve = motif.search(ligne)
                if trouve:
                    relatif = chemin.relative_to(RACINE)
                    violations.append(
                        f"{relatif}:{ligne_num} — {quoi} : « {trouve.group(0)} »"
                    )
    return violations, lus


def test_aucune_identite_reelle_dans_les_sources_livrees():
    violations, lus = _violations()
    assert violations == [], (
        "l'identité réelle d'une personne ou d'une entreprise sert de texte "
        f"d'exemple dans les sources livrées ({len(violations)} occurrences) :\n"
        + "\n".join(violations)
        + "\nRemplace par un exemple fictif et reconnaissable comme tel "
        "(Marie Exemple, 12 rue de l'Exemple, SIREN 123 456 789)."
    )


def test_le_balayage_a_bien_lu_le_perimetre():
    """Témoin de cardinalité (B-043) : un balayage à vide n'innocente personne.

    Le plancher n'est pas le seul garde-fou : les deux fichiers où le défaut
    vivait doivent figurer nommément dans l'ensemble lu, sinon un jour où
    `git ls-files` rend autre chose la garde deviendrait verte sans les avoir
    ouverts.
    """
    fichiers = _fichiers_du_perimetre()
    _, lus = _violations()

    assert lus >= 200, (
        f"seulement {lus} fichiers lus sous {PERIMETRE}/ : le balayage ne "
        "couvre plus le périmètre, il ne prouve donc plus rien"
    )

    relatifs = {str(chemin.relative_to(RACINE)) for chemin in fichiers}
    for temoin in (
        "src/frontend/src/components/settings/ProfileTab.tsx",
        "src/backend/app/services/user_profile.py",
    ):
        assert temoin in relatifs, (
            f"{temoin} n'est pas dans l'ensemble balayé alors que le défaut y "
            "vivait : la garde regarde ailleurs"
        )
