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


@pytest.mark.asyncio
async def test_une_liste_sans_objets_est_refusee_a_l_apercu_et_a_l_import(db_session):
    """B-1312 : résidu de B-1301, `[1, 2]` passait la lecture et l'aperçu
    tombait en 500 sur `raw_data[0].keys()`. Lecteur α, passe 6."""
    service = CRMImportService(db_session)
    apercu = await service.preview_contacts(b"[1, 2]", filename="c.json")
    assert apercu.can_import is False and apercu.validation_errors, apercu
    res = await service.import_contacts(b"[1, 2]", filename="c.json")
    assert res.message.startswith("Import impossible"), res.message


@pytest.mark.asyncio
@pytest.mark.parametrize("contenu", [b"{pas du json", b"\xff\xfe\x00"])
async def test_un_json_illisible_repond_en_francais(db_session, contenu):
    """B-1326 : le message technique anglais de JSONDecodeError (ou de
    UnicodeDecodeError) remontait tel quel. Lecteur δ, passe 7."""
    res = await CRMImportService(db_session).import_contacts(contenu, filename="c.json")
    assert res.message.startswith("Import impossible : Fichier JSON illisible"), res.message
