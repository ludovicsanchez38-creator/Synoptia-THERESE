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
        # Normaliser les fins de ligne : Windows rend « \r\n » et le fichier
        # commité porte « \n ». Comparer brut faisait échouer le gate sur une
        # plateforme et pas l'autre - même famille que l'encodage implicite
        # corrigé le 29/08. Un gate dont le résultat dépend de la machine n'en
        # est pas un.
        attendu = resultat.stdout.replace("\r\n", "\n")
        obtenu = INDEX.read_text(encoding="utf-8").replace("\r\n", "\n")
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


class TestLesAretesSontLaAussi:
    """
    Dr_logic-3D, #discussion du 29/08 :

      « à partir du moment où on nomme distinctement chaque élément graphique
        du frontend, je peux faire une représentation graphique des
        interactions, sous forme de graphe. La logique et l'ergonomie seront
        alors plus simples à appréhender. »

    Il ne demande pas de la documentation : il demande la MATIÈRE pour en
    produire lui-même. Les nœuds y étaient depuis la 0.55 ; les liens y sont
    maintenant, lus dans le code et non recopiés.
    """

    def test_les_liens_entre_surfaces_sont_generes(self):
        texte = INDEX.read_text(encoding="utf-8")
        assert "## Les liens entre surfaces" in texte
        # Chaque carte de conversation qui ouvre une vue doit figurer.
        for carte in (
            "MeetingConversationCard",
            "InvoiceConversationCard",
            "ContactsMemoryCard",
            "EmailConversationCard",
        ):
            assert carte in texte, f"arête manquante pour {carte}"

    def test_le_graphe_est_directement_lisible(self):
        """Un graphe Mermaid : il n'a rien à retranscrire à la main."""
        texte = INDEX.read_text(encoding="utf-8")
        assert "```mermaid" in texte and "graph LR" in texte
        assert '-->' in texte

    def test_une_arete_porte_le_nom_de_sa_destination(self):
        """Le libellé dérive de la table qui titre la vue : il ne peut pas mentir."""
        texte = INDEX.read_text(encoding="utf-8")
        assert "| Ouvrir Agenda |" in texte
        assert "| Ouvrir Devis et factures |" in texte
