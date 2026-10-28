"""Reprise hors base : uniquement au démarrage, avant les services métier.

La copie choisie est vérifiée dans un dossier de préparation. Les originaux
sont ensuite déplacés dans un abri unique, jamais écrasés ni élagués. Un témoin
empêche toute ouverture normale après une interruption entre deux déplacements.
"""
from __future__ import annotations

import os
import shutil
import sqlite3
from pathlib import Path
from uuid import uuid4

from app.services.copie_auto import _copies_existantes, dossier_copies

TEMOIN = '.reprise-en-cours'


def lister_copies(profil: Path) -> list[dict[str, str]]:
    auto = dossier_copies(profil)
    if auto.is_symlink() or auto.parent.is_symlink():
        return []
    return [
        {'id': dossier.name, 'date': date.isoformat(), 'version': version}
        for date, version, dossier in reversed(_copies_existantes(auto))
        if not dossier.is_symlink()
        and (dossier / 'therese.db').is_file()
        and not any(p.is_symlink() for p in dossier.iterdir())
    ]


def verifier_base(base: Path, cle: Path | None = None, *, exiger_tables: bool = False) -> None:
    """Contrôle sans migration, compatible avec le journal WAL copié."""
    from app.models.database import db_is_encrypted
    from app.services.encryption import derive_db_key_from_master, get_db_key_hex

    module = sqlite3
    chiffree = db_is_encrypted(base)
    if chiffree:
        import sqlcipher3
        module = sqlcipher3
    connexion = module.connect(f'{base.as_uri()}?mode=ro', uri=True)
    try:
        if chiffree:
            key = derive_db_key_from_master(cle.read_bytes()) if cle and cle.is_file() else get_db_key_hex()
            connexion.execute(f'''PRAGMA key = "x'{key}'"''')
        connexion.execute('PRAGMA query_only=ON')
        if connexion.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
            raise ValueError('Le contrôle de la base a échoué.')
        if exiger_tables and not connexion.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchone():
            raise ValueError('La copie ne contient aucune table.')
    finally:
        connexion.close()


def restaurer_copie(profil: Path, base: Path, identifiant: str) -> Path:
    if identifiant not in {c['id'] for c in lister_copies(profil)}:
        raise ValueError('Cette copie automatique est introuvable.')
    source = dossier_copies(profil) / identifiant
    racine = profil / 'backups' / 'reprises'
    if racine.is_symlink():
        raise ValueError('Le dossier de reprise doit être un dossier local.')
    racine.mkdir(parents=True, exist_ok=True, mode=0o700)
    travail = racine / uuid4().hex
    travail.mkdir(mode=0o700)
    preparation = travail / 'preparation'
    preparation.mkdir(mode=0o700)
    abri = travail / 'avant-restauration'
    abri.mkdir(mode=0o700)
    # Noms fixes, jamais de chemin fourni par le client.
    for nom in ('therese.db', 'therese.db-wal', '.encryption_key'):
        fichier = source / nom
        if fichier.is_file():
            shutil.copy2(fichier, preparation / nom)
            os.chmod(preparation / nom, 0o600)
    verifier_base(preparation / 'therese.db', preparation / '.encryption_key', exiger_tables=True)
    # La clé courante reste nécessaire aux copies sans fichier de clé.
    cle = profil / '.encryption_key'
    if not (preparation / '.encryption_key').exists() and cle.is_file():
        shutil.copy2(cle, preparation / '.encryption_key')
        os.chmod(preparation / '.encryption_key', 0o600)
    # Si la préparation manque de place ou est illisible, aucun original n'a bougé.
    (profil / TEMOIN).write_text(str(abri), encoding='utf-8')
    os.chmod(profil / TEMOIN, 0o600)
    for chemin, nom in [
        (base, 'therese.db'),
        (Path(str(base) + '-wal'), 'therese.db-wal'),
        (Path(str(base) + '-shm'), 'therese.db-shm'),
        (Path(str(base) + '-journal'), 'therese.db-journal'),
        (cle, '.encryption_key'),
    ]:
        if chemin.exists() or chemin.is_symlink():
            # Le chemin personnalisé de la base peut être sur un autre disque.
            shutil.move(str(chemin), str(abri / nom))
    for nom, destination in [
        ('therese.db', base), ('therese.db-wal', Path(str(base) + '-wal')),
        ('.encryption_key', cle),
    ]:
        fichier = preparation / nom
        if fichier.exists():
            shutil.move(str(fichier), str(destination))
    # Le témoin et l'abri restent conservés, mais ne bloquent plus le démarrage.
    (profil / TEMOIN).rename(travail / 'restauration-terminee')
    return abri
