"""B-1664 : la synchro tableur effaçait le courriel de chaque fiche quand la
feuille n'avait pas de colonne Email. Une cellule vide garde son sens de
miroir (B-1107) ; une colonne absente ne dit rien et ne touche à rien.
"""

import pytest


@pytest.mark.asyncio
async def test_une_colonne_email_absente_garde_le_courriel(db_session):
    from app.services.crm_utils import upsert_contact

    await upsert_contact(db_session, {"ID": "crm-b1664", "Nom": "Jeanne Martin", "Email": "jeanne@exemple.fr"})
    await db_session.commit()
    contact, _ = await upsert_contact(db_session, {"ID": "crm-b1664", "Nom": "Jeanne Martin", "Tel": "06 00 00 00 00"})

    assert contact.email == "jeanne@exemple.fr"


@pytest.mark.asyncio
async def test_temoin_une_cellule_email_vide_efface_toujours(db_session):
    from app.services.crm_utils import upsert_contact

    await upsert_contact(db_session, {"ID": "crm-b1664b", "Nom": "Jeanne Martin", "Email": "jeanne@exemple.fr"})
    await db_session.commit()
    contact, _ = await upsert_contact(db_session, {"ID": "crm-b1664b", "Nom": "Jeanne Martin", "Email": ""})

    assert contact.email is None
