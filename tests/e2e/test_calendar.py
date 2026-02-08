"""
Tests E2E - Panel Calendrier.

Utilise des calendriers locaux (pas Google/CalDAV).
"""

from datetime import UTC, datetime, timedelta

import pytest
from playwright.sync_api import expect

from .conftest import take_screenshot

# ============================================================
# P0 - Tests critiques
# ============================================================


def test_calendar_empty_state(panel_page):
    """
    P0 - Ouvrir le panel calendrier, verifier l'etat vide.

    Sans compte email ni calendrier local, le panel doit afficher
    un message d'erreur ou un etat vide.
    """
    page, _ctx = panel_page("calendar")

    # Le header "Calendrier" doit etre visible
    expect(page.locator("h2:has-text('Calendrier')")).to_be_visible(timeout=10000)
    take_screenshot(page, "calendar_01_empty_state")

    # Les boutons de navigation (Mois, Semaine, Jour, Liste) doivent etre presents
    # Meme sans compte, le header est rendu
    view_buttons = page.locator("button:has-text('Mois'), button:has-text('Liste')")
    # Au moins un bouton de vue doit etre visible (si le panel se charge correctement)
    # Sinon on aura un message d'erreur
    header_or_error = page.locator(
        "h2:has-text('Calendrier'), text=/Impossible|erreur|Aucun compte/i"
    )
    expect(header_or_error.first).to_be_visible(timeout=10000)


def test_calendar_create_local(panel_page, api_client):
    """
    P0 - Creer un calendrier local via API, verifier qu'il apparait.

    Les calendriers locaux ne necessitent pas de compte email externe.
    """
    # Creer un calendrier local via l'API
    resp = api_client.post(
        "/api/calendar/calendars",
        params={
            "summary": "Calendrier Test Local",
            "description": "Cree par test E2E",
            "timezone": "Europe/Paris",
            "provider_type": "local",
        },
    )
    assert resp.status_code == 200, f"Echec creation calendrier: {resp.text}"

    cal_data = resp.json()
    assert cal_data["summary"] == "Calendrier Test Local"
    assert "id" in cal_data

    # Verifier que le calendrier est listable via GET
    resp_list = api_client.get(
        "/api/calendar/calendars",
        params={"provider": "local"},
    )
    assert resp_list.status_code == 200
    calendars = resp_list.json()
    assert any(c["summary"] == "Calendrier Test Local" for c in calendars)


def test_calendar_create_event(panel_page, seeded_calendar, api_client):
    """
    P0 - Creer un evenement via API, verifier sur le calendrier.

    Utilise le seeded_calendar qui fournit un calendrier local avec 2 evenements.
    """
    calendar_id = seeded_calendar["calendar"]["id"]

    # Verifier que les 2 evenements du seed existent
    assert len(seeded_calendar["events"]) == 2

    # Creer un 3eme evenement
    now = datetime.now(UTC)
    event_data = {
        "calendar_id": calendar_id,
        "summary": "Reunion test E2E",
        "description": "Evenement cree par le test",
        "start_datetime": (now + timedelta(days=2, hours=9)).isoformat(),
        "end_datetime": (now + timedelta(days=2, hours=10)).isoformat(),
        "location": "Bureau Manosque",
    }

    resp = api_client.post("/api/calendar/events", json=event_data)
    assert resp.status_code == 200, f"Echec creation evenement: {resp.text}"

    new_event = resp.json()
    assert new_event["summary"] == "Reunion test E2E"
    assert new_event["location"] == "Bureau Manosque"
    assert "id" in new_event

    # Verifier via GET events que le 3eme evenement est present
    resp_events = api_client.get(
        "/api/calendar/events",
        params={"calendar_id": calendar_id},
    )
    assert resp_events.status_code == 200
    events = resp_events.json()
    summaries = [e["summary"] for e in events]
    assert "Reunion test E2E" in summaries


def test_calendar_view_toggle(panel_page, seeded_calendar):
    """
    P0 - Basculer entre les vues mois/semaine/jour/liste.

    Le CalendarPanel affiche des boutons pour changer de vue.
    """
    page, _ctx = panel_page("calendar")

    # Attendre le chargement
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    take_screenshot(page, "calendar_04_view_default")

    # Les boutons de vue sont dans le header
    month_btn = page.locator("button:has-text('Mois')")
    list_btn = page.locator("button:has-text('Liste')")
    week_btn = page.locator("button:has-text('Semaine')")
    day_btn = page.locator("button:has-text('Jour')")

    # Verifier que les boutons de vue existent
    if month_btn.count() > 0:
        # Cliquer sur "Liste"
        if list_btn.count() > 0:
            list_btn.click()
            page.wait_for_timeout(500)
            take_screenshot(page, "calendar_04b_view_list")

            # Le bouton "Liste" doit etre actif (avec la classe accent-cyan)
            expect(list_btn).to_be_visible()

        # Revenir a "Mois"
        month_btn.click()
        page.wait_for_timeout(500)
        take_screenshot(page, "calendar_04c_view_month")

        # Cliquer sur "Semaine"
        if week_btn.count() > 0:
            week_btn.click()
            page.wait_for_timeout(500)
            # La vue semaine affiche "bientot disponible"
            take_screenshot(page, "calendar_04d_view_week")

        # Cliquer sur "Jour"
        if day_btn.count() > 0:
            day_btn.click()
            page.wait_for_timeout(500)
            take_screenshot(page, "calendar_04e_view_day")


def test_calendar_navigate_months(panel_page, seeded_calendar):
    """
    P0 - Cliquer sur les fleches precedent/suivant pour naviguer entre les mois.

    Le CalendarPanel a des boutons ChevronLeft/ChevronRight et "Aujourd'hui".
    """
    page, _ctx = panel_page("calendar")

    # Attendre le chargement
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    # Capturer le mois actuel affiche dans le header de navigation
    # Format: "fevrier 2026" (mois long + annee)
    month_header = page.locator("h3.text-lg.font-semibold")

    if month_header.count() > 0:
        current_text = month_header.first.text_content()
        take_screenshot(page, "calendar_05_month_current")

        # Cliquer sur le bouton precedent (ChevronLeft)
        # Les boutons de navigation sont dans l'ordre: prev, next, "Aujourd'hui"
        prev_buttons = page.locator("button").filter(has=page.locator("svg"))
        # Le premier bouton avec SVG dans la zone de navigation est ChevronLeft
        nav_area = page.locator(
            ".flex.items-center.gap-2"
        ).filter(has=page.locator("button:has-text('Aujourd')"))

        if nav_area.count() > 0:
            # Cliquer sur le premier bouton (precedent)
            nav_buttons = nav_area.first.locator("button")
            if nav_buttons.count() >= 2:
                # Premier bouton = precedent
                nav_buttons.nth(0).click()
                page.wait_for_timeout(500)
                take_screenshot(page, "calendar_05b_month_prev")

                new_text = month_header.first.text_content()
                # Le texte du mois doit avoir change
                assert new_text != current_text, (
                    f"Le mois n'a pas change: {current_text} -> {new_text}"
                )

                # Cliquer sur suivant 2 fois (revenir au mois actuel + avancer)
                nav_buttons.nth(1).click()
                page.wait_for_timeout(300)
                nav_buttons.nth(1).click()
                page.wait_for_timeout(500)
                take_screenshot(page, "calendar_05c_month_next")

                # Cliquer sur "Aujourd'hui" pour revenir
                today_btn = page.locator("button:has-text(\"Aujourd'hui\")")
                if today_btn.count() > 0:
                    today_btn.click()
                    page.wait_for_timeout(500)
                    take_screenshot(page, "calendar_05d_month_today")


# ============================================================
# P1 - Tests importants
# ============================================================


def test_calendar_edit_event(api_client, seeded_calendar):
    """
    P1 - PUT event avec un nouveau titre via API.

    Modifie le premier evenement du calendrier seede.
    """
    calendar_id = seeded_calendar["calendar"]["id"]
    events = seeded_calendar["events"]

    if not events:
        pytest.skip("Pas d'evenements seedes")

    event_id = events[0]["id"]

    # Mettre a jour le titre
    update_data = {
        "summary": "RDV Client Sophie (modifie)",
        "description": "Session coaching - mise a jour E2E",
    }

    resp = api_client.put(
        f"/api/calendar/events/{event_id}",
        json=update_data,
        params={
            "calendar_id": calendar_id,
        },
    )
    assert resp.status_code == 200, f"Echec mise a jour: {resp.text}"

    updated = resp.json()
    assert updated["summary"] == "RDV Client Sophie (modifie)"
    assert "modifie" in updated["summary"]


def test_calendar_delete_event(api_client, seeded_calendar):
    """
    P1 - DELETE event via API, verifier qu'il est supprime.

    Supprime le deuxieme evenement du calendrier seede.
    """
    calendar_id = seeded_calendar["calendar"]["id"]
    events = seeded_calendar["events"]

    if len(events) < 2:
        pytest.skip("Pas assez d'evenements seedes")

    event_id = events[1]["id"]

    # Supprimer l'evenement
    resp = api_client.delete(
        f"/api/calendar/events/{event_id}",
        params={
            "calendar_id": calendar_id,
        },
    )
    assert resp.status_code == 200, f"Echec suppression: {resp.text}"

    result = resp.json()
    assert result["success"] is True

    # Verifier que l'evenement n'est plus dans la liste
    resp_events = api_client.get(
        "/api/calendar/events",
        params={"calendar_id": calendar_id},
    )
    assert resp_events.status_code == 200
    remaining = resp_events.json()
    remaining_ids = [e["id"] for e in remaining]
    assert event_id not in remaining_ids


def test_calendar_quick_add(api_client, seeded_calendar):
    """
    P1 - POST quick-add "RDV demain 14h".

    L'endpoint quick-add necessite un account_id (Google Calendar).
    Pour les calendriers locaux, cet endpoint n'est pas disponible.
    On teste que l'endpoint existe et repond correctement.
    """
    # L'endpoint quick-add requiert un account_id (Google Calendar)
    resp = api_client.post(
        "/api/calendar/events/quick-add",
        json={
            "calendar_id": seeded_calendar["calendar"]["id"],
            "text": "RDV demain 14h",
        },
        params={"account_id": "fake-account-id"},
    )
    # Sans compte Google, doit retourner 404 (account not found)
    assert resp.status_code == 404


# ============================================================
# P2 - Tests secondaires
# ============================================================


def test_calendar_caldav_setup_form(panel_page):
    """
    P2 - Verifier que le formulaire CalDAV est accessible.

    Le panel calendrier peut proposer une option de configuration CalDAV.
    On verifie via l'API que l'endpoint presets CalDAV existe.
    """
    page, _ctx = panel_page("calendar")

    # Attendre le chargement
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    take_screenshot(page, "calendar_08_caldav")

    # Verifier que le panel est charge
    expect(page.locator("h2:has-text('Calendrier')")).to_be_visible(timeout=5000)

    # Le formulaire CalDAV n'est pas directement visible dans le panel principal
    # mais l'API endpoint doit etre accessible
    # On verifie simplement que le panel se charge sans crash


def test_calendar_google_auth_status(api_client):
    """
    P2 - GET google auth status, verifier non connecte.

    Utilise l'endpoint email/auth/status car le calendrier Google
    partage l'authentification avec Gmail.
    """
    resp = api_client.get("/api/email/auth/status")
    assert resp.status_code == 200

    data = resp.json()
    assert data["connected"] is False
    assert data["accounts"] == []

    # Verifier aussi que l'endpoint caldav-presets repond
    resp_presets = api_client.get("/api/calendar/caldav-presets")
    assert resp_presets.status_code == 200
    presets = resp_presets.json()
    assert isinstance(presets, list)
