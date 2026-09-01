"""Un protocole qui cite un sélecteur inexistant conclut sans pouvoir se tromper.

01/09/2026. Les protocoles de test citent des `data-testid` que le testeur —
humain ou agent — est censé trouver à l'écran. Quand le sélecteur n'existe pas,
le scénario ne rougit pas : il conclut « pas de doublon » ou « zéro donnée
restante » quoi qu'il arrive. Le scénario RGPD constatait un effacement complet
sans que rien n'ait été supprimé.

Ce test ne prétend pas réparer les dix sélecteurs orphelins d'un coup : il
empêche la liste de grandir, et rend chaque retrait visible. Les protocoles de
`server/` sont exclus — ils visent THÉRÈSE Server, un autre dépôt.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
PROTOCOLES = RACINE / "tests" / "protocols"
FRONTEND = RACINE / "src" / "frontend" / "src"

# Dette connue au 01/09/2026. Chaque ligne retirée d'ici est un scénario qui
# redevient capable d'échouer. N'ajouter JAMAIS une entrée : la corriger.
ORPHELINS_CONNUS = {
    "confirm-delete-modal",
    "connection-lost",
    "crm-import-vcard-btn",
    "error-banner",
    "error-message",
    "import-progress",
    "invoice-create-btn",
    "llm-provider-select",
    "onboarding-step",
    "rgpd-delete-all-btn",
}

# Gabarits de nommage cités en exemple dans la convention, pas des sélecteurs.
GABARITS = re.compile(r"xxx|-$")


def _sources_frontend() -> str:
    morceaux = [
        f.read_text(encoding="utf-8", errors="replace")
        for f in FRONTEND.rglob("*")
        if f.is_file() and f.suffix in (".ts", ".tsx")
    ]
    assert len(morceaux) > 200, f"balayage a vide : {len(morceaux)} sources lues"
    return "\n".join(morceaux)


def _selecteurs_cites(dossier: Path) -> set[str]:
    trouves: set[str] = set()
    for f in dossier.rglob("*"):
        if not f.is_file() or f.suffix not in (".md", ".js", ".ts"):
            continue
        texte = f.read_text(encoding="utf-8", errors="replace")
        trouves |= set(re.findall(r"data-testid=[\"']([\w-]+)[\"']", texte))
        trouves |= set(re.findall(r"\[data-testid=[\"']?([\w-]+)", texte))
    return trouves


def _absents(ids: set[str], sources: str) -> set[str]:
    manquants = set()
    for identifiant in ids:
        if GABARITS.search(identifiant):
            continue
        if re.search(r"[\"'`]" + re.escape(identifiant) + r"[\"'`]", sources):
            continue
        # Un identifiant assemblé à l'exécution : `settings-tab-${tab.id}`.
        prefixe = identifiant.rsplit("-", 1)[0]
        if re.search(re.escape(prefixe) + r"-\$\{", sources):
            continue
        manquants.add(identifiant)
    return manquants


class TestLesProtocolesVisentDesElementsQuiExistent:
    def test_le_balayage_ne_tourne_pas_a_vide(self):
        cites = _selecteurs_cites(PROTOCOLES) - _selecteurs_cites(PROTOCOLES / "server")
        assert len(cites) > 30, (
            f"seulement {len(cites)} selecteurs lus dans les protocoles : "
            "le balayage ne mesure plus rien"
        )

    def test_aucun_selecteur_orphelin_nouveau(self):
        sources = _sources_frontend()
        cites = _selecteurs_cites(PROTOCOLES) - _selecteurs_cites(PROTOCOLES / "server")
        manquants = _absents(cites, sources)
        nouveaux = manquants - ORPHELINS_CONNUS
        assert not nouveaux, (
            f"{len(nouveaux)} selecteur(s) cite(s) par un protocole et absent(s) "
            f"du frontend : {sorted(nouveaux)}"
        )

    def test_la_dette_ne_contient_pas_de_selecteur_deja_repare(self):
        """Un orphelin réparé doit sortir de la liste, sinon elle ment."""
        sources = _sources_frontend()
        cites = _selecteurs_cites(PROTOCOLES) - _selecteurs_cites(PROTOCOLES / "server")
        manquants = _absents(cites, sources)
        perimes = ORPHELINS_CONNUS - manquants
        assert not perimes, (
            f"{len(perimes)} entree(s) de dette a retirer, le selecteur existe "
            f"desormais : {sorted(perimes)}"
        )
