"""
THÉRÈSE v2 - Tests E2E Chat

Test des fonctionnalités de chat avec le LLM.
"""

import pytest
from playwright.sync_api import Page, expect

from .conftest import take_screenshot


def test_chat_send_message_and_receive_response(page: Page, skip_onboarding):
    """
    US-CHAT-01: L'utilisateur peut envoyer un message et recevoir une réponse.
    """
    # Vérifier écran vide
    expect(page.locator("text=Comment puis-je t'aider ?")).to_be_visible()
    take_screenshot(page, "chat_01_empty")

    # Saisir un message
    textarea = page.locator("textarea[placeholder*='Écrivez votre message']")
    textarea.fill("Dis bonjour en une phrase courte")

    # Envoyer
    page.click("button[title='Envoyer (↵)']")

    # Vérifier que le message utilisateur apparaît
    expect(page.locator("text=Dis bonjour en une phrase courte").first).to_be_visible(timeout=5000)

    # Attendre la réponse (typing indicator puis message)
    expect(page.locator(".typing-indicator")).to_be_visible(timeout=2000)
    take_screenshot(page, "chat_02_typing")

    # Attendre la réponse complète (timeout plus long pour LLM)
    # Chercher simplement "Bonjour" dans la page (le LLM répondra avec ce mot)
    expect(page.locator("text=/Bonjour/i").first).to_be_visible(timeout=20000)
    take_screenshot(page, "chat_03_response")


def test_chat_new_conversation(page: Page, skip_onboarding):
    """
    US-CHAT-02: Créer une nouvelle conversation.
    """
    # Envoyer un message
    page.fill("textarea[placeholder*='Écrivez votre message']", "Test message")
    page.click("button[title='Envoyer (↵)']")

    # Attendre réponse
    page.wait_for_timeout(5000)

    # Cliquer sur le bouton nouvelle conversation (Plus icon, title contient "Nouvelle conversation")
    new_conv_button = page.locator("button[title*='Nouvelle conversation']")
    expect(new_conv_button).to_be_enabled(timeout=2000)  # Attendre qu'il soit activé
    new_conv_button.click()

    # Vérifier que l'écran est vide
    expect(page.locator("text=Comment puis-je t'aider ?")).to_be_visible()

    # Le textarea doit être vide
    textarea = page.locator("textarea[placeholder*='Écrivez votre message']")
    expect(textarea).to_have_value("")


def test_chat_conversations_sidebar(page: Page, skip_onboarding):
    """
    US-CHAT-03: Ouvrir la sidebar conversations avec Cmd+B.
    """
    # Ouvrir sidebar avec raccourci
    page.keyboard.press("Meta+B")

    # Vérifier que la sidebar est visible en cherchant le titre
    expect(page.locator("h2:has-text('Conversations')")).to_be_visible(timeout=2000)
    take_screenshot(page, "chat_sidebar_open")

    # Fermer avec le même raccourci
    page.keyboard.press("Meta+B")

    # Vérifier que la sidebar est cachée
    expect(page.locator("h2:has-text('Conversations')")).to_be_hidden(timeout=2000)


def test_chat_keyboard_shortcuts(page: Page, skip_onboarding):
    """
    US-CHAT-04: Les raccourcis clavier fonctionnent.
    """
    # Cmd+K pour ouvrir la command palette
    page.keyboard.press("Meta+K")
    expect(page.locator("input[placeholder='Rechercher une commande...']")).to_be_visible(timeout=2000)
    take_screenshot(page, "chat_command_palette")

    # Escape pour fermer
    page.keyboard.press("Escape")
    expect(page.locator("input[placeholder='Rechercher une commande...']")).to_be_hidden(timeout=1000)

    # Cmd+M pour ouvrir mémoire
    page.keyboard.press("Meta+M")
    expect(page.locator("text=Espace de travail")).to_be_visible(timeout=2000)
    take_screenshot(page, "chat_memory_panel")


def test_chat_guided_prompts_navigation(page: Page, skip_onboarding):
    """
    US-CHAT-05: Navigation dans les guided prompts.
    """
    # Cliquer sur "Produire"
    page.click("button:has-text('Produire')")

    # Vérifier que les sous-options s'affichent
    expect(page.locator("text=Email pro")).to_be_visible(timeout=2000)
    expect(page.locator("text=Post LinkedIn")).to_be_visible()
    take_screenshot(page, "chat_guided_suboptions")

    # Cliquer sur "← Retour"
    page.click("button:has-text('Retour')")

    # Vérifier retour à la grille principale
    expect(page.locator("text=Produire")).to_be_visible()
    expect(page.locator("text=Comprendre")).to_be_visible()
    expect(page.locator("text=Organiser")).to_be_visible()


def test_chat_guided_prompt_fills_textarea(page: Page, skip_onboarding):
    """
    US-CHAT-06: Sélectionner un guided prompt remplit le textarea.
    """
    # Navigation: Produire → Email pro
    page.click("button:has-text('Produire')")
    page.click("button:has-text('Email pro')")

    # Vérifier que le textarea contient le prompt template
    textarea = page.locator("textarea[placeholder*='Écrivez votre message']")
    expect(textarea).to_have_value("Rédige un email professionnel à propos de [sujet]. Contexte : [destinataire, ton souhaité].")
    take_screenshot(page, "chat_guided_prompt_filled")


def test_chat_message_persistence(page: Page, skip_onboarding):
    """
    US-CHAT-07: Les messages persistent dans la conversation.
    """
    # Envoyer 2 messages et attendre qu'ils apparaissent
    page.fill("textarea[placeholder*='Écrivez votre message']", "Premier message test")
    page.click("button[title='Envoyer (↵)']")
    # Attendre que le message apparaisse
    expect(page.locator("text=Premier message test").first).to_be_visible(timeout=5000)
    page.wait_for_timeout(2000)  # Laisser le temps à la DB de sauvegarder

    page.fill("textarea[placeholder*='Écrivez votre message']", "Deuxième message test")
    page.click("button[title='Envoyer (↵)']")
    expect(page.locator("text=Deuxième message test").first).to_be_visible(timeout=5000)
    page.wait_for_timeout(2000)

    # Recharger la page
    page.reload()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)  # Attendre le rechargement des conversations

    # Vérifier que les 2 messages sont toujours là
    expect(page.locator("text=Premier message test").first).to_be_visible(timeout=5000)
    expect(page.locator("text=Deuxième message test").first).to_be_visible()
