"""B-1340 : la clé maîtresse n'est jamais remplacée par une clé neuve.

Audit bêta du 27/10/2026 (A6) : si le trousseau refuse la lecture puis la
première écriture et accepte la suivante (« Refuser » puis « Autoriser », ou un
trousseau GNOME verrouillé qui redemande son mot de passe), le service
fabriquait une clé neuve, l'écrivait au trousseau et écrasait
`.encryption_key`. La base SQLCipher, chiffrée avec une clé dérivée de
l'ancienne, ne s'ouvrait plus, et plus aucune copie de l'ancienne n'existait.

Règles posées :
- un `.encryption_key` existant reste LA clé, même si le trousseau refuse
  de l'enregistrer ;
- sans clé lisible, une base chiffrée présente interdit d'en créer une :
  refus explicite, l'ancienne clé est peut-être encore au trousseau ;
- un fichier de secours différent n'est jamais écrasé sans copie.
"""
import os
import sys

import pytest

CLE_ANCIENNE = b"cle-ancienne-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
CLE_TROUSSEAU = b"cle-trousseau-BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB="


class RefusTrousseau(Exception):
    """Ce que lève keyring quand l'utilisateur clique « Refuser »."""


class TrousseauCapricieux:
    """Lecture refusée ; écritures refusées tant que `refus_restants` > 0."""

    def __init__(self, refus_ecriture: int = 1, lecture_refusee: bool = True):
        self.refus_restants = refus_ecriture
        self.lecture_refusee = lecture_refusee
        self.secret: str | None = None
        self.ecrits: list[str] = []

    def get_password(self, service, compte):
        if self.lecture_refusee:
            raise RefusTrousseau("(-128, 'User canceled the operation')")
        return self.secret

    def set_password(self, service, compte, valeur):
        if self.refus_restants > 0:
            self.refus_restants -= 1
            raise RefusTrousseau("(-128, 'User canceled the operation')")
        self.secret = valeur
        self.ecrits.append(valeur)

    def delete_password(self, service, compte):
        self.secret = None


@pytest.fixture
def profil(monkeypatch, tmp_path):
    from app.services import encryption as module

    module.EncryptionService._instance = None
    module.EncryptionService._fernet = None
    module.EncryptionService._using_keychain = False
    monkeypatch.setattr(module, "THERESE_DIR", tmp_path)
    monkeypatch.setattr(module, "KEY_FILE", tmp_path / ".encryption_key")
    monkeypatch.setattr(module._settings, "db_path", tmp_path / "therese.db")
    # La suite fixe la clé de la base (conftest) ; en production elle dérive
    # de la clé maîtresse, c'est ce cas que ces tests exercent.
    monkeypatch.delenv("THERESE_DB_KEY", raising=False)
    # Profil réel : les branches du trousseau doivent être exercées.
    monkeypatch.setattr(module, "_est_dossier_temporaire", lambda _p: False)
    yield module, tmp_path
    module.EncryptionService._instance = None
    module.EncryptionService._fernet = None
    module.EncryptionService._using_keychain = False


def _avec_trousseau(monkeypatch, module, trousseau):
    monkeypatch.setattr(module, "_try_keyring_available", lambda: True)
    monkeypatch.setitem(sys.modules, "keyring", trousseau)


def _base_chiffree(dossier):
    # Une base SQLCipher ne commence pas par l'en-tête SQLite en clair.
    (dossier / "therese.db").write_bytes(os.urandom(4096))


def _base_claire(dossier):
    (dossier / "therese.db").write_bytes(b"SQLite format 3\x00" + b"\x00" * 4080)


def test_scenario_de_l_audit_le_fichier_existant_reste_la_cle(profil, monkeypatch):
    module, dossier = profil
    module.KEY_FILE.write_bytes(CLE_ANCIENNE)
    _base_chiffree(dossier)
    trousseau = TrousseauCapricieux(refus_ecriture=1)
    _avec_trousseau(monkeypatch, module, trousseau)

    cle = module.EncryptionService()._get_or_create_key()

    assert cle == CLE_ANCIENNE, "la clé rendue doit être celle qui a chiffré la base"
    assert module.KEY_FILE.read_bytes() == CLE_ANCIENNE, ".encryption_key ne doit pas être écrasé"
    assert all(e.encode() == CLE_ANCIENNE for e in trousseau.ecrits), (
        "aucune clé neuve ne doit être écrite au trousseau"
    )


def test_le_fichier_reste_la_cle_meme_si_le_trousseau_refuse_toujours(profil, monkeypatch):
    module, dossier = profil
    module.KEY_FILE.write_bytes(CLE_ANCIENNE)
    trousseau = TrousseauCapricieux(refus_ecriture=99)
    _avec_trousseau(monkeypatch, module, trousseau)

    assert module.EncryptionService()._get_or_create_key() == CLE_ANCIENNE
    assert module.KEY_FILE.read_bytes() == CLE_ANCIENNE


def test_sans_cle_lisible_une_base_chiffree_interdit_d_en_creer_une(profil, monkeypatch):
    module, dossier = profil
    _base_chiffree(dossier)
    trousseau = TrousseauCapricieux(refus_ecriture=0)
    _avec_trousseau(monkeypatch, module, trousseau)

    with pytest.raises(module.CleMaitresseIntrouvableError):
        module.EncryptionService()._get_or_create_key()

    assert trousseau.ecrits == [], "l'entrée du trousseau (peut-être l'ancienne clé) ne doit pas être écrasée"
    assert not module.KEY_FILE.exists()


def test_sans_trousseau_une_base_chiffree_interdit_aussi_d_en_creer_une(profil, monkeypatch):
    module, dossier = profil
    _base_chiffree(dossier)
    monkeypatch.setattr(module, "_try_keyring_available", lambda: False)

    with pytest.raises(module.CleMaitresseIntrouvableError):
        module.EncryptionService()._get_or_create_key()

    assert not module.KEY_FILE.exists(), (
        "un fichier neuf serait préféré à l'ancienne clé du trousseau au lancement suivant (BUG-050)"
    )


def test_le_message_d_erreur_dit_quoi_faire_sans_jargon(profil, monkeypatch):
    module, dossier = profil
    _base_chiffree(dossier)
    monkeypatch.setattr(module, "_try_keyring_available", lambda: False)

    with pytest.raises(module.CleMaitresseIntrouvableError) as erreur:
        module.EncryptionService()._get_or_create_key()

    message = str(erreur.value)
    assert "trousseau" in message and "relance" in message.lower()


@pytest.mark.parametrize("avec_trousseau", [True, False])
def test_premiere_installation_cree_toujours_une_cle(profil, monkeypatch, avec_trousseau):
    module, dossier = profil
    if avec_trousseau:
        trousseau = TrousseauCapricieux(refus_ecriture=0, lecture_refusee=False)
        _avec_trousseau(monkeypatch, module, trousseau)
    else:
        monkeypatch.setattr(module, "_try_keyring_available", lambda: False)

    cle = module.EncryptionService()._get_or_create_key()

    assert cle and module.KEY_FILE.read_bytes() == cle


@pytest.mark.parametrize("avec_trousseau", [True, False])
def test_une_base_encore_en_clair_n_empeche_pas_la_creation(profil, monkeypatch, avec_trousseau):
    """Mise à jour depuis une version d'avant US-014 : la base claire sera chiffrée ensuite."""
    module, dossier = profil
    _base_claire(dossier)
    if avec_trousseau:
        _avec_trousseau(monkeypatch, module, TrousseauCapricieux(refus_ecriture=0, lecture_refusee=False))
    else:
        monkeypatch.setattr(module, "_try_keyring_available", lambda: False)

    assert module.EncryptionService()._get_or_create_key()


def test_un_fichier_de_secours_different_est_copie_avant_d_etre_remplace(profil):
    module, dossier = profil
    module.KEY_FILE.write_bytes(CLE_ANCIENNE)

    module.EncryptionService()._write_key_backup(CLE_TROUSSEAU)

    assert module.KEY_FILE.read_bytes() == CLE_TROUSSEAU
    copies = sorted(dossier.glob(".encryption_key.avant-*"))
    assert len(copies) == 1 and copies[0].read_bytes() == CLE_ANCIENNE
    if os.name != "nt":
        assert (copies[0].stat().st_mode & 0o777) == 0o600


def test_reecrire_la_meme_cle_ne_cree_pas_de_copie(profil):
    module, dossier = profil
    module.KEY_FILE.write_bytes(CLE_ANCIENNE)

    module.EncryptionService()._write_key_backup(CLE_ANCIENNE)

    assert list(dossier.glob(".encryption_key.avant-*")) == []


def test_une_base_a_cle_fixe_ne_depend_pas_de_la_cle_maitresse(profil, monkeypatch):
    """THERESE_DB_KEY (tests, headless) : la base n'est pas chiffrée par la clé maîtresse."""
    module, dossier = profil
    _base_chiffree(dossier)
    monkeypatch.setenv("THERESE_DB_KEY", "ad" * 32)
    monkeypatch.setattr(module, "_try_keyring_available", lambda: False)

    assert module.EncryptionService()._get_or_create_key()


def test_une_base_d_un_autre_profil_n_entre_pas_en_compte(profil, monkeypatch, tmp_path_factory):
    module, dossier = profil
    autre = tmp_path_factory.mktemp("autre-profil")
    _base_chiffree(autre)
    monkeypatch.setattr(module._settings, "db_path", autre / "therese.db")
    monkeypatch.setattr(module, "_try_keyring_available", lambda: False)

    assert module.EncryptionService()._get_or_create_key()


def test_un_chemin_de_base_personnalise_du_meme_profil_est_protege(profil, monkeypatch):
    module, dossier = profil
    (dossier / "donnees").mkdir()
    personnalisee = dossier / "donnees" / "ma-base.db"
    personnalisee.write_bytes(os.urandom(4096))
    monkeypatch.setattr(module._settings, "data_dir", dossier)
    monkeypatch.setattr(module._settings, "db_path", personnalisee)
    monkeypatch.setattr(module, "_try_keyring_available", lambda: False)

    with pytest.raises(module.CleMaitresseIntrouvableError):
        module.EncryptionService()._get_or_create_key()
