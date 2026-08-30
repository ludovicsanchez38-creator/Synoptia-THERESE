"""US-002 : confirmation humaine avant les outils sensibles (ex. send_email).

Le LLM ne doit pas pouvoir déclencher seul un envoi de mail : l'action est
mise en attente et n'est exécutée qu'après validation explicite de l'utilisateur.
"""
from app.services.tool_confirmations import (
    pop_pending,
    register_pending,
    requires_confirmation,
)


def test_send_email_requiert_une_confirmation():
    assert requires_confirmation("send_email") is True


def test_outils_en_lecture_seule_ne_requierent_pas_de_confirmation():
    assert requires_confirmation("read_emails") is False
    assert requires_confirmation("search_emails") is False
    assert requires_confirmation("read_contact") is False
    assert requires_confirmation("search_files") is False
    assert requires_confirmation("read_file") is False
    assert requires_confirmation("list_calendar_events") is False
    assert requires_confirmation("search_invoices") is False
    assert requires_confirmation("invoice_totals") is False
    assert requires_confirmation("summarize_emails") is False


def test_une_mutation_locale_exige_une_carte():
    """Passe 4, frontière de confiance : create_contact / create_project /
    generate_document s'exécutaient sans relecture. La décision suit la
    classe d'effet, pas une liste de deux noms."""
    assert requires_confirmation("create_contact") is True
    assert requires_confirmation("create_project") is True
    assert requires_confirmation("generate_document") is True
    assert requires_confirmation("create_calendar_event") is True


def test_une_mutation_externe_exige_une_carte():
    """web_search partait chez Brave avec le contexte ; browser_navigate
    pouvait viser l'API locale. Plus de fail-open sur le nom."""
    assert requires_confirmation("web_search") is True
    assert requires_confirmation("browser_navigate") is True
    assert requires_confirmation("send_email") is True


def test_un_outil_inconnu_est_traite_comme_sortant():
    """classe_de() le savait déjà ; le portillon ne s'en servait pas.
    Slack, WhatsApp, Stripe, filesystem : un clic d'install, puis plus
    de carte. Fail-closed : inconnu = confirmation."""
    assert requires_confirmation("slack__post_message") is True
    assert requires_confirmation("whatsapp__send_message") is True
    assert requires_confirmation("stripe__create_payment") is True
    assert requires_confirmation("filesystem__read_file") is True
    assert requires_confirmation("mcp__inconnu__outil") is True
    # Un préfixe MCP ne blanchit pas un nom de lecture native : on ne
    # sait pas si c'est vraiment l'outil local, ou un serveur homonyme.
    assert requires_confirmation("therese__read_emails") is True


def test_register_puis_pop_rend_l_action_une_seule_fois():
    cid = register_pending("send_email", {"to": "x@y.fr", "subject": "S", "body": "B"})
    assert isinstance(cid, str) and cid

    action = pop_pending(cid)
    assert action == ("send_email", {"to": "x@y.fr", "subject": "S", "body": "B"}, None)

    # Consommée : un second pop ne rejoue pas l'action (anti-double envoi).
    assert pop_pending(cid) is None


def test_pop_d_un_id_inconnu_retourne_none():
    assert pop_pending("inconnu-xyz") is None


def test_send_email_mcp_prefixe_requiert_aussi_confirmation():
    """BUG-121 : un send_email exposé via MCP est nommé '{server_id}__send_email'.

    Il doit être gaté comme le send_email natif, sinon il échappe au contrôle
    (nom préfixé) et s'exécute sans validation - violation de l'invariant US-002.
    """
    assert requires_confirmation("therese__send_email") is True
    assert requires_confirmation("mon-serveur__send_email") is True


def test_prefixe_mcp_ne_blanchit_pas_un_nom_de_lecture():
    """Ancien invariant (fail-open) : le préfixe MCP laissait passer
    `therese__read_emails` comme la lecture native. Un serveur MCP peut
    s'appeler comme on veut ; `filesystem__read_file` n'est pas `read_file`.
    Fail-closed : le nom préfixé est inconnu, donc sortant."""
    assert requires_confirmation("therese__read_emails") is True
    assert requires_confirmation("therese__list_invoices") is True
