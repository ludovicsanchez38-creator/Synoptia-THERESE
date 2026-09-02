"""Les portes de l'agenda qui prennent un identifiant.

Quatre défauts de la deuxième salve « robustesse API » du cycle 2, tous sur
`routers/calendar.py`, tous sur des routes qui reçoivent un identifiant :

- B-181 (RB2-011) : `GET` et `DELETE /calendars/{id}` exigent un `account_id`
  et le comparent à celui du calendrier. Un calendrier local naît avec
  `account_id` à NULL : aucune valeur ne pouvait convenir, la route était donc
  fermée à tout ce que l'application crée elle-même. Le `DELETE` chargeait de
  surcroît un compte Google pour supprimer un calendrier SQLite.
- B-180 (RB2-010) : `GET /events/{id}` déclare `calendar_id` et `account_id`
  (obligatoire) et n'en lit AUCUN. N'importe quelle valeur donnait accès à
  n'importe quel événement, y compris celui d'un autre compte connecté.
- B-182 (RB2-012) : `POST /calendars` lit ses paramètres dans l'URL. Un corps
  JSON était ignoré en entier et la route rendait 200 comme si elle avait
  obéi - le client `createCalendar` envoie pourtant un corps JSON.
- B-236 (volet serveur) : `GET /events?calendar_id=<inconnu>` tombait dans la
  branche Google et répondait « account_id requis pour Google Calendar » pour
  un calendrier qui n'existe simplement pas.
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient


@pytest.fixture
def sample_event_datetime() -> dict:
    maintenant = datetime.now(UTC)
    return {
        "summary": "Reunion test",
        "description": "Description de la reunion",
        "location": "Bureau Manosque",
        "start_datetime": (maintenant + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S"),
        "end_datetime": (maintenant + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S"),
    }


async def _calendrier_local(client: AsyncClient, nom: str = "Agenda RB2") -> dict:
    reponse = await client.post(
        "/api/calendar/calendars",
        params={"summary": nom, "timezone": "Europe/Paris", "provider_type": "local"},
    )
    assert reponse.status_code == 200, reponse.text[:200]
    return reponse.json()


class TestUnCalendrierLocalEstLisibleEtSupprimable:
    """B-181."""

    @pytest.mark.asyncio
    async def test_il_se_lit_par_son_identifiant(self, client: AsyncClient):
        calendrier = await _calendrier_local(client, "Agenda lisible")

        reponse = await client.get(f"/api/calendar/calendars/{calendrier['id']}")

        assert reponse.status_code == 200, (
            "un calendrier local n'est pas lisible par son identifiant : "
            f"{reponse.status_code} {reponse.text[:200]}"
        )
        assert reponse.json()["summary"] == "Agenda lisible"

    @pytest.mark.asyncio
    async def test_il_se_supprime_par_son_identifiant(self, client: AsyncClient):
        calendrier = await _calendrier_local(client, "Agenda jetable")

        reponse = await client.delete(f"/api/calendar/calendars/{calendrier['id']}")

        assert reponse.status_code == 200, (
            "un calendrier local n'est pas supprimable : "
            f"{reponse.status_code} {reponse.text[:200]}"
        )
        restants = [c["id"] for c in (await client.get("/api/calendar/calendars?create_default=false")).json()]
        assert calendrier["id"] not in restants, "le calendrier est toujours là"

    @pytest.mark.asyncio
    async def test_le_compte_d_un_autre_ne_l_ouvre_pas(self, client: AsyncClient):
        """La garde reste fermée dans l'autre sens."""
        calendrier = await _calendrier_local(client, "Agenda cloisonné")

        reponse = await client.get(
            f"/api/calendar/calendars/{calendrier['id']}?account_id=un-autre-compte"
        )

        assert reponse.status_code == 404, (
            f"un compte étranger lit le calendrier : {reponse.status_code}"
        )


class TestUnEvenementNeSOuvrePasAvecNImporteQuoi:
    """B-180."""

    @pytest.mark.asyncio
    async def test_un_compte_etranger_est_refuse(self, client: AsyncClient, sample_event_datetime):
        calendrier = await _calendrier_local(client, "Agenda événement")
        evenement = (
            await client.post(
                "/api/calendar/events",
                json={**sample_event_datetime, "calendar_id": calendrier["id"]},
            )
        ).json()

        reponse = await client.get(
            f"/api/calendar/events/{evenement['id']}"
            "?account_id=NIMPORTEQUOI&calendar_id=AUSSI"
        )

        assert reponse.status_code == 404, (
            "deux paramètres déclarés, aucun lu : n'importe quelle valeur ouvre "
            f"n'importe quel événement ({reponse.status_code})"
        )

    @pytest.mark.asyncio
    async def test_un_calendrier_etranger_est_refuse(self, client: AsyncClient, sample_event_datetime):
        calendrier = await _calendrier_local(client, "Agenda A")
        autre = await _calendrier_local(client, "Agenda B")
        evenement = (
            await client.post(
                "/api/calendar/events",
                json={**sample_event_datetime, "calendar_id": calendrier["id"]},
            )
        ).json()

        reponse = await client.get(
            f"/api/calendar/events/{evenement['id']}?calendar_id={autre['id']}"
        )

        assert reponse.status_code == 404, (
            f"un événement se lit depuis un calendrier voisin : {reponse.status_code}"
        )

    @pytest.mark.asyncio
    async def test_la_lecture_legitime_passe_toujours(self, client: AsyncClient, sample_event_datetime):
        calendrier = await _calendrier_local(client, "Agenda légitime")
        evenement = (
            await client.post(
                "/api/calendar/events",
                json={**sample_event_datetime, "calendar_id": calendrier["id"]},
            )
        ).json()

        reponse = await client.get(
            f"/api/calendar/events/{evenement['id']}?calendar_id={calendrier['id']}"
        )

        assert reponse.status_code == 200, (
            f"la garde ferme la lecture légitime : {reponse.status_code} {reponse.text[:200]}"
        )
        assert reponse.json()["summary"] == "Reunion test"


class TestLeCorpsDeCreationDeCalendrierEstLu:
    """B-182."""

    @pytest.mark.asyncio
    async def test_un_corps_conforme_nomme_le_calendrier(self, client: AsyncClient):
        reponse = await client.post(
            "/api/calendar/calendars",
            json={"summary": "Cal2 RB2", "provider_type": "local"},
        )

        assert reponse.status_code == 200, reponse.text[:200]
        assert reponse.json()["summary"] == "Cal2 RB2", (
            "le corps JSON est ignoré en entier et la route rend 200 comme si "
            f"elle avait obéi : {reponse.text[:200]}"
        )

    @pytest.mark.asyncio
    async def test_un_champ_inconnu_est_refuse(self, client: AsyncClient):
        """La charge exacte de la reproduction : `provider` n'existe pas."""
        reponse = await client.post(
            "/api/calendar/calendars",
            json={"summary": "Cal2 RB2", "provider": "local"},
        )

        assert reponse.status_code == 422, (
            f"un champ inconnu est absorbé en silence : {reponse.status_code} "
            f"{reponse.text[:200]}"
        )

    @pytest.mark.asyncio
    async def test_les_parametres_d_url_restent_acceptes(self, client: AsyncClient):
        calendrier = await _calendrier_local(client, "Par l'URL")
        assert calendrier["summary"] == "Par l'URL"


class TestUnCalendrierInconnuLeDit:
    """B-236, volet serveur."""

    @pytest.mark.asyncio
    async def test_les_evenements_d_un_calendrier_inconnu_rendent_404(self, client: AsyncClient):
        reponse = await client.get(
            "/api/calendar/events?calendar_id=be06b033-0000-0000-0000-000000000000"
        )

        assert reponse.status_code == 404, (
            "un calendrier introuvable rend un 400 sur un fournisseur qui n'est "
            f"pas en cause : {reponse.status_code} {reponse.text[:200]}"
        )
        message = reponse.text.lower()
        assert "account_id" not in message and "google" not in message, (
            f"le message parle de Google pour un calendrier qui n'existe pas : {reponse.text[:200]}"
        )

    @pytest.mark.asyncio
    async def test_le_calendrier_google_par_defaut_reclame_toujours_un_compte(
        self, client: AsyncClient
    ):
        """`primary` est l'alias Google : lui, réclame bien un compte."""
        reponse = await client.get("/api/calendar/events?calendar_id=primary")

        assert reponse.status_code == 400, reponse.text[:200]
        assert "account_id" in reponse.text
