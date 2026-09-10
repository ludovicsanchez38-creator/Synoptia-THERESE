"""Cycle 6 (10/09/2026) : candidats des lecteurs de la carte, contredits par Grok,
reproduits ici côté moteur. Chaque test énonce l'attendu que le code ne tenait pas.

- navigateur interne : une cible locale ou privée est refusée (le jeton de session
  vit sur 127.0.0.1) ;
- téléchargement d'un fichier de skill : l'identifiant n'entre pas brut dans un glob ;
- purge du journal d'audit : une rétention nulle ou négative est refusée ;
- RGPD : une tâche rattachée directement au contact est exportée et effacée ;
- Gmail : pièces jointes et fil de discussion transmis au service ;
- outil e-mail : un corps vide est refusé avant tout appel ;
- agenda : créer et modifier un événement sur l'alias `primary` tombe sur l'agenda
  local principal, comme la lecture et la suppression (B-557).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

# --- navigateur interne ------------------------------------------------------

@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:17293/api/auth/token",
        "http://localhost:1420/",
        "http://[::1]:17293/health",
        "http://10.0.0.5/admin",
        "http://192.168.1.56:8098/",
        "http://0.0.0.0/",
    ],
)
def test_le_navigateur_interne_refuse_les_cibles_locales_et_privees(url):
    from app.services.browser_agent import _validate_url

    assert _validate_url(url) is not None, f"cible locale acceptée : {url}"


def test_le_navigateur_interne_accepte_une_cible_publique(monkeypatch):
    import socket

    from app.services.browser_agent import _validate_url

    # Revue Grok 0.70.0 : le garde résout désormais le nom ; ce test ne dépend pas du réseau.
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))])
    assert _validate_url("https://www.legifrance.gouv.fr/") is None


# --- fichiers de skill --------------------------------------------------------

@pytest.mark.asyncio
async def test_le_telechargement_d_un_fichier_de_skill_refuse_un_identifiant_a_jokers(client: AsyncClient, tmp_path, monkeypatch):
    from app.routers import skills as routeur

    class FauxRegistre:
        output_dir = tmp_path

        def get_file(self, file_id):
            return None

    monkeypatch.setattr(routeur, "get_skills_registry", lambda: FauxRegistre())
    (tmp_path / "Proposition_abcd1234.docx").write_bytes(b"PK\x03\x04 faux docx")
    for identifiant in ("*", "?", "[a-z]*"):
        reponse = await client.get(f"/api/skills/download/{identifiant}")
        assert reponse.status_code in (400, 404, 422), f"{identifiant!r} a servi un fichier : {reponse.status_code}"


# --- journal d'audit ----------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("jours", [0, -5])
async def test_la_purge_du_journal_refuse_une_retention_nulle_ou_negative(client: AsyncClient, jours):
    reponse = await client.delete(f"/api/data/logs?days={jours}")
    assert reponse.status_code == 422, f"days={jours} accepté : {reponse.status_code} {reponse.text[:120]}"


# --- RGPD : tâches rattachées au contact --------------------------------------

async def _contact(client: AsyncClient) -> str:
    reponse = await client.post("/api/memory/contacts", json={"first_name": "Camille", "last_name": "Martin", "email": "camille@example.com"})
    assert reponse.status_code in (200, 201), reponse.text
    return reponse.json()["id"]


@pytest.mark.asyncio
async def test_l_export_rgpd_inclut_la_tache_rattachee_directement_au_contact(client: AsyncClient):
    contact = await _contact(client)
    tache = await client.post("/api/tasks/", json={"title": "Relancer Camille", "contact_id": contact})
    assert tache.status_code in (200, 201), tache.text
    export = await client.get(f"/api/rgpd/export/{contact}")
    assert export.status_code == 200, export.text
    titres = [t.get("title") for t in export.json().get("tasks", [])]
    assert "Relancer Camille" in titres, f"tâche absente de l'export : {titres}"


@pytest.mark.asyncio
async def test_l_anonymisation_rgpd_efface_la_tache_rattachee_directement_au_contact(client: AsyncClient):
    contact = await _contact(client)
    tache = await client.post("/api/tasks/", json={"title": "Relancer Camille", "contact_id": contact})
    identifiant = tache.json()["id"]
    reponse = await client.post(f"/api/rgpd/anonymize/{contact}", json={"confirm": True})
    assert reponse.status_code == 200, reponse.text
    relecture = await client.get(f"/api/tasks/{identifiant}")
    assert relecture.status_code == 404, f"la tâche survit à l'anonymisation : {relecture.status_code}"


# --- Gmail : pièces jointes et fil --------------------------------------------

@pytest.mark.asyncio
async def test_gmail_transmet_pieces_jointes_et_fil_de_discussion():
    from app.services.email.base_provider import SendEmailRequest
    from app.services.email.gmail_provider import GmailProvider

    appels: list[dict] = []

    class FauxService:
        async def send_message(self, **kwargs):
            appels.append(kwargs)
            return {"id": "msg-envoye"}

        async def create_draft(self, **kwargs):
            appels.append(kwargs)
            return {"id": "brouillon"}

        async def get_message(self, message_id, format="full"):
            return {"id": message_id, "threadId": "fil-42"}

    provider = GmailProvider("jeton")
    provider._service = FauxService()
    requete = SendEmailRequest(
        to=["camille@example.com"], subject="Devis", body="Ci-joint le devis.",
        attachments=[("devis.pdf", b"%PDF-1.4 faux", "application/pdf")],
        reply_to_message_id="msg-origine", in_reply_to="<origine@example.com>", references="<origine@example.com>",
    )
    await provider.send_message(requete)
    await provider.create_draft(requete)
    assert len(appels) == 2
    for appel in appels:
        assert appel.get("attachments") == requete.attachments, f"pièce jointe perdue : {sorted(appel)}"
        assert appel.get("in_reply_to") == "<origine@example.com>" and appel.get("references") == "<origine@example.com>", sorted(appel)
        assert appel.get("thread_id") == "fil-42", f"fil non transmis : {sorted(appel)}"


def test_le_service_gmail_encode_pieces_jointes_et_en_tetes_de_fil():
    import base64
    from email import message_from_bytes

    from app.services.gmail_service import GmailService

    brut = GmailService._encoder_message(
        to=["camille@example.com"], subject="Devis", body="Ci-joint.", cc=None, bcc=None, html=False,
        attachments=[("devis.pdf", b"%PDF-1.4 faux", "application/pdf")],
        in_reply_to="<origine@example.com>", references="<origine@example.com>",
    )
    message = message_from_bytes(base64.urlsafe_b64decode(brut))
    assert message["In-Reply-To"] == "<origine@example.com>" and message["References"] == "<origine@example.com>"
    pieces = [p for p in message.walk() if p.get_filename()]
    assert [p.get_filename() for p in pieces] == ["devis.pdf"]
    assert pieces[0].get_payload(decode=True) == b"%PDF-1.4 faux"
    assert pieces[0].get_content_type() == "application/pdf"


# --- outil e-mail : corps vide ------------------------------------------------

@pytest.mark.asyncio
async def test_l_outil_send_email_refuse_un_corps_vide_avant_tout_appel(db_session, monkeypatch):
    from app.services import workspace_tools

    async def _jamais(*_a, **_k):
        raise AssertionError("le fournisseur ne doit pas être sollicité pour un corps vide")

    monkeypatch.setattr(workspace_tools, "_get_email_provider", _jamais)
    for corps in ("", "   \n"):
        resultat = await workspace_tools._send_email({"to": "camille@example.com", "subject": "Devis", "body": corps}, db_session)
        assert resultat.startswith("Erreur"), resultat
        assert "corps" in resultat.lower() or "message" in resultat.lower(), resultat


# --- agenda : primary en écriture ---------------------------------------------

@pytest.mark.asyncio
async def test_creer_puis_modifier_un_evenement_sur_primary_tombe_sur_l_agenda_local(client: AsyncClient):
    creation = await client.post("/api/calendar/calendars", params={"summary": "Perso", "timezone": "Europe/Paris", "provider_type": "local"})
    assert creation.status_code in (200, 201), creation.text
    evenement = await client.post(
        "/api/calendar/events",
        json={"summary": "Point Camille", "start_datetime": "2026-09-15T09:00:00", "end_datetime": "2026-09-15T10:00:00"},
    )
    assert evenement.status_code in (200, 201), f"POST /events sur primary : {evenement.status_code} {evenement.text[:160]}"
    identifiant = evenement.json()["id"]
    modification = await client.put(f"/api/calendar/events/{identifiant}", json={"summary": "Point Camille (déplacé)"})
    assert modification.status_code == 200, f"PUT /events sur primary : {modification.status_code} {modification.text[:160]}"
    assert modification.json()["summary"] == "Point Camille (déplacé)"


# --- revue Grok du diff 0.70.0, finding 2 : le garde local résout et revalide ----

@pytest.mark.parametrize("hote", ["127.0.0.1.nip.io", "2130706433", "0x7f000001"])
def test_le_garde_local_resout_le_nom_avant_de_juger(monkeypatch, hote):
    """Un nom qui se résout vers la machine (nip.io, entier décimal, hexadécimal)
    passait le garde, qui ne regardait que les littéraux IP."""
    import socket

    from app.services.browser_agent import _cible_locale_ou_privee

    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))])
    assert _cible_locale_ou_privee(hote) is True, hote


def test_le_garde_local_laisse_passer_un_nom_public(monkeypatch):
    import socket

    from app.services.browser_agent import _cible_locale_ou_privee

    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))])
    assert _cible_locale_ou_privee("www.legifrance.gouv.fr") is False


class _FausseReponse:
    status = 200


class _FaussePage:
    """Une page dont la navigation aboutit ailleurs que l'URL demandée (redirection)."""

    def __init__(self, url_finale: str):
        self.url = url_finale
        self.contenu_lu = False

    async def goto(self, url, **kwargs):
        return _FausseReponse()

    async def title(self):
        return "Jeton de session"

    async def inner_text(self, selector):
        self.contenu_lu = True
        return '{"token": "secret"}'

    async def click(self, selector, **kwargs):
        return None

    async def wait_for_load_state(self, *a, **k):
        return None


@pytest.mark.asyncio
async def test_une_redirection_vers_la_machine_locale_est_refusee_apres_navigation(monkeypatch):
    """`navigate` validait l'URL demandée, jamais l'URL atteinte : une page publique
    qui redirige vers 127.0.0.1:17293/api/auth/token ramenait le jeton."""
    import socket

    from app.services.browser_agent import BrowserAgent

    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))])
    agent = BrowserAgent()
    page = _FaussePage("http://127.0.0.1:17293/api/auth/token")
    agent._page = page

    async def _ensure_page():
        return None

    monkeypatch.setattr(agent, "_ensure_page", _ensure_page)
    resultat = await agent.navigate("https://public.example/redirige")
    assert resultat.success is False and "Cible interdite" in (resultat.error or ""), resultat
    assert page.contenu_lu is False, "le contenu de la cible interdite a été lu"


@pytest.mark.asyncio
async def test_un_clic_qui_mene_a_la_machine_locale_est_refuse(monkeypatch):
    from app.services.browser_agent import BrowserAgent

    agent = BrowserAgent()
    page = _FaussePage("http://localhost:17293/api/auth/token")
    agent._page = page

    async def _ensure_page():
        return None

    monkeypatch.setattr(agent, "_ensure_page", _ensure_page)
    resultat = await agent.click("a.lien")
    assert resultat.success is False and "Cible interdite" in (resultat.error or ""), resultat


# --- revue Grok du diff 0.70.0, finding 7 : MIME des pièces jointes et alternative ----

def test_le_service_gmail_encode_un_nom_de_piece_accentue_et_une_alternative_texte():
    import base64
    from email import message_from_bytes

    from app.services.gmail_service import GmailService

    brut = GmailService._encoder_message(
        to=["camille@example.com"], subject="Devis", body="<p>Bonjour <b>Camille</b>,<br>ci-joint le devis.</p>", cc=None, bcc=None, html=True,
        attachments=[('Devis_société "été".pdf', b"%PDF-1.4 faux", "application/pdf")],
        in_reply_to=None, references=None,
    )
    message = message_from_bytes(base64.urlsafe_b64decode(brut))
    pieces = [p for p in message.walk() if p.get_filename()]
    assert [p.get_filename() for p in pieces] == ['Devis_société "été".pdf'], [p.get_filename() for p in pieces]
    types = [p.get_content_type() for p in message.walk()]
    assert "text/plain" in types and "text/html" in types, types
    texte = next(p for p in message.walk() if p.get_content_type() == "text/plain").get_payload(decode=True).decode("utf-8")
    assert "Bonjour Camille" in texte and "<b>" not in texte, texte


def test_le_service_gmail_donne_une_alternative_texte_a_un_html_sans_piece():
    import base64
    from email import message_from_bytes

    from app.services.gmail_service import GmailService

    brut = GmailService._encoder_message(
        to=["camille@example.com"], subject="Devis", body="<p>Bonjour</p>", cc=None, bcc=None, html=True,
        attachments=None, in_reply_to=None, references=None,
    )
    message = message_from_bytes(base64.urlsafe_b64decode(brut))
    types = [p.get_content_type() for p in message.walk()]
    assert types.count("text/plain") == 1 and types.count("text/html") == 1, types
