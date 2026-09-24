"""B-1110 (cycle 12, réparé au cycle 13) : sans périmètre, `read_contact`
ferme comme les fichiers.

`_perimetre_de_conversation` rend (None, None) quand la conversation est
absente ou introuvable. `_cloison_contacts` n'appliquait alors aucun filtre :
le modèle lisait les contacts rattachés à n'importe quel dossier et ceux
enregistrés dans d'autres conversations, alors que `_cloison_fichiers` ferme
dans le même cas. Sans périmètre, l'outil ne rend plus que le carnet général.
"""

import json

import pytest
from app.models.entities import Contact
from app.services.memory_tools import execute_read_contact


async def _carnet(session) -> None:
    session.add(Contact(id="c-general", first_name="Martin", last_name="Général", scope="global"))
    session.add(Contact(id="c-dossier", first_name="Martin", last_name="Dossier", scope="project", scope_id="projet-a"))
    session.add(Contact(id="c-prive", first_name="Martin", last_name="Privé", scope="conversation", scope_id="conv-autre"))
    await session.commit()


def _noms(reponse: str) -> set[str]:
    charge = json.loads(reponse)
    fiches = charge.get("contacts") or charge.get("matches") or ([charge["contact"]] if "contact" in charge else [])
    return {f.get("last_name") for f in fiches}


@pytest.mark.asyncio
async def test_sans_perimetre_seul_le_carnet_general_est_lisible(db_session):
    await _carnet(db_session)
    reponse = await execute_read_contact({"query": "Martin"}, db_session, scope=None, scope_id=None, conversation_id=None)
    assert "Dossier" not in reponse and "Privé" not in reponse, reponse[:400]
    assert "Général" in reponse


@pytest.mark.asyncio
async def test_dans_son_dossier_le_contact_du_dossier_reste_lisible(db_session):
    await _carnet(db_session)
    reponse = await execute_read_contact({"query": "Martin"}, db_session, scope="project", scope_id="projet-a")
    assert "Dossier" in reponse and "Général" in reponse
    assert "Privé" not in reponse
