"""
Une seule définition de « à relancer » (plan du 29/08, lot 2).

Avant : le brief et la cloche répondaient différemment à la même question.
Sur les vraies données de Ludo, le brief comptait 24 et la cloche 20, parce
que l'un comptait les contacts sans aucune date et l'autre les excluait.

Après : une relance est une DATE POSÉE et échue. Pas de date, pas de devoir.
THÉRÈSE n'invente plus une relance à partir d'un silence.
"""
from datetime import UTC, datetime, time, timedelta

import pytest
from app.models.entities import Contact, Notification
from app.services.civil_time import date_civile_paris
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
    # `next_follow_up` désigne un JOUR décidé, et le seuil est la date civile
    # de Paris (cf. `contacts_a_relancer`). `now + 24 h` n'est donc pas
    # toujours un AUTRE jour : entre 22 h et minuit UTC, l'heure d'été place
    # l'instant obtenu sur le jour civil de Paris en cours, et le test
    # rougissait deux heures par nuit sans qu'aucun code n'ait changé.
    demain = datetime.combine(
        date_civile_paris() + timedelta(days=1), time(12, 0), tzinfo=UTC
    )
    db_session.add(_contact(next_follow_up=demain))
    await db_session.commit()

    trouves = (await db_session.execute(contacts_a_relancer())).scalars().all()

    assert trouves == []


@pytest.mark.asyncio
async def test_une_relance_est_due_pendant_tout_son_jour_civil_paris(
    db_session: AsyncSession,
):
    """Le 30 civil commence avant le 30 UTC pendant l'heure d'été."""
    contact = _contact(
        id="relance-frontiere-paris",
        next_follow_up=datetime(2026, 8, 30, 23, 59, tzinfo=UTC),
    )
    db_session.add(contact)
    await db_session.commit()

    instant = datetime(2026, 8, 29, 22, 30, tzinfo=UTC)
    trouves = (await db_session.execute(contacts_a_relancer(instant))).scalars().all()

    assert [item.id for item in trouves] == [contact.id]


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


@pytest.mark.asyncio
async def test_un_contact_anonymise_ne_se_relance_pas(db_session: AsyncSession):
    """`archive` est le tombeau RGPD, pas une étape commerciale.

    L'anonymisation vide le nom, l'e-mail et les notes, pose `stage=archive`
    et ne touche PAS `next_follow_up`. Sans exclusion, le brief afficherait
    « Relancer [ANONYMISÉ] » et la cloche sonnerait dessus.
    """
    hier = datetime.now(UTC) - timedelta(days=1)
    db_session.add(_contact(first_name="[ANONYMISÉ]", stage="archive", next_follow_up=hier))
    await db_session.commit()

    trouves = (await db_session.execute(contacts_a_relancer())).scalars().all()

    assert trouves == []


@pytest.mark.asyncio
async def test_relancer_pour_de_vrai_solde_la_date(db_session: AsyncSession):
    """Le devoir doit pouvoir s'éteindre.

    Sans ce geste, une date échue reste au brief pour toujours : on aurait
    remplacé un devoir inventé par un devoir éternel.
    """
    from app.services.relances import solder_la_relance

    hier = datetime.now(UTC) - timedelta(days=1)
    c = _contact(next_follow_up=hier)
    db_session.add(c)
    await db_session.commit()

    solder_la_relance(c)
    await db_session.commit()

    assert c.next_follow_up is None
    assert (await db_session.execute(contacts_a_relancer())).scalars().all() == []


@pytest.mark.asyncio
async def test_une_activite_crm_solde_la_relance(db_session: AsyncSession):
    """Consigner un appel, c'est avoir relancé. Le parcours, pas l'helper."""
    from app.models.schemas import CreateActivityRequest
    from app.routers.crm import create_activity

    hier = datetime.now(UTC) - timedelta(days=1)
    c = _contact(next_follow_up=hier)
    db_session.add(c)
    await db_session.commit()

    await create_activity(
        CreateActivityRequest(contact_id=c.id, type="call", title="Appel de relance"),
        db_session,
    )

    await db_session.refresh(c)
    assert c.next_follow_up is None, "consigner une relance doit éteindre le devoir"


@pytest.mark.asyncio
async def test_la_plus_en_retard_est_la_premiere(db_session: AsyncSession):
    """La plus en retard vient en premier.

    LIMITE CONNUE de ce test : il ne detecte PAS un `order_by` manquant, parce
    que SQLite utilise l'index sur `next_follow_up` pour le balayage et rend
    donc les lignes deja triees. Le sabotage a ete joue : il passe. Ce que ce
    test garantit reellement, c'est le contrat rendu a l'appelant, pas le
    mecanisme. Le `order_by` reste indispensable : sur une base migree sans
    index, l'ordre serait celui du rowid (d'ou l'index pose dans la migration).
    """
    for jours, nom in ((1, "Recente"), (90, "Ancienne"), (30, "Moyenne")):
        db_session.add(_contact(last_name=nom, next_follow_up=datetime.now(UTC) - timedelta(days=jours)))
    await db_session.commit()

    trouves = (await db_session.execute(contacts_a_relancer())).scalars().all()

    assert [c.last_name for c in trouves] == ["Ancienne", "Moyenne", "Recente"]


@pytest.mark.asyncio
async def test_le_brief_http_expose_la_date_et_ignore_les_archives(
    client, db_session: AsyncSession
):
    """Le garde passe par GET /today, pas par le wrapper interne.

    La première version de ce test appelait `prospects_a_relancer` : une
    requête réécrite en ligne dans la route serait passée inaperçue.
    """
    hier = datetime.now(UTC) - timedelta(days=1)
    db_session.add(_contact(last_name="Vivant", next_follow_up=hier))
    db_session.add(_contact(last_name="Mort", stage="archive", next_follow_up=hier))
    await db_session.commit()

    reponse = await client.get("/api/dashboard/today")
    prospects = reponse.json()["stale_prospects"]

    assert [p["name"] for p in prospects] == ["Alex Vivant"]
    assert prospects[0]["next_follow_up"] is not None, (
        "l'écran doit pouvoir dire POURQUOI cette ligne est là"
    )


@pytest.mark.asyncio
async def test_on_peut_poser_et_solder_une_date_depuis_l_api(client):
    """Sans écriture, seul un import peut poser une relance : la
    fonctionnalité serait inutilisable depuis l'application.
    """
    cree = await client.post(
        "/api/memory/contacts",
        json={"first_name": "Poser", "last_name": "Date", "next_follow_up": "2026-01-15T00:00:00Z"},
    )
    assert cree.status_code in (200, 201), cree.text
    fiche = cree.json()
    assert fiche["next_follow_up"] is not None, "la réponse doit rendre la date posée"

    du_brief = (await client.get("/api/dashboard/today")).json()["stale_prospects"]
    assert [p["name"] for p in du_brief] == ["Poser Date"]

    solde = await client.patch(
        f"/api/memory/contacts/{fiche['id']}", json={"next_follow_up": None}
    )
    assert solde.status_code == 200, solde.text

    apres = (await client.get("/api/dashboard/today")).json()["stale_prospects"]
    assert apres == [], "solder la date doit retirer la ligne du brief"


@pytest.mark.asyncio
async def test_le_chat_voit_la_date_de_relance(db_session: AsyncSession):
    """« Qui dois-je relancer ? » ne doit pas se répondre avec le passé.

    `read_contact` envoyait `last_interaction` et pas la date décidée : le
    modèle parlait de la dernière fois qu'on s'était parlé, ou inventait.
    """
    import json as _json

    from app.services.memory_tools import execute_memory_tool

    hier = datetime.now(UTC) - timedelta(days=1)
    c = _contact(last_name="Ponzo", next_follow_up=hier)
    db_session.add(c)
    await db_session.commit()

    brut = await execute_memory_tool("read_contact", {"query": "Ponzo"}, db_session)
    charge = _json.loads(brut)

    fiche = charge.get("contacts", [charge])[0] if isinstance(charge, dict) else charge[0]
    assert "next_follow_up" in fiche, "le modèle doit voir la date décidée"
    assert fiche["next_follow_up"] is not None


@pytest.mark.asyncio
async def test_une_note_ne_solde_pas_la_relance(db_session: AsyncSession):
    """Écrire une note n'est PAS avoir relancé.

    Défaut introduit le 29/08 : `solder_la_relance` s'exécutait pour tous les
    types d'activité. Consigner une correction (« CORRECTION de ma note de ce
    matin ») éteignait silencieusement un devoir. Seul un GESTE vers la
    personne solde : appel, e-mail, rendez-vous.
    """
    from app.models.schemas import CreateActivityRequest
    from app.routers.crm import create_activity

    hier = datetime.now(UTC) - timedelta(days=1)
    c = _contact(next_follow_up=hier)
    db_session.add(c)
    await db_session.commit()

    await create_activity(
        CreateActivityRequest(contact_id=c.id, type="note", title="CORRECTION : c'est PROPULSER"),
        db_session,
    )

    await db_session.refresh(c)
    assert c.next_follow_up is not None, "une note n'est pas une relance"


@pytest.mark.asyncio
async def test_un_geste_vers_la_personne_solde_bien(db_session: AsyncSession):
    from app.models.schemas import CreateActivityRequest
    from app.routers.crm import create_activity

    hier = datetime.now(UTC) - timedelta(days=1)
    for type_de_geste in ("call", "email", "meeting"):
        c = _contact(last_name=type_de_geste, next_follow_up=hier)
        db_session.add(c)
        await db_session.commit()

        await create_activity(
            CreateActivityRequest(contact_id=c.id, type=type_de_geste, title="Relance"),
            db_session,
        )
        await db_session.refresh(c)
        assert c.next_follow_up is None, f"{type_de_geste} doit solder la relance"


@pytest.mark.asyncio
async def test_une_echeance_posee_en_instant_utc_garde_son_jour_civil_paris(
    client, db_session: AsyncSession
):
    """Une échéance envoyée en instant absolu ne doit pas avancer d'un jour.

    `next_follow_up` est lu comme un JOUR décidé (`func.date` dans
    `contacts_a_relancer`), mais l'API l'acceptait en instant brut. Or SQLite
    JETTE le décalage à l'écriture : `2026-08-30T23:30:00Z` devenait
    `2026-08-30 23:30`, dont la date lue est le 30 alors que le jour civil de
    Paris est le 31. La relance tombait due le 30, un jour trop tôt, et
    l'information nécessaire pour le rattraper à la lecture n'existait plus.
    """
    reponse = await client.post(
        "/api/memory/contacts",
        json={
            "first_name": "Nadia",
            "last_name": "Frontiere",
            # 23 h 30 UTC = 1 h 30 le lendemain à Paris (heure d'été).
            "next_follow_up": "2026-08-30T23:30:00Z",
        },
    )
    assert reponse.status_code == 200, reponse.text
    identifiant = reponse.json()["id"]

    enregistre = await db_session.get(Contact, identifiant)
    await db_session.refresh(enregistre)
    assert enregistre is not None
    assert enregistre.next_follow_up is not None
    assert enregistre.next_follow_up.date().isoformat() == "2026-08-31", (
        "le jour retenu doit être le jour civil de Paris, pas la date UTC"
    )

    # Le 30 à 22 h UTC, il est minuit passé de rien à Paris : on est le 30
    # civil, et une échéance du 31 n'est pas encore due.
    veille = datetime(2026, 8, 30, 20, 0, tzinfo=UTC)
    trouves = (await db_session.execute(contacts_a_relancer(veille))).scalars().all()
    assert trouves == [], "une échéance du 31 ne doit pas être due le 30"

    # ... et elle l'est bien dès le 31 civil, qui commence à 22 h UTC le 30.
    lendemain = datetime(2026, 8, 30, 22, 30, tzinfo=UTC)
    dues = (await db_session.execute(contacts_a_relancer(lendemain))).scalars().all()
    assert [c.id for c in dues] == [identifiant]
