"""R1 : l'identité d'un profil vient du disque, pas d'une réduction de '..'."""
from pathlib import Path
from stat import S_IFDIR
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.config import settings
from app.routers.config import get_stats
from app.routers.consents import _verifier_profil
from app.services.identite_profil import identite_profil
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
    # Les lectures et créations sur le volume simulé suivent aussi la casse.
    open_original = Path.open

    def open_du_volume(path, *args, **kwargs):
        if path.parent == variante:
            path = profil / path.name
        return open_original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", open_du_volume)
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


def test_r3_c4_un_inode_reutilise_ne_reprend_pas_l_identite_du_dossier_precedent(tmp_path, monkeypatch):
    dossier = tmp_path / "profil"
    dossier.mkdir()
    stat_original = Path.stat

    def stat_linux(path, *args, **kwargs):
        if path == dossier:
            return SimpleNamespace(st_mode=S_IFDIR, st_dev=7, st_ino=42)
        return stat_original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", stat_linux)
    monkeypatch.setattr(settings, "data_dir", dossier)
    premiere = identite_profil(dossier)
    _verifier_profil(premiere)
    (dossier / "donnee").write_text("modification du contenu", encoding="utf-8")
    assert identite_profil(dossier) == premiere, "Une écriture ne change pas le profil"
    dossier.rename(tmp_path / "ancien-profil")
    dossier.mkdir()

    assert identite_profil(dossier) != premiere, "Un inode réutilisé doit désigner un nouveau profil"
    with pytest.raises(HTTPException) as erreur:
        _verifier_profil(premiere)
    assert erreur.value.status_code == 409


def test_r3_c4_identite_durable_apres_relecture_et_par_un_lien(tmp_path):
    dossier = tmp_path / "profil"
    dossier.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(dossier, target_is_directory=True)
    premiere = identite_profil(dossier)
    assert identite_profil(alias) == premiere
    assert identite_profil(dossier) == premiere


def test_r3_c4_un_marqueur_incomplet_est_refuse_sans_etre_remplace(tmp_path):
    marqueur = tmp_path / ".therese-profile-id"
    marqueur.write_text("", encoding="ascii")
    with pytest.raises(ValueError):
        identite_profil(tmp_path)
    assert marqueur.read_text(encoding="ascii") == ""
