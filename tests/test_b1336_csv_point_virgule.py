"""B-1336 : un CSV exporté par Excel en français est séparé par des
points-virgules ; lu comme séparé par des virgules, chaque ligne était
rejetée (« Au moins un nom ou une entreprise est requis »). Lecteur ε,
passe 8."""

import pytest
from app.services.crm_import import CRMImportService


@pytest.mark.asyncio
@pytest.mark.parametrize("separateur", [";", ",", "\t"])
async def test_le_separateur_est_detecte(db_session, separateur):
    lignes = [["first_name", "last_name", "company"], ["Marie", "Exemple", "Exemple, SARL"]]
    contenu = "\n".join(
        separateur.join(f'"{c}"' if separateur == "," and "," in c else c for c in ligne) for ligne in lignes
    ).encode()
    res = await CRMImportService(db_session).import_contacts(contenu, filename="c.csv")
    assert res.created == 1, [e.message for e in res.errors]
