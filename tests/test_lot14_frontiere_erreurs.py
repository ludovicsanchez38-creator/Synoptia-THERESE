"""Lot 14 (05/09/2026) : huit sorties de route du backend, reproduites par RP17.

Chaque classe porte un bug confirmé. Le fil commun : une entrée inattendue
mais légitime (fichier mal formé, chaîne trop longue, date impossible,
identifiant fantôme, double clic) doit rendre une réponse française et
maîtrisée, jamais un 500 ni le texte brut d'une bibliothèque.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

VCF_CASSE = b"PAS UNE VCARD\nDU TOUT\n"


async def _contact(client: AsyncClient) -> str:
    reponse = await client.post(
        "/api/memory/contacts",
        json={"first_name": "Claire", "last_name": "Roux", "email": "claire@roux.test"},
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["id"]


async def _agenda_local(client: AsyncClient, nom: str = "Agenda local") -> dict:
    reponse = await client.post(
        "/api/calendar/calendars",
        params={"summary": nom, "timezone": "Europe/Paris", "provider_type": "local"},
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


async def _evenement(client: AsyncClient, calendar_id: str) -> dict:
    reponse = await client.post(
        "/api/calendar/events",
        json={
            "calendar_id": calendar_id,
            "summary": "Point lot 14",
            "start_datetime": "2026-09-10T10:00:00",
            "end_datetime": "2026-09-10T11:00:00",
        },
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


class TestB552VcfIllisible:
    """Le message d'un VCF cassé est français, sans le texte brut de vobject."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "route", ["/api/crm/import/vcf", "/api/memory/contacts/import"]
    )
    async def test_message_francais(self, client: AsyncClient, route: str):
        reponse = await client.post(
            route, files={"file": ("cassé.vcf", VCF_CASSE, "text/vcard")}
        )
        assert reponse.status_code == 400, reponse.text
        message = reponse.json()["message"]
        assert "Failed to parse" not in message
        assert "At line" not in message
        assert "VCF" in message or "vCard" in message


class TestB553B555FuseauHostile:
    """Un fuseau trop long, vide ou traversant est refusé par le même message."""

    def _evenement(self, timezone: str):
        from app.models.schemas import CreateEventRequest

        return CreateEventRequest(
            summary="Test",
            start_datetime="2026-09-10T10:00:00",
            end_datetime="2026-09-10T11:00:00",
            timezone=timezone,
        )

    def _planning(self, timezone: str):
        from app.models.planning_schemas import CalculateScheduleRequest

        return CalculateScheduleRequest(timezone=timezone)

    @pytest.mark.parametrize("timezone", ["ROBUSTESSE-Z" * 450])
    def test_fuseau_trop_long_sur_un_evenement(self, timezone: str):
        with pytest.raises(ValidationError) as erreur:
            self._evenement(timezone)
        assert "Fuseau horaire IANA invalide" in str(erreur.value)

    @pytest.mark.parametrize(
        "timezone", ["ROBUSTESSE-Z" * 450, "", "../../etc/localtime"]
    )
    def test_fuseau_hostile_sur_le_planning(self, timezone: str):
        with pytest.raises(ValidationError) as erreur:
            self._planning(timezone)
        texte = str(erreur.value)
        assert "Fuseau horaire IANA invalide" in texte
        assert "TZPATH" not in texte
        assert "normalized relative paths" not in texte


class TestB554CheminTropLong:
    """Un chemin de 5000 caractères est refusé, pas une OSError en 500."""

    @pytest.mark.asyncio
    async def test_dossier_de_travail(self, client: AsyncClient):
        reponse = await client.post(
            "/api/config/working-directory", json={"path": "A" * 5000}
        )
        assert reponse.status_code == 400, reponse.text
        assert "unknown_error" not in reponse.text

    @pytest.mark.asyncio
    async def test_indexation_de_fichier(self, client: AsyncClient):
        reponse = await client.post("/api/files/index", json={"path": "A" * 5000})
        assert reponse.status_code in (400, 404), reponse.text
        assert "unknown_error" not in reponse.text


class TestB556SuppressionDeuxFois:
    """Supprimer un événement local absent rend 404, comme sa lecture."""

    @pytest.mark.asyncio
    async def test_second_clic(self, client: AsyncClient):
        agenda = await _agenda_local(client)
        evenement = await _evenement(client, agenda["id"])
        premier = await client.delete(
            f"/api/calendar/events/{evenement['id']}?calendar_id={agenda['id']}"
        )
        assert premier.status_code == 200, premier.text
        second = await client.delete(
            f"/api/calendar/events/{evenement['id']}?calendar_id={agenda['id']}"
        )
        assert second.status_code == 404, second.text
        assert "Google" not in second.json()["message"]

    @pytest.mark.asyncio
    async def test_identifiant_inconnu(self, client: AsyncClient):
        agenda = await _agenda_local(client)
        reponse = await client.delete(
            f"/api/calendar/events/jamais-existe?calendar_id={agenda['id']}"
        )
        assert reponse.status_code == 404, reponse.text


class TestB557AliasPrimaryLocal:
    """Sans compte Google, l'alias `primary` désigne l'agenda local principal."""

    @pytest.mark.asyncio
    async def test_lecture_sans_calendar_id(self, client: AsyncClient):
        agendas = (await client.get("/api/calendar/calendars")).json()
        principal = next(a for a in agendas if a["primary"])
        assert principal["provider"] == "local"
        await _evenement(client, principal["id"])

        reponse = await client.get("/api/calendar/events")
        assert reponse.status_code == 200, reponse.text
        assert [e["summary"] for e in reponse.json()] == ["Point lot 14"]

    @pytest.mark.asyncio
    async def test_suppression_sans_calendar_id(self, client: AsyncClient):
        agendas = (await client.get("/api/calendar/calendars")).json()
        principal = next(a for a in agendas if a["primary"])
        evenement = await _evenement(client, principal["id"])

        reponse = await client.delete(f"/api/calendar/events/{evenement['id']}")
        assert reponse.status_code == 200, reponse.text
        restants = await client.get(f"/api/calendar/events?calendar_id={principal['id']}")
        assert restants.json() == []

    @pytest.mark.asyncio
    async def test_sans_agenda_local_l_alias_reclame_toujours_un_compte(
        self, client: AsyncClient
    ):
        reponse = await client.get("/api/calendar/events?calendar_id=primary")
        assert reponse.status_code == 400, reponse.text


class TestB558DateImpossible:
    """Un 30 février rend 422 en français, à la création comme à la mise à jour."""

    @pytest.mark.asyncio
    async def test_creation(self, client: AsyncClient):
        contact = await _contact(client)
        reponse = await client.post(
            "/api/invoices/",
            json={
                "contact_id": contact,
                "issue_date": "2026-02-30",
                "lines": [{"description": "Conseil", "unit_price_ht": 1}],
            },
        )
        assert reponse.status_code == 422, reponse.text
        assert "invalide" in reponse.text

    @pytest.mark.asyncio
    async def test_mise_a_jour(self, client: AsyncClient):
        contact = await _contact(client)
        creation = await client.post(
            "/api/invoices/",
            json={"contact_id": contact, "lines": [{"description": "Conseil", "unit_price_ht": 1}]},
        )
        assert creation.status_code == 200, creation.text
        reponse = await client.put(
            f"/api/invoices/{creation.json()['id']}", json={"due_date": "2026-13-01"}
        )
        assert reponse.status_code == 422, reponse.text
        assert "invalide" in reponse.text


class TestB559MontantNonFini:
    """Infinity et NaN n'atteignent ni le calcul des totaux ni la base."""

    @pytest.mark.parametrize("valeur", [float("inf"), float("nan"), float("-inf")])
    def test_le_schema_refuse(self, valeur: float):
        from app.models.schemas import InvoiceLineRequest

        with pytest.raises(ValidationError):
            InvoiceLineRequest(description="x", unit_price_ht=valeur)

    @pytest.mark.asyncio
    async def test_l_api_rend_422(self, client: AsyncClient):
        contact = await _contact(client)
        corps = (
            '{"contact_id": "%s", "lines": [{"description": "x", "unit_price_ht": Infinity}]}'
            % contact
        ).encode()
        reponse = await client.post(
            "/api/invoices/", content=corps, headers={"content-type": "application/json"}
        )
        assert reponse.status_code == 422, reponse.text


class TestB561DocumentSurProjetFantome:
    """Un document ne naît pas rattaché à un projet ou un contact inexistant."""

    @pytest.mark.asyncio
    async def test_projet_fantome(self, client: AsyncClient):
        reponse = await client.post(
            "/api/documents",
            json={"title": "Doc", "brief": "b", "project_id": "projet-fantome"},
        )
        assert reponse.status_code == 404, reponse.text
        assert "Projet" in reponse.json()["message"]

    @pytest.mark.asyncio
    async def test_contact_fantome(self, client: AsyncClient):
        reponse = await client.post(
            "/api/documents",
            json={"title": "Doc", "brief": "b", "contact_id": "contact-fantome"},
        )
        assert reponse.status_code == 404, reponse.text
        assert "Contact" in reponse.json()["message"]

    @pytest.mark.asyncio
    async def test_sans_rattachement_reste_possible(self, client: AsyncClient):
        reponse = await client.post("/api/documents", json={"title": "Doc", "brief": "b"})
        assert reponse.status_code == 200, reponse.text
