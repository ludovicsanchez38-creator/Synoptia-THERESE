"""
THÉRÈSE v2 - Tests E2E Guided Prompts

Test des 3 actions et leurs sous-options.
"""

import pytest
from playwright.sync_api import Page, expect

from .conftest import take_screenshot


@pytest.mark.parametrize("action,suboptions", [
    ("Produire", ["Email pro", "Post LinkedIn", "Document Word", "Présentation PPT"]),
    ("Comprendre", ["Fichier Excel", "Document PDF", "Site web", "Marché"]),
    ("Organiser", ["Réunion", "Projet", "Semaine", "Objectifs"]),
])
def test_guided_action_displays_suboptions(page: Page, skip_onboarding, action, suboptions):
    """
    US-GUIDED-01: Chaque action affiche ses sous-options.
    """
    # Cliquer sur l'action
    page.click(f"button:has-text('{action}')")

    # Vérifier que les sous-options s'affichent
    for suboption in suboptions:
        expect(page.locator(f"text={suboption}")).to_be_visible(timeout=2000)

    take_screenshot(page, f"guided_{action.lower()}_suboptions")


def test_guided_back_navigation(page: Page, skip_onboarding):
    """
    US-GUIDED-02: Le bouton retour fonctionne correctement.
    """
    # Cliquer sur Produire
    page.click("button:has-text('Produire')")
    expect(page.locator("text=Email pro")).to_be_visible()

    # Retour
    page.click("button:has-text('Retour')")

    # Vérifier qu'on est revenu à la grille principale
    expect(page.locator("button:has-text('Produire')")).to_be_visible()
    expect(page.locator("button:has-text('Comprendre')")).to_be_visible()
    expect(page.locator("button:has-text('Organiser')")).to_be_visible()


def test_guided_prompt_template_structure(page: Page, skip_onboarding):
    """
    US-GUIDED-03: Les prompts templates sont correctement structurés.
    """
    # Email pro
    page.click("button:has-text('Produire')")
    page.click("button:has-text('Email pro')")

    textarea = page.locator("textarea")
    content = textarea.input_value()

    # Vérifier structure avec placeholders
    assert "email professionnel" in content.lower()
    assert "[" in content  # Placeholders entre crochets

    take_screenshot(page, "guided_prompt_template")


def test_guided_skills_trigger_prompt_panel(page: Page, skip_onboarding):
    """
    US-GUIDED-04: Les sous-options avec skills affichent le panel de prompt.
    """
    # Document Word (a un skill docx-pro)
    page.click("button:has-text('Produire')")
    page.click("button:has-text('Document Word')")

    # Vérifier que le SkillPromptPanel s'affiche
    expect(page.locator("text=Document Word")).to_be_visible(timeout=2000)
    expect(page.locator("textarea[placeholder='Décris ce que tu veux créer...']").first).to_be_visible()
    expect(page.locator("button:has-text('Générer')")).to_be_visible()

    take_screenshot(page, "guided_skill_prompt_panel")


def test_guided_images_trigger_prompt_panel(page: Page, skip_onboarding):
    """
    US-GUIDED-05: Les sous-options images affichent le panel de prompt.
    """
    # Image IA (GPT)
    page.click("button:has-text('Produire')")
    page.click("button:has-text('Image IA (GPT)')")

    # Vérifier que le SkillPromptPanel s'affiche
    expect(page.locator("text=Image IA (GPT)")).to_be_visible(timeout=2000)
    expect(page.locator("textarea[placeholder='Décris ce que tu veux créer...']").first).to_be_visible()
    expect(page.locator("button:has-text('Générer')")).to_be_visible()

    take_screenshot(page, "guided_image_prompt_panel")


def test_guided_animations_smooth(page: Page, skip_onboarding):
    """
    US-GUIDED-06: Les animations de transition sont fluides.
    """
    # Capturer avant transition
    take_screenshot(page, "guided_anim_01_grid")

    # Transition vers sous-options
    page.click("button:has-text('Produire')")
    page.wait_for_timeout(300)  # Attendre animation

    take_screenshot(page, "guided_anim_02_suboptions")

    # Transition retour
    page.click("button:has-text('Retour')")
    page.wait_for_timeout(300)

    take_screenshot(page, "guided_anim_03_back_to_grid")

    # Vérifier qu'il n'y a pas de flash/glitch
    # (visuel - à vérifier manuellement via screenshots)
