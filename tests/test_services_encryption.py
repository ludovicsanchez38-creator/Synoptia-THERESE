"""
THERESE v2 - Tests Service Encryption

Teste le service de chiffrement Fernet (AES-128-CBC + HMAC) pour les donnees sensibles.
"""

import stat

import pytest
from app.services.encryption import (
    EncryptionService,
    decrypt_value,
    encrypt_value,
    get_encryption_service,
    is_value_encrypted,
)
from cryptography.fernet import InvalidToken


@pytest.fixture
def temp_encryption_dir(tmp_path):
    """Fixture pour creer un repertoire temporaire pour les cles de chiffrement."""
    encryption_dir = tmp_path / ".therese_test"
    encryption_dir.mkdir(parents=True, exist_ok=True)
    return encryption_dir


@pytest.fixture
def mock_encryption_paths(temp_encryption_dir, monkeypatch):
    """Fixture pour mocker les chemins des fichiers de cle de chiffrement."""
    monkeypatch.setattr(
        "app.services.encryption.THERESE_DIR", temp_encryption_dir
    )
    monkeypatch.setattr(
        "app.services.encryption.KEY_FILE", temp_encryption_dir / ".encryption_key"
    )
    monkeypatch.setattr(
        "app.services.encryption.SALT_FILE", temp_encryption_dir / ".encryption_salt"
    )
    # Sprint 2 - PERF-2.10: Disable keychain for file-based tests
    monkeypatch.setattr(
        "app.services.encryption._try_keyring_available", lambda: False
    )
    # Reset le singleton
    EncryptionService._instance = None
    EncryptionService._fernet = None
    EncryptionService._using_keychain = False
    yield temp_encryption_dir
    # Cleanup apres le test
    EncryptionService._instance = None
    EncryptionService._fernet = None
    EncryptionService._using_keychain = False


class TestEncryptionRoundtrip:
    """Tests de chiffrement/dechiffrement."""

    def test_encrypt_decrypt_roundtrip(self, mock_encryption_paths):
        """Chiffrement puis dechiffrement retourne la valeur originale."""
        service = EncryptionService()
        plaintext = "Ma clé API secrète: sk-1234567890"

        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)

        assert decrypted == plaintext
        assert encrypted != plaintext
        assert len(encrypted) > 0

    def test_encrypt_empty_string(self, mock_encryption_paths):
        """Chiffrement d'une chaine vide retourne chaine vide."""
        service = EncryptionService()

        encrypted = service.encrypt("")
        decrypted = service.decrypt("")

        assert encrypted == ""
        assert decrypted == ""

    def test_encrypt_long_value(self, mock_encryption_paths):
        """Chiffrement d'une grande valeur (>1MB) fonctionne."""
        service = EncryptionService()
        # Cree une valeur de 2 MB
        plaintext = "X" * (2 * 1024 * 1024)

        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)

        assert decrypted == plaintext
        assert len(encrypted) > len(plaintext)


class TestDecryptionErrors:
    """Tests des erreurs de dechiffrement."""

    def test_decrypt_with_invalid_token(self, mock_encryption_paths):
        """Dechiffrement avec token invalide leve une exception."""
        service = EncryptionService()

        # Utilise un token base64 valide mais invalide pour Fernet
        with pytest.raises((InvalidToken, Exception)):
            service.decrypt("Z0FBQUFBQl9pbnZhbGlkX3Rva2Vu")

    def test_decrypt_with_corrupted_data(self, mock_encryption_paths):
        """Dechiffrement de donnees corrompues echoue."""
        service = EncryptionService()

        # Chiffre une valeur correctement
        encrypted = service.encrypt("test data")

        # Corrompt le contenu chiffre (change un caractere)
        corrupted = encrypted[:-1] + chr((ord(encrypted[-1]) + 1) % 256)

        with pytest.raises((InvalidToken, Exception)):
            service.decrypt(corrupted)


class TestIsEncrypted:
    """Tests de detection de donnees chiffrees."""

    def test_is_encrypted_with_encrypted_value(self, mock_encryption_paths):
        """is_encrypted() retourne True pour valeur chiffree."""
        service = EncryptionService()
        encrypted_value = service.encrypt("secret data")

        assert service.is_encrypted(encrypted_value) is True

    def test_is_encrypted_with_plain_value(self, mock_encryption_paths):
        """is_encrypted() retourne False pour valeur non chiffree."""
        service = EncryptionService()
        plain_value = "not encrypted"

        assert service.is_encrypted(plain_value) is False

    def test_is_encrypted_empty_string(self, mock_encryption_paths):
        """is_encrypted('') retourne False."""
        service = EncryptionService()

        assert service.is_encrypted("") is False

    def test_is_encrypted_with_invalid_base64(self, mock_encryption_paths):
        """is_encrypted() retourne False pour invalide base64."""
        service = EncryptionService()

        # Donnees qui ne sont pas valides base64
        assert service.is_encrypted("@#$%^&*()") is False


class TestSingletonPattern:
    """Tests du pattern singleton."""

    def test_singleton_pattern(self, mock_encryption_paths):
        """Plusieurs appels a get_encryption_service() retournent la meme instance."""
        service1 = get_encryption_service()
        service2 = get_encryption_service()

        assert service1 is service2

    def test_encryption_service_class_singleton(self, mock_encryption_paths):
        """EncryptionService() retourne toujours la meme instance."""
        service1 = EncryptionService()
        service2 = EncryptionService()

        assert service1 is service2


class TestKeyFilePermissions:
    """Tests des permissions des fichiers de cle."""

    def test_key_file_permissions(self, mock_encryption_paths):
        """Le fichier de cle a les permissions 600."""
        service = EncryptionService()
        key_file = mock_encryption_paths / ".encryption_key"

        assert key_file.exists()

        # Recupere les permissions du fichier (octal)
        file_stat = key_file.stat()
        permissions = stat.filemode(file_stat.st_mode)

        # Verifie que c'est -rw------- (600)
        assert oct(stat.S_IMODE(file_stat.st_mode)) == "0o600"

    def test_salt_file_permissions(self, mock_encryption_paths):
        """Le fichier de salt a les permissions 600."""
        service = EncryptionService()
        # Force la derivation de cle pour creer le salt
        _ = service._derive_key_from_password("test_password")

        salt_file = mock_encryption_paths / ".encryption_salt"

        assert salt_file.exists()

        file_stat = salt_file.stat()
        assert oct(stat.S_IMODE(file_stat.st_mode)) == "0o600"


class TestUnicodeSupport:
    """Tests du support unicode."""

    def test_encrypt_unicode(self, mock_encryption_paths):
        """Chiffrement de caracteres unicode fonctionne."""
        service = EncryptionService()
        unicode_text = "Bonjour 🔐 你好 مرحبا Здравствуй"

        encrypted = service.encrypt(unicode_text)
        decrypted = service.decrypt(encrypted)

        assert decrypted == unicode_text

    def test_encrypt_special_characters(self, mock_encryption_paths):
        """Chiffrement de caracteres speciaux fonctionne."""
        service = EncryptionService()
        special_text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"

        encrypted = service.encrypt(special_text)
        decrypted = service.decrypt(encrypted)

        assert decrypted == special_text

    def test_encrypt_newlines_and_tabs(self, mock_encryption_paths):
        """Chiffrement avec newlines et tabs fonctionne."""
        service = EncryptionService()
        text_with_whitespace = "Line 1\nLine 2\tTabbed\rCarriage return"

        encrypted = service.encrypt(text_with_whitespace)
        decrypted = service.decrypt(encrypted)

        assert decrypted == text_with_whitespace


class TestHelperFunctions:
    """Tests des fonctions helper."""

    def test_encrypt_value_helper(self, mock_encryption_paths):
        """encrypt_value() helper fonctionne."""
        plaintext = "test secret"

        encrypted = encrypt_value(plaintext)

        assert encrypted != plaintext
        assert len(encrypted) > 0

    def test_decrypt_value_helper(self, mock_encryption_paths):
        """decrypt_value() helper fonctionne."""
        plaintext = "test secret"
        encrypted = encrypt_value(plaintext)

        decrypted = decrypt_value(encrypted)

        assert decrypted == plaintext

    def test_is_value_encrypted_helper(self, mock_encryption_paths):
        """is_value_encrypted() helper fonctionne."""
        plaintext = "test secret"
        encrypted = encrypt_value(plaintext)

        assert is_value_encrypted(encrypted) is True
        assert is_value_encrypted(plaintext) is False


class TestKeyGeneration:
    """Tests de generation de cles."""

    def test_key_generation_creates_file(self, mock_encryption_paths):
        """Generation d'une nouvelle cle cree le fichier."""
        service = EncryptionService()
        key_file = mock_encryption_paths / ".encryption_key"

        assert key_file.exists()
        assert key_file.stat().st_size > 0

    def test_key_persistence(self, mock_encryption_paths):
        """La meme cle est utilisee pour les deux services."""
        # Creer d'abord service
        service1 = EncryptionService()
        encrypted1 = service1.encrypt("test")

        # Reinitialiser le singleton
        EncryptionService._instance = None
        EncryptionService._fernet = None

        # Creer deuxieme service
        service2 = EncryptionService()
        decrypted = service2.decrypt(encrypted1)

        assert decrypted == "test"

    def test_key_loading_from_file(self, mock_encryption_paths):
        """Cle chargee depuis le fichier au lieu de generee."""
        # Genere une premiere cle
        service1 = EncryptionService()
        key_file = mock_encryption_paths / ".encryption_key"
        original_key = key_file.read_bytes()

        # Reinitialiser et creer nouveau service
        EncryptionService._instance = None
        EncryptionService._fernet = None
        service2 = EncryptionService()

        # Verifie que la meme cle est utilisee
        loaded_key = key_file.read_bytes()
        assert loaded_key == original_key


class TestErrorHandling:
    """Tests de gestion d'erreurs."""

    def test_encrypt_with_uninitialized_service(self, mock_encryption_paths):
        """Chiffrement avec service non initialise leve RuntimeError."""
        service = EncryptionService()
        service._fernet = None

        with pytest.raises(RuntimeError, match="non initialise"):
            service.encrypt("test")

    def test_decrypt_with_uninitialized_service(self, mock_encryption_paths):
        """Dechiffrement avec service non initialise leve RuntimeError."""
        service = EncryptionService()
        service._fernet = None

        with pytest.raises(RuntimeError, match="non initialise"):
            service.decrypt("test")

    def test_invalid_token_logging(self, mock_encryption_paths, caplog):
        """Les erreurs de dechiffrement sont loggees."""
        service = EncryptionService()

        # Utilise un token base64 valide mais invalide pour Fernet
        with pytest.raises((InvalidToken, Exception)):
            service.decrypt("Z0FBQUFBQl9pbnZhbGlkX3Rva2Vu")

        # Verifie qu'une erreur a ete loggee
        assert "dechiffrement" in caplog.text.lower() or "erreur" in caplog.text.lower()


class TestKeyRotation:
    """Tests de rotation de cle."""

    def test_rotate_key(self, mock_encryption_paths):
        """Rotation de cle change la cle utilisee."""
        service = EncryptionService()

        # Chiffrer avec cle 1
        plaintext = "secret data"
        encrypted_v1 = service.encrypt(plaintext)

        # Recuperer l'ancienne cle
        old_key = service.rotate_key()

        assert old_key is not None

        # Nouvelle cle ne dechiffre pas l'ancienne donnee
        with pytest.raises(InvalidToken):
            service.decrypt(encrypted_v1)

    def test_rotate_key_returns_old_key(self, mock_encryption_paths):
        """rotate_key() retourne l'ancienne cle."""
        service = EncryptionService()
        key_file = mock_encryption_paths / ".encryption_key"
        first_key = key_file.read_bytes()

        old_key = service.rotate_key()

        assert old_key == first_key


class TestConcurrency:
    """Tests de concurrence et isolation."""

    def test_multiple_encryptions_different_tokens(self, mock_encryption_paths):
        """Deux chiffrements du meme texte donnent des resultats differents."""
        service = EncryptionService()
        plaintext = "same text"

        encrypted1 = service.encrypt(plaintext)
        encrypted2 = service.encrypt(plaintext)

        # Fernet ajoute un IV aleatoire, donc les ciphertexts sont differents
        assert encrypted1 != encrypted2

        # Mais dechiffrement redonne le meme texte
        assert service.decrypt(encrypted1) == plaintext
        assert service.decrypt(encrypted2) == plaintext


class TestEdgeCases:
    """Tests des cas limites."""

    def test_encrypt_only_spaces(self, mock_encryption_paths):
        """Chiffrement d'une chaine de seulement espaces."""
        service = EncryptionService()
        spaces = "     "

        encrypted = service.encrypt(spaces)
        decrypted = service.decrypt(encrypted)

        assert decrypted == spaces

    def test_encrypt_very_long_base64(self, mock_encryption_paths):
        """Dechiffrement d'une tres longue chaine base64."""
        service = EncryptionService()
        # Cree un texte long qui sera chiffre
        long_text = "A" * 10000

        encrypted = service.encrypt(long_text)
        decrypted = service.decrypt(encrypted)

        assert decrypted == long_text

    def test_encrypt_null_bytes(self, mock_encryption_paths):
        """Chiffrement avec null bytes fonctionne."""
        service = EncryptionService()
        # Note: les null bytes ne peuvent pas etre dans une string Python directement
        # mais on peut les tester via encoding
        text_with_potential_nulls = "test\x00data"

        encrypted = service.encrypt(text_with_potential_nulls)
        decrypted = service.decrypt(encrypted)

        assert decrypted == text_with_potential_nulls
