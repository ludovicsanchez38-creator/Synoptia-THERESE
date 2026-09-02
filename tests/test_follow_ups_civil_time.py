"""Une date de relance e-mail est un jour civil Europe/Paris."""

from datetime import UTC, datetime

import pytest
from app.models.entities import EmailAccount, EmailFollowUp, EmailMessage
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_due_utilise_le_jour_de_paris_a_la_frontiere_utc(
    client: AsyncClient, db_session, monkeypatch
):
    """À 22 h 30 UTC en été, la relance du lendemain UTC est déjà due à Paris."""
    class DateUTC(datetime):
        @classmethod
        def now(cls, tz=None):
            instant = cls(2026, 8, 29, 22, 30, tzinfo=UTC)
            return instant.astimezone(tz) if tz else instant.replace(tzinfo=None)

    account = EmailAccount(id="account-follow-up-clock", email="ludo@example.test")
    message = EmailMessage(
        id="message-follow-up-clock",
        thread_id="thread-follow-up-clock",
        account_id=account.id,
        subject="Relance civile",
        from_email="client@example.test",
        to_emails='["ludo@example.test"]',
        date=datetime(2026, 8, 1, tzinfo=UTC),
        internal_date=datetime(2026, 8, 1, tzinfo=UTC),
        labels="[]",
    )
    follow_up = EmailFollowUp(
        id="follow-up-clock",
        email_message_id=message.id,
        due_date="2026-08-30T09:00:00",
    )
    db_session.add_all([account, message, follow_up])
    await db_session.commit()
    monkeypatch.setattr("app.routers.follow_ups.datetime", DateUTC)

    response = await client.get("/api/follow-ups/due")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [follow_up.id]


# ============================================================
# B-062 — l'API n'accepte plus d'heure métier qu'elle perdra ensuite
# ============================================================


async def _message_de_relance(db_session, suffixe: str) -> str:
    """Un e-mail auquel accrocher une relance."""
    compte = EmailAccount(id=f"compte-{suffixe}", email="ludo@example.test")
    message = EmailMessage(
        id=f"message-{suffixe}",
        thread_id=f"fil-{suffixe}",
        account_id=compte.id,
        subject="Relance à reporter",
        from_email="client@example.test",
        to_emails='["ludo@example.test"]',
        date=datetime(2026, 8, 1, tzinfo=UTC),
        internal_date=datetime(2026, 8, 1, tzinfo=UTC),
        labels="[]",
    )
    db_session.add_all([compte, message])
    await db_session.commit()
    return message.id


class TestB062EcheanceNormaliseeEnJourCivil:
    """Une échéance de relance est un JOUR, pas un instant.

    Les trois lecteurs backend tronquent déjà `due_date` à dix caractères
    (follow_ups.py:98 et :138, dashboard.py:400) et l'interface ne collecte
    qu'une date. Mais l'API acceptait n'importe quelle chaîne ISO : une
    relance posée à 17 h 30 par un appel direct ou un import portait une heure
    que la première modification écrasait en 09:00, sans que rien ne l'ait
    annoncé — c'est le « report qui réécrit l'heure » de la fiche. Poser la
    normalisation à l'entrée rend cette perte impossible : il n'y a plus
    d'heure d'utilisateur à perdre, à aucun moment.

    Ce que ce test NE couvre PAS, et qui vit dans src/frontend : le calcul
    « En retard » (FollowUpsWorkspaceCanvas.tsx, comparaison à l'instant) et
    l'affichage de l'heure (`timeStyle: 'short'`), qui donne au remplissage
    l'apparence d'une donnée métier.
    """

    @pytest.mark.asyncio
    async def test_la_creation_normalise_l_heure(self, client, db_session):
        message_id = await _message_de_relance(db_session, "b062-creation")

        creee = await client.post(
            "/api/follow-ups",
            json={"email_message_id": message_id, "due_date": "2026-09-10T17:30:00"},
        )
        assert creee.status_code == 200, creee.text
        assert creee.json()["due_date"] == "2026-09-10T09:00:00", (
            "une heure métier a été acceptée : la première modification la perdra"
        )

    @pytest.mark.asyncio
    async def test_le_report_ne_reecrit_aucune_heure_stockee(self, client, db_session):
        """Le scénario exact de la fiche.

        Une relance posée à 17 h 30 hors interface, puis reportée depuis
        l'écran — qui n'envoie QUE `T09:00:00`, sa constante de remplissage.
        Avant, l'heure passait de 17:30 à 09:00 sans que personne l'ait
        demandé. Après, il n'y a plus d'heure à réécrire : les deux valeurs
        portent la même partie horaire.
        """
        message_id = await _message_de_relance(db_session, "b062-report")

        creee = await client.post(
            "/api/follow-ups",
            json={"email_message_id": message_id, "due_date": "2026-09-10T17:30:00"},
        )
        assert creee.status_code == 200, creee.text
        avant = creee.json()["due_date"]

        # Charge utile réelle de FollowUpsWorkspaceCanvas.saveEdit.
        reportee = await client.put(
            f"/api/follow-ups/{creee.json()['id']}",
            json={"due_date": "2026-09-12T09:00:00", "note": ""},
        )
        assert reportee.status_code == 200, reportee.text
        apres = reportee.json()["due_date"]

        assert avant[10:] == apres[10:], (
            f"le report a changé la partie horaire ({avant} -> {apres}) : "
            "une heure avait donc été stockée, puis réécrite en silence"
        )
        assert apres == "2026-09-12T09:00:00"

    @pytest.mark.asyncio
    async def test_une_date_seule_est_acceptee(self, client, db_session):
        """Le jour civil est la seule information demandée : il suffit."""
        message_id = await _message_de_relance(db_session, "b062-date-seule")

        creee = await client.post(
            "/api/follow-ups",
            json={"email_message_id": message_id, "due_date": "2026-09-10"},
        )
        assert creee.status_code == 200, creee.text
        assert creee.json()["due_date"] == "2026-09-10T09:00:00"

    @pytest.mark.asyncio
    async def test_un_instant_date_est_ramene_au_jour_de_paris(self, client, db_session):
        """23 h 30 UTC le 10 = déjà le 11 à Paris : c'est le jour métier qui compte."""
        message_id = await _message_de_relance(db_session, "b062-fuseau")

        creee = await client.post(
            "/api/follow-ups",
            json={"email_message_id": message_id, "due_date": "2026-09-10T23:30:00+00:00"},
        )
        assert creee.status_code == 200, creee.text
        assert creee.json()["due_date"] == "2026-09-11T09:00:00"

    @pytest.mark.asyncio
    async def test_une_echeance_illisible_est_refusee(self, client, db_session):
        """Une chaîne qui ne désigne aucun jour ne doit pas atteindre la base."""
        message_id = await _message_de_relance(db_session, "b062-illisible")

        refus = await client.post(
            "/api/follow-ups",
            json={"email_message_id": message_id, "due_date": "la semaine prochaine"},
        )
        assert refus.status_code == 422, refus.text
