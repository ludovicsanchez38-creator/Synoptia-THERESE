"""US-003 : les sauvegardes sont chiffrées par une passphrase utilisateur.

L'archive embarque la clé de chiffrement (pour rester restaurable après perte de
la machine, US-014), donc une archive en clair équivaudrait à une base en clair.
On chiffre toute l'archive (PBKDF2 + Fernet, sel frais par sauvegarde).
"""
import tarfile

import pytest
from app.services.encryption import decrypt_backup_archive, encrypt_backup_archive


def test_encrypt_decrypt_round_trip(tmp_path):
    plain = tmp_path / "a.tar.gz"
    plain.write_bytes(b"contenu-archive-binaire")
    enc = tmp_path / "a.tar.gz.enc"

    encrypt_backup_archive(plain, enc, "hunter2-passphrase")

    blob = enc.read_bytes()
    assert blob[:5] == b"THBK1"
    assert b"contenu-archive-binaire" not in blob  # le clair n'apparait pas

    out = tmp_path / "out.tar.gz"
    decrypt_backup_archive(enc, out, "hunter2-passphrase")
    assert out.read_bytes() == b"contenu-archive-binaire"


def test_deux_sauvegardes_ont_des_sels_differents(tmp_path):
    plain = tmp_path / "a.tar.gz"
    plain.write_bytes(b"meme-contenu")
    enc1 = tmp_path / "1.enc"
    enc2 = tmp_path / "2.enc"
    encrypt_backup_archive(plain, enc1, "pw")
    encrypt_backup_archive(plain, enc2, "pw")
    # Sel frais par sauvegarde -> blobs differents malgre le meme contenu/passphrase.
    assert enc1.read_bytes() != enc2.read_bytes()


def test_mauvaise_passphrase_leve_valueerror(tmp_path):
    plain = tmp_path / "a.tar.gz"
    plain.write_bytes(b"x")
    enc = tmp_path / "a.enc"
    encrypt_backup_archive(plain, enc, "bonne-passphrase")
    with pytest.raises(ValueError):
        decrypt_backup_archive(enc, tmp_path / "o", "mauvaise-passphrase")


@pytest.mark.asyncio
async def test_backup_sans_passphrase_refuse(client):
    resp = await client.post("/api/data/backup", json={})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_backup_passphrase_vide_refuse(client):
    resp = await client.post("/api/data/backup", json={"password": "   "})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_backup_produit_une_archive_chiffree(client):
    resp = await client.post("/api/data/backup", json={"password": "pw-solide-123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["encrypted"] is True
    assert body["path"].endswith(".tar.gz.enc")
    # Ce n'est pas un tar lisible tel quel.
    with pytest.raises(tarfile.ReadError):
        tarfile.open(body["path"], "r:gz")


@pytest.mark.asyncio
async def test_restore_chiffre_sans_passphrase_refuse(client):
    created = await client.post("/api/data/backup", json={"password": "pw-solide-123"})
    name = created.json()["backup_name"]

    resp = await client.post(f"/api/data/restore/{name}?confirm=true")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_restore_chiffre_mauvaise_passphrase_refuse(client):
    created = await client.post("/api/data/backup", json={"password": "bonne-pw-123"})
    name = created.json()["backup_name"]

    resp = await client.post(
        f"/api/data/restore/{name}?confirm=true", json={"password": "mauvaise-pw"}
    )
    assert resp.status_code == 400
