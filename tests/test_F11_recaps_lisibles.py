"""
Tests de régression - F-11 : Récaps LLM lisibles
Vérifie que convert_markdown_tables_to_bullets convertit correctement
les tableaux Markdown en listes à puces sans toucher au reste du texte.
"""

import pytest
from app.services.llm import convert_markdown_tables_to_bullets


class TestConvertMarkdownTablesToBullets:
    """Tests de la fonction de post-processing F-11."""

    def test_tableau_simple_avec_en_tetes(self) -> None:
        """Un tableau avec en-tête → liste à puces clé:valeur."""
        tableau = (
            "| Sujet | Action | Date |\n"
            "|-------|--------|------|\n"
            "| Projet X | Livraison | 15 mars |\n"
            "| Client Y | Réunion | 20 mars |"
        )
        result = convert_markdown_tables_to_bullets(tableau)
        assert "| Sujet |" not in result
        assert "---" not in result
        assert "- Sujet : Projet X | Action : Livraison | Date : 15 mars" in result
        assert "- Sujet : Client Y | Action : Réunion | Date : 20 mars" in result

    def test_texte_mixte_preservé(self) -> None:
        """Le texte autour du tableau est préservé intact."""
        texte = (
            "Voici le récap de notre échange :\n\n"
            "| Point | Valeur |\n"
            "|-------|--------|\n"
            "| Budget | 50 000€ |\n"
            "| Délai | 6 mois |\n\n"
            "Bonne continuation !"
        )
        result = convert_markdown_tables_to_bullets(texte)
        assert "Voici le récap de notre échange :" in result
        assert "Bonne continuation !" in result
        assert "| Point |" not in result
        assert "- Point : Budget | Valeur : 50 000€" in result

    def test_texte_sans_tableau_inchangé(self) -> None:
        """Un texte sans tableau reste identique."""
        texte = "Voici ma réponse.\n- Point 1\n- Point 2"
        result = convert_markdown_tables_to_bullets(texte)
        assert result == texte

    def test_tableau_une_colonne(self) -> None:
        """Tableau à une seule colonne → liste simple."""
        tableau = (
            "| Item |\n"
            "|------|\n"
            "| Alpha |\n"
            "| Beta |"
        )
        result = convert_markdown_tables_to_bullets(tableau)
        assert "- Alpha" in result or "Alpha" in result
        assert "---" not in result

    def test_tableau_sans_separateur(self) -> None:
        """Tableau sans ligne séparatrice → données converties sans en-têtes."""
        tableau = (
            "| Val1 | Val2 |\n"
            "| Val3 | Val4 |"
        )
        result = convert_markdown_tables_to_bullets(tableau)
        assert "---" not in result
        assert "|" not in result.replace("- Val1, Val2", "").replace("- Val3, Val4", "")

    def test_texte_vide(self) -> None:
        """Texte vide → retourne vide."""
        result = convert_markdown_tables_to_bullets("")
        assert result == ""

    def test_multiples_tableaux(self) -> None:
        """Plusieurs tableaux dans le même texte sont tous convertis."""
        texte = (
            "Premier tableau :\n"
            "| A | B |\n"
            "|---|---|\n"
            "| 1 | 2 |\n\n"
            "Second tableau :\n"
            "| C | D |\n"
            "|---|---|\n"
            "| 3 | 4 |"
        )
        result = convert_markdown_tables_to_bullets(texte)
        assert "| A |" not in result
        assert "| C |" not in result
        assert "---" not in result
        assert "Premier tableau :" in result
        assert "Second tableau :" in result
