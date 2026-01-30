"""
THÉRÈSE v2 - Tests E2E Images

Test de la génération d'images IA (GPT Image 1.5 et Gemini Nano Banana Pro).
"""

import pytest
from playwright.sync_api import Page, expect

from .conftest import take_screenshot


def test_image_generation_openai(page: Page, skip_onboarding):
    """
    US-IMAGE-01: Générer une image avec GPT Image 1.5 (OpenAI).
    """
    # Naviguer vers "Produire" → "Image IA (GPT)"
    page.click("button:has-text('Produire')")
    page.click("button:has-text('Image IA (GPT)')")

    # Vérifier que le SkillPromptPanel s'affiche
    expect(page.locator("text=Image IA (GPT)")).to_be_visible(timeout=2000)
    prompt_textarea = page.locator("textarea[placeholder='Décris ce que tu veux créer...']").first
    expect(prompt_textarea).to_be_visible()

    # Saisir un prompt
    prompt_textarea.fill("Un paysage de montagne au coucher du soleil, style aquarelle.")
    take_screenshot(page, "image_gpt_prompt")

    # Cliquer sur Générer
    page.click("button:has-text('Générer')")

    # Attendre l'état "generating"
    expect(page.locator("text=Génération en cours...")).to_be_visible(timeout=2000)
    take_screenshot(page, "image_gpt_generating")

    # Attendre la génération (peut prendre 10-20s)
    expect(page.locator("text=✅ Image générée")).to_be_visible(timeout=30000)
    take_screenshot(page, "image_gpt_success")

    # Vérifier que l'image est affichée (il devrait y avoir un <img>)
    expect(page.locator("img[alt*='Générée']")).to_be_visible(timeout=5000)

    # Vérifier que le bouton de téléchargement est visible
    expect(page.locator("button:has-text('Télécharger')")).to_be_visible()


def test_image_generation_gemini(page: Page, skip_onboarding):
    """
    US-IMAGE-02: Générer une image avec Gemini Nano Banana Pro.
    """
    # Naviguer vers "Produire" → "Image IA (Gemini)"
    page.click("button:has-text('Produire')")

    # Le texte exact peut varier, cherchons "Gemini"
    expect(page.locator("button:has-text('Image IA (Gemini)')")).to_be_visible(timeout=2000)
    page.click("button:has-text('Image IA (Gemini)')")

    # Vérifier le panel
    expect(page.locator("text=Image IA (Gemini)")).to_be_visible(timeout=2000)
    prompt_textarea = page.locator("textarea[placeholder='Décris ce que tu veux créer...']").first
    expect(prompt_textarea).to_be_visible()

    # Saisir un prompt
    prompt_textarea.fill("Un chat robot futuriste, style cyberpunk, néons bleus et roses.")

    # Générer
    page.click("button:has-text('Générer')")
    expect(page.locator("text=Génération en cours...")).to_be_visible(timeout=2000)

    # Attendre succès
    expect(page.locator("text=✅ Image générée")).to_be_visible(timeout=30000)

    # Vérifier image affichée
    expect(page.locator("img[alt*='Générée']")).to_be_visible(timeout=5000)

    take_screenshot(page, "image_gemini_success")


def test_image_download(page: Page, skip_onboarding):
    """
    US-IMAGE-03: Télécharger une image générée.
    """
    # Générer une image simple
    page.click("button:has-text('Produire')")
    page.click("button:has-text('Image IA (GPT)')")

    prompt_textarea = page.locator("textarea[placeholder='Décris ce que tu veux créer...']").first
    prompt_textarea.fill("Un logo minimaliste.")

    page.click("button:has-text('Générer')")
    expect(page.locator("text=✅ Image générée")).to_be_visible(timeout=30000)

    # Vérifier que le bouton télécharger est présent et enabled
    download_button = page.locator("button:has-text('Télécharger')")
    expect(download_button).to_be_visible()
    expect(download_button).to_be_enabled()


def test_image_error_no_api_key(page: Page, skip_onboarding):
    """
    US-IMAGE-04: Gestion erreur si clé API manquante.

    Note: Ce test suppose qu'aucune clé API image n'est configurée dans le sandbox.
    Si une clé est configurée, le test échouera (ce qui est normal).
    """
    # Essayer de générer une image sans clé API configurée
    page.click("button:has-text('Produire')")
    page.click("button:has-text('Image IA (GPT)')")

    prompt_textarea = page.locator("textarea[placeholder='Décris ce que tu veux créer...']").first
    prompt_textarea.fill("Un test d'erreur.")

    page.click("button:has-text('Générer')")

    # Attendre un message d'erreur lié à la clé API
    # Le texte peut être "Clé API manquante", "Authentication failed", etc.
    expect(page.locator("text=/clé API|API key|authentication/i")).to_be_visible(timeout=10000)
    take_screenshot(page, "image_error_no_key")


def test_image_multiple_in_conversation(page: Page, skip_onboarding):
    """
    US-IMAGE-05: Générer plusieurs images dans la même conversation.
    """
    # Générer une première image
    page.click("button:has-text('Produire')")
    page.click("button:has-text('Image IA (GPT)')")

    prompt_textarea = page.locator("textarea[placeholder='Décris ce que tu veux créer...']").first
    prompt_textarea.fill("Premier test image.")

    page.click("button:has-text('Générer')")
    expect(page.locator("text=✅ Image générée")).to_be_visible(timeout=30000)

    # Fermer le panel
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)

    # Générer une deuxième image
    page.click("button:has-text('Produire')")
    page.click("button:has-text('Image IA (GPT)')")

    prompt_textarea = page.locator("textarea[placeholder='Décris ce que tu veux créer...']").first
    prompt_textarea.fill("Deuxième test image.")

    page.click("button:has-text('Générer')")
    expect(page.locator("text=✅ Image générée")).to_be_visible(timeout=30000)

    # Vérifier qu'il y a bien 2 images dans la page
    images = page.locator("img[alt*='Générée']")
    expect(images).to_have_count(2, timeout=5000)


def test_image_prompt_panel(page: Page, skip_onboarding):
    """
    US-IMAGE-06: Le SkillPromptPanel fonctionne correctement pour les images.
    """
    # Ouvrir le panel image
    page.click("button:has-text('Produire')")
    page.click("button:has-text('Image IA (GPT)')")

    # Vérifier structure du panel
    expect(page.locator("text=Image IA (GPT)")).to_be_visible()
    expect(page.locator("textarea[placeholder='Décris ce que tu veux créer...']").first).to_be_visible()
    expect(page.locator("button:has-text('Générer')")).to_be_visible()

    # Fermer avec Escape
    page.keyboard.press("Escape")

    # Vérifier que le panel se ferme
    expect(page.locator("text=Image IA (GPT)")).to_be_hidden(timeout=2000)
    expect(page.locator("text=Comment puis-je t'aider ?")).to_be_visible()

    take_screenshot(page, "image_panel_closed")
