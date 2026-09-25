"""B-1301 : un fichier JSON d'import CRM qui n'est ni une liste ni un objet
(« 42 », « "texte" », {"contacts": 5}) faisait tomber l'import en 500 au lieu
d'un refus lisible. Lecteur X, passe 5."""

import pytest
from app.services.crm_import import CRMImportService


@pytest.mark.asyncio
@pytest.mark.parametrize("contenu", [b"42", b'"texte"', b'{"contacts": 5}', b"null"])
async def test_un_json_hors_forme_est_refuse_lisiblement(db_session, contenu):
    res = await CRMImportService(db_session).import_contacts(contenu, filename="c.json")
    assert res.success is False, res
    assert res.message.startswith("Import impossible"), res.message
