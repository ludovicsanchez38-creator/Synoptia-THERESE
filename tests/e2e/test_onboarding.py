"""
THÉRÈSE v2 - Tests E2E Onboarding

Test du wizard d'onboarding complet (6 étapes).
"""

import pytest
from playwright.sync_api import Page, expect

from .conftest import take_screenshot


def test_onboarding_wizard_complete_flow(page: Page):
    """
    US-ONBOARDING-01: Le wizard d'onboarding se lance au premier démarrage
    et guide l'utilisateur à travers les 6 étapes.
    """
    # Vérifier que le wizard s'affiche
    expect(page.locator("text=Bienvenue dans THÉRÈSE")).to_be_visible(timeout=5000)
    take_screenshot(page, "onboarding_01_welcome")

    # Étape 1: Welcome
    expect(page.locator("text=Ta mémoire, tes données, ton business")).to_be_visible()
    page.click("button:has-text('Commencer')")

    # Étape 2: Profil utilisateur
    expect(page.locator("text=Parle-moi de toi")).to_be_visible(timeout=2000)
    take_screenshot(page, "onboarding_02_profile")

    page.fill("input[placeholder*='Ludovic']", "Test User")
    page.fill("input[placeholder*='Ludo']", "TestU")
    page.fill("input[placeholder*='Synoptïa']", "Test Corp")
    page.fill("input[placeholder*='Fondateur']", "Testeur")

    page.click("button:has-text('Continuer')")

    # Étape 3: Configuration LLM
    expect(page.locator("text=Choisis ton modèle IA")).to_be_visible(timeout=2000)
    take_screenshot(page, "onboarding_03_llm")

    # Sélectionner Anthropic (recommandé)
    page.click("button:has-text('Anthropic')")

    # Remplir clé API (fictive pour test)
    page.fill("input[type='password']", "sk-ant-test-key-12345")

    page.click("button:has-text('Continuer')")

    # Étape 4: Sécurité
    expect(page.locator("text=Sécurité & Confidentialité")).to_be_visible(timeout=2000)
    take_screenshot(page, "onboarding_04_security")

    # Lire et accepter
    page.scroll_into_view_if_needed("input[type='checkbox']")
    page.click("input[type='checkbox']")

    page.click("button:has-text('Continuer')")

    # Étape 5: Dossier de travail
    expect(page.locator("text=Dossier de travail")).to_be_visible(timeout=2000)
    take_screenshot(page, "onboarding_05_working_dir")

    # Passer cette étape (optionnelle)
    page.click("button:has-text('Passer')")

    # Étape 6: Terminé
    expect(page.locator("text=Tu es prêt")).to_be_visible(timeout=2000)
    take_screenshot(page, "onboarding_06_complete")

    # Vérifier résumé configuration
    expect(page.locator("text=Test User")).to_be_visible()
    expect(page.locator("text=Anthropic")).to_be_visible()

    page.click("button:has-text('Commencer')")

    # Vérifier qu'on arrive sur l'écran principal
    expect(page.locator("text=Comment puis-je t'aider ?")).to_be_visible(timeout=5000)
    take_screenshot(page, "onboarding_07_main_screen")


def test_onboarding_validation_profile_required(page: Page):
    """
    US-ONBOARDING-02: Les champs obligatoires du profil sont validés.
    """
    # Welcome
    page.click("button:has-text('Commencer')")

    # Profil - essayer de continuer sans remplir
    page.click("button:has-text('Continuer')")

    # Vérifier qu'on reste sur la même page (validation échoue)
    expect(page.locator("text=Parle-moi de toi")).to_be_visible()

    # Remplir uniquement le nom
    page.fill("input[placeholder*='Ludovic']", "Test")
    page.click("button:has-text('Continuer')")

    # Doit passer à l'étape suivante maintenant
    expect(page.locator("text=Choisis ton modèle IA")).to_be_visible(timeout=2000)


def test_onboarding_llm_validation(page: Page):
    """
    US-ONBOARDING-03: La clé API LLM est validée (format).
    """
    # Skip welcome + profile
    page.click("button:has-text('Commencer')")
    page.fill("input[placeholder*='Ludovic']", "Test")
    page.click("button:has-text('Continuer')")

    # LLM config
    page.click("button:has-text('Anthropic')")

    # Essayer avec une clé invalide
    page.fill("input[type='password']", "invalid-key")

    # Vérifier warning visible
    expect(page.locator("text=commence par sk-ant-")).to_be_visible(timeout=1000)
    take_screenshot(page, "onboarding_llm_validation_error")

    # Bouton Continuer doit être désactivé
    button = page.locator("button:has-text('Continuer')")
    expect(button).to_be_disabled()

    # Corriger avec une bonne clé
    page.fill("input[type='password']", "sk-ant-valid-key-123")

    # Bouton doit être activé
    expect(button).to_be_enabled(timeout=1000)


def test_onboarding_security_acknowledgement_required(page: Page):
    """
    US-ONBOARDING-04: L'acknowledgement sécurité est obligatoire.
    """
    # Skip welcome + profile + llm
    page.click("button:has-text('Commencer')")
    page.fill("input[placeholder*='Ludovic']", "Test")
    page.click("button:has-text('Continuer')")
    page.click("button:has-text('Anthropic')")
    page.fill("input[type='password']", "sk-ant-test")
    page.click("button:has-text('Continuer')")

    # Security step
    # Essayer de continuer sans cocher
    button = page.locator("button:has-text('Continuer')")
    expect(button).to_be_disabled()

    # Cocher la case
    page.click("input[type='checkbox']")

    # Bouton doit être activé
    expect(button).to_be_enabled(timeout=1000)


def test_onboarding_navigation_back(page: Page):
    """
    US-ONBOARDING-05: On peut revenir en arrière dans le wizard.
    """
    # Avancer jusqu'à l'étape 3
    page.click("button:has-text('Commencer')")
    page.fill("input[placeholder*='Ludovic']", "Test")
    page.click("button:has-text('Continuer')")

    # On est à l'étape LLM
    expect(page.locator("text=Choisis ton modèle IA")).to_be_visible()

    # Cliquer sur Étape 1 dans le stepper
    page.click("button:has-text('Bienvenue')")

    # Vérifier qu'on est revenu à l'étape 1
    expect(page.locator("text=Ta mémoire, tes données, ton business")).to_be_visible()
