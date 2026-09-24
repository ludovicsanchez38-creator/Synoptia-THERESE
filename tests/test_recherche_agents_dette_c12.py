"""Dette de la recherche des agents relevée par l'audit de la release 0.74.1
(PR #96, parcours Python au lieu de grep), traitée au cycle 12.

- B-1040 : un motif non borné (`a{10000000}`) faisait allouer des gigaoctets
  à `regex.compile` ; grep le refusait.
- B-1041 : au délai, les correspondances déjà trouvées étaient jetées.
- B-1042 : la troncature à `max_results` n'était pas dite au modèle.
- B-1043 : un fichier non UTF-8 était ignoré sans le dire ; un BOM restait
  collé à la première ligne (`^import` ne la trouvait pas).
- B-1044 : `venv/`, `env/`, `dist/`, `src-tauri/target/` étaient parcourus ;
  une ligne de plusieurs milliers de caractères partait entière au modèle.
- B-1045 : un nom Windows déguisé (`cle.pem::$DATA`, `cle.pem.`, `.env `)
  passait le filtre des fichiers sensibles.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from app.services.agents import tools as module_outils
from app.services.agents.tools import AgentToolExecutor, _nom_de_fichier_sensible

# --- B-1040 -----------------------------------------------------------------


@pytest.mark.parametrize(
    "motif",
    [
        "a{10000000}",
        "a{2000,}",
        "(ab){1,5000}",
        "x" * 1200,
        "(a{1000}){1000}",
        "((ab){100}){100}c{900}",
    ],
)
async def test_un_motif_demesure_est_refuse_avant_compilation(
    tmp_path: Path, monkeypatch, motif: str
):
    (tmp_path / "a.py").write_text("aaa\n", encoding="utf-8")

    def compile_interdit(*_args, **_kwargs):
        raise AssertionError("regex.compile appelé sur un motif démesuré")

    monkeypatch.setattr(module_outils.regex, "compile", compile_interdit)
    debut = time.monotonic()
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase(motif, "*.py")
    assert time.monotonic() - debut < 1
    assert sortie.startswith("Erreur : motif trop coûteux"), sortie


async def test_une_repetition_raisonnable_et_des_accolades_echappees_passent(tmp_path: Path):
    (tmp_path / "a.py").write_text("x = {1000}\nidentifiant_abc\n2026-09-24\n", encoding="utf-8")
    executeur = AgentToolExecutor(str(tmp_path))
    assert await executeur.search_codebase(r"\{1000\}", "*.py") == "a.py:1:x = {1000}"
    assert await executeur.search_codebase(r"[a-z_]{3,40}abc", "*.py") == "a.py:2:identifiant_abc"
    assert await executeur.search_codebase(r"\d{4}-\d{2}-\d{2}", "*.py") == "a.py:3:2026-09-24"
    assert (
        await executeur.search_codebase(r"[{]1000[}]|(?:ab){0,10}_abc", "*.py")
        == "a.py:1:x = {1000}\na.py:2:identifiant_abc"
    )


# --- B-1041 -----------------------------------------------------------------


async def test_au_delai_les_correspondances_deja_trouvees_sont_rendues(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(module_outils, "DELAI_RECHERCHE_S", 0.5)
    (tmp_path / "a.py").write_text("trouve_moi = 1\n", encoding="utf-8")
    (tmp_path / "z.py").write_text("a" * 60 + "!\n", encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("trouve_moi|(a|aa)+$", "*.py")
    lignes = sortie.splitlines()
    assert lignes[0] == "a.py:1:trouve_moi = 1", sortie
    assert "partiel" in lignes[-1] and "délai" in lignes[-1], sortie


# --- B-1042 -----------------------------------------------------------------


async def test_la_troncature_au_nombre_de_resultats_est_dite(tmp_path: Path):
    (tmp_path / "a.py").write_text("cible\n" * 30, encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("cible", "*.py", max_results=5)
    lignes = sortie.splitlines()
    assert lignes[:5] == [f"a.py:{n}:cible" for n in range(1, 6)], sortie
    assert len(lignes) == 6 and "5" in lignes[5] and "limit" in lignes[5], sortie


async def test_exactement_max_resultats_sans_autre_correspondance_n_annonce_pas_de_troncature(
    tmp_path: Path,
):
    (tmp_path / "a.py").write_text("cible\n" * 5, encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("cible", "*.py", max_results=5)
    assert sortie.splitlines() == [f"a.py:{n}:cible" for n in range(1, 6)], sortie


# --- B-1043 -----------------------------------------------------------------


async def test_un_fichier_non_utf8_ignore_est_signale_au_modele(tmp_path: Path):
    (tmp_path / "latin.py").write_bytes("cible = 'élan'\n".encode("cp1252"))
    (tmp_path / "texte.py").write_text("cible = 'lisible'\n", encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("cible", "*.py")
    lignes = sortie.splitlines()
    assert lignes[0] == "texte.py:1:cible = 'lisible'", sortie
    assert any("UTF-8" in ligne for ligne in lignes[1:]), sortie


async def test_un_bom_n_empeche_pas_de_trouver_la_premiere_ligne(tmp_path: Path):
    (tmp_path / "bom.py").write_bytes(b"\xef\xbb\xbfimport os\n")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("^import os", "*.py")
    assert sortie == "bom.py:1:import os", sortie


# --- B-1044 -----------------------------------------------------------------


async def test_les_dossiers_lourds_ne_sont_pas_parcourus(tmp_path: Path):
    for dossier in ("venv", "env", "dist", "src/frontend/src-tauri/target", "build/.venv"):
        (tmp_path / dossier).mkdir(parents=True)
        (tmp_path / dossier / "a.py").write_text("cible = 'exclu'\n", encoding="utf-8")
    (tmp_path / "target").mkdir()
    (tmp_path / "target" / "garde.py").write_text("cible = 'hors src-tauri'\n", encoding="utf-8")
    (tmp_path / "garde.py").write_text("cible = 'garde'\n", encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("cible", "*.py")
    assert sortie.splitlines() == [
        "garde.py:1:cible = 'garde'",
        "target/garde.py:1:cible = 'hors src-tauri'",
    ], sortie


async def test_une_ligne_tres_longue_est_tronquee_pour_le_modele(tmp_path: Path):
    (tmp_path / "min.py").write_text("cible" + "x" * 5000 + "\n", encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("cible", "*.py")
    assert sortie.startswith("min.py:1:cible"), sortie[:80]
    assert len(sortie) < 700, len(sortie)
    assert "tronqu" in sortie, sortie[-120:]


# --- B-1045 -----------------------------------------------------------------


@pytest.mark.parametrize(
    "nom",
    [
        "cle.pem::$DATA",
        "cle.pem.",
        "cle.pem. .",
        ".env ",
        ".ENV.",
        "CLE.PEM:zone",
        "certificat.p12::$data",
    ],
)
def test_un_nom_windows_deguise_reste_sensible(nom: str):
    assert _nom_de_fichier_sensible(nom), nom


@pytest.mark.parametrize("nom", ["cle.py", "pem.md", "environnement.py", "notes:pem.txt"])
def test_un_nom_ordinaire_n_est_pas_sensible(nom: str):
    assert not _nom_de_fichier_sensible(nom), nom


def test_read_file_refuse_un_nom_deguise_par_un_point_final(tmp_path: Path):
    (tmp_path / "cle.pem.").write_text("-----BEGIN PRIVATE KEY-----\n", encoding="utf-8")
    with pytest.raises(PermissionError):
        AgentToolExecutor(str(tmp_path))._validate_path("cle.pem.")


# --- B-1046, B-1047, B-1048 (relevés par les lecteurs de la carte c12) -------


@pytest.mark.parametrize(
    "nom",
    [
        "id_rsa",
        "id_ed25519",
        ".netrc",
        ".npmrc",
        ".pypirc",
        "credentials.json",
        "service-account.json",
    ],
)
def test_les_secrets_usuels_sont_sensibles(nom: str):
    assert _nom_de_fichier_sensible(nom), nom


async def test_read_file_ne_rend_pas_de_chemin_absolu_au_modele(tmp_path: Path):
    (tmp_path / "dossier").mkdir()
    (tmp_path / "dossier" / "a.txt").write_text("x", encoding="utf-8")
    (tmp_path / "dossier" / "a.txt").chmod(0)
    try:
        sortie = await AgentToolExecutor(str(tmp_path)).read_file("dossier/a.txt")
    finally:
        (tmp_path / "dossier" / "a.txt").chmod(0o644)
    assert sortie.startswith("Erreur"), sortie
    assert str(tmp_path) not in sortie and "/Users/" not in sortie and "/home/" not in sortie, (
        sortie
    )


@pytest.mark.parametrize("max_lines", [-3, 0])
async def test_read_file_borne_max_lines(tmp_path: Path, max_lines: int):
    (tmp_path / "a.txt").write_text("\n".join(f"ligne {n}" for n in range(10)), encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).read_file("a.txt", max_lines=max_lines)
    assert "-" not in sortie.splitlines()[-1] or "tronqué" not in sortie, sortie
    assert sortie.splitlines()[0] == "ligne 0", sortie


# --- B-1049 (lecteur B de la carte c12) --------------------------------------


def test_un_lien_interne_vers_un_secret_est_refuse(tmp_path: Path):
    (tmp_path / ".env").write_text("CLE_API=secret\n", encoding="utf-8")
    (tmp_path / "notes.txt").symlink_to(tmp_path / ".env")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("[core]\n", encoding="utf-8")
    (tmp_path / "config_git").symlink_to(tmp_path / ".git" / "config")
    executeur = AgentToolExecutor(str(tmp_path))
    with pytest.raises(PermissionError):
        executeur._validate_path("notes.txt")
    with pytest.raises(PermissionError):
        executeur._validate_path("config_git")
