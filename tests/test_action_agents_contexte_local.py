"""B-342 et B-343 (05/09/2026) : le contexte local des agents actionnables
était vide pour les outils courriel et agenda, et personne ne le voyait.

`_gather_local_context` importait une entité `Email` qui n'existe pas
(`EmailMessage` est la bonne), et instanciait `CalendarService()` sans jeton
avec une méthode `get_upcoming_events` absente de la classe. Les deux
erreurs tombaient dans un `except Exception` journalisé en debug : l'agent
« Préparation RDV » recevait « (Aucune donnée locale disponible pour cette
action.) » et raisonnait sans les courriels ni l'agenda qu'il annonçait.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.services.action_agents import _gather_local_context


async def _seme_un_courriel(subject: str) -> None:
    from app.models import database as db_module
    from app.models.entities import EmailAccount, EmailMessage

    async with db_module.AsyncSessionLocal() as session:
        compte = EmailAccount(email="marie@atelier.test", provider="imap")
        session.add(compte)
        await session.flush()
        session.add(
            EmailMessage(
                id="msg-contexte-1",
                thread_id="thr-1",
                account_id=compte.id,
                subject=subject,
                from_email="paul@durand.test",
                from_name="Paul Durand",
                to_emails="[]",
                labels="[]",
                date=datetime.now(UTC),
                internal_date=datetime.now(UTC),
            )
        )
        await session.commit()


async def _seme_un_evenement(summary: str, dans_jours: int) -> None:
    from app.models import database as db_module
    from app.models.entities import Calendar, CalendarEvent

    async with db_module.AsyncSessionLocal() as session:
        agenda = Calendar(id="cal-contexte", summary="Agenda", provider="local")
        session.add(agenda)
        await session.flush()
        debut = datetime.now(UTC) + timedelta(days=dans_jours)
        session.add(
            CalendarEvent(
                id=f"evt-{summary}",
                calendar_id=agenda.id,
                summary=summary,
                start_datetime=debut,
                end_datetime=debut + timedelta(hours=1),
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_l_outil_email_livre_les_courriels_recents(client):
    await _seme_un_courriel("Relance devis salon")

    contexte = await _gather_local_context(["email"])

    assert "Emails recents" in contexte, contexte
    assert "Relance devis salon" in contexte
    assert "Paul Durand" in contexte


@pytest.mark.asyncio
async def test_l_outil_calendar_livre_les_evenements_a_venir(client):
    await _seme_un_evenement("Rendez-vous Garage Benali", dans_jours=2)

    contexte = await _gather_local_context(["calendar"])

    assert "Evenements a venir" in contexte, contexte
    assert "Rendez-vous Garage Benali" in contexte


@pytest.mark.asyncio
async def test_l_outil_calendar_ignore_le_passe(client):
    await _seme_un_evenement("Reunion d'hier", dans_jours=-1)

    contexte = await _gather_local_context(["calendar"])

    assert "Reunion d'hier" not in contexte


class TestLOutilRechercheWeb:
    """B-331 (05/09/2026) : « Veille concurrentielle » et « Préparation RDV »
    déclaraient l'outil `web_search` (action_agents.json) sans qu'aucun code
    ne le serve : ni collecteur de contexte, ni passage d'outils au modèle.
    L'agent annonçait une recherche qu'il ne faisait pas, et le modèle
    remplissait le vide. Désormais : la recherche est faite avec les
    paramètres de l'action quand elle est autorisée, et l'absence est dite
    en clair sinon.
    """

    @pytest.fixture(autouse=True)
    def _autorisation_neutre(self):
        from app.services.web_search import poser_autorisation_recherche

        yield
        poser_autorisation_recherche(None)

    @pytest.mark.asyncio
    async def test_la_recherche_est_faite_avec_les_parametres_de_l_action(self, monkeypatch):
        from app.services import web_search as module
        from app.services.web_search import (
            SearchResponse,
            SearchResult,
            poser_autorisation_recherche,
        )

        poser_autorisation_recherche(True)
        requetes: list[str] = []

        class Faux:
            async def search(self, query, max_results=5, **kwargs):
                requetes.append(query)
                return SearchResponse(
                    query=query,
                    results=[SearchResult(title="Garage Benali : avis", url="https://exemple.test/benali", snippet="Carrosserie à Manosque", source="test")],
                    total_results=1,
                )

        monkeypatch.setattr(module, "get_web_search_service", lambda: Faux())

        contexte = await _gather_local_context(["web_search"], {"entreprise": "Garage Benali"})

        assert requetes == ["Garage Benali"], requetes
        assert "Recherche web" in contexte, contexte
        assert "Garage Benali : avis" in contexte
        assert "exemple.test/benali" in contexte

    @pytest.mark.asyncio
    async def test_sans_autorisation_l_absence_est_dite(self, monkeypatch):
        from app.services import web_search as module
        from app.services.web_search import poser_autorisation_recherche

        poser_autorisation_recherche(False)
        appels = {"n": 0}

        class Faux:
            async def search(self, query, max_results=5, **kwargs):
                appels["n"] += 1
                raise AssertionError("aucune recherche ne doit partir sans autorisation")

        monkeypatch.setattr(module, "get_web_search_service", lambda: Faux())

        contexte = await _gather_local_context(["web_search"], {"entreprise": "Garage Benali"})

        assert appels["n"] == 0
        assert "Recherche web" in contexte
        assert "aucune recherche" in contexte.lower(), contexte
