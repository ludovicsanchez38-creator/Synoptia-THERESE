"""
Une seule définition de « à relancer » (plan du 29/08, lot 2).

Avant : le brief et la cloche répondaient différemment à la même question.
Sur les vraies données de Ludo, le brief comptait 24 et la cloche 20, parce
que l'un comptait les contacts sans aucune date et l'autre les excluait.

Après : une relance est une DATE POSÉE et échue. Pas de date, pas de devoir.
THÉRÈSE n'invente plus une relance à partir d'un silence.
"""
from datetime import UTC, datetime, timedelta

import pytest
from app.models.entities import Contact, Notification
from app.services.relances import contacts_a_relancer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select


def _contact(**kw) -> Contact:
    base = {"first_name": "Alex", "last_name": "Martin", "stage": "contact"}
    return Contact(**{**base, **kw})


@pytest.mark.asyncio
async def test_une_date_echue_est_une_relance(db_session: AsyncSession):
    hier = datetime.now(UTC) - timedelta(days=1)
    db_session.add(_contact(next_follow_up=hier))
    await db_session.commit()

    trouves = (await db_session.execute(contacts_a_relancer())).scalars().all()

    assert len(trouves) == 1


@pytest.mark.asyncio
async def test_une_date_a_venir_n_est_pas_une_relance(db_session: AsyncSession):
    demain = datetime.now(UTC) + timedelta(days=1)
    db_session.add(_contact(next_follow_up=demain))
    await db_session.commit()

    trouves = (await db_session.execute(contacts_a_relancer())).scalars().all()

    assert trouves == []


@pytest.mark.asyncio
async def test_le_silence_n_est_pas_un_devoir(db_session: AsyncSession):
    """Le coeur du lot : sans date, aucune relance, meme apres deux ans.

    L'ancienne regle deduisait un devoir d'une absence d'interaction. Elle
    affirmait « Relancer Dupont » a propos de quelqu'un qui n'avait rien
    demande.
    """
    il_y_a_deux_ans = datetime.now(UTC) - timedelta(days=730)
    db_session.add(_contact(last_interaction=il_y_a_deux_ans, next_follow_up=None))
    db_session.add(_contact(first_name="Sans", last_name="Trace", last_interaction=None))
    await db_session.commit()

    trouves = (await db_session.execute(contacts_a_relancer())).scalars().all()

    assert trouves == []


@pytest.mark.asyncio
async def test_l_etape_ne_filtre_pas(db_session: AsyncSession):
    """Un devoir pose sur un client en est un.

    Les vraies echeances de Ludo (questionnaire a froid, seance, attestation)
    portent sur des contacts `active`, que l'ancienne regle ne regardait meme
    pas.
    """
    hier = datetime.now(UTC) - timedelta(days=1)
    for etape in ("contact", "discovery", "proposition", "active", "delivery"):
        db_session.add(_contact(last_name=etape, stage=etape, next_follow_up=hier))
    await db_session.commit()

    trouves = (await db_session.execute(contacts_a_relancer())).scalars().all()

    assert len(trouves) == 5


@pytest.mark.asyncio
async def test_le_brief_et_la_cloche_comptent_pareil(db_session: AsyncSession):
    """Le garde-fou contre le jumeau.

    Les deux surfaces doivent appeler la MEME fonction. Ce test echoue si
    quelqu'un reintroduit une deuxieme definition ailleurs.
    """
    from app.routers.dashboard import prospects_a_relancer
    from app.services.notification_service import _check_inactive_prospects

    hier = datetime.now(UTC) - timedelta(days=1)
    db_session.add(_contact(next_follow_up=hier))
    db_session.add(_contact(first_name="Sans", last_name="Date", last_interaction=None))
    await db_session.commit()

    du_brief = await prospects_a_relancer(db_session)

    # La cloche est REELLEMENT executee, pas seulement importee : la premiere
    # version de ce test se contentait de `assert callable(...)`, ce qui est
    # vrai quoi qu'il arrive. Un sabotage qui redonnait sa propre requete a la
    # cloche passait sans bruit.
    posees = await _check_inactive_prospects(db_session)
    await db_session.commit()

    notifs = (
        await db_session.execute(
            select(Notification).where(Notification.source == "crm")
        )
    ).scalars().all()

    assert len(du_brief) == 1, "le brief doit voir la seule relance echue"
    assert posees == 1, "la cloche doit poser exactement une notification"
    assert len(notifs) == 1
    assert notifs[0].action_url == f"/crm/contacts/{du_brief[0]['id']}", (
        "la cloche et le brief doivent parler du MEME contact"
    )
