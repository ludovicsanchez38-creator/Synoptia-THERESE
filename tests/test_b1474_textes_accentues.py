"""B-1474 (recette P-146, lot 5, KO-12) : textes affichés sans accents.

Paramètres > Outils > Presets affichait « Recupere le contenu d'URLs »,
« Bases de donnees », « Gestion de taches », « Recherche web avancee »...
Le test passe par la route que lit l'écran.
"""

import re

import pytest
from httpx import AsyncClient

# Formes sans accent relevées à l'écran ; chacune n'existe qu'accentuée en français.
FORMES_SANS_ACCENT = re.compile(
    r"\b(recupere|donnees|taches|avancee|augmentee|activites|etape|structure$|strategie)\b",
    re.IGNORECASE,
)


@pytest.mark.asyncio
async def test_les_descriptions_des_preglages_sont_accentuees(client: AsyncClient):
    reponse = await client.get("/api/mcp/presets")
    assert reponse.status_code == 200
    fautes = [
        f"{p['name']} : {p['description']}"
        for p in reponse.json()
        if FORMES_SANS_ACCENT.search(p.get("description", ""))
    ]
    assert fautes == []

