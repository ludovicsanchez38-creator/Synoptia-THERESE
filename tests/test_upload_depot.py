"""Revue 30/08 : l'upload écrivait avant de valider.

Un nom en `../` sortait du dossier projet, un nom avec `/` créait des
sous-dossiers, et la limite de 50 Mo n'était consultée qu'après la copie :
un binaire de 800 Mo saturait le disque avant le 413. Un échec franc
avant toute écriture vaut mieux qu'un fichier hors périmètre ou trop gros.
"""
from __future__ import annotations

import io
from pathlib import Path

import pytest
from app.config import settings
from app.routers.files import (
    FichierTropVolumineux,
    NomDeFichierInvalide,
    chemin_de_depot,
    copier_plafonne,
)


def test_chemin_de_depot_refuse_la_traversee(tmp_path: Path) -> None:
    depot = tmp_path / "projects" / "p1" / "files"
    depot.mkdir(parents=True)

    with pytest.raises(NomDeFichierInvalide):
        chemin_de_depot(depot, "../escape.txt")
    with pytest.raises(NomDeFichierInvalide):
        chemin_de_depot(depot, "..\\..\\backups\\x.txt")
    with pytest.raises(NomDeFichierInvalide):
        chemin_de_depot(depot, "sous/dossier.txt")


def test_chemin_de_depot_accepte_un_nom_simple(tmp_path: Path) -> None:
    depot = tmp_path / "files"
    depot.mkdir()
    dest = chemin_de_depot(depot, "rapport.pdf")
    assert dest == (depot / "rapport.pdf").resolve()
    assert dest.is_relative_to(depot.resolve())


def test_copier_plafonne_refuse_sans_laisser_le_fichier(tmp_path: Path) -> None:
    dest = tmp_path / "out.bin"
    with pytest.raises(FichierTropVolumineux):
        copier_plafonne(io.BytesIO(b"x" * 50), dest, plafond=10)
    assert not dest.exists()


def test_copier_plafonne_ecrit_un_fichier_sous_le_plafond(tmp_path: Path) -> None:
    dest = tmp_path / "ok.bin"
    copier_plafonne(io.BytesIO(b"hello"), dest, plafond=10)
    assert dest.read_bytes() == b"hello"


@pytest.mark.asyncio
async def test_upload_refuse_un_nom_qui_sort_du_projet(client) -> None:
    resp = await client.post("/api/memory/projects", json={"name": "Lot G upload"})
    assert resp.status_code in (200, 201), resp.text
    projet_id = resp.json()["id"]
    hors_cible = Path(settings.data_dir) / "projects" / projet_id / "escape.txt"

    resp = await client.post(
        "/api/files/upload",
        files={"file": ("../escape.txt", b"contenu interdit", "text/plain")},
        data={"project_id": projet_id},
    )
    assert resp.status_code == 400
    assert not hors_cible.exists()


@pytest.mark.asyncio
async def test_upload_refuse_avant_d_ecrire_un_fichier_trop_gros(
    client, monkeypatch
) -> None:
    import app.routers.files as files_router

    monkeypatch.setattr(files_router, "MAX_INDEXABLE_SIZE", 20)

    resp = await client.post("/api/memory/projects", json={"name": "Lot G gros"})
    assert resp.status_code in (200, 201), resp.text
    projet_id = resp.json()["id"]
    dest = (
        Path(settings.data_dir)
        / "projects"
        / projet_id
        / "files"
        / "gros.txt"
    )

    resp = await client.post(
        "/api/files/upload",
        files={"file": ("gros.txt", b"x" * 80, "text/plain")},
        data={"project_id": projet_id},
    )
    assert resp.status_code == 413
    assert not dest.exists()
