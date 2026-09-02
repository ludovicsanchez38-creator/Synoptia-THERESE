"""B-216 — un horodatage servi par l'API porte son fuseau.

Les entités écrivent un datetime conscient (`datetime.now(UTC)`), mais SQLite
le relit sans tzinfo et la réponse le rendait tel quel :
`"2026-09-02T12:05:13.825470"`, sans « Z » ni décalage. ECMAScript parse une
date-heure sans offset comme HEURE LOCALE : le poste affichait donc l'heure
UTC comme si c'était la sienne, soit deux heures de retard à Paris en
septembre. Le rattrapage appartient à la sérialisation, pas à chaque écran :
les consommateurs sont nombreux et un correctif par appelant en laisse passer.
"""

from datetime import datetime

import pytest
from httpx import AsyncClient


def _est_conscient(valeur: str) -> bool:
    """Vrai si la chaîne ISO désigne un instant absolu, pas une heure de mur."""
    instant = datetime.fromisoformat(valeur.replace("Z", "+00:00"))
    return instant.tzinfo is not None and instant.utcoffset() is not None


@pytest.mark.asyncio
async def test_created_at_porte_le_fuseau(client: AsyncClient):
    """POST puis GET /api/chat/conversations : les deux horodatages sont datés."""
    creee = await client.post("/api/chat/conversations", json={"title": "Horodatage B-216"})
    assert creee.status_code == 200, creee.text

    for champ in ("created_at", "updated_at"):
        valeur = creee.json()[champ]
        assert _est_conscient(valeur), f"POST {champ} = {valeur!r} : aucun fuseau"

    listees = await client.get("/api/chat/conversations")
    assert listees.status_code == 200, listees.text
    conversation = next(c for c in listees.json() if c["title"] == "Horodatage B-216")

    for champ in ("created_at", "updated_at"):
        valeur = conversation[champ]
        assert _est_conscient(valeur), f"GET {champ} = {valeur!r} : aucun fuseau"


@pytest.mark.asyncio
async def test_l_instant_rendu_est_bien_l_instant_ecrit(client: AsyncClient):
    """La chaîne datée désigne le même instant que l'horloge du serveur.

    Un correctif qui se contenterait de coller « Z » sur une heure LOCALE
    passerait le test précédent tout en décalant l'instant : on vérifie donc
    l'écart au temps réel, pas seulement la présence du suffixe.
    """
    avant = datetime.now(tz=datetime.now().astimezone().tzinfo)
    creee = await client.post("/api/chat/conversations", json={"title": "Instant B-216"})
    assert creee.status_code == 200, creee.text

    brut = creee.json()["created_at"]
    assert _est_conscient(brut), f"created_at = {brut!r} : aucun fuseau, instant indéterminable"

    rendu = datetime.fromisoformat(brut.replace("Z", "+00:00"))
    ecart = abs((rendu - avant).total_seconds())
    assert ecart < 120, (
        f"created_at rendu {rendu.isoformat()} contre {avant.isoformat()} : "
        f"{ecart:.0f} s d'écart, l'instant n'est pas celui de l'écriture"
    )


class TestLaTimelineCrmPorteSonFuseau:
    """B-206 — la même panne, sur les surfaces du CRM.

    `_activity_to_response` et `_deliverable_to_response` construisent leur
    horodatage à la main (`.isoformat()` sur la date relue de SQLite, donc
    naïve), sans passer par le sérialiseur posé pour B-216. Une activité créée
    trois minutes plus tôt s'affichait « Il y a 2h » à Paris en septembre :
    l'écran lisait une heure UTC comme si c'était la sienne.

    Ce qui reste volontairement en heure de mur : `due_date` d'un livrable,
    qui est un JOUR décidé par quelqu'un (`<input type="date">`) et non un
    instant d'horloge — lui coller « +00:00 » le ferait basculer d'un jour.
    """

    @pytest.mark.asyncio
    async def test_une_activite_rend_un_instant_date(self, client: AsyncClient):
        contact = await client.post(
            "/api/memory/contacts", json={"first_name": "Fuseau", "last_name": "Activite"}
        )
        assert contact.status_code == 200, contact.text

        creee = await client.post(
            "/api/crm/activities",
            json={
                "contact_id": contact.json()["id"],
                "type": "note",
                "title": "Horodatage B-206",
            },
        )
        assert creee.status_code == 200, creee.text

        valeur = creee.json()["created_at"]
        assert _est_conscient(valeur), f"POST created_at = {valeur!r} : aucun fuseau"

        listees = await client.get("/api/crm/activities")
        assert listees.status_code == 200, listees.text
        activite = next(a for a in listees.json() if a["title"] == "Horodatage B-206")
        assert _est_conscient(activite["created_at"]), (
            f"GET created_at = {activite['created_at']!r} : aucun fuseau"
        )

    @pytest.mark.asyncio
    async def test_l_instant_d_une_activite_est_celui_de_l_ecriture(
        self, client: AsyncClient
    ):
        """Coller « Z » sur une heure locale passerait le test précédent."""
        contact = await client.post(
            "/api/memory/contacts", json={"first_name": "Instant", "last_name": "Activite"}
        )
        avant = datetime.now(tz=datetime.now().astimezone().tzinfo)

        creee = await client.post(
            "/api/crm/activities",
            json={
                "contact_id": contact.json()["id"],
                "type": "note",
                "title": "Instant B-206",
            },
        )
        assert creee.status_code == 200, creee.text

        brut = creee.json()["created_at"]
        assert _est_conscient(brut), f"created_at = {brut!r} : instant indéterminable"
        ecart = abs((datetime.fromisoformat(brut.replace("Z", "+00:00")) - avant).total_seconds())
        assert ecart < 120, (
            f"created_at rendu {brut} contre {avant.isoformat()} : {ecart:.0f} s d'écart"
        )

    @pytest.mark.asyncio
    async def test_un_livrable_date_ses_instants_sans_dater_son_echeance(
        self, client: AsyncClient
    ):
        projet = await client.post(
            "/api/memory/projects", json={"name": "Projet horodatage B-206"}
        )
        assert projet.status_code == 200, projet.text

        cree = await client.post(
            "/api/crm/deliverables",
            json={
                "project_id": projet.json()["id"],
                "title": "Livrable B-206",
                "due_date": "2026-09-30T00:00:00",
            },
        )
        assert cree.status_code == 200, cree.text
        corps = cree.json()

        for champ in ("created_at", "updated_at"):
            assert _est_conscient(corps[champ]), (
                f"{champ} = {corps[champ]!r} : aucun fuseau"
            )

        # L'échéance est un JOUR, pas un instant : elle reste littérale.
        assert corps["due_date"].startswith("2026-09-30"), corps["due_date"]

        valide = await client.put(
            f"/api/crm/deliverables/{corps['id']}", json={"status": "valide"}
        )
        assert valide.status_code == 200, valide.text
        assert _est_conscient(valide.json()["completed_at"]), (
            f"completed_at = {valide.json()['completed_at']!r} : aucun fuseau"
        )
