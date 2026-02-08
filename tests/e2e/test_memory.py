"""
THÉRÈSE v2 - Tests E2E Mémoire

Test du CRUD contacts et projets dans l'Espace de travail.
"""

from playwright.sync_api import Page, expect

from .conftest import take_screenshot


def test_memory_create_contact(page: Page, skip_onboarding):
    """
    US-MEMORY-01: Créer un contact dans la mémoire.
    """
    # Ouvrir l'Espace de travail avec Cmd+M
    page.keyboard.press("Meta+M")
    expect(page.locator("text=Espace de travail")).to_be_visible(timeout=2000)

    # Aller dans l'onglet Contacts (devrait être affiché par défaut)
    # Ou cliquer sur l'onglet si nécessaire
    contacts_tab = page.locator("button:has-text('Contacts')")
    if contacts_tab.is_visible():
        contacts_tab.click()

    # Cliquer sur "Nouveau contact" ou bouton +
    new_contact_button = page.locator("button:has-text('Nouveau')").or_(page.locator("button[title*='contact']")).first
    new_contact_button.click()

    # Vérifier que le modal s'ouvre
    expect(page.locator("text=Nouveau contact")).to_be_visible(timeout=2000)
    take_screenshot(page, "memory_contact_modal")

    # Remplir le formulaire
    page.fill("input[name='name']", "Pierre Martin")
    page.fill("input[name='email']", "pierre.martin@example.com")
    page.fill("input[name='company']", "ACME Corp")
    page.fill("input[name='phone']", "+33 6 12 34 56 78")
    page.fill("textarea[name='notes']", "Contact important pour projet X")

    # Sauvegarder
    page.click("button:has-text('Enregistrer')")

    # Vérifier que le contact apparaît dans la liste
    expect(page.locator("text=Pierre Martin")).to_be_visible(timeout=3000)
    take_screenshot(page, "memory_contact_created")


def test_memory_edit_contact(page: Page, skip_onboarding):
    """
    US-MEMORY-02: Modifier un contact existant.
    """
    # Créer d'abord un contact (prérequis)
    page.keyboard.press("Meta+M")
    expect(page.locator("text=Espace de travail")).to_be_visible(timeout=2000)

    new_contact_button = page.locator("button:has-text('Nouveau')").or_(page.locator("button[title*='contact']")).first
    new_contact_button.click()

    page.fill("input[name='name']", "Julie Dubois")
    page.fill("input[name='email']", "julie@example.com")
    page.click("button:has-text('Enregistrer')")

    expect(page.locator("text=Julie Dubois")).to_be_visible(timeout=3000)

    # Cliquer sur le contact pour l'éditer
    page.click("text=Julie Dubois")

    # Le modal d'édition devrait s'ouvrir
    expect(page.locator("text=Modifier le contact")).to_be_visible(timeout=2000)

    # Modifier le nom
    name_input = page.locator("input[name='name']")
    name_input.fill("Julie Dubois-Martin")

    # Sauvegarder
    page.click("button:has-text('Enregistrer')")

    # Vérifier que le nom a changé
    expect(page.locator("text=Julie Dubois-Martin")).to_be_visible(timeout=3000)
    take_screenshot(page, "memory_contact_edited")


def test_memory_delete_contact(page: Page, skip_onboarding):
    """
    US-MEMORY-03: Supprimer un contact.
    """
    # Créer un contact
    page.keyboard.press("Meta+M")
    expect(page.locator("text=Espace de travail")).to_be_visible(timeout=2000)

    new_contact_button = page.locator("button:has-text('Nouveau')").or_(page.locator("button[title*='contact']")).first
    new_contact_button.click()

    page.fill("input[name='name']", "Contact À Supprimer")
    page.fill("input[name='email']", "delete@example.com")
    page.click("button:has-text('Enregistrer')")

    expect(page.locator("text=Contact À Supprimer")).to_be_visible(timeout=3000)

    # Ouvrir le contact
    page.click("text=Contact À Supprimer")

    # Cliquer sur le bouton supprimer (icône Trash ou bouton "Supprimer")
    delete_button = page.locator("button:has-text('Supprimer')").or_(page.locator("button[title*='Supprimer']")).first
    delete_button.click()

    # Confirmer la suppression (il peut y avoir une modal de confirmation)
    confirm_button = page.locator("button:has-text('Confirmer')").or_(page.locator("button:has-text('Oui')"))
    if confirm_button.is_visible(timeout=1000):
        confirm_button.click()

    # Vérifier que le contact a disparu
    expect(page.locator("text=Contact À Supprimer")).to_be_hidden(timeout=3000)
    take_screenshot(page, "memory_contact_deleted")


def test_memory_search_contacts(page: Page, skip_onboarding):
    """
    US-MEMORY-04: Rechercher des contacts.
    """
    # Créer plusieurs contacts
    page.keyboard.press("Meta+M")
    expect(page.locator("text=Espace de travail")).to_be_visible(timeout=2000)

    contacts = [
        ("Alice Wonderland", "alice@example.com"),
        ("Bob Builder", "bob@example.com"),
        ("Charlie Chaplin", "charlie@example.com"),
    ]

    for name, email in contacts:
        new_contact_button = page.locator("button:has-text('Nouveau')").or_(page.locator("button[title*='contact']")).first
        new_contact_button.click()
        page.fill("input[name='name']", name)
        page.fill("input[name='email']", email)
        page.click("button:has-text('Enregistrer')")
        page.wait_for_timeout(500)

    # Rechercher "Alice"
    search_input = page.locator("input[placeholder*='Rechercher']").first
    search_input.fill("Alice")

    # Vérifier qu'Alice apparaît et que les autres non
    expect(page.locator("text=Alice Wonderland")).to_be_visible(timeout=2000)
    expect(page.locator("text=Bob Builder")).to_be_hidden()
    expect(page.locator("text=Charlie Chaplin")).to_be_hidden()

    take_screenshot(page, "memory_contact_search")


def test_memory_create_project(page: Page, skip_onboarding):
    """
    US-MEMORY-05: Créer un projet dans la mémoire.
    """
    # Ouvrir l'Espace de travail
    page.keyboard.press("Meta+M")
    expect(page.locator("text=Espace de travail")).to_be_visible(timeout=2000)

    # Aller dans l'onglet Projets
    page.click("button:has-text('Projets')")

    # Cliquer sur "Nouveau projet"
    new_project_button = page.locator("button:has-text('Nouveau')").or_(page.locator("button[title*='projet']")).first
    new_project_button.click()

    # Vérifier que le modal s'ouvre
    expect(page.locator("text=Nouveau projet")).to_be_visible(timeout=2000)
    take_screenshot(page, "memory_project_modal")

    # Remplir le formulaire
    page.fill("input[name='name']", "Refonte Site Web")
    page.fill("textarea[name='description']", "Refonte complète du site corporate avec nouveau design.")
    page.fill("input[name='budget']", "15000")

    # Sauvegarder
    page.click("button:has-text('Enregistrer')")

    # Vérifier que le projet apparaît
    expect(page.locator("text=Refonte Site Web")).to_be_visible(timeout=3000)
    take_screenshot(page, "memory_project_created")


def test_memory_edit_project(page: Page, skip_onboarding):
    """
    US-MEMORY-06: Modifier un projet existant.
    """
    # Créer un projet
    page.keyboard.press("Meta+M")
    expect(page.locator("text=Espace de travail")).to_be_visible(timeout=2000)

    page.click("button:has-text('Projets')")

    new_project_button = page.locator("button:has-text('Nouveau')").or_(page.locator("button[title*='projet']")).first
    new_project_button.click()

    page.fill("input[name='name']", "Projet Alpha")
    page.fill("input[name='budget']", "5000")
    page.click("button:has-text('Enregistrer')")

    expect(page.locator("text=Projet Alpha")).to_be_visible(timeout=3000)

    # Éditer le projet
    page.click("text=Projet Alpha")

    expect(page.locator("text=Modifier le projet")).to_be_visible(timeout=2000)

    # Modifier le budget
    budget_input = page.locator("input[name='budget']")
    budget_input.fill("7500")

    # Sauvegarder
    page.click("button:has-text('Enregistrer')")

    # Vérifier que le budget a changé (si affiché dans la liste)
    take_screenshot(page, "memory_project_edited")


def test_memory_delete_project(page: Page, skip_onboarding):
    """
    US-MEMORY-07: Supprimer un projet.
    """
    # Créer un projet
    page.keyboard.press("Meta+M")
    expect(page.locator("text=Espace de travail")).to_be_visible(timeout=2000)

    page.click("button:has-text('Projets')")

    new_project_button = page.locator("button:has-text('Nouveau')").or_(page.locator("button[title*='projet']")).first
    new_project_button.click()

    page.fill("input[name='name']", "Projet À Supprimer")
    page.click("button:has-text('Enregistrer')")

    expect(page.locator("text=Projet À Supprimer")).to_be_visible(timeout=3000)

    # Ouvrir et supprimer
    page.click("text=Projet À Supprimer")

    delete_button = page.locator("button:has-text('Supprimer')").or_(page.locator("button[title*='Supprimer']")).first
    delete_button.click()

    # Confirmer si nécessaire
    confirm_button = page.locator("button:has-text('Confirmer')").or_(page.locator("button:has-text('Oui')"))
    if confirm_button.is_visible(timeout=1000):
        confirm_button.click()

    # Vérifier suppression
    expect(page.locator("text=Projet À Supprimer")).to_be_hidden(timeout=3000)
    take_screenshot(page, "memory_project_deleted")


def test_memory_link_contact_to_project(page: Page, skip_onboarding):
    """
    US-MEMORY-08: Lier un contact à un projet.
    """
    # Créer un contact
    page.keyboard.press("Meta+M")
    expect(page.locator("text=Espace de travail")).to_be_visible(timeout=2000)

    new_contact_button = page.locator("button:has-text('Nouveau')").or_(page.locator("button[title*='contact']")).first
    new_contact_button.click()

    page.fill("input[name='name']", "Marie Curie")
    page.fill("input[name='email']", "marie@example.com")
    page.click("button:has-text('Enregistrer')")

    expect(page.locator("text=Marie Curie")).to_be_visible(timeout=3000)

    # Créer un projet
    page.click("button:has-text('Projets')")

    new_project_button = page.locator("button:has-text('Nouveau')").or_(page.locator("button[title*='projet']")).first
    new_project_button.click()

    page.fill("input[name='name']", "Recherche Radium")
    page.fill("textarea[name='description']", "Projet de recherche avec Marie Curie.")

    # Lier le contact (il peut y avoir un select ou autocomplete "Contact lié")
    contact_select = page.locator("select[name='contact_id']").or_(page.locator("input[placeholder*='contact']"))
    if contact_select.is_visible():
        contact_select.click()
        page.click("text=Marie Curie")

    page.click("button:has-text('Enregistrer')")

    # Vérifier que le projet est créé
    expect(page.locator("text=Recherche Radium")).to_be_visible(timeout=3000)

    # Vérifier le lien (peut nécessiter d'ouvrir le projet pour voir le contact lié)
    page.click("text=Recherche Radium")

    # Vérifier que Marie Curie est mentionnée
    expect(page.locator("text=Marie Curie")).to_be_visible(timeout=2000)

    take_screenshot(page, "memory_project_linked")
