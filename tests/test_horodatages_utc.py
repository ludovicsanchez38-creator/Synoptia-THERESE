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
