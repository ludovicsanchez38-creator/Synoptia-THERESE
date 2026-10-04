"""B-1772 : invalidation de la clé en mémoire avant réouverture de la base.

Contrôles unitaires sans HTTP, base, archive ou trousseau. Les clés Fernet
sont synthétiques et le chargement de clé est simulé.
"""
import asyncio
from unittest.mock import AsyncMock

import pytest
from app.models import database
from app.routers import data
from app.services import encryption, llm
from cryptography.fernet import Fernet


@pytest.fixture
def service_et_cles(monkeypatch):
    monkeypatch.delenv("THERESE_DB_KEY", raising=False)
    monkeypatch.setattr(encryption, "_encryption_service", None)
    monkeypatch.setattr(encryption.EncryptionService, "_instance", None)
    cle = [Fernet.generate_key()]
    monkeypatch.setattr(encryption.EncryptionService, "_get_or_create_key", lambda self: cle[0])
    service = encryption.get_encryption_service()
    # Ne créer aucun dossier : l'initialisation ne lit que le témoin en mémoire.
    def initialiser():
        service._master_key = cle[0]
        service._fernet = Fernet(cle[0])
    monkeypatch.setattr(service, "_initialize", initialiser)
    encryption.get_db_key_hex()
    return service, cle


def test_la_reference_existante_recharge_la_cle_sans_creation(service_et_cles):
    service, cle = service_et_cles
    identite = id(service)
    ancienne = encryption.get_db_key_hex()
    cle[0] = Fernet.generate_key()
    encryption.invalidate_encryption_service()
    assert service._fernet is None
    assert service._master_key is None
    assert service.is_using_keychain is False
    assert id(encryption.get_encryption_service()) == identite
    assert encryption.get_db_key_hex() == encryption.derive_db_key_from_master(cle[0])
    assert encryption.get_db_key_hex() != ancienne
    assert service.decrypt(service.encrypt("témoin synthétique")) == "témoin synthétique"


def test_invalidation_sans_instance_ne_cree_pas_de_service(monkeypatch):
    monkeypatch.setattr(encryption, "_encryption_service", None)
    monkeypatch.setattr(encryption.EncryptionService, "_instance", None)
    encryption.invalidate_encryption_service()
    assert encryption._encryption_service is None
    assert encryption.EncryptionService._instance is None


@pytest.mark.asyncio
async def test_reouverture_ou_rollback_recharge_la_cle_avant_init(service_et_cles, monkeypatch):
    service, cle = service_et_cles
    cle_initiale = cle[0]
    cle[0] = Fernet.generate_key()
    monkeypatch.setattr(database, "sync_engine", None)
    invalider_llm = []
    monkeypatch.setattr(llm, "invalidate_llm_service", lambda: invalider_llm.append(True))
    for cle_finale in (cle[0], cle_initiale):
        cle[0] = cle_finale  # Succès B puis état A après un retour arrière.
        async def initialiser_base(cle_attendue=cle_finale):
            assert encryption.get_db_key_hex() == encryption.derive_db_key_from_master(cle_attendue)
        monkeypatch.setattr(database, "init_db", initialiser_base)
        await data._rouvrir_la_base_apres_restauration()
        assert service._master_key == cle_finale
    assert len(invalider_llm) == 2


@pytest.mark.asyncio
async def test_moteur_actif_conserve_son_cache(service_et_cles, monkeypatch):
    service, _ = service_et_cles
    ancienne = service._master_key
    monkeypatch.setattr(database, "sync_engine", object())
    init = AsyncMock()
    monkeypatch.setattr(database, "init_db", init)
    monkeypatch.setattr(llm, "invalidate_llm_service", lambda: None)
    await data._rouvrir_la_base_apres_restauration()
    assert service._master_key == ancienne
    init.assert_not_awaited()


@pytest.mark.asyncio
async def test_annulation_de_reouverture_est_propagee(service_et_cles, monkeypatch):
    service, _ = service_et_cles
    monkeypatch.setattr(database, "sync_engine", None)
    monkeypatch.setattr(database, "init_db", AsyncMock(side_effect=asyncio.CancelledError))
    monkeypatch.setattr(llm, "invalidate_llm_service", lambda: None)
    with pytest.raises(asyncio.CancelledError):
        await data._rouvrir_la_base_apres_restauration()
    assert service._master_key is None
