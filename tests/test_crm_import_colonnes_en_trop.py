"""B-551 (05/09/2026) : une ligne CSV plus longue que son en-tête.

`csv.DictReader` range les valeurs excédentaires sous la clé `None`. Cette
clé remontait dans `detected_columns`, dont le schéma de réponse exige des
chaînes : l'aperçu d'import rendait 500 pour un fichier que l'import réel
acceptait. L'aperçu et l'import doivent digérer les mêmes fichiers.
"""
import pytest
from app.services.crm_import import _parse_csv


def test_parse_csv_ignore_les_valeurs_sans_en_tete():
    lignes = _parse_csv(b"first_name,email\nFoo,foo@x.com,extra1,extra2\n")
    assert lignes == [{"first_name": "Foo", "email": "foo@x.com"}]


@pytest.mark.asyncio
async def test_apercu_import_accepte_une_ligne_trop_longue(client):
    contenu = "first_name,email\nFoo,foo@x.com,extra1,extra2\n"
    files = {"file": ("trop-long.csv", contenu.encode(), "text/csv")}
    response = await client.post("/api/crm/import/contacts/preview", files=files)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["detected_columns"] == ["first_name", "email"]
    assert data["total_rows"] == 1
