"""R1 : l'identité d'un profil vient du disque, pas d'une réduction de '..'."""
from pathlib import Path

import pytest
from app.config import settings


async def test_r1_c1_stats_identifient_le_dossier_reel(client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    profil = tmp_path / "A"
    profil.mkdir()
    intermediaire = tmp_path / "intermediaire"
    intermediaire.mkdir()
    alias = intermediaire / ".." / "A"
    monkeypatch.setattr(settings, "data_dir", alias)

    response = await client.get("/api/config/stats", params=[("data_profiles", str(profil))])

    assert response.status_code == 200
    assert response.json().get("data_profile") == str(profil.resolve()), "Le moteur doit annoncer le dossier canonique"
    assert response.json()["data_profile_aliases"] == [str(profil)]


async def test_r1_c1_garde_aussi_le_chemin_configure_pour_la_migration_historique(client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    profil = tmp_path / "A"
    profil.mkdir()
    historique = tmp_path / ".therese"
    historique.symlink_to(profil, target_is_directory=True)
    monkeypatch.setattr(settings, "data_dir", historique)

    response = await client.get("/api/config/stats")

    assert response.status_code == 200
    assert response.json()["data_dir"] == str(historique), "Le chemin configuré reste nécessaire à la migration historique"
    assert response.json()["data_profile"] == str(profil.resolve())


async def test_r1_c1_ne_confond_pas_un_parent_de_lien_avec_le_parent_lexical(client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    profil = tmp_path / "A"
    profil.mkdir()
    (tmp_path / "intermediaire").mkdir()
    (tmp_path / "autre" / "enfant").mkdir(parents=True)
    (tmp_path / "autre" / "A").mkdir()
    lien = tmp_path / "lien"
    lien.symlink_to(tmp_path / "autre" / "enfant", target_is_directory=True)
    vrai_alias = str(tmp_path / "intermediaire" / ".." / "A")
    faux_alias = str(lien / ".." / "A")
    absent = str(tmp_path / "absent" / ".." / "A")
    monkeypatch.setattr(settings, "data_dir", profil)

    response = await client.get("/api/config/stats", params=[
        ("data_profiles", p) for p in [vrai_alias, faux_alias, absent]
    ])

    assert response.status_code == 200
    assert response.json()["data_profile_aliases"] == [vrai_alias]
