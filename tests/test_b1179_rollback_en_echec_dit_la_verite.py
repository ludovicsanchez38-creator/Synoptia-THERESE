"""B-1179 : une restauration en échec dont le rollback échoue aussi répond
quand même « Données restaurées à l'état précédent ».

Attendu : le message ne promet la remise en état que si le rollback a réussi
(règle maison du faux succès, cf. memory.py:241-244 « un faux succès plus
grave qu'une suppression refusée »). `_rollback` (data.py:1429-1440) attrape
sa propre exception et ne rend rien ; la branche `except Exception`
(data.py:1494-1508) affirme la restauration dans tous les cas.

Panne injectée : `_safe_extractall` lève (disque plein), à la restauration
PUIS au rollback, qui rappelle la même fonction.
"""

from __future__ import annotations

import errno
import logging
from pathlib import Path

import pytest
from app.config import settings
from app.routers import data as data_router

PASSE = "Passphrase-Test-123"


def _etat_courant(data_dir: Path) -> None:
    (data_dir / "images").mkdir(parents=True, exist_ok=True)
    (data_dir / "images" / "img.png").write_bytes(b"image-courante")
    (data_dir / "THERESE.md").write_text("Mes consignes actuelles", encoding="utf-8")


@pytest.mark.asyncio
async def test_un_rollback_en_echec_n_annonce_pas_des_donnees_restaurees(
    client, monkeypatch, caplog
):
    data_dir = Path(settings.data_dir)
    _etat_courant(data_dir)
    resp = await client.post("/api/data/backup", json={"password": PASSE})
    assert resp.status_code == 200, resp.text
    nom = resp.json()["backup_name"]

    appels: list[str] = []

    def _disque_plein(tar, dest):
        appels.append(str(dest))
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(data_router, "_safe_extractall", _disque_plein)

    with caplog.at_level(logging.ERROR):
        resp = await client.post(
            f"/api/data/restore/{nom}?confirm=true", json={"password": PASSE}
        )

    corps = resp.json()
    # Le gestionnaire d'erreurs de l'application rend {"code", "message"},
    # pas {"detail"} : lire « detail » donnait "" et un faux vert.
    detail = corps.get("message") or corps.get("detail") or ""
    assert detail, corps
    images_ok = (data_dir / "images" / "img.png").exists()
    consignes_ok = (data_dir / "THERESE.md").exists()
    rollback_rate = "Rollback du restore en échec" in caplog.text

    # Mesures posées avant le verdict (lisibles dans la trace d'échec).
    assert resp.status_code == 500, resp.text
    assert len(appels) == 2, appels  # restauration + rollback
    assert rollback_rate, "le rollback n'a pas échoué : la panne n'a pas porté"
    assert not images_ok and not consignes_ok, (images_ok, consignes_ok)
    assert "Données restaurées à l'état précédent" not in detail, (
        f"rollback en échec (journal : « Rollback du restore en échec »), "
        f"images/img.png présent={images_ok}, THERESE.md présent={consignes_ok}, "
        f"et pourtant la réponse 500 dit : {detail!r}"
    )


@pytest.mark.asyncio
async def test_temoin_un_rollback_reussi_remet_bien_l_etat(client, monkeypatch):
    """Témoin : si seule la restauration échoue, le rollback rend l'état, et
    le message dit vrai."""
    data_dir = Path(settings.data_dir)
    _etat_courant(data_dir)
    resp = await client.post("/api/data/backup", json={"password": PASSE})
    assert resp.status_code == 200, resp.text
    nom = resp.json()["backup_name"]

    vraie = data_router._safe_extractall
    appels: list[int] = []

    def _echoue_une_fois(tar, dest):
        appels.append(1)
        if len(appels) == 1:
            raise OSError(errno.ENOSPC, "No space left on device")
        return vraie(tar, dest)

    monkeypatch.setattr(data_router, "_safe_extractall", _echoue_une_fois)

    resp = await client.post(
        f"/api/data/restore/{nom}?confirm=true", json={"password": PASSE}
    )

    assert resp.status_code == 500
    corps = resp.json()
    assert "Données restaurées à l'état précédent" in (corps.get("message") or corps.get("detail") or "")
    assert (data_dir / "images" / "img.png").read_bytes() == b"image-courante"
    assert (data_dir / "THERESE.md").read_text(encoding="utf-8") == "Mes consignes actuelles"


@pytest.mark.asyncio
async def test_une_base_refusee_puis_un_rollback_en_echec_ne_dit_pas_intactes(client, monkeypatch):
    """B-1203 : régression de B-1179, la réponse disait à la fois « tes données
    actuelles sont intactes » (409 de la vérification) et « des données ont pu
    être perdues » (rollback en échec)."""
    from fastapi import HTTPException

    data_dir = Path(settings.data_dir)
    _etat_courant(data_dir)
    resp = await client.post("/api/data/backup", json={"password": PASSE})
    assert resp.status_code == 200, resp.text
    nom = resp.json()["backup_name"]

    vraie_extraction = data_router._safe_extractall
    appels: list[str] = []

    def _extraction(tar, dest):
        appels.append(str(dest))
        if len(appels) == 1:
            return vraie_extraction(tar, dest)  # la restauration passe
        raise OSError(errno.ENOSPC, "No space left on device")  # le rollback, non

    def _base_refusee():
        raise HTTPException(
            status_code=409,
            detail=(
                "La base restaurée est chiffrée avec une clé introuvable sur cette "
                "machine (archive sans .encryption_key ?). Restauration annulée, "
                "tes données actuelles sont intactes."
            ),
        )

    monkeypatch.setattr(data_router, "_safe_extractall", _extraction)
    monkeypatch.setattr(data_router, "_verify_restored_db", _base_refusee)

    resp = await client.post(f"/api/data/restore/{nom}?confirm=true", json={"password": PASSE})

    corps = resp.json()
    detail = corps.get("message") or corps.get("detail") or ""
    assert resp.status_code == 409, resp.text
    assert len(appels) == 2, appels
    assert "intactes" not in detail and "ont pu être perdues" in detail, detail
