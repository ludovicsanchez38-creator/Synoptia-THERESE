"""
Tests E2E - Parametres (Settings Modal).

Couverture du modal Parametres : ouverture, profil, cles API, LLM,
recherche web, dossier de travail, presets MCP, accessibilite, performance.
"""

from playwright.sync_api import Page, expect

from .conftest import take_screenshot

# ============================================================
# P0 - Critiques
# ============================================================


def test_settings_open_modal(page: Page, skip_onboarding):
    """
    P0 - Ouvre les parametres via le bouton header,
    verifie que le modal s'affiche avec ses onglets.
    """
    # Cliquer sur le bouton Parametres dans le header
    settings_btn = page.locator("button[title='Paramètres']")
    expect(settings_btn).to_be_visible(timeout=5000)
    settings_btn.click()

    # Le modal doit s'afficher avec le titre "Parametres"
    expect(page.get_by_text("Paramètres", exact=True).first).to_be_visible(timeout=3000)
    take_screenshot(page, "settings_modal_open")

    # Verifier que les onglets principaux sont visibles
    expect(page.get_by_text("Profil")).to_be_visible()
    expect(page.get_by_text("LLM")).to_be_visible()
    expect(page.get_by_text("Tools")).to_be_visible()
    expect(page.get_by_text("Données")).to_be_visible()
    expect(page.get_by_text("A11Y")).to_be_visible()
    expect(page.get_by_text("Perf")).to_be_visible()
    expect(page.get_by_text("Limites")).to_be_visible()

    # Fermer le modal
    page.get_by_role("button", name="Fermer").click()

    # Le modal doit disparaitre
    expect(page.get_by_text("Paramètres", exact=True).first).not_to_be_visible(timeout=2000)


def test_settings_profile_crud(page: Page, skip_onboarding):
    """
    P0 - Remplit le profil (nom, entreprise), sauvegarde,
    recharge la page et verifie que les donnees persistent.
    """
    # Ouvrir les parametres
    page.locator("button[title='Paramètres']").click()
    expect(page.get_by_text("Paramètres", exact=True).first).to_be_visible(timeout=3000)

    # On est sur l'onglet Profil par defaut
    expect(page.get_by_text("Ton profil")).to_be_visible(timeout=2000)

    # Remplir le formulaire de profil
    name_input = page.locator("input[placeholder='Ludovic Sanchez']")
    expect(name_input).to_be_visible(timeout=2000)
    name_input.fill("E2E Testeur")

    company_input = page.locator("input[placeholder*='Synoptïa']")
    company_input.fill("E2E Corp")

    take_screenshot(page, "settings_profile_filled")

    # Sauvegarder via le bouton Enregistrer
    save_btn = page.get_by_role("button", name="Enregistrer")
    expect(save_btn).to_be_enabled()
    save_btn.click()

    # Attendre la confirmation visuelle (badge vert "Profil configure")
    page.wait_for_timeout(1500)

    # Fermer le modal
    page.get_by_role("button", name="Fermer").click()

    # Recharger la page
    page.reload()
    page.wait_for_load_state("networkidle")

    # Rouvrir les parametres
    page.locator("button[title='Paramètres']").click()
    expect(page.get_by_text("Paramètres", exact=True).first).to_be_visible(timeout=3000)

    # Verifier que les valeurs ont persiste
    name_input = page.locator("input[placeholder='Ludovic Sanchez']")
    expect(name_input).to_have_value("E2E Testeur", timeout=3000)

    company_input = page.locator("input[placeholder*='Synoptïa']")
    expect(company_input).to_have_value("E2E Corp")

    # Verifier le badge "Profil configure"
    expect(page.get_by_text("Profil configuré")).to_be_visible()
    take_screenshot(page, "settings_profile_persisted")


def test_settings_api_key_save(page: Page, skip_onboarding):
    """
    P0 - Entre une fausse cle Anthropic (sk-ant-test123),
    sauvegarde, verifie le badge 'Cle API configuree'.
    """
    # Ouvrir les parametres
    page.locator("button[title='Paramètres']").click()
    expect(page.get_by_text("Paramètres", exact=True).first).to_be_visible(timeout=3000)

    # Naviguer vers l'onglet LLM
    page.get_by_text("LLM").click()
    page.wait_for_timeout(500)

    # Anthropic devrait etre selectionne par defaut
    # Verifier qu'on voit la section cle API
    expect(page.get_by_text("Clé API")).to_be_visible(timeout=2000)

    # Entrer une fausse cle API Anthropic
    api_key_input = page.locator("input[placeholder='sk-ant-...']")
    expect(api_key_input).to_be_visible(timeout=2000)
    api_key_input.fill("sk-ant-test123-fake-key-for-e2e")

    # Cliquer sur Sauver
    save_btn = page.get_by_role("button", name="Sauver")
    expect(save_btn).to_be_enabled()
    save_btn.click()

    # Verifier le message de succes
    expect(page.get_by_text("Clé API enregistrée")).to_be_visible(timeout=3000)

    # Verifier le badge "Cle API configuree"
    expect(page.get_by_text("Clé API configurée")).to_be_visible()
    take_screenshot(page, "settings_api_key_saved")


# ============================================================
# P1 - Importants
# ============================================================


def test_settings_llm_change_provider(page: Page, skip_onboarding):
    """
    P1 - Bascule du provider Anthropic vers Gemini,
    verifie que la liste de modeles change.
    """
    # Ouvrir les parametres
    page.locator("button[title='Paramètres']").click()
    expect(page.get_by_text("Paramètres", exact=True).first).to_be_visible(timeout=3000)

    # Aller a l'onglet LLM
    page.get_by_text("LLM").click()
    page.wait_for_timeout(500)

    # Verifier qu'Anthropic est affiche (par defaut)
    expect(page.get_by_text("Claude (Anthropic)")).to_be_visible(timeout=2000)

    # Cliquer sur Gemini (Google)
    gemini_btn = page.get_by_text("Gemini (Google)")
    expect(gemini_btn).to_be_visible()
    gemini_btn.click()

    page.wait_for_timeout(500)

    # Verifier que les modeles Gemini sont visibles
    expect(page.get_by_text("Gemini 3 Pro")).to_be_visible(timeout=2000)
    expect(page.get_by_text("Gemini 3 Flash")).to_be_visible()

    # Le placeholder de la cle API devrait changer
    expect(page.locator("input[placeholder='AIza...']")).to_be_visible()

    take_screenshot(page, "settings_llm_gemini_selected")


def test_settings_web_search_toggle(page: Page, skip_onboarding):
    """
    P1 - Active/desactive la recherche web, verifie l'etat du toggle.
    """
    # Ouvrir les parametres
    page.locator("button[title='Paramètres']").click()
    expect(page.get_by_text("Paramètres", exact=True).first).to_be_visible(timeout=3000)

    # Aller a l'onglet LLM
    page.get_by_text("LLM").click()
    page.wait_for_timeout(500)

    # Scroller vers la section Recherche Web
    web_search_heading = page.get_by_text("Recherche Web")
    web_search_heading.scroll_into_view_if_needed()
    expect(web_search_heading).to_be_visible(timeout=2000)

    # Le toggle est un bouton rond avec fond cyan (active) ou gris (inactif)
    # Trouver le toggle (bouton contenant un span rond)
    toggle = page.locator("button.rounded-full").first
    expect(toggle).to_be_visible()

    # Verifier l'etat initial (active par defaut - bg-accent-cyan)
    initial_class = toggle.get_attribute("class") or ""
    is_initially_enabled = "bg-accent-cyan" in initial_class

    # Cliquer pour changer l'etat
    toggle.click()
    page.wait_for_timeout(500)

    # Verifier que l'etat a change
    new_class = toggle.get_attribute("class") or ""
    if is_initially_enabled:
        assert "bg-surface-elevated" in new_class or "bg-accent-cyan" not in new_class
    else:
        assert "bg-accent-cyan" in new_class

    take_screenshot(page, "settings_web_search_toggled")

    # Re-cliquer pour revenir a l'etat initial
    toggle.click()
    page.wait_for_timeout(500)

    final_class = toggle.get_attribute("class") or ""
    if is_initially_enabled:
        assert "bg-accent-cyan" in final_class
    else:
        assert "bg-accent-cyan" not in final_class


def test_settings_working_directory(page: Page, skip_onboarding):
    """
    P1 - Verifie que la section dossier de travail est visible dans l'onglet Donnees,
    et affiche 'Non configure' si aucun dossier n'est defini.
    """
    # Ouvrir les parametres
    page.locator("button[title='Paramètres']").click()
    expect(page.get_by_text("Paramètres", exact=True).first).to_be_visible(timeout=3000)

    # Aller a l'onglet Donnees
    page.get_by_text("Données").click()
    page.wait_for_timeout(500)

    # Verifier que la section dossier de travail est presente
    expect(page.get_by_text("Dossier de travail")).to_be_visible(timeout=2000)

    # Verifier le bouton Parcourir
    browse_btn = page.get_by_role("button", name="Parcourir")
    expect(browse_btn).to_be_visible()

    # Verifier l'affichage du chemin (ou "Non configure")
    dir_display = page.locator("p.font-mono.truncate")
    expect(dir_display).to_be_visible()

    dir_text = dir_display.text_content() or ""
    # Soit un chemin est configure, soit on voit "Non configure"
    assert dir_text == "Non configuré" or "/" in dir_text

    # Verifier la section Stockage des donnees
    expect(page.get_by_text("Stockage des données")).to_be_visible()

    take_screenshot(page, "settings_working_directory")


def test_settings_mcp_preset_install(page: Page, skip_onboarding):
    """
    P1 - Installe le preset Filesystem (Tier 1 - pas de cle requise),
    verifie qu'il apparait comme installe.
    """
    # Ouvrir les parametres
    page.locator("button[title='Paramètres']").click()
    expect(page.get_by_text("Paramètres", exact=True).first).to_be_visible(timeout=3000)

    # Aller a l'onglet Tools
    page.get_by_text("Tools").click()
    page.wait_for_timeout(500)

    # Ouvrir la section Presets si pas deja ouverte
    presets_btn = page.get_by_text("Presets")
    if presets_btn.is_visible():
        presets_btn.click()
        page.wait_for_timeout(500)

    # Chercher le preset Filesystem dans la categorie Essentiels
    filesystem_preset = page.get_by_text("Filesystem").first
    expect(filesystem_preset).to_be_visible(timeout=3000)

    take_screenshot(page, "settings_mcp_presets_visible")

    # Cliquer sur le preset Filesystem pour l'installer
    # Le preset est un bouton contenant le texte "Filesystem"
    filesystem_btn = page.locator("button:has-text('Filesystem')").first
    filesystem_btn.click()

    # Attendre l'installation (spinner puis check vert)
    # Le serveur apparait dans la liste des serveurs installes
    page.wait_for_timeout(3000)

    take_screenshot(page, "settings_mcp_filesystem_installed")

    # Verifier qu'il apparait comme installe (check vert ou opacity reduite)
    # Apres installation, le preset est disable et a un check vert
    # On verifie qu'on ne peut plus cliquer dessus
    filesystem_installed = page.locator("button:has-text('Filesystem')").first
    expect(filesystem_installed).to_be_disabled()


# ============================================================
# P2 - Nice to have
# ============================================================


def test_settings_mcp_preset_with_key(page: Page, skip_onboarding):
    """
    P2 - Tente d'installer un preset Tier 3 (ex: Brave Search),
    verifie que le modal de saisie EnvVarModal apparait.
    """
    # Ouvrir les parametres
    page.locator("button[title='Paramètres']").click()
    expect(page.get_by_text("Paramètres", exact=True).first).to_be_visible(timeout=3000)

    # Aller a l'onglet Tools
    page.get_by_text("Tools").click()
    page.wait_for_timeout(500)

    # Ouvrir la section Presets si pas deja ouverte
    presets_btn = page.get_by_text("Presets")
    if presets_btn.is_visible():
        presets_btn.click()
        page.wait_for_timeout(500)

    # Chercher un preset qui requiert une cle API (Brave Search)
    brave_preset = page.get_by_text("Brave Search").first
    expect(brave_preset).to_be_visible(timeout=3000)

    # Cliquer pour tenter l'installation
    brave_btn = page.locator("button:has-text('Brave Search')").first
    brave_btn.click()

    # Le modal EnvVarModal doit apparaitre avec le champ BRAVE_API_KEY
    expect(page.get_by_text("BRAVE_API_KEY")).to_be_visible(timeout=3000)

    take_screenshot(page, "settings_mcp_envvar_modal")

    # Verifier qu'il y a un champ de saisie pour la cle
    env_input = page.locator("input[type='password']").last
    expect(env_input).to_be_visible()

    # Fermer le modal (bouton Annuler ou clic exterieur)
    cancel_btn = page.get_by_role("button", name="Annuler")
    if cancel_btn.is_visible():
        cancel_btn.click()


def test_settings_accessibility(page: Page, skip_onboarding):
    """
    P2 - Verifie que les inputs du profil ont des labels,
    et que l'onglet A11Y est accessible.
    """
    # Ouvrir les parametres
    page.locator("button[title='Paramètres']").click()
    expect(page.get_by_text("Paramètres", exact=True).first).to_be_visible(timeout=3000)

    # Verifier que l'onglet Profil a des labels pour chaque champ
    labels = page.locator("label")
    label_count = labels.count()
    assert label_count >= 4, f"Attendu au moins 4 labels, trouve {label_count}"

    # Verifier les labels specifiques
    expect(page.get_by_text("Nom complet *")).to_be_visible()
    expect(page.get_by_text("Surnom")).to_be_visible()
    expect(page.get_by_text("Entreprise")).to_be_visible()

    # Naviguer vers l'onglet A11Y
    page.get_by_text("A11Y").click()
    page.wait_for_timeout(500)

    take_screenshot(page, "settings_accessibility_tab")

    # L'onglet A11Y est visible et charge sans erreur
    # (le contenu exact depend de AccessibilityTab)


def test_settings_performance(page: Page, skip_onboarding):
    """
    P2 - Ouvre l'onglet Performance, verifie qu'il charge et affiche des metriques.
    """
    # Ouvrir les parametres
    page.locator("button[title='Paramètres']").click()
    expect(page.get_by_text("Paramètres", exact=True).first).to_be_visible(timeout=3000)

    # Naviguer vers l'onglet Perf
    page.get_by_text("Perf").click()
    page.wait_for_timeout(500)

    take_screenshot(page, "settings_performance_tab")

    # L'onglet Performance charge sans erreur
    # On verifie que le contenu s'affiche (pas de spinner infini)
    # Attendre que le loader disparaisse si present
    page.wait_for_timeout(1000)

    # Le contenu doit etre visible (pas d'erreur, pas de spinner)
    content_area = page.locator(".overflow-y-auto")
    expect(content_area).to_be_visible()
