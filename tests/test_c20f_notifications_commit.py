"""B-1168 : une notification n'est annoncée lue qu'après son commit."""

import httpx
import pytest
from app.main import app
from app.models import database
from app.models.entities import Notification
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlmodel import select


async def appeler_avec_commit_en_echec(db_session, monkeypatch, methode, chemin, erreur=None):
    notification = Notification(id="a-lire", title="Relance", message="Relance locale")
    db_session.add(notification)
    await db_session.commit()
    fabrique = database.AsyncSessionLocal
    traces = []

    def session_en_echec():
        session = fabrique()

        async def commit():
            traces.append("commit refusé")
            if erreur is not None:
                raise erreur
            raise OperationalError("COMMIT", {}, RuntimeError("Échec simulé du commit"))

        monkeypatch.setattr(session, "commit", commit)
        return session

    monkeypatch.setattr(database, "AsyncSessionLocal", session_en_echec)

    async def application(scope, receive, send):
        async def observer(message):
            if message["type"] == "http.response.start":
                traces.append(f"HTTP {message['status']}")
            await send(message)

        await app(scope, receive, observer)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        reponse = await client.request(methode, chemin)
    async with fabrique() as relecture:
        relue = await relecture.get(Notification, "a-lire")
        assert relue.is_read is False
        assert relue.read_at is None
    print(f"{methode} {chemin} : {traces}; notification toujours non lue")
    return reponse, traces


@pytest.mark.parametrize("methode,chemin", [
    ("PATCH", "/api/notifications/a-lire/read"),
    ("POST", "/api/notifications/read-all"),
])
async def test_echec_commit_visible_avant_reponse(db_session, monkeypatch, methode, chemin):
    reponse, traces = await appeler_avec_commit_en_echec(db_session, monkeypatch, methode, chemin)
    assert reponse.status_code == 500, traces
    assert traces.index("commit refusé") < traces.index("HTTP 500")


@pytest.mark.parametrize("methode,chemin,erreur,etats", [
    ("PATCH", "/api/notifications/a-lire/read", OSError("Disque simulé"), (False,)),
    ("PATCH", "/api/notifications/a-lire/read", ConnectionError("Connexion simulée"), (False,)),
    ("PATCH", "/api/notifications/a-lire/read", RuntimeError("Transaction simulée"), (False,)),
    ("POST", "/api/notifications/read-all", OSError("Disque simulé"), (False,)),
    ("POST", "/api/notifications/read-all", ConnectionError("Connexion simulée"), (False,)),
    ("POST", "/api/notifications/read-all", RuntimeError("Transaction simulée"), (False,)),
    ("PATCH", "/api/notifications/a-lire/read", None, (False, False)),
    ("PATCH", "/api/notifications/a-lire/read", None, (True, False)),
    ("POST", "/api/notifications/read-all", None, (False, True, False)),
    ("POST", "/api/notifications/read-all", None, (True, True)),
])
async def test_dix_rejeux_commit_apres_astra(db_session, monkeypatch, methode, chemin, erreur, etats):
    if erreur is not None:
        reponse, traces = await appeler_avec_commit_en_echec(
            db_session, monkeypatch, methode, chemin, erreur,
        )
        assert reponse.status_code == 500
        assert traces.index("commit refusé") < traces.index("HTTP 500")
        return
    for i, lu in enumerate(etats):
        db_session.add(Notification(
            id="a-lire" if i == 0 else f"autre-{i}", title="Relance", message="Locale", is_read=lu,
        ))
    await db_session.commit()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test",
    ) as client:
        reponse = await client.request(methode, chemin)
        assert reponse.status_code == 200
        if methode == "POST":
            assert reponse.json()["marked_read"] == etats.count(False)
        else:
            assert reponse.json()["is_read"] is True
        async with database.AsyncSessionLocal() as relecture:
            notifications = (await relecture.execute(select(Notification))).scalars().all()
            assert sum(not n.is_read for n in notifications) == (
                0 if methode == "POST" else etats[1:].count(False)
            )
        bis = await client.request(methode, chemin)
        assert bis.status_code == 200
        if methode == "POST":
            assert bis.json()["marked_read"] == 0


@pytest.mark.parametrize("methode,chemin", [
    ("PATCH", "/api/notifications/a-lire/read"),
    ("POST", "/api/notifications/read-all"),
])
async def test_verrou_sqlite_echoue_avant_le_commit(db_session, monkeypatch, methode, chemin):
    db_session.add(Notification(id="a-lire", title="Relance", message="Locale"))
    await db_session.commit()
    fabrique = database.AsyncSessionLocal
    commits = []
    erreurs_sql = []

    def session_avec_delai_court():
        session = fabrique()
        executer, commettre, vider = session.execute, session.commit, session.flush

        async def execute(*args, **kwargs):
            await executer(text("PRAGMA busy_timeout=50"))
            try:
                return await executer(*args, **kwargs)
            except OperationalError:
                erreurs_sql.append("execute")
                raise

        async def flush(*args, **kwargs):
            try:
                return await vider(*args, **kwargs)
            except OperationalError:
                erreurs_sql.append("flush")
                raise

        async def commit():
            commits.append(True)
            await commettre()

        monkeypatch.setattr(session, "execute", execute)
        monkeypatch.setattr(session, "flush", flush)
        monkeypatch.setattr(session, "commit", commit)
        return session

    async with fabrique() as ecriture:
        await ecriture.execute(text("BEGIN IMMEDIATE"))
        monkeypatch.setattr(database, "AsyncSessionLocal", session_avec_delai_court)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test",
        ) as client:
            reponse = await client.request(methode, chemin)
        await ecriture.rollback()
    assert reponse.status_code == 500
    assert erreurs_sql == (["flush"] if methode == "PATCH" else ["execute"])
    assert commits == []
    async with fabrique() as relecture:
        assert (await relecture.get(Notification, "a-lire")).is_read is False
    print(f"Verrou réel {methode} : HTTP 500, erreur dans {erreurs_sql}, aucun commit")
