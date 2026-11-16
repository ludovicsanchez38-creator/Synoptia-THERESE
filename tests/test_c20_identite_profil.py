"""R1 : l'identité d'un profil vient du disque, pas d'une réduction de '..'."""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.config import settings
from app.routers.config import get_stats
from app.routers.consents import _verifier_profil
from fastapi import HTTPException


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


async def test_r2_c1_casse_du_volume_et_identite_historique(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    profil = tmp_path / "synoptia"
    profil.mkdir()
    variante = tmp_path / "SYNOPTIA"
    variante.mkdir(exist_ok=True)
    # Volume insensible à la casse simulé sous Linux : les deux graphies ont
    # le même stat, même si resolve() conserve leurs écritures distinctes.
    stat_original = Path.stat

    def stat_du_volume(path, *args, **kwargs):
        return stat_original(profil if path == variante else path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", stat_du_volume)
    monkeypatch.setattr(settings, "data_dir", profil)
    session = AsyncMock(execute=AsyncMock(return_value=MagicMock(scalar=lambda: 0)))
    response = await get_stats(session=session, data_profiles=[str(variante)])
    assert response["data_profile_aliases"] == [str(variante)], "La casse dépend du volume, pas de resolve()"
    identite = response["data_profile_id"]
    monkeypatch.setattr(settings, "data_dir", variante)
    autre_graphie = await get_stats(session=session)
    assert autre_graphie["data_profile_id"] == identite


async def test_r2_c1_deux_dossiers_distincts_ne_partagent_pas_une_identite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    a, b = tmp_path / "A", tmp_path / "B"
    a.mkdir()
    b.mkdir()
    monkeypatch.setattr(settings, "data_dir", a)
    session = AsyncMock(execute=AsyncMock(return_value=MagicMock(scalar=lambda: 0)))
    premiere = await get_stats(session=session, data_profiles=[str(b)])
    monkeypatch.setattr(settings, "data_dir", b)
    seconde = await get_stats(session=session)
    assert premiere["data_profile_aliases"] == []
    assert premiere["data_profile_id"] != seconde["data_profile_id"]


async def test_r2_c2_un_lien_reoriente_ne_peut_recevoir_les_accords_de_sa_cible_ancienne(tmp_path, monkeypatch):
    a, b, lien = tmp_path / "A", tmp_path / "B", tmp_path / "lien"
    a.mkdir()
    b.mkdir()
    lien.symlink_to(a, target_is_directory=True)
    monkeypatch.setattr(settings, "data_dir", lien)
    session = AsyncMock(execute=AsyncMock(return_value=MagicMock(scalar=lambda: 0)))
    ancienne_identite = (await get_stats(session=session))["data_profile_id"]
    _verifier_profil(ancienne_identite)
    # Le lien initial est conservé pour pouvoir constater son ancienne cible.
    lien.rename(tmp_path / "ancien-lien")
    lien.symlink_to(b, target_is_directory=True)

    with pytest.raises(HTTPException) as erreur:
        _verifier_profil(ancienne_identite)

    assert erreur.value.status_code == 409
    _verifier_profil((await get_stats(session=session))["data_profile_id"])
