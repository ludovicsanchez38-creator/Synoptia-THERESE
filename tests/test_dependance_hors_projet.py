"""B-531 (cycle 4) : une dépendance dont une seule extrémité appartient au projet
rendait TOUT le planning invalide, et aucune route ne permettait de la retirer :
l'écran ne pouvait qu'afficher une erreur sans issue. Elle est désormais
écartée du calcul avec un avertissement, et une route de suppression existe."""

from __future__ import annotations

import pytest
from sqlalchemy import select


async def _deux_projets_lies(db_session):
    from app.models.entities import Project, Task, TaskDependency

    chantier = Project(name="Chantier Ruiz")
    autre = Project(name="Dossier Martin")
    db_session.add_all([chantier, autre])
    await db_session.flush()
    t1 = Task(title="Dépose", project_id=chantier.id)
    t2 = Task(title="Pose", project_id=chantier.id)
    ailleurs = Task(title="Devis Martin", project_id=autre.id)
    db_session.add_all([t1, t2, ailleurs])
    await db_session.flush()
    interne = TaskDependency(predecessor_task_id=t1.id, successor_task_id=t2.id)
    a_cheval = TaskDependency(predecessor_task_id=ailleurs.id, successor_task_id=t2.id)
    db_session.add_all([interne, a_cheval])
    await db_session.commit()
    return chantier.id, autre.id, interne.id, a_cheval.id


@pytest.mark.asyncio
async def test_une_dependance_a_cheval_n_invalide_plus_le_planning(client, db_session):
    chantier, _autre, _interne, _a_cheval = await _deux_projets_lies(db_session)

    reponse = await client.post(f"/api/projects/{chantier}/schedule/calculate", json={})
    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert corps["state"] != "invalid", corps
    assert any("autre projet" in avertissement for avertissement in corps["warnings"]), corps["warnings"]


@pytest.mark.asyncio
async def test_la_dependance_a_cheval_se_supprime_depuis_le_projet_et_l_avertissement_tombe(client, db_session):
    from app.models.entities import TaskDependency

    chantier, _autre, interne, a_cheval = await _deux_projets_lies(db_session)
    await client.post(f"/api/projects/{chantier}/schedule/calculate", json={})

    suppression = await client.delete(f"/api/projects/{chantier}/dependencies/{a_cheval}")
    assert suppression.status_code == 204, suppression.text

    db_session.expire_all()
    restantes = (await db_session.execute(select(TaskDependency.id))).scalars().all()
    assert set(restantes) == {interne}

    recalcul = await client.post(f"/api/projects/{chantier}/schedule/calculate", json={})
    assert recalcul.status_code == 200, recalcul.text
    assert recalcul.json()["reused_snapshot"] is False, "la suppression doit changer l'empreinte des entrées"
    assert not any("autre projet" in a for a in recalcul.json()["warnings"])


@pytest.mark.asyncio
async def test_une_dependance_etrangere_au_projet_n_est_pas_supprimable_par_lui(client, db_session):
    from app.models.entities import Project, Task, TaskDependency

    chantier, autre, _interne, _a_cheval = await _deux_projets_lies(db_session)
    tiers = Project(name="Tiers")
    db_session.add(tiers)
    await db_session.flush()
    a = Task(title="a", project_id=tiers.id)
    b = Task(title="b", project_id=tiers.id)
    db_session.add_all([a, b])
    await db_session.flush()
    etrangere = TaskDependency(predecessor_task_id=a.id, successor_task_id=b.id)
    db_session.add(etrangere)
    await db_session.commit()

    reponse = await client.delete(f"/api/projects/{chantier}/dependencies/{etrangere.id}")
    assert reponse.status_code == 404
    reponse = await client.delete(f"/api/projects/{autre}/dependencies/inconnue")
    assert reponse.status_code == 404
