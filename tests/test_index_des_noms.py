"""
L'index des noms est GÉNÉRÉ, et il est à jour.

Demandé par Dr_logic-3D : « un document de travail qui nomme tous les
composants graphiques de l'IHM, de manière distincte et explicite », pour
pouvoir citer une surface dans un signalement de bug.

Katia en avait produit un à la main. Il a vieilli en dix jours : le chantier
nommage a renommé des surfaces qu'il décrivait encore sous leur ancien nom.
D'où la règle appliquée ici - un index qu'un humain doit se souvenir de mettre
à jour est un mensonge en attente.

Ce test régénère l'index et le compare au fichier commité. S'ils diffèrent,
c'est qu'un nom a changé dans l'application sans que l'index suive : le
message dit quoi lancer.
"""

import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).parent.parent
INDEX = RACINE / "docs" / "INDEX-DES-NOMS.md"
GENERATEUR = RACINE / "scripts" / "index-des-noms.mjs"


class TestLIndexNeDerivePas:
    def test_le_generateur_existe_et_tourne(self):
        assert GENERATEUR.exists()
        resultat = subprocess.run(
            ["node", str(GENERATEUR)], capture_output=True, text=True, cwd=RACINE
        )
        assert resultat.returncode == 0, resultat.stderr
        assert "Index des noms" in resultat.stdout

    def test_le_fichier_commite_est_celui_que_le_code_produit(self):
        resultat = subprocess.run(
            ["node", str(GENERATEUR)], capture_output=True, text=True, cwd=RACINE
        )
        attendu = resultat.stdout
        obtenu = INDEX.read_text(encoding="utf-8")
        assert obtenu == attendu, (
            "l'index a dérivé du code. Régénérer :\n"
            "  node scripts/index-des-noms.mjs > docs/INDEX-DES-NOMS.md"
        )

    @pytest.mark.parametrize(
        "surface",
        ["Agenda", "Contacts", "Devis et factures", "Décision", "Améliorer THÉRÈSE"],
    )
    def test_les_surfaces_que_les_testeurs_citent_y_figurent(self, surface):
        assert surface in INDEX.read_text(encoding="utf-8")

    def test_le_protocole_de_citation_est_dans_le_document(self):
        """Le vocabulaire ne sert que si on dit comment s'en servir."""
        texte = INDEX.read_text(encoding="utf-8")
        assert "le texte visible à l'écran" in texte
        assert "deux contrôles portent le même texte" in texte
