"""Un certificat invalide ne doit pas faire repartir le mot de passe.

Trouvé le 31/08/2026 par la boucle d'amélioration, sur `imap_smtp_provider`.
Toute `ssl.SSLError` déclenchait un second essai avec un contexte où la
vérification du nom d'hôte et celle du certificat sont désactivées
(`check_hostname = False`, `verify_mode = CERT_NONE`), puis rejouait le login
avec l'adresse et le mot de passe de l'utilisateur.

Personne n'était prévenu : ni consentement, ni affichage, un simple
avertissement au journal. Quelqu'un qui s'interpose présente un certificat
quelconque, provoque l'erreur, et reçoit les identifiants sur un canal qu'on
a soi-même cessé de vérifier.

La souplesse reste possible pour un serveur d'entreprise auto-signé, mais
elle devient un choix explicite, jamais un repli automatique.
"""

import ssl
from unittest.mock import MagicMock

import pytest
from app.services.email.imap_smtp_provider import ImapSmtpProvider

MOT_DE_PASSE = "secret-de-ludo"


def _fournisseur(**extra):
    return ImapSmtpProvider(
        email_address="ludo@synoptia.fr",
        password=MOT_DE_PASSE,
        imap_host="imap.exemple.fr",
        **extra,
    )


def test_par_defaut_une_erreur_tls_ne_rejoue_pas_le_mot_de_passe(monkeypatch):
    """La garantie centrale : aucun second login sans vérification."""
    fournisseur = _fournisseur()
    permissif_appele = []

    def strict(timeout=None):
        raise ssl.SSLError("certificate verify failed: self signed certificate")

    def permissif(timeout=None):
        permissif_appele.append(True)
        boite = MagicMock()
        boite.login = MagicMock()
        return boite

    monkeypatch.setattr(fournisseur, "_create_mailbox", strict)
    monkeypatch.setattr(fournisseur, "_create_mailbox_permissive", permissif)

    with pytest.raises(ssl.SSLError):
        fournisseur._connect_mailbox()

    assert not permissif_appele, (
        "le repli sans verification ne doit pas etre emprunte par defaut"
    )


def test_le_repli_reste_possible_s_il_est_explicitement_consenti(monkeypatch):
    """La souplesse pour un serveur auto-signé n'est pas supprimée,
    elle devient un choix."""
    fournisseur = _fournisseur(allow_insecure_tls=True)
    boite_permissive = MagicMock()
    boite_permissive.login = MagicMock(return_value="ok")

    monkeypatch.setattr(
        fournisseur, "_create_mailbox",
        lambda timeout=None: (_ for _ in ()).throw(ssl.SSLError("bad cert")),
    )
    monkeypatch.setattr(
        fournisseur, "_create_mailbox_permissive", lambda timeout=None: boite_permissive
    )

    assert fournisseur._connect_mailbox() == "ok"
    boite_permissive.login.assert_called_once()


def test_un_serveur_sain_n_est_pas_penalise(monkeypatch):
    """Aucun sur-blocage : le chemin nominal reste intact."""
    fournisseur = _fournisseur()
    boite = MagicMock()
    boite.login = MagicMock(return_value="ok")
    monkeypatch.setattr(fournisseur, "_create_mailbox", lambda timeout=None: boite)
    assert fournisseur._connect_mailbox() == "ok"


def test_la_fabrique_ferme_par_defaut_et_sait_transmettre_le_consentement():
    """Le consentement doit pouvoir remonter jusqu'a l'appelant.

    Sans ce passage, fermer le repli rendrait tout serveur auto-signe
    inutilisable sans aucune issue : on aurait echange une faille contre une
    impasse.
    """
    from app.services.email.provider_factory import get_email_provider

    defaut = get_email_provider(
        provider_type="imap", email_address="ludo@synoptia.fr",
        password=MOT_DE_PASSE, imap_host="imap.exemple.fr",
    )
    assert defaut._allow_insecure_tls is False, "la valeur sure doit etre le defaut"

    consenti = get_email_provider(
        provider_type="imap", email_address="ludo@synoptia.fr",
        password=MOT_DE_PASSE, imap_host="imap.exemple.fr",
        allow_insecure_tls=True,
    )
    assert consenti._allow_insecure_tls is True
