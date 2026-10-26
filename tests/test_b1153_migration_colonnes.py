"""B-1153 : conserver les colonnes enrichies et différer sans bloquer le démarrage."""
import logging
from contextlib import closing

import pytest
from app.models.activity_migration import migrer_activites

from tests.test_activity_migration import COLONNES, activite, connecter, etat, lire, preparer


@pytest.mark.parametrize("pilote", ["sqlite", "sqlcipher"])
@pytest.mark.parametrize("schema", ["ancien", "minimal"])
def test_reconstruction_ne_perd_pas_de_colonne(tmp_path, caplog, pilote, schema):
    with closing(connecter(tmp_path / "activites.db", pilote)) as conn:
        preparer(conn, schema, [activite()], 1)
        conn.execute("ALTER TABLE activities ADD COLUMN origine_archive TEXT")
        conn.execute("UPDATE activities SET origine_archive='archive-locale-42'")
        conn.commit()
        avant = lire(conn)
        migrer_activites(conn)
        assert [{n: ligne[n] for n in avant[0]} for ligne in lire(conn)] == avant
        infos = {r[1]: r for r in conn.execute('PRAGMA table_xinfo(activities)')}
        assert set(COLONNES) <= infos.keys()
        assert infos['contact_id'][3] == 0
        assert "archive-locale-42" not in caplog.text
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert not conn.in_transaction


# Dix entrées inventées après le correctif, dont les colonnes générées.
@pytest.mark.parametrize("schema,definitions,valeurs", [
    ("ancien", {"annotation": "TEXT"}, {"annotation": "archivé à Lyon"}),
    ("minimal", {"revision": "INTEGER"}, {"revision": 42}),
    ("partiel", {"poids": "REAL"}, {"poids": 12.75}),
    ("ancien", {"empreinte": "BLOB"}, {"empreinte": b"\x00\xff\x42"}),
    ("minimal", {"option": "TEXT"}, {"option": None}),
    ("ancien", {'note "locale"': "TEXT"}, {'note "locale"': "citation"}),
    ("partiel", {"source": "TEXT", "revision": "INTEGER"}, {"source": "papier", "revision": 3}),
    ("ancien", {"priorite": "INTEGER NOT NULL DEFAULT 7 CHECK (priorite > 0)"}, {}),
    ("minimal", {"titre_calcule": "TEXT GENERATED ALWAYS AS (lower(title)) VIRTUAL"}, {}),
    ("ancien", {"taille_titre": "INTEGER GENERATED ALWAYS AS (length(title)) STORED"}, {}),
])
def test_rejeu_astra_colonnes(tmp_path, caplog, schema, definitions, valeurs):
    with closing(connecter(tmp_path / "rejeu.db", "sqlite")) as conn:
        preparer(conn, schema, [activite()], 1)
        for nom, definition in definitions.items():
            identifiant = '"' + nom.replace('"', '""') + '"'
            if "STORED" in definition:
                # SQLite n'ajoute une colonne STORED que sur une table vide.
                conn.execute("DELETE FROM activities")
            conn.execute(f"ALTER TABLE activities ADD COLUMN {identifiant} {definition}")
            if nom in valeurs:
                conn.execute(f"UPDATE activities SET {identifiant}=?", (valeurs[nom],))
        if any("STORED" in d for d in definitions.values()):
            conn.execute("INSERT INTO activities (id, contact_id, type, title, created_at) "
                         "VALUES ('a1', 'contact-valide', 'note', 'Titre généré', '2026-01-01')")
        conn.commit()
        avant = lire(conn)
        migrer_activites(conn)
        assert [{n: ligne[n] for n in avant[0]} for ligne in lire(conn)] == avant
        assert all(definition in conn.execute("SELECT sql FROM sqlite_master WHERE name='activities'").fetchone()[0]
                   for definition in definitions.values())
        apres = etat(conn)
        migrer_activites(conn)
        assert etat(conn) == apres
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert not conn.in_transaction


@pytest.mark.parametrize("pilote", ["sqlite", "sqlcipher"])
@pytest.mark.parametrize("mode", ["lecture-seule", "verrou"])
def test_table_saine_avec_colonne_en_plus_ne_demande_pas_de_verrou(tmp_path, pilote, mode):
    chemin = tmp_path / "saine.db"
    with closing(connecter(chemin, pilote)) as conn, closing(connecter(chemin, pilote)) as autre:
        preparer(conn, "migre", [activite()], 1)
        conn.execute("ALTER TABLE activities ADD COLUMN provenance TEXT DEFAULT 'archive'")
        conn.commit()
        avant = etat(conn)
        if mode == "lecture-seule":
            conn.execute("PRAGMA query_only=ON")
        else:
            autre.execute("BEGIN IMMEDIATE")
            conn.execute("PRAGMA busy_timeout=0")
        requetes = []
        conn.set_trace_callback(requetes.append)
        migrer_activites(conn)
        assert etat(conn) == avant
        assert not any(sql.startswith(("BEGIN", "COMMIT", "UPDATE", "INSERT", "DELETE", "CREATE", "DROP")) for sql in requetes)
        assert not conn.in_transaction


def test_refus_ne_commite_pas_la_transaction_appelante(tmp_path, caplog):
    with closing(connecter(tmp_path / "transaction.db", "sqlite")) as conn:
        preparer(conn, "ancien", [activite()], 1)
        conn.execute("ALTER TABLE activities ADD COLUMN origine TEXT DEFAULT 'avant'")
        conn.commit()
        conn.execute("UPDATE activities SET origine='en cours'")
        assert conn.in_transaction
        with caplog.at_level(logging.WARNING, logger="app.models.activity_migration"):
            migrer_activites(conn)
        assert 'Migration sautée' in caplog.text
        assert conn.in_transaction
        conn.rollback()
        assert conn.execute("SELECT origine FROM activities").fetchone()[0] == "avant"
