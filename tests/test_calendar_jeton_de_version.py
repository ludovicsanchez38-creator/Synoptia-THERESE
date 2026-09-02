"""B-029 — deux écrivains du même événement d'agenda, sans jeton de version.

02/09/2026. `CalendarService.update_event` lit l'événement complet, y applique
les champs fournis, puis renvoie le document ENTIER par un PUT qui ne porte que
`Authorization` et `Content-Type`. L'ETag renvoyé par Google voyage dans le
CORPS, où il n'a aucun effet de précondition.

Scénario réaliste en poste unique : l'utilisateur déplace le rendez-vous sur
son téléphone pendant que THÉRÈSE réécrit la copie lue à t0. La modification
faite sur le téléphone est écrasée sans que rien ne le signale.

Le remède est celui de HTTP : `If-Match` sur l'ETag lu, et un 412 du serveur
qui remonte en conflit lisible plutôt qu'en 500 générique.

Périmètre : l'écrivain Google. Le second écrivain (CalDAV, `event.save()`)
n'est PAS traité dans ce lot — voir la note du rapport.
"""

from __future__ import annotations

import pytest


class _Reponse:
    status_code = 200

    def __init__(self, corps=None):
        self._corps = corps or {"id": "evt1", "etag": '"ETAG-T1"'}

    def raise_for_status(self):
        return None

    def json(self):
        return self._corps


def _client_capturant(captures, reponse=None):
    class FauxClient:
        async def put(self, url, headers=None, json=None, timeout=None):
            captures["url"] = url
            captures["headers"] = dict(headers or {})
            captures["corps"] = json
            if reponse is not None:
                return reponse
            return _Reponse()

    async def faux_get_http_client():
        return FauxClient()

    return faux_get_http_client


@pytest.mark.asyncio
async def test_update_event_porte_un_jeton_de_version(monkeypatch):
    from app.services import calendar_service as module

    captures: dict = {}
    monkeypatch.setattr(module, "get_http_client", _client_capturant(captures))

    service = module.CalendarService("jeton-bidon")

    async def faux_get_event(calendar_id, event_id):
        return {
            "id": "evt1",
            "etag": '"ETAG-T0"',
            "summary": "Titre t0",
            "location": "Salle A (choisie sur le téléphone)",
        }

    monkeypatch.setattr(service, "get_event", faux_get_event)

    await service.update_event("cal1", "evt1", summary="Titre t1")

    conditionnels = {
        cle.lower(): valeur
        for cle, valeur in captures["headers"].items()
        if cle.lower() == "if-match"
    }
    assert conditionnels, (
        "PUT sans précondition de version : toute écriture concurrente est "
        f"écrasée. en-têtes={sorted(captures['headers'])}"
    )
    assert conditionnels["if-match"] == '"ETAG-T0"', conditionnels


@pytest.mark.asyncio
async def test_sans_etag_connu_l_ecriture_reste_possible(monkeypatch):
    """Verrou : un événement sans ETag ne doit pas devenir immodifiable."""
    from app.services import calendar_service as module

    captures: dict = {}
    monkeypatch.setattr(module, "get_http_client", _client_capturant(captures))

    service = module.CalendarService("jeton-bidon")

    async def faux_get_event(calendar_id, event_id):
        return {"id": "evt1", "summary": "Titre t0"}

    monkeypatch.setattr(service, "get_event", faux_get_event)

    await service.update_event("cal1", "evt1", summary="Titre t1")

    assert "If-Match" not in captures["headers"], captures["headers"]
    assert captures["corps"]["summary"] == "Titre t1"


@pytest.mark.asyncio
async def test_un_412_remonte_en_conflit_lisible(monkeypatch, db_session):
    """Un 412 est un CONFLIT, pas une panne : le 500 générique était muet."""
    import httpx
    from app.models.schemas import UpdateEventRequest
    from app.routers import calendar as routeur
    from fastapi import HTTPException

    async def faux_token(*_a, **_k):
        return "jeton"

    monkeypatch.setattr(routeur, "ensure_valid_access_token", faux_token)

    class ServiceEnConflit:
        def __init__(self, *_a, **_k):
            pass

        async def update_event(self, **_k):
            raise httpx.HTTPStatusError(
                "412 Precondition Failed",
                request=httpx.Request("PUT", "https://exemple.test"),
                response=httpx.Response(412),
            )

    monkeypatch.setattr(routeur, "CalendarService", ServiceEnConflit)

    from app.models.entities import EmailAccount

    compte = EmailAccount(
        id="compte-b029",
        email="b029@exemple.test",
        provider="gmail",
    )
    db_session.add(compte)
    await db_session.commit()

    with pytest.raises(HTTPException) as leve:
        await routeur.update_event(
            event_id="evt1",
            request=UpdateEventRequest(summary="Titre t1"),
            calendar_id="primary",
            account_id="compte-b029",
            session=db_session,
        )

    assert leve.value.status_code == 409, (
        f"un 412 sort en {leve.value.status_code} : l'écran ne peut pas "
        "distinguer un conflit d'une panne"
    )
    assert "modifi" in str(leve.value.detail).lower(), leve.value.detail
