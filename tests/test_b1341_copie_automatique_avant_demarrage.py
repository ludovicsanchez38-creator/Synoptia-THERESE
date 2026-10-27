"""B-1341 : une copie automatique de la base précède chaque nouvelle version.

Audit bêta du 27/10/2026 (A6) : init_db réécrit des données à chaque
démarrage (réparations idempotentes, migrations d'une nouvelle version) sans
aucune copie préalable, et la seule sauvegarde est un clic manuel avec phrase
de passe. Un défaut de migration ou une base abîmée n'avait aucun recours.

Règle posée : avant que le moteur ouvre la base, une copie de therese.db, de
son journal WAL et de .encryption_key part dans backups/auto/, quand la
version change ou que la dernière copie a plus d'un jour ; trois copies
conservées ; jamais d'exception qui empêcherait le démarrage ; « Effacer
toutes mes données » les emporte.
"""
import ast
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


@pytest.fixture
def profil(tmp_path):
    return tmp_path


def _base(dossier: Path, wal: bool = True):
    (dossier / "therese.db").write_bytes(b"base-chiffree" * 100)
    if wal:
        (dossier / "therese.db-wal").write_bytes(b"journal" * 10)
    (dossier / ".encryption_key").write_bytes(b"cle-maitresse")


def _copies(dossier: Path) -> list[Path]:
    auto = dossier / "backups" / "auto"
    return sorted(p for p in auto.iterdir() if p.is_dir()) if auto.exists() else []


def _copier(dossier, version="0.81.2", maintenant=None):
    from app.services.copie_auto import copier_avant_demarrage

    return copier_avant_demarrage(dossier, version, maintenant=maintenant)


def test_premier_lancement_sans_base_aucune_copie(profil):
    assert _copier(profil) is None
    assert _copies(profil) == []


def test_une_base_existante_est_copiee_avec_son_journal_et_sa_cle(profil):
    _base(profil)

    copie = _copier(profil)

    assert copie is not None and copie.parent == profil / "backups" / "auto"
    assert (copie / "therese.db").read_bytes() == (profil / "therese.db").read_bytes()
    assert (copie / "therese.db-wal").read_bytes() == (profil / "therese.db-wal").read_bytes()
    assert (copie / ".encryption_key").read_bytes() == b"cle-maitresse"
    if os.name != "nt":
        assert (copie.stat().st_mode & 0o777) == 0o700
        assert all((f.stat().st_mode & 0o777) == 0o600 for f in copie.iterdir())


def test_meme_version_le_meme_jour_pas_de_seconde_copie(profil):
    _base(profil)
    t0 = datetime(2026, 10, 27, 8, 0, tzinfo=UTC)

    assert _copier(profil, maintenant=t0)
    assert _copier(profil, maintenant=t0 + timedelta(hours=5)) is None
    assert len(_copies(profil)) == 1


def test_une_nouvelle_version_copie_meme_dans_la_journee(profil):
    _base(profil)
    t0 = datetime(2026, 10, 27, 8, 0, tzinfo=UTC)

    _copier(profil, "0.81.1", maintenant=t0)
    copie = _copier(profil, "0.81.2", maintenant=t0 + timedelta(minutes=10))

    assert copie is not None and copie.name.endswith("-v0.81.2")
    assert len(_copies(profil)) == 2


def test_au_dela_d_un_jour_la_meme_version_copie_de_nouveau(profil):
    _base(profil)
    t0 = datetime(2026, 10, 27, 8, 0, tzinfo=UTC)

    _copier(profil, maintenant=t0)

    assert _copier(profil, maintenant=t0 + timedelta(hours=25)) is not None


def test_trois_copies_conservees_les_plus_recentes(profil):
    _base(profil)
    t0 = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
    for jour in range(5):
        _copier(profil, f"0.8{jour}.0", maintenant=t0 + timedelta(days=jour))

    noms = [p.name for p in _copies(profil)]
    assert len(noms) == 3
    assert [n.rsplit("-v", 1)[1] for n in noms] == ["0.82.0", "0.83.0", "0.84.0"]


def test_place_insuffisante_aucune_copie_et_aucune_exception(profil, monkeypatch):
    import shutil

    from app.services import copie_auto

    _base(profil)
    monkeypatch.setattr(copie_auto.shutil, "disk_usage", lambda _p: shutil._ntuple_diskusage(10, 10, 5))

    assert _copier(profil) is None
    assert _copies(profil) == []


def test_une_erreur_de_copie_n_empeche_pas_le_demarrage_et_ne_laisse_rien(profil, monkeypatch):
    from app.services import copie_auto

    _base(profil)

    def panne(*_a, **_k):
        raise OSError("disque plein")

    monkeypatch.setattr(copie_auto.shutil, "copy2", panne)

    assert _copier(profil) is None
    assert _copies(profil) == [], "une copie à moitié écrite ne doit pas passer pour une copie"


def test_une_copie_sans_cle_reste_utile(profil):
    """Profil sans fichier de clé (trousseau seul) : la base est copiée quand même."""
    _base(profil)
    (profil / ".encryption_key").unlink()

    copie = _copier(profil)

    assert copie is not None and (copie / "therese.db").exists()
    assert not (copie / ".encryption_key").exists()


def test_les_dossiers_etrangers_dans_auto_ne_sont_ni_comptes_ni_effaces(profil):
    _base(profil)
    auto = profil / "backups" / "auto"
    auto.mkdir(parents=True)
    (auto / "notes-perso").mkdir()
    t0 = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
    for jour in range(4):
        _copier(profil, f"0.8{jour}.0", maintenant=t0 + timedelta(days=jour))

    assert (auto / "notes-perso").exists()
    assert len([p for p in auto.iterdir() if p.name != "notes-perso"]) == 3


def test_effacer_toutes_mes_donnees_emporte_les_copies_automatiques(profil):
    from app.services.copie_auto import purger_copies_auto

    _base(profil)
    _copier(profil)

    purger_copies_auto(profil)

    assert _copies(profil) == []


def test_la_route_effacer_tout_appelle_la_purge_des_copies():
    source = Path(__file__).resolve().parents[1] / "src/backend/app/routers/data.py"
    arbre = ast.parse(source.read_text(encoding="utf-8"))
    fonction = next(
        n for n in ast.walk(arbre) if isinstance(n, ast.AsyncFunctionDef) and n.name == "_supprimer_toutes_les_donnees"
    )
    appels = {
        n.func.id if isinstance(n.func, ast.Name) else getattr(n.func, "attr", "")
        for n in ast.walk(fonction)
        if isinstance(n, ast.Call)
    }
    assert "purger_copies_auto" in appels


def test_le_demarrage_copie_avant_d_ouvrir_la_base():
    source = Path(__file__).resolve().parents[1] / "src/backend/app/main.py"
    arbre = ast.parse(source.read_text(encoding="utf-8"))
    fonction = next(n for n in ast.walk(arbre) if isinstance(n, ast.AsyncFunctionDef) and n.name == "lifespan")
    lignes: dict[str, int] = {}
    for n in ast.walk(fonction):
        if isinstance(n, ast.Name) and n.id in {"init_db", "copier_avant_demarrage"}:
            lignes.setdefault(n.id, n.lineno)
    assert "copier_avant_demarrage" in lignes, "le démarrage doit appeler la copie automatique"
    assert lignes["copier_avant_demarrage"] < lignes["init_db"], "la copie doit précéder l'ouverture de la base"
