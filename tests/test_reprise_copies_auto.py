"""Reprise de démarrage sur copies jetables, sans trousseau ni données réelles."""
import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient


def copie(profil):
    dossier = profil / 'backups/auto/20261027T080000Z-v0.81.1'
    dossier.mkdir(parents=True)
    with sqlite3.connect(dossier / 'therese.db') as db:
        db.execute('CREATE TABLE souvenir (texte TEXT)')
        db.execute("INSERT INTO souvenir VALUES ('retrouvé')")
    return dossier


def test_liste_date_version_et_exclut_liens_et_incompletes(tmp_path):
    from app.services.reprise_auto import lister_copies
    dossier = copie(tmp_path)
    (dossier.parent / '20261028T080000Z-v0.82').mkdir()
    (dossier.parent / '20261029T080000Z-v0.82').symlink_to(dossier, target_is_directory=True)
    assert lister_copies(tmp_path) == [{
        'id': dossier.name, 'date': '2026-10-27T08:00:00+00:00', 'version': '0.81.1',
    }]


def test_restauration_conserve_base_wal_shm_et_cle_avant_remplacement(tmp_path):
    from app.services.reprise_auto import restaurer_copie
    dossier = copie(tmp_path)
    anciens = {'therese.db': b'abimee', 'therese.db-wal': b'wal', 'therese.db-shm': b'shm', '.encryption_key': b'cle-factice'}
    for nom, contenu in anciens.items():
        (tmp_path / nom).write_bytes(contenu)
    abri = restaurer_copie(tmp_path, tmp_path / 'therese.db', dossier.name)
    for nom, contenu in anciens.items():
        assert (abri / nom).read_bytes() == contenu
    with sqlite3.connect(tmp_path / 'therese.db') as db:
        assert db.execute('SELECT texte FROM souvenir').fetchone() == ('retrouvé',)
    assert not (tmp_path / 'therese.db-wal').exists()
    assert not (tmp_path / 'therese.db-shm').exists()
    # Une copie sans clé garde la clé courante (trousseau seul possible).
    assert (tmp_path / '.encryption_key').read_bytes() == b'cle-factice'
    assert (dossier / 'therese.db').exists()


@pytest.mark.parametrize('identifiant', ['../therese.db', 'inconnue'])
def test_chemin_refuse_sans_toucher_la_base(tmp_path, identifiant):
    from app.services.reprise_auto import restaurer_copie
    (tmp_path / 'therese.db').write_bytes(b'originale')
    with pytest.raises(ValueError):
        restaurer_copie(tmp_path, tmp_path / 'therese.db', identifiant)
    assert (tmp_path / 'therese.db').read_bytes() == b'originale'


def test_copie_illisible_refusee_avant_mise_de_cote(tmp_path):
    from app.services.reprise_auto import restaurer_copie
    dossier = copie(tmp_path)
    (dossier / 'therese.db').write_bytes(b'illisible')
    (tmp_path / 'therese.db').write_bytes(b'originale')
    import sqlcipher3
    with pytest.raises(sqlcipher3.DatabaseError):
        restaurer_copie(tmp_path, tmp_path / 'therese.db', dossier.name)
    assert (tmp_path / 'therese.db').read_bytes() == b'originale'


@pytest.mark.parametrize('erreur', [sqlite3.DatabaseError('file is not a database'), RuntimeError('migration impossible')])
def test_demarrage_en_echec_sert_la_reprise_et_bloque_les_routes_metier(tmp_path, monkeypatch, erreur):
    import app.main as main
    dossier = copie(tmp_path)
    monkeypatch.setattr(main.settings, 'data_dir', tmp_path)
    monkeypatch.setattr(main.settings, 'db_path', tmp_path / 'therese.db')
    monkeypatch.setattr(main, 'init_db', AsyncMock(side_effect=erreur))
    monkeypatch.setattr(main.app.router, 'lifespan_context', main.lifespan)
    monkeypatch.setattr(main.app.state, 'session_token', None, raising=False)
    monkeypatch.setattr(main.app.state, 'reprise_donnees', None, raising=False)
    with TestClient(main.app) as client:
        assert client.get('/health').json()['status'] == 'recovery'
        assert client.get('/api/reprise/copies').status_code == 401
        headers = {'X-Therese-Token': main.app.state.session_token}
        assert client.get('/api/reprise/copies', headers=headers).json()['copies'][0]['id'] == dossier.name
        assert client.get('/api/config', headers=headers).status_code == 503
        assert client.post('/api/reprise/restaurer', headers=headers, json={'copie': dossier.name, 'confirmer': False}).status_code == 400
        response = client.post('/api/reprise/restaurer', headers=headers, json={'copie': dossier.name, 'confirmer': True})
        assert response.status_code == 200, response.text
        assert response.json()['redemarrage_requis'] is True
        # Ne pas rouvrir les routes avant le redémarrage effectif.
        assert client.get('/health').json()['status'] == 'recovery'


def test_interruption_apres_deplacement_garde_original_et_temoin(tmp_path, monkeypatch):
    from app.services import reprise_auto as reprise
    dossier = copie(tmp_path)
    (tmp_path / 'therese.db').write_bytes(b'originale')
    deplacer = reprise.shutil.move
    def panne(source, cible):
        if Path(source).parent.name == 'preparation':
            raise OSError('disque plein')
        return deplacer(source, cible)
    monkeypatch.setattr(reprise.shutil, 'move', panne)
    with pytest.raises(OSError):
        reprise.restaurer_copie(tmp_path, tmp_path / 'therese.db', dossier.name)
    assert (tmp_path / reprise.TEMOIN).exists()
    abri = Path((tmp_path / reprise.TEMOIN).read_text())
    assert (abri / 'therese.db').read_bytes() == b'originale'


def test_restaure_base_chiffree_et_son_wal_sans_modifier_la_copie(tmp_path):
    import sqlcipher3
    from app.services.reprise_auto import restaurer_copie
    dossier = tmp_path / 'backups/auto/20261027T080000Z-v0.81.1'
    dossier.mkdir(parents=True)
    # Clé déterministe du profil jetable de conftest, aucun trousseau.
    db = sqlcipher3.connect(dossier / 'therese.db')
    db.execute('PRAGMA key = "x\'' + 'ad' * 32 + '\'"')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE souvenir (texte TEXT)')
    db.execute("INSERT INTO souvenir VALUES ('dans le journal')")
    db.commit()
    wal = (dossier / 'therese.db-wal').read_bytes()
    try:
        restaurer_copie(tmp_path, tmp_path / 'therese.db', dossier.name)
        assert (dossier / 'therese.db-wal').read_bytes() == wal
        with sqlcipher3.connect(tmp_path / 'therese.db') as resultat:
            resultat.execute('PRAGMA key = "x\'' + 'ad' * 32 + '\'"')
            assert resultat.execute('SELECT texte FROM souvenir').fetchone() == ('dans le journal',)
    finally:
        db.close()


def test_effacement_explicite_emporte_aussi_les_bases_mises_de_cote(tmp_path):
    from app.services.copie_auto import purger_copies_auto
    from app.services.reprise_auto import restaurer_copie
    dossier = copie(tmp_path)
    (tmp_path / 'therese.db').write_bytes(b'ancienne')
    abri = restaurer_copie(tmp_path, tmp_path / 'therese.db', dossier.name)
    purger_copies_auto(tmp_path)
    assert not abri.exists()


def test_base_vide_valide_peut_etre_initialisee_mais_pas_restauree(tmp_path):
    from app.services.reprise_auto import verifier_base
    base = tmp_path / 'therese.db'
    with sqlite3.connect(base) as connexion:
        connexion.execute('VACUUM')
    # Arrêt juste après création du fichier : ce n'est pas une corruption.
    verifier_base(base)
    with pytest.raises(ValueError, match='aucune table'):
        verifier_base(base, exiger_tables=True)
