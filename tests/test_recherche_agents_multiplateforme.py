"""Recherche des agents sans grep (23/09/2026, CI Windows du run 35903233291).

`search_codebase` lançait grep. Sous Windows, le grep fourni par Git (MSYS)
développe lui-même les jokers de sa ligne de commande : `--include *.py`
devenait `--include test_validation_bug.py` (le seul `.py` du dossier courant
de la CI), `*.json` devenait `package.json`, et la recherche rendait « Aucun
résultat » sans erreur. `*.yaml`, sans fichier correspondant à la racine,
passait : c'est ce qui a trahi la cause. Sans grep dans le PATH, la recherche
échouait tout court.

La recherche est désormais faite en Python : aucun processus n'est lancé,
le comportement ne dépend plus du poste ni du dossier courant.
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path

import pytest
from app.services.agents import tools as module_outils
from app.services.agents.tools import AgentToolExecutor


@pytest.fixture
def depot(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    source.mkdir()
    (source / "reglages.py").write_text(
        'OPTIONS = ["--timeout=30"]\ndef lire() -> None:\n    return None\n',
        encoding="utf-8",
    )
    (source / "config.json").write_text('{"cle": "valeur"}\n', encoding="utf-8")
    return source


class _GrepMuet:
    """Le grep de la CI Windows : il répond, sans rien trouver."""

    returncode = 1
    pid = 4242

    async def communicate(self):
        return b"", b""


@pytest.mark.parametrize("grep_du_poste", ["absent", "muet"])
async def test_la_recherche_ne_depend_pas_du_grep_du_poste(depot: Path, monkeypatch, grep_du_poste: str):
    lances: list[tuple] = []

    async def faux_exec(*args, **kwargs):
        lances.append(args)
        if grep_du_poste == "absent":
            raise FileNotFoundError(2, "No such file or directory", "grep")
        return _GrepMuet()

    monkeypatch.setattr(module_outils.asyncio, "create_subprocess_exec", faux_exec)
    executeur = AgentToolExecutor(str(depot))
    assert "reglages.py:2:def lire() -> None:" in await executeur.search_codebase("def lire", "*.py")
    assert 'config.json:1:{"cle": "valeur"}' in await executeur.search_codebase("valeur", "*.json")
    assert lances == [], "la recherche ne doit lancer aucun processus"


async def test_le_filtre_ne_depend_pas_du_dossier_courant(depot: Path, tmp_path: Path, monkeypatch):
    """Le dossier courant de la CI contenait un `.py` qui capturait le joker."""
    ailleurs = tmp_path / "ailleurs"
    ailleurs.mkdir()
    (ailleurs / "leurre.py").write_text("def lire(): pass\n", encoding="utf-8")
    monkeypatch.chdir(ailleurs)
    sortie = await AgentToolExecutor(str(depot)).search_codebase("def lire", "*.py")
    assert "reglages.py:2:" in sortie and "leurre" not in sortie, sortie


async def test_le_nombre_de_resultats_est_borne(tmp_path: Path):
    (tmp_path / "a.py").write_text("cible\n" * 30, encoding="utf-8")
    (tmp_path / "b.py").write_text("cible\n" * 30, encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("cible", "*.py", max_results=5)
    assert sortie.splitlines() == [f"a.py:{n}:cible" for n in range(1, 6)], sortie
    defaut = await AgentToolExecutor(str(tmp_path)).search_codebase("cible", "*.py")
    assert len(defaut.splitlines()) == 20, defaut


async def test_les_dossiers_exclus_ne_sont_pas_parcourus(tmp_path: Path):
    # La variante de casse vit dans un sous-dossier : sous Windows (NTFS,
    # insensible à la casse), `Node_Modules` et `node_modules` sont le même nom.
    for dossier in (".git", ".venv", "node_modules", "src/Node_Modules"):
        (tmp_path / dossier).mkdir(parents=True)
        (tmp_path / dossier / "a.py").write_text("cible = 'exclu'\n", encoding="utf-8")
    (tmp_path / "garde.py").write_text("cible = 'garde'\n", encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("cible", "*.py")
    assert sortie == "garde.py:1:cible = 'garde'", sortie


async def test_un_fichier_binaire_n_est_pas_lu(tmp_path: Path):
    (tmp_path / "donnees.json").write_bytes(b'{"cible": 1}\x00\x01\x02\n')
    (tmp_path / "texte.json").write_text('{"cible": 2}\n', encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("cible", "*.json")
    assert sortie == 'texte.json:1:{"cible": 2}', sortie


async def test_un_fichier_trop_volumineux_est_signale_sans_etre_lu(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(module_outils, "TAILLE_MAX_FICHIER_RECHERCHE", 64)
    (tmp_path / "gros.py").write_text("cible = 1\n" + "#" * 200 + "\n", encoding="utf-8")
    (tmp_path / "petit.py").write_text("cible = 2\n", encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("cible", "*.py")
    assert sortie.splitlines() == [
        "petit.py:1:cible = 2",
        "(certains fichiers trop volumineux n'ont pas été parcourus)",
    ], sortie


async def test_une_fin_de_ligne_windows_n_est_pas_rendue(tmp_path: Path):
    (tmp_path / "a.py").write_bytes(b"cible = 1\r\nautre = 2\r\n")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("cible = 1$", "*.py")
    assert sortie == "a.py:1:cible = 1", repr(sortie)


def _lien_ou_saut(lien: Path, cible: Path, dossier: bool = False) -> None:
    try:
        lien.symlink_to(cible, target_is_directory=dossier)
    except OSError as exc:
        # Sous Windows, créer un lien exige un privilège ou le mode développeur.
        if getattr(exc, "winerror", None) == 1314:
            pytest.skip("liens symboliques indisponibles sur ce poste Windows")
        raise


async def test_un_lien_vers_l_exterieur_du_depot_n_est_pas_suivi(tmp_path: Path):
    """Comme `grep -r` : un lien rencontré dans le dépôt n'est pas suivi."""
    dehors = tmp_path / "dehors"
    dehors.mkdir()
    (dehors / "secret.py").write_text("cible = 'hors du depot'\n", encoding="utf-8")
    depot = tmp_path / "depot"
    depot.mkdir()
    (depot / "ok.py").write_text("cible = 'dans le depot'\n", encoding="utf-8")
    _lien_ou_saut(depot / "lien.py", dehors / "secret.py")
    _lien_ou_saut(depot / "lien_dossier", dehors, dossier=True)
    sortie = await AgentToolExecutor(str(depot)).search_codebase("cible", "*.py")
    assert sortie == "ok.py:1:cible = 'dans le depot'", sortie


async def test_une_racine_designee_par_un_lien_est_parcourue(tmp_path: Path):
    """Le dépôt lui-même peut être un lien (B-961 : /var -> /private/var)."""
    reel = tmp_path / "reel"
    reel.mkdir()
    (reel / "a.py").write_text("cible = 1\n", encoding="utf-8")
    _lien_ou_saut(tmp_path / "lien", reel, dossier=True)
    sortie = await AgentToolExecutor(str(tmp_path / "lien")).search_codebase("cible", "*.py")
    assert sortie == "a.py:1:cible = 1", sortie


async def test_un_motif_pathologique_ne_bloque_pas_la_recherche(tmp_path: Path, monkeypatch):
    """Le module `re` de Python peut mouliner des minutes sur `(x+x+)+y`, et un
    fil d'exécution ne s'annule pas : la recherche est bornée dans le temps."""
    monkeypatch.setattr(module_outils, "DELAI_RECHERCHE_S", 0.5)
    (tmp_path / "a.py").write_text("a" * 60 + "!\n", encoding="utf-8")
    debut = time.monotonic()
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("(a|aa)+$", "*.py")
    assert sortie == "Erreur : timeout de recherche", sortie
    assert time.monotonic() - debut < 5, "la recherche n'a pas respecté son délai"
    for fil in _fils_de_recherche():
        fil.join(2)
    assert not any(fil.is_alive() for fil in _fils_de_recherche()), "le fil de recherche tourne encore"


def _fils_de_recherche() -> list[threading.Thread]:
    return [fil for fil in threading.enumerate() if fil.name == "recherche-agents"]


async def test_une_lecture_bloquee_ne_retient_ni_le_pool_ni_les_recherches_suivantes(tmp_path: Path, monkeypatch):
    """Revue Codex P1 : grep bloqué sur un lecteur réseau était tué ; un fil
    Python ne l'est pas. Il ne doit donc ni occuper le pool partagé de
    l'application (fil démon dédié) ni s'accumuler sans limite."""
    monkeypatch.setattr(module_outils, "DELAI_RECHERCHE_S", 0.3)
    monkeypatch.setattr(module_outils, "MAX_RECHERCHES_EN_VOL", 1)
    monkeypatch.setattr(module_outils, "_recherches_en_vol", {})
    debloquer = threading.Event()
    lire = module_outils._lire_octets
    fige = tmp_path / "partage-fige"
    sain = tmp_path / "depot-sain"
    for racine in (fige, sain):
        racine.mkdir()
        (racine / "a.py").write_text("cible = 1\n", encoding="utf-8")

    def lecture_bloquee(chemin: str, *args) -> bytes | None:
        if str(fige) in chemin:
            debloquer.wait(10)
        return lire(chemin, *args)

    monkeypatch.setattr(module_outils, "_lire_octets", lecture_bloquee)
    executeur = AgentToolExecutor(str(fige))
    try:
        debut = time.monotonic()
        assert await executeur.search_codebase("cible", "*.py") == "Erreur : timeout de recherche"
        assert time.monotonic() - debut < 5
        bloques = _fils_de_recherche()
        assert bloques and all(fil.daemon for fil in bloques), "un fil bloqué doit être un fil démon dédié"
        refus = await executeur.search_codebase("cible", "*.py")
        assert refus.startswith("Erreur") and "bloquée" in refus, refus
        # Seconde revue Codex P1 : le plafond vaut par dépôt, un autre reste cherchable.
        assert await AgentToolExecutor(str(sain)).search_codebase("cible", "*.py") == "a.py:1:cible = 1"
    finally:
        debloquer.set()
    for fil in bloques:
        fil.join(5)
    assert await executeur.search_codebase("cible", "*.py") == "a.py:1:cible = 1"


async def test_un_fichier_remplace_par_un_lien_pendant_la_recherche_n_est_pas_suivi(tmp_path: Path, monkeypatch):
    """Seconde revue Codex P2 : entre le contrôle du type et l'ouverture, un
    autre processus peut remplacer le fichier par un lien vers l'extérieur."""
    dehors = tmp_path / "dehors"
    dehors.mkdir()
    (dehors / "secret.py").write_text("cible = 'hors du depot'\n", encoding="utf-8")
    depot = tmp_path / "depot"
    (depot / "sous").mkdir(parents=True)
    (depot / "a.py").write_text("cible = 'original a'\n", encoding="utf-8")
    (depot / "sous" / "secret.py").write_text("cible = 'original b'\n", encoding="utf-8")
    lire = module_outils._lire_octets

    def remplacer_puis_lire(chemin: str, *args) -> bytes | None:
        cible = Path(chemin)
        if cible.name == "a.py":  # le fichier lui-même devient un lien
            cible.unlink()
            _lien_ou_saut(cible, dehors / "secret.py")
        elif cible.parent.name == "sous":  # son dossier devient un lien
            (depot / "sous" / "secret.py").unlink()
            (depot / "sous").rmdir()
            _lien_ou_saut(depot / "sous", dehors, dossier=True)
        return lire(chemin, *args)

    monkeypatch.setattr(module_outils, "_lire_octets", remplacer_puis_lire)
    sortie = await AgentToolExecutor(str(depot)).search_codebase("cible", "*.py")
    assert "hors du depot" not in sortie, sortie


async def test_un_fichier_qui_n_est_pas_du_texte_utf8_n_est_pas_lu(tmp_path: Path):
    """Revue Codex P2 : grep, en locale UTF-8, tient ce fichier pour binaire."""
    (tmp_path / "latin.py").write_bytes(b"\xffcible = 'illisible'\n")
    (tmp_path / "texte.py").write_text("cible = 'lisible'\n", encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("cible", "*.py")
    assert sortie == "texte.py:1:cible = 'lisible'", sortie


async def test_un_motif_invalide_dit_au_modele_comment_le_corriger(tmp_path: Path):
    """Revue Codex P2 : la syntaxe est celle de Python, plus celle de grep.
    `search_codebase(` passait avec grep ; il doit maintenant rendre une erreur
    qui dit quoi échapper, et le motif échappé doit trouver."""
    (tmp_path / "a.py").write_text("async def search_codebase(self):\n", encoding="utf-8")
    executeur = AgentToolExecutor(str(tmp_path))
    erreur = await executeur.search_codebase("search_codebase(", "*.py")
    assert erreur.startswith("Erreur : la recherche a échoué (motif invalide"), erreur
    assert "\\(" in erreur, erreur
    assert await executeur.search_codebase("search_codebase\\(", "*.py") == "a.py:1:async def search_codebase(self):"


async def test_un_dossier_absent_est_une_erreur_sans_chemin(tmp_path: Path):
    absent = tmp_path / "absent"
    sortie = await AgentToolExecutor(str(absent)).search_codebase("cible", "*.py")
    assert sortie.startswith("Erreur : la recherche a échoué"), sortie
    assert str(tmp_path) not in sortie, sortie


@pytest.mark.skipif(not hasattr(os, "O_NOFOLLOW"), reason="O_NOFOLLOW absent (Windows)")
def test_la_lecture_n_ouvre_jamais_un_lien_final(tmp_path: Path):
    """Seconde garde de la course ci-dessus, indépendante du contrôle d'inode."""
    (tmp_path / "secret.py").write_text("cible = 1\n", encoding="utf-8")
    _lien_ou_saut(tmp_path / "lien.py", tmp_path / "secret.py")
    with pytest.raises(OSError):
        module_outils._lire_octets(str(tmp_path / "lien.py"), 1024)


async def test_un_dossier_remplace_par_un_lien_avant_son_listage_n_est_pas_suivi(tmp_path: Path, monkeypatch):
    """Troisième revue Codex P2 : le dossier est contrôlé, empilé, puis remplacé
    par un lien avant d'être listé."""
    dehors = tmp_path / "dehors"
    dehors.mkdir()
    (dehors / "secret.py").write_text("cible = 'hors du depot'\n", encoding="utf-8")
    depot = tmp_path / "depot"
    (depot / "sous").mkdir(parents=True)
    (depot / "sous" / "b.py").write_text("cible = 'original'\n", encoding="utf-8")
    lister = os.scandir

    def remplacer_puis_lister(chemin):
        if isinstance(chemin, str) and Path(chemin).name == "sous" and not Path(chemin).is_symlink():
            (depot / "sous" / "b.py").unlink()
            (depot / "sous").rmdir()
            _lien_ou_saut(depot / "sous", dehors, dossier=True)
        return lister(chemin)

    monkeypatch.setattr(module_outils.os, "scandir", remplacer_puis_lister)
    sortie = await AgentToolExecutor(str(depot)).search_codebase("cible", "*.py")
    assert "hors du depot" not in sortie, sortie


def test_sans_inode_dans_le_listage_l_identite_vient_de_lstat(tmp_path: Path):
    """Troisième revue Codex P2 : sous Windows, DirEntry.stat laisse l'inode à
    zéro ; l'identité doit alors venir de os.lstat, sinon aucun contrôle."""
    fichier = tmp_path / "a.py"
    fichier.write_text("x = 1\n", encoding="utf-8")
    vrai = os.lstat(fichier)

    class EntreeWindows:
        path = str(fichier)

        def stat(self, follow_symlinks: bool = True):
            return os.stat_result((vrai.st_mode, 0, 0, 1, 0, 0, vrai.st_size, 0, 0, 0))

    assert module_outils._identite_entree(EntreeWindows()) == (vrai.st_dev, vrai.st_ino)
