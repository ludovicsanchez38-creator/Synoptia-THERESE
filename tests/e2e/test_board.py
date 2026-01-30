"""
THÉRÈSE v2 - Tests E2E Board de Décision

Test du board de conseil avec 5 advisors IA.
"""

import pytest
from playwright.sync_api import Page, expect

from .conftest import take_screenshot


def test_board_open_panel(page: Page, skip_onboarding):
    """
    US-BOARD-01: Ouvrir le Board panel avec Cmd+D.
    """
    # Ouvrir le Board avec raccourci
    page.keyboard.press("Meta+D")

    # Vérifier que le panel s'affiche
    expect(page.locator("text=Board de Décision").or_(page.locator("text=Conseil"))).to_be_visible(timeout=2000)
    take_screenshot(page, "board_panel_open")

    # Vérifier que les 5 conseillers sont affichés
    advisors = ["L'Analyste", "Le Stratège", "L'Avocat du Diable", "Le Pragmatique", "Le Visionnaire"]

    for advisor in advisors:
        expect(page.locator(f"text={advisor}")).to_be_visible()

    # Vérifier qu'il y a un champ de question
    question_field = page.locator("textarea[placeholder*='question']").or_(page.locator("textarea[placeholder*='décision']"))
    expect(question_field.first).to_be_visible()


def test_board_submit_decision(page: Page, skip_onboarding):
    """
    US-BOARD-02: Soumettre une question au board et recevoir les avis.
    """
    # Ouvrir le Board
    page.keyboard.press("Meta+D")
    expect(page.locator("text=Board de Décision").or_(page.locator("text=Conseil"))).to_be_visible(timeout=2000)

    # Saisir une question stratégique
    question_field = page.locator("textarea[placeholder*='question']").or_(page.locator("textarea[placeholder*='décision']")).first
    question_field.fill("Dois-je lancer mon produit maintenant ou attendre 3 mois pour avoir plus de fonctionnalités ?")

    # Optionnel: ajouter du contexte
    context_field = page.locator("textarea[placeholder*='contexte']")
    if context_field.is_visible():
        context_field.fill("Budget limité, 2 concurrents déjà sur le marché.")

    take_screenshot(page, "board_question_entered")

    # Soumettre
    submit_button = page.locator("button:has-text('Convoquer le Board')").or_(page.locator("button:has-text('Soumettre')"))
    submit_button.first.click()

    # Vérifier que la délibération démarre (spinner ou message "Délibération en cours")
    expect(page.locator("text=/Délibération|en cours/i")).to_be_visible(timeout=3000)
    take_screenshot(page, "board_deliberating")

    # Attendre les avis des 5 conseillers (peut prendre 30-60s selon les LLMs)
    # On vérifie que les cartes des advisors affichent des réponses
    expect(page.locator("text=/L'Analyste/i")).to_be_visible(timeout=60000)

    # Attendre la synthèse finale
    expect(page.locator("text=/Synthèse|Recommandation/i")).to_be_visible(timeout=70000)
    take_screenshot(page, "board_synthesis")


def test_board_view_synthesis(page: Page, skip_onboarding):
    """
    US-BOARD-03: Voir la synthèse après délibération.
    """
    # Ouvrir le Board et soumettre une question
    page.keyboard.press("Meta+D")
    expect(page.locator("text=Board de Décision").or_(page.locator("text=Conseil"))).to_be_visible(timeout=2000)

    question_field = page.locator("textarea[placeholder*='question']").or_(page.locator("textarea[placeholder*='décision']")).first
    question_field.fill("Quelle stack technique choisir : React ou Vue ?")

    submit_button = page.locator("button:has-text('Convoquer le Board')").or_(page.locator("button:has-text('Soumettre')"))
    submit_button.first.click()

    # Attendre la synthèse
    expect(page.locator("text=/Synthèse|Recommandation/i")).to_be_visible(timeout=70000)

    # Vérifier que la synthèse contient les éléments clés
    synthesis_section = page.locator("div:has-text('Synthèse')").or_(page.locator("div:has-text('Recommandation')")).first

    # Vérifier présence de sections : consensus, divergences, recommandation
    expect(page.locator("text=/Consensus|Points communs/i")).to_be_visible()
    expect(page.locator("text=/Divergences|Désaccords/i")).to_be_visible()
    expect(page.locator("text=/Recommandation|Décision/i")).to_be_visible()

    # Vérifier niveau de confiance (badge ou texte)
    expect(page.locator("text=/Confiance|Confidence/i")).to_be_visible()

    take_screenshot(page, "board_synthesis_detail")


def test_board_history(page: Page, skip_onboarding):
    """
    US-BOARD-04: Accéder à l'historique des décisions.
    """
    # Créer une décision d'abord
    page.keyboard.press("Meta+D")
    expect(page.locator("text=Board de Décision").or_(page.locator("text=Conseil"))).to_be_visible(timeout=2000)

    question_field = page.locator("textarea[placeholder*='question']").or_(page.locator("textarea[placeholder*='décision']")).first
    question_field.fill("Première décision de test historique.")

    submit_button = page.locator("button:has-text('Convoquer le Board')").or_(page.locator("button:has-text('Soumettre')"))
    submit_button.first.click()

    # Attendre la synthèse
    expect(page.locator("text=/Synthèse|Recommandation/i")).to_be_visible(timeout=70000)

    # Fermer le panel
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)

    # Rouvrir le Board
    page.keyboard.press("Meta+D")

    # Chercher un onglet "Historique" ou bouton pour voir les décisions passées
    history_tab = page.locator("button:has-text('Historique')").or_(page.locator("text=Historique"))
    if history_tab.is_visible():
        history_tab.first.click()

        # Vérifier que la décision précédente est listée
        expect(page.locator("text=Première décision de test historique")).to_be_visible(timeout=3000)

        take_screenshot(page, "board_history")
    else:
        # Si pas d'onglet historique, peut-être que les décisions sont listées directement
        # On vérifie qu'il y a une liste de décisions passées
        expect(page.locator("text=Première décision de test historique")).to_be_visible(timeout=3000)
