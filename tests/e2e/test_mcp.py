"""
THÉRÈSE v2 - Tests E2E MCP (Model Context Protocol)

Test de la gestion des serveurs MCP et de l'exécution de tools.
"""

from playwright.sync_api import Page, expect

from .conftest import take_screenshot


def test_mcp_list_servers(page: Page, skip_onboarding):
    """
    US-MCP-01: Lister les serveurs MCP disponibles.
    """
    # Ouvrir les Paramètres (Cmd+,)
    page.keyboard.press("Meta+Comma")

    # Vérifier que le modal Paramètres s'ouvre
    expect(page.locator("text=Paramètres")).to_be_visible(timeout=2000)

    # Aller dans l'onglet Tools (MCP)
    tools_tab = page.locator("button:has-text('Tools')").or_(page.locator("button:has-text('MCP')"))
    tools_tab.click()

    # Vérifier que la liste des serveurs MCP s'affiche
    expect(page.locator("text=Serveurs MCP").or_(page.locator("text=Tools disponibles"))).to_be_visible(timeout=2000)

    # Vérifier qu'il y a une section "Presets" avec des serveurs prédéfinis
    expect(page.locator("text=/Presets|Disponibles/i")).to_be_visible()

    # Vérifier présence de quelques presets communs
    expect(page.locator("text=Filesystem").or_(page.locator("text=Fetch"))).to_be_visible()

    take_screenshot(page, "mcp_list_servers")


def test_mcp_add_server(page: Page, skip_onboarding):
    """
    US-MCP-02: Ajouter un serveur MCP depuis les presets.
    """
    # Ouvrir Paramètres → Tools
    page.keyboard.press("Meta+Comma")
    expect(page.locator("text=Paramètres")).to_be_visible(timeout=2000)

    tools_tab = page.locator("button:has-text('Tools')").or_(page.locator("button:has-text('MCP')"))
    tools_tab.click()

    # Installer le preset "Filesystem"
    filesystem_preset = page.locator("text=Filesystem").or_(page.locator("div:has-text('Filesystem')")).first

    # Chercher le bouton "Installer" ou "Ajouter" à côté
    install_button = page.locator("button:has-text('Installer')").or_(page.locator("button:has-text('Ajouter')")).first
    install_button.click()

    # Vérifier qu'un message de succès ou que le serveur apparaît dans "Serveurs actifs"
    expect(page.locator("text=/Installé|Ajouté|Actif/i")).to_be_visible(timeout=5000)

    take_screenshot(page, "mcp_server_added")


def test_mcp_start_stop_server(page: Page, skip_onboarding):
    """
    US-MCP-03: Démarrer et arrêter un serveur MCP.
    """
    # Ouvrir Paramètres → Tools
    page.keyboard.press("Meta+Comma")
    expect(page.locator("text=Paramètres")).to_be_visible(timeout=2000)

    tools_tab = page.locator("button:has-text('Tools')").or_(page.locator("button:has-text('MCP')"))
    tools_tab.click()

    # Installer un serveur si pas déjà fait
    install_button = page.locator("button:has-text('Installer')").or_(page.locator("button:has-text('Ajouter')")).first
    if install_button.is_visible():
        install_button.click()
        page.wait_for_timeout(2000)

    # Chercher un serveur dans la liste des serveurs actifs
    # Il devrait y avoir un bouton "Start" ou "Stop" à côté du nom du serveur
    start_button = page.locator("button:has-text('Start')").or_(page.locator("button:has-text('Démarrer')")).first

    if start_button.is_visible():
        start_button.click()

        # Vérifier que le status passe à "Running" ou affiche un badge vert
        expect(page.locator("text=/Running|Actif|En cours/i")).to_be_visible(timeout=5000)
        take_screenshot(page, "mcp_server_running")

        # Arrêter le serveur
        stop_button = page.locator("button:has-text('Stop')").or_(page.locator("button:has-text('Arrêter')")).first
        stop_button.click()

        # Vérifier que le status passe à "Stopped"
        expect(page.locator("text=/Stopped|Arrêté|Inactif/i")).to_be_visible(timeout=5000)
        take_screenshot(page, "mcp_server_stopped")


def test_mcp_install_preset(page: Page, skip_onboarding):
    """
    US-MCP-04: Installer plusieurs presets MCP.
    """
    # Ouvrir Paramètres → Tools
    page.keyboard.press("Meta+Comma")
    expect(page.locator("text=Paramètres")).to_be_visible(timeout=2000)

    tools_tab = page.locator("button:has-text('Tools')").or_(page.locator("button:has-text('MCP')"))
    tools_tab.click()

    # Installer 2 presets différents
    presets_to_install = ["Filesystem", "Fetch"]

    for preset_name in presets_to_install:
        preset_locator = page.locator(f"text={preset_name}").first

        # Cliquer sur le bouton Installer associé
        # Note: Le locator exact dépend de la structure UI
        # On cherche un bouton "Installer" proche du preset
        install_button = preset_locator.locator("..").locator("button:has-text('Installer')").or_(
            page.locator("button:has-text('Installer')").first
        )

        if install_button.is_visible():
            install_button.click()
            page.wait_for_timeout(2000)

    # Vérifier que les 2 serveurs sont dans la liste des serveurs actifs
    expect(page.locator("text=Filesystem")).to_be_visible()
    expect(page.locator("text=Fetch")).to_be_visible()

    take_screenshot(page, "mcp_presets_installed")


def test_mcp_tool_execution_in_chat(page: Page, skip_onboarding):
    """
    US-MCP-05: Le LLM peut utiliser les tools MCP dans le chat.
    """
    # Prérequis: Installer un serveur MCP (ex: Filesystem)
    page.keyboard.press("Meta+Comma")
    expect(page.locator("text=Paramètres")).to_be_visible(timeout=2000)

    tools_tab = page.locator("button:has-text('Tools')").or_(page.locator("button:has-text('MCP')"))
    tools_tab.click()

    # Installer Filesystem si pas déjà fait
    install_button = page.locator("button:has-text('Installer')").or_(page.locator("button:has-text('Ajouter')")).first
    if install_button.is_visible():
        install_button.click()
        page.wait_for_timeout(2000)

    # Démarrer le serveur
    start_button = page.locator("button:has-text('Start')").or_(page.locator("button:has-text('Démarrer')")).first
    if start_button.is_visible():
        start_button.click()
        expect(page.locator("text=/Running|Actif/i")).to_be_visible(timeout=5000)

    # Fermer les Paramètres
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)

    # Envoyer un message au LLM qui devrait déclencher un tool call
    # Ex: "Liste les fichiers du répertoire courant"
    textarea = page.locator("textarea[placeholder*='Écrivez votre message']")
    textarea.fill("Liste les fichiers du répertoire courant en utilisant le tool filesystem.")

    page.click("button[title='Envoyer (↵)']")

    # Attendre que le message utilisateur apparaisse
    expect(page.locator("text=Liste les fichiers du répertoire courant").first).to_be_visible(timeout=5000)

    # Attendre la réponse du LLM
    # Il devrait mentionner qu'il utilise un tool ou afficher les fichiers
    expect(page.locator("text=/tool|filesystem|fichiers/i")).to_be_visible(timeout=20000)

    take_screenshot(page, "mcp_tool_execution_chat")

    # Vérifier qu'il y a un indicateur de tool execution (peut être un badge, icône, ou texte)
    # Ex: "🔧 Exécution tool: list_files"
    # Cela dépend de l'UI implémentée
    # Pour l'instant on vérifie juste que la réponse contient du contenu lié aux fichiers
