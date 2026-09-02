"""B-023 — le cache de clés API était à sens unique.

02/09/2026. `_get_api_key_from_db` (llm.py:145) rendait le contenu du cache dès
que `_api_key_cache_loaded` valait `True`, et ne relisait JAMAIS la base. Le
bloc « Fallback: direct DB read » qui suit était inatteignable dans ce cas,
contrairement à ce que dit son propre commentaire (« Ce fallback est rarement
appelé »).

Les deux seules invalidations vivent dans `POST /api-key` et `DELETE /api-key`
(config.py:334, :392). `restore_backup` remplace pourtant la base ENTIÈRE,
table `preferences` comprise, sans jamais invalider : une clé arrivée par une
sauvegarde restaurée restait invisible.

Deux fermetures, l'une générale, l'autre ciblée :
- lecture traversante sur défaut de cache (la base redevient la référence) ;
- invalidation explicite après une restauration.

Reste hors d'atteinte, et dit tel quel : une clé SUPPRIMÉE en base après le
chargement continue d'être servie par le cache. La lecture traversante ne se
déclenche que sur un défaut, pas sur une valeur présente.
"""

from __future__ import annotations

from contextlib import contextmanager


def _connexion_qui_rend(valeur, compteur=None):
    @contextmanager
    def _fausse_connexion():
        class _Resultat:
            def fetchone(self):
                if compteur is not None:
                    compteur.append(1)
                return (valeur,) if valeur is not None else None

        class _Connexion:
            def execute(self, *_a, **_k):
                return _Resultat()

        yield _Connexion()

    return _fausse_connexion


def test_une_cle_ecrite_hors_route_api_key_est_relue(monkeypatch):
    """Le défaut reproduit : la base a la clé, le cache dit non, le cache gagne."""
    from app.models import database as db
    from app.services import llm

    monkeypatch.setattr(
        db, "get_sync_connection", _connexion_qui_rend("CLE-ARRIVEE-APRES-LE-CHARGEMENT")
    )
    monkeypatch.setattr(llm, "_api_key_cache", {}, raising=False)
    monkeypatch.setattr(llm, "_api_key_cache_loaded", True, raising=False)

    assert llm._get_api_key_from_db("openai") == "CLE-ARRIVEE-APRES-LE-CHARGEMENT", (
        "la base n'est jamais relue une fois le cache chargé : une clé écrite "
        "par un autre chemin (restauration de sauvegarde) reste invisible"
    )


def test_une_cle_deja_en_cache_ne_declenche_aucune_lecture(monkeypatch):
    """Verrou : le cache reste un cache, on ne va pas en base à chaque appel."""
    from app.models import database as db
    from app.services import llm

    lectures: list[int] = []
    monkeypatch.setattr(
        db, "get_sync_connection", _connexion_qui_rend("PAS-CELLE-LA", lectures)
    )
    monkeypatch.setattr(
        llm, "_api_key_cache", {"openai_api_key": "CLE-EN-CACHE"}, raising=False
    )
    monkeypatch.setattr(llm, "_api_key_cache_loaded", True, raising=False)

    assert llm._get_api_key_from_db("openai") == "CLE-EN-CACHE"
    assert lectures == [], f"lecture inutile en base : {len(lectures)} appel(s)"


def test_une_absence_reelle_reste_une_absence(monkeypatch):
    """Verrou : pas de clé en base, pas de clé rendue - et pas de plantage."""
    from app.models import database as db
    from app.services import llm

    monkeypatch.setattr(db, "get_sync_connection", _connexion_qui_rend(None))
    monkeypatch.setattr(llm, "_api_key_cache", {}, raising=False)
    monkeypatch.setattr(llm, "_api_key_cache_loaded", True, raising=False)

    assert llm._get_api_key_from_db("mistral") is None


def test_une_cle_relue_alimente_le_cache(monkeypatch):
    """La lecture traversante ne doit pas devenir une lecture PERMANENTE."""
    from app.models import database as db
    from app.services import llm

    lectures: list[int] = []
    monkeypatch.setattr(
        db, "get_sync_connection", _connexion_qui_rend("CLE-RELUE", lectures)
    )
    monkeypatch.setattr(llm, "_api_key_cache", {}, raising=False)
    monkeypatch.setattr(llm, "_api_key_cache_loaded", True, raising=False)

    assert llm._get_api_key_from_db("grok") == "CLE-RELUE"
    assert llm._get_api_key_from_db("grok") == "CLE-RELUE"
    assert len(lectures) == 1, (
        f"la clé relue n'est pas mémorisée : {len(lectures)} lectures en base"
    )


def test_la_restauration_invalide_le_cache_des_cles():
    """`restore_backup` remplace la table `preferences` : le cache est périmé.

    Garde au niveau de la SOURCE de la fonction, faute de pouvoir dérouler une
    restauration complète en test (archive, purge disque, remplacement de la
    base). Le précédent existe : `tests/test_pluriel_fournisseur.py`.
    """
    import inspect
    import re

    from app.routers import data as routeur

    corps = inspect.getsource(routeur.restore_backup)
    # L'APPEL, pas la simple mention : la ligne d'import contient déjà le nom,
    # et un test qui la lit ne détecte pas le retrait de l'appel (constaté au
    # sabotage de ce lot).
    appels = re.findall(r"(?<![\w.])invalidate_api_key_cache\s*\(\s*\)", corps)
    assert appels, (
        "restore_backup remplace la base entière sans APPELER "
        "invalidate_api_key_cache() : les clés de la sauvegarde restaurée "
        "restent invisibles"
    )
