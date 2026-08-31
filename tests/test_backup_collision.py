"""Revue 30/08 : deux sauvegardes dans la même seconde se recouvraient.

Le nom s'arrêtait à la seconde. La seconde archive réécrivait le même
`.tar.gz.enc` et le même `.json` : l'utilisateur croyait en avoir deux,
il n'en restait qu'une, parfois incomplète. On ne recouvre jamais une
archive existante.
"""
from pathlib import Path

import pytest
from app.routers.data import nom_sauvegarde_libre


def test_nom_sauvegarde_libre_sans_collision(tmp_path: Path) -> None:
    nom = nom_sauvegarde_libre(tmp_path, "20260830_120000")
    assert nom == "therese_backup_20260830_120000"


def test_nom_sauvegarde_libre_evite_un_enc_deja_la(tmp_path: Path) -> None:
    (tmp_path / "therese_backup_20260830_120000.tar.gz.enc").write_bytes(b"x")
    nom = nom_sauvegarde_libre(tmp_path, "20260830_120000")
    assert nom != "therese_backup_20260830_120000"
    assert nom.startswith("therese_backup_20260830_120000")


def test_nom_sauvegarde_libre_evite_un_json_deja_la(tmp_path: Path) -> None:
    (tmp_path / "therese_backup_20260830_120000.json").write_text("{}")
    nom = nom_sauvegarde_libre(tmp_path, "20260830_120000")
    assert nom != "therese_backup_20260830_120000"


@pytest.mark.asyncio
async def test_deux_sauvegardes_la_meme_seconde_restent_distinctes(
    client, monkeypatch
) -> None:
    from datetime import UTC, datetime

    from app.routers import data as data_router

    fige = datetime(2026, 8, 30, 12, 0, 0, tzinfo=UTC)

    class HorlogeFigee(datetime):
        @classmethod
        def now(cls, tz=None):  # noqa: ANN001
            return fige

    monkeypatch.setattr(data_router, "datetime", HorlogeFigee)

    r1 = await client.post("/api/data/backup", json={"password": "pw-solide-123"})
    r2 = await client.post("/api/data/backup", json={"password": "pw-solide-123"})
    assert r1.status_code == 200, r1.text
    assert r2.status_code == 200, r2.text
    n1 = r1.json()["backup_name"]
    n2 = r2.json()["backup_name"]
    assert n1 != n2
    assert Path(r1.json()["path"]).exists()
    assert Path(r2.json()["path"]).exists()
