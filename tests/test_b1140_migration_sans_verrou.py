"""B-1140 : une migration sans travail ne demande aucun verrou d'écriture."""
from contextlib import closing

import pytest
from app.models.activity_migration import migrer_activites

from tests.test_activity_migration import activite, connecter, etat, preparer


def verifier_sans_ecriture(tmp_path, pilote, mode, lignes, tables_absentes=()):
    chemin = tmp_path / "deja-migree.db"
    with closing(connecter(chemin, pilote)) as conn, closing(connecter(chemin, pilote)) as autre:
        preparer(conn, "migre", lignes, 1, tables_absentes=tables_absentes)
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
        assert not any(sql.startswith(("BEGIN", "UPDATE", "INSERT", "DELETE", "CREATE", "DROP")) for sql in requetes)
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert not conn.in_transaction


@pytest.mark.parametrize("pilote", ["sqlite", "sqlcipher"])
@pytest.mark.parametrize("mode", ["lecture-seule", "verrou"])
def test_table_deja_migree_reste_en_lecture(tmp_path, pilote, mode):
    verifier_sans_ecriture(tmp_path, pilote, mode, [activite()])


# Entrées inventées après le correctif, y compris les tables absentes de B-1089.
@pytest.mark.parametrize("lignes,absentes", [
    ([], ()),
    ([activite("k1", statut="annulee")], ()),
    ([activite("k2", contact_id=None)], ()),
    ([activite("k3", project_id=None)], ()),
    ([activite("k4", conversation_id=None)], ()),
    ([activite("k5", remplace_id="k5")], ()),
    ([activite("k6", remplace_id="k7"), activite("k7", remplace_id="k6")], ()),
    ([activite("k8", project_id="projet-en-attente")], ("projects",)),
    ([activite("k9", contact_id="contact-en-attente")], ("contacts",)),
    ([activite("k10", conversation_id="conversation-en-attente")], ("conversations",)),
])
def test_rejeu_apres_correctif(tmp_path, lignes, absentes):
    verifier_sans_ecriture(tmp_path, "sqlite", "lecture-seule", lignes, absentes)
