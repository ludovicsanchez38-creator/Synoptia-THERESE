"""B-260 — l'écrivain CalDAV du même événement, sans jeton de version.

Moitié non traitée de B-029 : RE27 a posé `If-Match` sur l'écrivain Google et
a laissé le CalDAV en `event.save()`, un PUT inconditionnel. Le scénario est
le même en poste unique — l'utilisateur déplace le rendez-vous sur son
téléphone pendant que THÉRÈSE réécrit la copie lue à t0 — et la modification
faite ailleurs est écrasée sans que rien ne le signale.

La bibliothèque `caldav` n'expose aucune précondition sur `save()`. Le remède
passe donc sous elle : on lit l'ETag (PROPFIND `getetag`, que la bibliothèque
sait faire) et on envoie le PUT par `client.put`, avec `If-Match`. Un 412
devient un conflit lisible, comme côté Google.
"""

from __future__ import annotations

import pytest
from app.services.calendar.base_provider import UpdateEventRequest
from app.services.calendar.caldav_provider import CalDAVProvider

ICS_T0 = (
    "BEGIN:VCALENDAR\r\n"
    "VERSION:2.0\r\n"
    "PRODID:-//THERESE//test//FR\r\n"
    "BEGIN:VEVENT\r\n"
    "UID:evt1\r\n"
    "SUMMARY:Titre t0\r\n"
    "LOCATION:Salle A (choisie sur le telephone)\r\n"
    "DTSTAMP:20260901T090000Z\r\n"
    "DTSTART:20260902T090000Z\r\n"
    "DTEND:20260902T100000Z\r\n"
    "END:VEVENT\r\n"
    "END:VCALENDAR\r\n"
)


class _Reponse:
    def __init__(self, status: int = 204) -> None:
        self.status = status
        self.headers: dict[str, str] = {}
        self.raw = ""


class _ClientCapturant:
    """Le DAVClient de la bibliothèque : `put(url, body, headers)`."""

    def __init__(self, captures: dict, status: int = 204) -> None:
        self._captures = captures
        self._status = status

    def put(self, url, body, headers=None):
        self._captures["url"] = str(url)
        self._captures["corps"] = body
        self._captures["entetes"] = dict(headers or {})
        return _Reponse(self._status)


#: L'ETag qu'un PROPFIND fait APRÈS la lecture rendrait si quelqu'un d'autre
#: a écrit entre-temps. Une précondition posée sur celui-ci passerait chez le
#: serveur et écraserait quand même : c'est la fenêtre que B-260 doit fermer.
ETAG_APRES_COUP = '"ETAG-T1-ECRIT-PAR-LE-TELEPHONE"'


class _Evenement:
    """Un événement dont la relecture et le PROPFIND ne disent PAS la même chose."""

    def __init__(self, client, etag: str | None) -> None:
        self.data = ICS_T0
        self.client = client
        self.url = "https://caldav.test/cal1/evt1.ics"
        self._etag = etag
        self.props: dict = {}
        self.sauvegardes = 0
        self.relectures = 0

    def load(self, only_if_unloaded: bool = False):
        """GET : le contenu et l'en-tête Etag arrivent dans la MÊME réponse."""
        self.relectures += 1
        self.data = ICS_T0
        if self._etag is not None:
            self.props["{DAV:}getetag"] = self._etag
        return self

    def get_property(self, prop, **_kw):  # PROPFIND, plus tard, donc trop tard
        return ETAG_APRES_COUP

    def save(self):
        self.sauvegardes += 1


class _Agenda:
    def __init__(self, evenement: _Evenement) -> None:
        self.id = "cal1"
        self.url = "https://caldav.test/cal1/"
        self._evenement = evenement

    def event_by_uid(self, _uid):
        return self._evenement

    def events(self):
        return [self._evenement]


class _Principal:
    def __init__(self, agenda: _Agenda) -> None:
        self._agenda = agenda

    def calendars(self):
        return [self._agenda]


def _provider_avec(monkeypatch, captures, etag, status=204):
    provider = CalDAVProvider(url="https://caldav.test", username="u", password="p")
    evenement = _Evenement(_ClientCapturant(captures, status), etag)
    monkeypatch.setattr(provider, "_get_principal", lambda: _Principal(_Agenda(evenement)))
    return provider, evenement


@pytest.mark.asyncio
async def test_la_mise_a_jour_caldav_porte_le_jeton_de_version(monkeypatch):
    captures: dict = {}
    provider, evenement = _provider_avec(monkeypatch, captures, '"ETAG-T0"')

    await provider.update_event("cal1", "evt1", UpdateEventRequest(summary="Titre t1"))

    assert captures, (
        "aucun PUT observé : l'écriture est passée par `event.save()`, un PUT "
        f"inconditionnel qui écrase l'écrivain concurrent (save={evenement.sauvegardes})"
    )
    conditionnels = {
        cle.lower(): valeur
        for cle, valeur in captures["entetes"].items()
        if cle.lower() == "if-match"
    }
    assert conditionnels, (
        "PUT sans précondition de version : toute écriture concurrente est "
        f"écrasée. en-têtes={sorted(captures['entetes'])}"
    )
    assert conditionnels["if-match"] == '"ETAG-T0"', (
        "la précondition doit porter l'ETag de la RELECTURE, pas celui d'un "
        "PROPFIND fait après coup : un jeton pris plus tard correspond à "
        "l'écriture concurrente qu'on prétend refuser, la précondition passe "
        f"et l'écrasement a lieu quand même. reçu={conditionnels['if-match']}"
    )
    assert evenement.relectures == 1, (
        "le contenu et son jeton doivent venir de la même réponse"
    )
    assert "Titre t1" in captures["corps"], "le corps envoyé doit porter la modification"


@pytest.mark.asyncio
async def test_un_412_caldav_devient_un_conflit_de_version(monkeypatch):
    """Le serveur refuse : l'appelant doit pouvoir le NOMMER, pas deviner."""
    from app.services.calendar.base_provider import ConflitDeVersion

    captures: dict = {}
    provider, _ = _provider_avec(monkeypatch, captures, '"ETAG-T0"', status=412)

    with pytest.raises(ConflitDeVersion):
        await provider.update_event("cal1", "evt1", UpdateEventRequest(summary="Titre t1"))


@pytest.mark.asyncio
async def test_sans_etag_connu_l_ecriture_caldav_reste_possible(monkeypatch):
    """Verrou (parité RE27) : un événement sans ETag ne devient pas immodifiable."""
    captures: dict = {}
    provider, evenement = _provider_avec(monkeypatch, captures, None)

    dto = await provider.update_event(
        "cal1", "evt1", UpdateEventRequest(summary="Titre t1")
    )

    assert dto.summary == "Titre t1"
    assert "If-Match" not in captures.get("entetes", {}), captures.get("entetes")
    assert captures or evenement.sauvegardes == 1, (
        "sans ETag, l'écriture doit tout de même avoir lieu"
    )


@pytest.mark.asyncio
async def test_un_conflit_caldav_sort_en_409_lisible(monkeypatch, db_session):
    """Un conflit est un CONFLIT, pas une panne : le 500 générique était muet."""
    from app.models.entities import Calendar
    from app.models.schemas import UpdateEventRequest as RequeteHttp
    from app.routers import calendar as routeur
    from app.services.calendar.base_provider import ConflitDeVersion
    from fastapi import HTTPException

    agenda = Calendar(
        id="cal-b260",
        summary="Agenda CalDAV",
        provider="caldav",
        caldav_url="https://caldav.test",
    )
    db_session.add(agenda)
    await db_session.commit()

    class ProviderEnConflit:
        async def update_event(self, *_a, **_k):
            raise ConflitDeVersion(
                "L'événement a été modifié ailleurs depuis sa lecture."
            )

    async def faux_provider(*_a, **_k):
        return ProviderEnConflit()

    monkeypatch.setattr(routeur, "_get_provider_for_calendar", faux_provider)

    with pytest.raises(HTTPException) as leve:
        await routeur.update_event(
            event_id="evt1",
            request=RequeteHttp(summary="Titre t1"),
            calendar_id="cal-b260",
            account_id=None,
            session=db_session,
        )

    assert leve.value.status_code == 409, (
        f"un conflit sort en {leve.value.status_code} : l'écran ne peut pas "
        "le distinguer d'une panne"
    )
    assert "modifi" in str(leve.value.detail).lower(), leve.value.detail
