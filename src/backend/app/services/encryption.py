"""
THERESE v2 - Service de Chiffrement

Chiffrement/dechiffrement des donnees sensibles (cles API, tokens).
Utilise Fernet (AES-128-CBC avec HMAC) via la librairie cryptography.

US-SEC-01: Chiffrement des cles API
Sprint 2 - PERF-2.10: Keychain support pour la cle de chiffrement
"""

import base64
import logging
import os
import threading
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# Chemin de la cle de chiffrement (fallback)
THERESE_DIR = Path.home() / ".therese"
KEY_FILE = THERESE_DIR / ".encryption_key"
SALT_FILE = THERESE_DIR / ".encryption_salt"

# Keychain identifiers
KEYCHAIN_SERVICE = "therese-app"
KEYCHAIN_ACCOUNT = "encryption-key"


def _try_keyring_available() -> bool:
    """Check if keyring is available and functional."""
    try:
        import keyring
        # Test if backend is available
        backend = keyring.get_keyring()
        # Exclude fail backend
        if "fail" in backend.__class__.__name__.lower():
            return False
        return True
    except Exception:
        return False


class EncryptionService:
    """Service de chiffrement pour les donnees sensibles.

    Thread-safe singleton: le verrou (_lock) protege la creation de l'instance
    pour eviter une double initialisation en contexte multi-thread (ex: uvicorn workers).
    """

    _instance: Optional["EncryptionService"] = None
    _fernet: Fernet | None = None
    _using_keychain: bool = False
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "EncryptionService":
        """Singleton pattern (thread-safe via double-checked locking)."""
        if cls._instance is None:
            with cls._lock:
                # Double-check apres acquisition du verrou
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialise le service de chiffrement."""
        THERESE_DIR.mkdir(parents=True, exist_ok=True)

        # Essayer d'abord le keychain, sinon fallback sur fichier
        key = self._get_or_create_key()
        self._fernet = Fernet(key)

        storage = "keychain" if self._using_keychain else "file"
        logger.info(f"Service de chiffrement initialise (storage: {storage})")

    def _get_or_create_key(self) -> bytes:
        """Recupere ou genere la cle de chiffrement."""
        # 1. Essayer le keychain (Sprint 2 - PERF-2.10)
        if _try_keyring_available():
            key = self._get_key_from_keychain()
            if key:
                self._using_keychain = True
                return key

            # Migrer depuis fichier si existant
            if KEY_FILE.exists():
                key = self._migrate_key_to_keychain()
                if key:
                    self._using_keychain = True
                    return key

            # Generer nouvelle cle dans keychain
            key = self._create_key_in_keychain()
            if key:
                self._using_keychain = True
                return key

        # 2. Fallback: stockage fichier
        return self._get_or_create_key_file()

    def _get_key_from_keychain(self) -> bytes | None:
        """Recupere la cle depuis le keychain systeme."""
        try:
            import keyring
            key_str = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT)
            if key_str:
                logger.debug("Cle chargee depuis le keychain")
                return key_str.encode("utf-8")
        except Exception as e:
            logger.debug(f"Keychain non disponible: {e}")
        return None

    def _create_key_in_keychain(self) -> bytes | None:
        """Genere et stocke une nouvelle cle dans le keychain."""
        try:
            import keyring
            key = Fernet.generate_key()
            keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT, key.decode("utf-8"))
            logger.info("Nouvelle cle generee dans le keychain")
            return key
        except Exception as e:
            logger.warning(f"Impossible de stocker dans le keychain: {e}")
        return None

    def _migrate_key_to_keychain(self) -> bytes | None:
        """Migre la cle du fichier vers le keychain."""
        try:
            import keyring

            # Lire la cle du fichier
            with open(KEY_FILE, "rb") as f:
                key = f.read()

            # Stocker dans le keychain
            keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT, key.decode("utf-8"))

            # Supprimer le fichier (optionnel - garder comme backup)
            # KEY_FILE.unlink()

            logger.info("Cle migree du fichier vers le keychain")
            return key
        except Exception as e:
            logger.warning(f"Migration vers keychain echouee: {e}")
        return None

    def _get_or_create_key_file(self) -> bytes:
        """Recupere ou genere la cle depuis un fichier (fallback)."""
        logger.warning(
            "SEC-004: Utilisation du stockage fichier pour la cle de chiffrement. "
            "Le Keychain systeme n'est pas disponible. La cle est stockee dans %s "
            "avec permissions 600. Pour une securite optimale, installez le package "
            "'keyring' et assurez-vous que le Keychain macOS est accessible.",
            KEY_FILE,
        )
        if KEY_FILE.exists():
            # Charger la cle existante
            with open(KEY_FILE, "rb") as f:
                return f.read()
        else:
            # Générer une nouvelle clé
            key = Fernet.generate_key()

            # Sauvegarder avec permissions restrictives (atomique)
            fd = os.open(KEY_FILE, os.O_CREAT | os.O_WRONLY, 0o600)
            try:
                os.write(fd, key)
            finally:
                os.close(fd)

            logger.info("Nouvelle cle de chiffrement generee (fichier)")
            return key

    def _derive_key_from_password(self, password: str) -> bytes:
        """Derive une cle depuis un mot de passe (pour futur usage)."""
        # Generer ou charger le salt
        if SALT_FILE.exists():
            with open(SALT_FILE, "rb") as f:
                salt = f.read()
        else:
            salt = os.urandom(16)
            with open(SALT_FILE, "wb") as f:
                f.write(salt)
            os.chmod(SALT_FILE, 0o600)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, plaintext: str) -> str:
        """
        Chiffre une chaine de caracteres.

        Args:
            plaintext: Texte en clair a chiffrer

        Returns:
            Texte chiffre en base64
        """
        if not plaintext:
            return ""

        if not self._fernet:
            raise RuntimeError("Service de chiffrement non initialise")

        encrypted = self._fernet.encrypt(plaintext.encode("utf-8"))
        return base64.urlsafe_b64encode(encrypted).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """
        Dechiffre une chaine de caracteres.

        Args:
            ciphertext: Texte chiffre en base64

        Returns:
            Texte en clair

        Raises:
            InvalidToken: Si le dechiffrement echoue
        """
        if not ciphertext:
            return ""

        if not self._fernet:
            raise RuntimeError("Service de chiffrement non initialise")

        try:
            encrypted = base64.urlsafe_b64decode(ciphertext.encode("utf-8"))
            decrypted = self._fernet.decrypt(encrypted)
            return decrypted.decode("utf-8")
        except InvalidToken:
            logger.warning("Echec du dechiffrement - token invalide")
            raise
        except Exception as e:
            logger.error(f"Erreur de dechiffrement: {e}")
            raise

    def is_encrypted(self, value: str) -> bool:
        """
        Verifie si une valeur semble etre chiffree.

        Heuristique: les valeurs chiffrees Fernet sont toujours
        en base64 et commencent par 'gAAAAA'.
        """
        if not value:
            return False

        # Les tokens Fernet commencent par 'gAAAAA' en base64
        try:
            decoded = base64.urlsafe_b64decode(value.encode("utf-8"))
            return decoded.startswith(b"gAAAAA") or len(decoded) > 50
        except Exception:
            return False

    def rotate_key(self) -> bytes | None:
        """
        Rotation de la cle de chiffrement.

        Note: Necessite de re-chiffrer toutes les donnees existantes.
        A appeler avec precaution.

        Returns:
            Ancienne cle pour permettre le re-chiffrement
        """
        # Sauvegarder l'ancienne cle
        old_key = None

        if self._using_keychain:
            try:
                import keyring
                old_key_str = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT)
                if old_key_str:
                    old_key = old_key_str.encode("utf-8")

                # Generer nouvelle cle
                new_key = Fernet.generate_key()
                keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT, new_key.decode("utf-8"))
                self._fernet = Fernet(new_key)
            except Exception as e:
                logger.error(f"Erreur rotation cle keychain: {e}")
                raise
        else:
            if KEY_FILE.exists():
                with open(KEY_FILE, "rb") as f:
                    old_key = f.read()

            # Generer nouvelle cle
            new_key = Fernet.generate_key()

            with open(KEY_FILE, "wb") as f:
                f.write(new_key)
            os.chmod(KEY_FILE, 0o600)

            self._fernet = Fernet(new_key)

        logger.warning("Cle de chiffrement rotee - re-chiffrement necessaire")
        return old_key

    @property
    def is_using_keychain(self) -> bool:
        """Indique si le keychain systeme est utilise."""
        return self._using_keychain


# Singleton global
_encryption_service: EncryptionService | None = None


def get_encryption_service() -> EncryptionService:
    """Recupere l'instance du service de chiffrement."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def encrypt_value(plaintext: str) -> str:
    """Helper pour chiffrer une valeur."""
    return get_encryption_service().encrypt(plaintext)


def decrypt_value(ciphertext: str) -> str:
    """Helper pour dechiffrer une valeur."""
    return get_encryption_service().decrypt(ciphertext)


def is_value_encrypted(value: str) -> bool:
    """Helper pour verifier si une valeur est chiffree."""
    return get_encryption_service().is_encrypted(value)
