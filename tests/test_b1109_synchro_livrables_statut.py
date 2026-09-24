"""B-1109 (lecteurs I1 et J1, carte c12) : la synchro tableur des livrables
(bouton de l'app, crm.py) n'acceptait que pending, in_progress, completed et
blocked, hors du contrat a_faire, en_cours, en_revision, valide. Un livrable
« valide » dans la feuille était réécrit « pending » à chaque synchro.
"""

from __future__ import annotations

import pytest
from app.models.entities import Deliverable, Project
from app.services.crm_utils import upsert_deliverable_from_import


async def _projet(session) -> None:
    session.add(Project(id="projet-b1109", name="Chantier"))
    await session.commit()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("saisi", "attendu"),
    [("valide", "valide"), ("Validé", "valide"), ("en_revision", "en_revision"), ("completed", "valide"), ("pending", "a_faire"), ("in_progress", "en_cours")],
)
async def test_le_statut_suit_le_contrat_des_livrables(db_session, saisi: str, attendu: str):
    await _projet(db_session)
    livrable, cree = await upsert_deliverable_from_import(
        db_session, {"ID": "livrable-b1109", "ProjectID": "projet-b1109", "Title": "Plan", "Status": saisi}, safe_get=True
    )
    assert cree
    assert livrable.status == attendu


@pytest.mark.asyncio
@pytest.mark.parametrize("saisi", ["", "Gelé"])
async def test_un_statut_absent_ou_inconnu_ne_remplace_rien(db_session, saisi: str):
    await _projet(db_session)
    db_session.add(Deliverable(id="livrable-b1109", project_id="projet-b1109", title="Plan", status="en_revision"))
    await db_session.commit()
    livrable, cree = await upsert_deliverable_from_import(
        db_session, {"ID": "livrable-b1109", "ProjectID": "projet-b1109", "Title": "Plan v2", "Status": saisi}, safe_get=True
    )
    assert not cree
    assert livrable.title == "Plan v2"
    assert livrable.status == "en_revision"


@pytest.mark.asyncio
async def test_un_nouveau_livrable_sans_statut_est_a_faire(db_session):
    await _projet(db_session)
    livrable, _ = await upsert_deliverable_from_import(
        db_session, {"ID": "livrable-b1109", "ProjectID": "projet-b1109", "Title": "Plan"}, safe_get=True
    )
    assert livrable.status == "a_faire"
