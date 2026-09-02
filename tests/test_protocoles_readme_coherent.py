"""B-075 : le tableau du README des protocoles compte ce que les fiches contiennent.

Le relevé de la boucle annonçait « S1 annonce 35, en contient 42 ». La lecture
des fiches montre autre chose, et c'est le vrai défaut : S1 a bien 35 étapes
NUMÉROTÉES, plus 7 étapes de complément (MT-1..4, CH-1..2, TP-1) que le README
ne mentionne nulle part. Idem pour S2 (38 + 8 : RBAC, VIS, PER). Les quinze
étapes de complément - isolation multi-tenant, séparation des privilèges,
persistance - sont exactement celles qu'on oublie de lancer quand rien ne les
compte.

Deuxième chiffre, deuxième défaut : la colonne « Duree Chrome MCP » du README
et la ligne « Durée estimée » des fiches mesurent DEUX choses différentes (une
campagne pilotée par un agent, une exécution à la main), et une seule fiche sur
six - S3 - déclare la première. Comparées sous un même nom, elles semblaient se
contredire d'un facteur 3 à 5.

Trois copies du même chiffre vivent dans ce seul README : l'arborescence, le
tableau, et la ligne TOTAL. Ce test les tient toutes les trois sur les fiches.
"""
import re
import unicodedata
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent / "protocols"
README = RACINE / "README.md"

# Trois ou quatre dièses : S3 emploie `#### Etape`, les cinq autres `### Étape`.
_ETAPE_NUMEROTEE = re.compile(r"^#{3,4}\s+Etape\s+\d+\b")
_ETAPE_COMPLEMENT = re.compile(r"^#{3,4}\s+Etape\s+[A-Z]{2,}-\d+\b")
_MINUTES = re.compile(r"(\d+)\s*[-–]\s*(\d+)\s*(?:min|minutes)\b")


def _sans_accents(texte: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texte)
        if unicodedata.category(c) != "Mn"
    )


def _fiches() -> dict[str, Path]:
    return {
        chemin.name.split("-", 1)[0]: chemin
        for chemin in sorted(RACINE.glob("*/personas/*.md"))
    }


def _compter(chemin: Path) -> tuple[int, int]:
    """(étapes numérotées, étapes de complément) d'une fiche."""
    numerotees = complements = 0
    for ligne in _sans_accents(chemin.read_text(encoding="utf-8")).splitlines():
        if _ETAPE_NUMEROTEE.match(ligne):
            numerotees += 1
        elif _ETAPE_COMPLEMENT.match(ligne):
            complements += 1
    return numerotees, complements


def _duree_declaree(chemin: Path) -> tuple[int, int] | None:
    """La durée d'exécution À LA MAIN déclarée par la fiche, en minutes."""
    texte = _sans_accents(chemin.read_text(encoding="utf-8"))
    for ligne in texte.splitlines():
        nu = ligne.strip()
        if nu.startswith("| Duree estimee") or nu.startswith("- Parcours complet"):
            trouve = _MINUTES.search(nu)
            if trouve:
                return int(trouve.group(1)), int(trouve.group(2))
    return None


def _tableau_du_readme() -> tuple[list[str], dict[str, dict[str, str]]]:
    """En-têtes + lignes du tableau « Personas », indexées par code persona."""
    lignes = README.read_text(encoding="utf-8").splitlines()
    debut = next(
        i for i, ligne in enumerate(lignes)
        if ligne.startswith("|") and "Persona" in ligne and "Produit" in ligne
    )
    entetes = [c.strip() for c in lignes[debut].strip("|").split("|")]
    rangs: dict[str, dict[str, str]] = {}
    for ligne in lignes[debut + 2:]:
        if not ligne.startswith("|"):
            break
        cellules = [c.strip() for c in ligne.strip("|").split("|")]
        cle = cellules[0].replace("*", "").strip().split()[0]
        rangs[cle] = dict(zip(entetes, cellules, strict=False))
    return entetes, rangs


def _cellule(rangs: dict, code: str, colonne: str) -> str:
    """La cellule d'une ligne, avec un message quand la colonne manque."""
    assert code in rangs, f"persona {code} absent du tableau du README"
    rang = rangs[code]
    assert colonne in rang, (
        f"{code} : colonne « {colonne} » absente du tableau du README "
        f"(colonnes présentes : {sorted(rang)})"
    )
    return rang[colonne]


def _entier(cellule: str) -> int:
    """Un entier de cellule Markdown : gras, tilde et tiret d'absence tolérés."""
    nu = cellule.replace("*", "").replace("~", "").strip()
    return 0 if nu in {"", "-", "—"} else int(nu)


@pytest.fixture(scope="module")
def tableau():
    return _tableau_du_readme()


def test_le_tableau_nomme_ce_qu_il_compte(tableau):
    """Une colonne sans nom exact est un chiffre qu'on ne peut pas vérifier."""
    entetes, _ = tableau
    for attendue in ("Etapes", "Complements", "Duree fiche"):
        assert any(_sans_accents(e).startswith(attendue) for e in entetes), (
            f"colonne « {attendue} » absente du tableau du README : "
            f"colonnes présentes = {entetes}"
        )


@pytest.mark.parametrize("code", sorted(_fiches()))
def test_le_readme_compte_ce_que_la_fiche_contient(code, tableau):
    entetes, rangs = tableau
    numerotees, complements = _compter(_fiches()[code])
    annonce_etapes = _cellule(rangs, code, "Etapes")
    annonce_complements = _cellule(rangs, code, "Complements")

    assert _entier(annonce_etapes) == numerotees, (
        f"{code} : le README annonce {annonce_etapes} étapes numérotées, la "
        f"fiche en contient {numerotees}"
    )
    assert _entier(annonce_complements) == complements, (
        f"{code} : le README annonce {annonce_complements} étapes de "
        f"complément, la fiche en contient {complements} - ce sont celles "
        "qu'on oublie de lancer quand rien ne les compte"
    )


@pytest.mark.parametrize("code", sorted(_fiches()))
def test_la_duree_du_readme_est_celle_de_la_fiche(code, tableau):
    """La colonne des durées cite la fiche, ou dit franchement qu'il n'y en a pas."""
    _entetes, rangs = tableau
    declaree = _duree_declaree(_fiches()[code])
    cellule = _sans_accents(_cellule(rangs, code, "Duree fiche")).strip()

    if declaree is None:
        assert cellule.lower().startswith("non renseignee"), (
            f"{code} : sa fiche ne déclare aucune durée, le README en affiche "
            f"pourtant « {cellule} »"
        )
        return

    trouve = _MINUTES.search(cellule)
    assert trouve, f"{code} : durée du README illisible en minutes « {cellule} »"
    assert (int(trouve.group(1)), int(trouve.group(2))) == declaree, (
        f"{code} : le README annonce {cellule}, la fiche déclare "
        f"{declaree[0]}-{declaree[1]} minutes"
    )


def test_la_ligne_total_est_la_somme_des_fiches(tableau):
    _entetes, rangs = tableau
    assert "TOTAL" in rangs, "le tableau du README n'a plus de ligne TOTAL"
    comptes = [_compter(chemin) for chemin in _fiches().values()]

    assert _entier(_cellule(rangs, "TOTAL", "Etapes")) == sum(n for n, _ in comptes)
    assert _entier(_cellule(rangs, "TOTAL", "Complements")) == sum(
        c for _, c in comptes
    )


def test_l_arborescence_annonce_les_memes_chiffres():
    """Troisième copie du chiffre, dans le MÊME fichier : le bloc d'archi."""
    texte = _sans_accents(README.read_text(encoding="utf-8"))
    for code, chemin in _fiches().items():
        numerotees, _complements = _compter(chemin)
        motif = re.compile(
            rf"{re.escape(chemin.name.replace('é', 'e'))}.*?\((\d+) etapes",
            re.DOTALL,
        )
        trouve = motif.search(texte)
        assert trouve, f"{code} : l'arborescence du README ne cite plus sa fiche"
        assert int(trouve.group(1)) == numerotees, (
            f"{code} : l'arborescence du README annonce {trouve.group(1)} "
            f"étapes, la fiche en contient {numerotees}"
        )
