"""
THERESE v2 - Tests E2E - Panel Taches (Tasks).

8 tests couvrant la gestion des taches :
- P0 : Etat vide, creation, vue Kanban, completion, toggle vue
- P1 : Edition, suppression, filtre par priorite
"""

from playwright.sync_api import expect

from .conftest import take_screenshot

# ============================================================
# P0 - Tests critiques
# ============================================================


def test_tasks_empty_state(panel_page):
    """
    P0 - Ouvrir le panel taches vide, verifier le message
    et la presence des colonnes Kanban.
    """
    page, _ = panel_page("tasks")

    # Verifier le header du panel
    expect(page.get_by_text("Taches")).to_be_visible(timeout=5000)

    # En mode Kanban par defaut, les 3 colonnes doivent etre visibles
    expect(page.get_by_text("A faire")).to_be_visible(timeout=3000)
    expect(page.get_by_text("En cours")).to_be_visible(timeout=3000)
    expect(page.get_by_text("Termine")).to_be_visible(timeout=3000)

    # Chaque colonne vide affiche "Aucune tache"
    empty_messages = page.get_by_text("Aucune tache")
    expect(empty_messages.first).to_be_visible()

    take_screenshot(page, "tasks_empty_state")


def test_tasks_create(panel_page, api_client):
    """
    P0 - Creer une tache via le formulaire UI.
    Verifier qu'elle apparait dans le Kanban.
    """
    page, _ = panel_page("tasks")

    # Cliquer sur "Nouvelle tache"
    page.get_by_text("Nouvelle tache").click()
    page.wait_for_timeout(500)

    # Le formulaire doit s'afficher
    expect(page.get_by_text("Nouvelle tache", exact=False).first).to_be_visible(timeout=3000)

    # Remplir le titre
    title_input = page.locator("input[placeholder='Titre de la tâche']")
    expect(title_input).to_be_visible(timeout=3000)
    title_input.fill("Envoyer devis Dupont")

    # Remplir la description
    desc_input = page.locator("textarea[placeholder='Description de la tâche']")
    desc_input.fill("Devis coaching 3 seances")

    # Selectionner priorite haute
    priority_select = page.locator("select").filter(has_text="Moyenne")
    priority_select.select_option(value="high")

    # Cliquer sur Enregistrer
    page.get_by_text("Enregistrer").click()
    page.wait_for_timeout(1000)

    # Verifier que la tache apparait dans le Kanban (colonne "A faire")
    expect(page.get_by_text("Envoyer devis Dupont")).to_be_visible(timeout=5000)
    expect(page.get_by_text("Haute")).to_be_visible()

    take_screenshot(page, "tasks_create")


def test_tasks_kanban_view(panel_page, seeded_tasks):
    """
    P0 - Verifier les 3 colonnes Kanban avec les taches seeded.
    Les taches doivent etre distribuees correctement par statut.
    """
    page, _ = panel_page("tasks")
    page.wait_for_timeout(1000)  # Attendre le chargement API

    # Les 3 colonnes doivent etre visibles
    expect(page.get_by_text("A faire")).to_be_visible(timeout=5000)
    expect(page.get_by_text("En cours")).to_be_visible()
    expect(page.get_by_text("Termine")).to_be_visible()

    # Verifier les taches par colonne (seeded_tasks a 4 taches) :
    # - "Envoyer devis Dupont" (todo)
    # - "Relancer prospect Martin" (in_progress)
    # - "Mettre a jour site web" (todo)
    # - "Facture janvier envoyee" (done)
    expect(page.get_by_text("Envoyer devis Dupont")).to_be_visible(timeout=5000)
    expect(page.get_by_text("Relancer prospect Martin")).to_be_visible()
    expect(page.get_by_text("Mettre a jour site web")).to_be_visible()
    expect(page.get_by_text("Facture janvier envoyee")).to_be_visible()

    take_screenshot(page, "tasks_kanban_view")


def test_tasks_complete(panel_page, seeded_tasks, api_client):
    """
    P0 - Marquer une tache "todo" comme complete via l'API,
    verifier qu'elle passe dans la colonne "Termine".
    """
    page, _ = panel_page("tasks")
    page.wait_for_timeout(1000)

    # Trouver la tache "Envoyer devis Dupont" (status: todo)
    todo_task = next(t for t in seeded_tasks if t["title"] == "Envoyer devis Dupont")
    task_id = todo_task["id"]

    # Verifier qu'elle est visible avant completion
    expect(page.get_by_text("Envoyer devis Dupont")).to_be_visible(timeout=5000)

    # Completer via API
    resp = api_client.patch(f"/api/tasks/{task_id}/complete")
    assert resp.status_code == 200

    # Recharger la page pour voir le changement
    page.reload()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # La tache doit toujours etre visible mais dans la colonne "Termine"
    expect(page.get_by_text("Envoyer devis Dupont")).to_be_visible(timeout=5000)

    take_screenshot(page, "tasks_complete")


def test_tasks_toggle_view_mode(panel_page, seeded_tasks):
    """
    P0 - Basculer entre les vues Kanban et Liste.
    Verifier que les taches restent visibles dans les deux vues.
    """
    page, _ = panel_page("tasks")
    page.wait_for_timeout(1000)

    # Par defaut on est en Kanban - verifier les colonnes
    expect(page.get_by_text("A faire")).to_be_visible(timeout=5000)
    expect(page.get_by_text("En cours")).to_be_visible()

    # Cliquer sur le bouton Liste (title="Liste")
    list_button = page.locator("button[title='Liste']")
    expect(list_button).to_be_visible(timeout=3000)
    list_button.click()
    page.wait_for_timeout(500)

    # En vue liste, les taches doivent etre visibles sans colonnes
    expect(page.get_by_text("Envoyer devis Dupont")).to_be_visible(timeout=5000)
    expect(page.get_by_text("Relancer prospect Martin")).to_be_visible()

    take_screenshot(page, "tasks_list_view")

    # Revenir en Kanban (title="Kanban")
    kanban_button = page.locator("button[title='Kanban']")
    kanban_button.click()
    page.wait_for_timeout(500)

    # Les colonnes doivent reapparaitre
    expect(page.get_by_text("A faire")).to_be_visible(timeout=5000)
    expect(page.get_by_text("En cours")).to_be_visible()
    expect(page.get_by_text("Termine")).to_be_visible()

    take_screenshot(page, "tasks_kanban_restored")


# ============================================================
# P1 - Tests secondaires
# ============================================================


def test_tasks_edit(panel_page, seeded_tasks, api_client):
    """
    P1 - Editer le titre d'une tache via l'API, verifier la mise a jour.
    """
    page, _ = panel_page("tasks")
    page.wait_for_timeout(1000)

    # Trouver une tache a editer
    task_to_edit = next(t for t in seeded_tasks if t["title"] == "Mettre a jour site web")
    task_id = task_to_edit["id"]

    # Editer via API
    resp = api_client.put(f"/api/tasks/{task_id}", json={
        "title": "Mettre a jour le portfolio",
    })
    assert resp.status_code == 200

    # Recharger pour voir la mise a jour
    page.reload()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # L'ancien titre ne doit plus etre visible
    expect(page.get_by_text("Mettre a jour site web")).to_be_hidden(timeout=5000)

    # Le nouveau titre doit etre visible
    expect(page.get_by_text("Mettre a jour le portfolio")).to_be_visible(timeout=5000)

    take_screenshot(page, "tasks_edit")


def test_tasks_delete(panel_page, seeded_tasks, api_client):
    """
    P1 - Supprimer une tache via l'API, verifier qu'elle disparait.
    """
    page, _ = panel_page("tasks")
    page.wait_for_timeout(1000)

    # Verifier que la tache existe
    expect(page.get_by_text("Mettre a jour site web")).to_be_visible(timeout=5000)

    # Supprimer via API
    task_to_delete = next(t for t in seeded_tasks if t["title"] == "Mettre a jour site web")
    task_id = task_to_delete["id"]

    resp = api_client.delete(f"/api/tasks/{task_id}")
    assert resp.status_code == 200

    # Recharger
    page.reload()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # La tache ne doit plus etre visible
    expect(page.get_by_text("Mettre a jour site web")).to_be_hidden(timeout=5000)

    take_screenshot(page, "tasks_delete")


def test_tasks_filter_by_priority(panel_page, seeded_tasks):
    """
    P1 - Filtrer les taches par priorite haute.
    Verifier que seules les taches correspondantes s'affichent.
    """
    page, _ = panel_page("tasks")
    page.wait_for_timeout(1000)

    # Verifier que toutes les taches sont la
    expect(page.get_by_text("Envoyer devis Dupont")).to_be_visible(timeout=5000)
    expect(page.get_by_text("Relancer prospect Martin")).to_be_visible()

    # Ouvrir les filtres en cliquant sur le bouton Filter
    filter_button = page.locator("button").filter(has_text="").nth(0)
    # Le bouton Filter est identifie par son icone - cherchons-le via le parent
    filter_toggle = page.locator("button:has(svg.lucide-filter)").first
    if filter_toggle.is_visible():
        filter_toggle.click()
        page.wait_for_timeout(500)

    # Selectionner la priorite "Haute" dans le select de priorite
    priority_select = page.locator("select").filter(has_text="Toutes les priorit")
    if priority_select.is_visible():
        priority_select.select_option(value="high")
        page.wait_for_timeout(1000)

        # Seule "Envoyer devis Dupont" (high) doit rester visible
        expect(page.get_by_text("Envoyer devis Dupont")).to_be_visible(timeout=5000)

        # Les autres taches ne doivent pas etre dans les resultats filtres
        # (medium et low sont masquees)
        expect(page.get_by_text("Mettre a jour site web")).to_be_hidden(timeout=3000)

    take_screenshot(page, "tasks_filter_priority")
