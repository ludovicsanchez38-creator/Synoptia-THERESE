"""B-1389 (persona Nathalie, cycle 13) : l'export vCard perdait les étiquettes.

Hélène a `tags: ["cliente", "reconversion"]` en base ; sa carte exportée n'avait
pas de ligne CATEGORIES (la propriété vCard standard des étiquettes). Une
étiquette saisie disparaissait du fichier, sans le dire.
"""

import pytest


@pytest.mark.asyncio
async def test_l_export_porte_les_etiquettes(client):
    reponse = await client.post("/api/memory/contacts", json={
        "first_name": "Hélène", "last_name": "Ménard-Lefèvre", "tags": ["cliente", "reconversion"],
    })
    assert reponse.status_code in (200, 201), reponse.text

    export = await client.get("/api/memory/contacts/export")
    assert export.status_code == 200
    texte = export.content.decode("utf-8")
    carte = next(bloc for bloc in texte.split("END:VCARD") if "Ménard-Lefèvre" in bloc)
    assert "CATEGORIES:cliente,reconversion" in carte
