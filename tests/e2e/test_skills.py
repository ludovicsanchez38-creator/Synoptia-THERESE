"""
THÉRÈSE v2 - Tests E2E Skills

Test de la génération de documents Office (DOCX, PPTX, XLSX).
"""

from playwright.sync_api import Page, expect

from .conftest import take_screenshot


def test_skill_docx_generation(page: Page, skip_onboarding):
    """
    US-SKILL-01: Générer un document Word via le skill docx-pro.
    """
    # Naviguer vers "Produire" → "Document Word"
    page.click("button:has-text('Produire')")
    page.click("button:has-text('Document Word')")

    # Vérifier que le SkillPromptPanel s'affiche
    expect(page.locator("text=Document Word")).to_be_visible(timeout=2000)
    prompt_textarea = page.locator("textarea[placeholder='Décris ce que tu veux créer...']").first
    expect(prompt_textarea).to_be_visible()

    # Saisir un prompt
    prompt_textarea.fill("Un rapport de réunion avec 3 sections : ordre du jour, décisions, actions.")
    take_screenshot(page, "skill_docx_prompt")

    # Cliquer sur Générer
    page.click("button:has-text('Générer')")

    # Attendre l'état "generating" (spinner)
    expect(page.locator("text=Génération en cours...")).to_be_visible(timeout=2000)
    take_screenshot(page, "skill_docx_generating")

    # Attendre la génération (peut prendre 10-15s avec LLM)
    expect(page.locator("text=✅ Document généré")).to_be_visible(timeout=30000)
    take_screenshot(page, "skill_docx_success")

    # Vérifier que le bouton de téléchargement est visible
    expect(page.locator("button:has-text('Télécharger')")).to_be_visible()


def test_skill_pptx_generation(page: Page, skip_onboarding):
    """
    US-SKILL-02: Générer une présentation PowerPoint via le skill pptx-pro.
    """
    # Naviguer vers "Produire" → "Présentation PPT"
    page.click("button:has-text('Produire')")
    page.click("button:has-text('Présentation PPT')")

    # Vérifier le panel
    expect(page.locator("text=Présentation PPT")).to_be_visible(timeout=2000)
    prompt_textarea = page.locator("textarea[placeholder='Décris ce que tu veux créer...']").first
    expect(prompt_textarea).to_be_visible()

    # Saisir un prompt
    prompt_textarea.fill("Une présentation de pitch startup avec 5 slides : problème, solution, marché, équipe, roadmap.")

    # Générer
    page.click("button:has-text('Générer')")
    expect(page.locator("text=Génération en cours...")).to_be_visible(timeout=2000)

    # Attendre succès
    expect(page.locator("text=✅ Présentation générée")).to_be_visible(timeout=30000)
    expect(page.locator("button:has-text('Télécharger')")).to_be_visible()

    take_screenshot(page, "skill_pptx_success")


def test_skill_xlsx_generation(page: Page, skip_onboarding):
    """
    US-SKILL-03: Générer un tableur Excel via le skill xlsx-pro.
    """
    # Naviguer vers "Produire" → "Tableur Excel"
    page.click("button:has-text('Produire')")
    page.click("button:has-text('Tableur Excel')")

    # Vérifier le panel
    expect(page.locator("text=Tableur Excel")).to_be_visible(timeout=2000)
    prompt_textarea = page.locator("textarea[placeholder='Décris ce que tu veux créer...']").first
    expect(prompt_textarea).to_be_visible()

    # Saisir un prompt
    prompt_textarea.fill("Un budget mensuel avec 3 colonnes : catégorie, budget prévu, dépensé. Ajoute un graphique en barre.")

    # Générer
    page.click("button:has-text('Générer')")
    expect(page.locator("text=Génération en cours...")).to_be_visible(timeout=2000)

    # Attendre succès
    expect(page.locator("text=✅ Tableur généré")).to_be_visible(timeout=30000)
    expect(page.locator("button:has-text('Télécharger')")).to_be_visible()

    take_screenshot(page, "skill_xlsx_success")


def test_skill_download(page: Page, skip_onboarding):
    """
    US-SKILL-04: Télécharger un document généré.
    """
    # Générer un document simple
    page.click("button:has-text('Produire')")
    page.click("button:has-text('Document Word')")

    prompt_textarea = page.locator("textarea[placeholder='Décris ce que tu veux créer...']").first
    prompt_textarea.fill("Un contrat de prestation simple.")

    page.click("button:has-text('Générer')")
    expect(page.locator("text=✅ Document généré")).to_be_visible(timeout=30000)

    # Vérifier que le bouton télécharger fonctionne (déclenche un download)
    download_button = page.locator("button:has-text('Télécharger')")
    expect(download_button).to_be_visible()

    # Note: Tester le téléchargement réel nécessite des APIs Playwright spéciales
    # Pour l'instant on vérifie juste que le bouton est cliquable
    expect(download_button).to_be_enabled()


def test_skill_error_handling(page: Page, skip_onboarding):
    """
    US-SKILL-05: Gestion des erreurs de génération.
    """
    # Générer avec un prompt vide (devrait échouer ou afficher un message)
    page.click("button:has-text('Produire')")
    page.click("button:has-text('Document Word')")

    prompt_textarea = page.locator("textarea[placeholder='Décris ce que tu veux créer...']").first
    prompt_textarea.fill("")

    # Le bouton Générer devrait être disabled si prompt vide
    generate_button = page.locator("button:has-text('Générer')")

    # Si le bouton est enabled, on vérifie qu'un message d'erreur s'affiche après click
    if generate_button.is_enabled():
        page.click("button:has-text('Générer')")
        # Attendre un message d'erreur
        expect(page.locator("text=/erreur|échec/i")).to_be_visible(timeout=5000)


def test_skill_prompt_panel_navigation(page: Page, skip_onboarding):
    """
    US-SKILL-06: Navigation du SkillPromptPanel (fermer, réessayer).
    """
    # Ouvrir un skill
    page.click("button:has-text('Produire')")
    page.click("button:has-text('Document Word')")

    expect(page.locator("text=Document Word")).to_be_visible(timeout=2000)

    # Fermer le panel (il devrait y avoir un bouton close ou Escape)
    page.keyboard.press("Escape")

    # Vérifier que le panel se ferme et qu'on revient à la vue principale
    expect(page.locator("text=Comment puis-je t'aider ?")).to_be_visible(timeout=2000)
