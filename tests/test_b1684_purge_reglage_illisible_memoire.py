"""B-1684 : le réglage illisible n'autorise pas une purge automatique.

Tests des deux fonctions produit extraites intégralement par AST. Pas d'import
de l'application, de moteur SQL, de profil, de réseau ou de purge réelle. La
lecture de préférence est simulée ; un témoin arrête le chemin positif AVANT
la lecture des contacts. Cela ne qualifie pas le scénario DB ou l'UI.
"""
from __future__ import annotations

import ast
import builtins
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

SOURCE = Path(__file__).resolve().parents[1] / "src/backend/app/services/rgpd_auto.py"


class SuiteAtteinte(Exception):
    """Témoin mémoire : le garde a laissé continuer, sans traitement réel."""


class ChampPreference:
    def __eq__(self, value: object) -> tuple[str, object]:
        return ("key", value)


class RequetePreference:
    def __init__(self) -> None:
        self.predicat: tuple[str, object] | None = None

    def where(self, predicat: tuple[str, object]) -> RequetePreference:
        self.predicat = predicat
        return self


class ContextePreference:
    def __init__(self, *, valeur: object = "true", presente: bool = True,
                 erreur: str | None = None, exception: BaseException | None = None) -> None:
        self.pref = SimpleNamespace(value=valeur) if presente else None
        self.erreur = erreur
        self.exception = exception if exception is not None else RuntimeError("panne simulée")
        self.etapes: list[str] = []
        self.factory = Mock(side_effect=self._factory)

    def _verifier(self, etape: str) -> None:
        self.etapes.append(etape)
        if self.erreur == etape:
            raise self.exception

    def _factory(self) -> ContextePreference:
        self._verifier("construction")
        return self

    async def __aenter__(self) -> ContextePreference:
        self._verifier("entree")
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        self._verifier("sortie")
        return False

    async def execute(self, requete: RequetePreference) -> ContextePreference:
        assert requete.predicat == ("key", "rgpd_purge_enabled"), requete.predicat
        self._verifier("requete")
        return self

    def scalar_one_or_none(self) -> SimpleNamespace | None:
        self._verifier("resultat")
        return self.pref


def fonctions_reelles(contexte: ContextePreference) -> tuple[dict[str, object], Mock, AsyncMock]:
    """Compile deux fonctions intactes ; seul l'import de Preference est simulé."""
    arbre = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    noms = {"_is_purge_enabled", "auto_purge_expired_contacts"}
    fonctions = [n for n in arbre.body if isinstance(n, ast.AsyncFunctionDef) and n.name in noms]
    assert {n.name for n in fonctions} == noms
    assert all(not n.decorator_list for n in fonctions)

    preference = type("Preference", (), {"key": ChampPreference()})

    def importer(name: str, globals: object = None, locals: object = None,
                 fromlist: tuple[str, ...] = (), level: int = 0) -> SimpleNamespace:
        if name != "app.models.entities" or tuple(fromlist) != ("Preference",) or level != 0:
            raise AssertionError(f"Import hors périmètre mémoire : {name}, {fromlist}, {level}")
        return SimpleNamespace(Preference=preference)

    def selectionner(modele: object) -> RequetePreference:
        assert modele is preference
        return RequetePreference()

    builtin_isoles = dict(vars(builtins))
    builtin_isoles["__import__"] = importer
    logger = Mock()
    suite = AsyncMock(side_effect=SuiteAtteinte("Le garde a laissé poursuivre la campagne"))
    espace: dict[str, object] = {
        "__builtins__": builtin_isoles,
        "get_session_context": contexte.factory,
        "select": selectionner,
        "logger": logger,
        "_get_purge_retention_months": suite,
    }
    module = ast.Module(body=fonctions, type_ignores=[])
    exec(compile(module, str(SOURCE), "exec"), espace)
    return espace, logger, suite


class TestReglagePurgeMemoire(unittest.IsolatedAsyncioTestCase):
    async def verifier_fermeture(self, erreur: str) -> None:
        # La préférence synthétique est "true" : chaque panne doit fermer,
        # même si une valeur activée avait été lue avant l'échec de sortie.
        contexte = ContextePreference(erreur=erreur)
        espace, _logger, suite = fonctions_reelles(contexte)
        self.assertFalse(await espace["_is_purge_enabled"]())
        self.assertIn(erreur, contexte.etapes)
        suite.assert_not_awaited()

    async def test_panne_construction_ferme(self) -> None:
        await self.verifier_fermeture("construction")

    async def test_panne_entree_ferme(self) -> None:
        await self.verifier_fermeture("entree")

    async def test_panne_requete_ferme(self) -> None:
        await self.verifier_fermeture("requete")

    async def test_panne_resultat_ferme(self) -> None:
        await self.verifier_fermeture("resultat")

    async def test_panne_sortie_ferme_meme_apres_valeur_true(self) -> None:
        await self.verifier_fermeture("sortie")

    async def test_preference_absente_garde_le_defaut_active(self) -> None:
        contexte = ContextePreference(presente=False)
        espace, _logger, suite = fonctions_reelles(contexte)
        self.assertTrue(await espace["_is_purge_enabled"]())
        self.assertEqual(contexte.etapes, ["construction", "entree", "requete", "resultat", "sortie"])
        suite.assert_not_awaited()

    async def test_valeur_vide_garde_le_defaut_active(self) -> None:
        for valeur in ("", None):
            with self.subTest(valeur=valeur):
                espace, _logger, _suite = fonctions_reelles(ContextePreference(valeur=valeur))
                self.assertTrue(await espace["_is_purge_enabled"]())

    async def test_valeurs_explicitement_activees(self) -> None:
        for valeur in ("true", "TRUE", "1", "yes", "YES"):
            with self.subTest(valeur=valeur):
                espace, _logger, _suite = fonctions_reelles(ContextePreference(valeur=valeur))
                self.assertTrue(await espace["_is_purge_enabled"]())

    async def test_valeurs_explicitement_desactivees(self) -> None:
        for valeur in ("false", "0", "no", "FALSE", "inconnue"):
            with self.subTest(valeur=valeur):
                espace, _logger, _suite = fonctions_reelles(ContextePreference(valeur=valeur))
                self.assertFalse(await espace["_is_purge_enabled"]())

    async def test_valeur_illisible_ferme(self) -> None:
        espace, _logger, _suite = fonctions_reelles(ContextePreference(valeur=123))
        self.assertFalse(await espace["_is_purge_enabled"]())

    async def test_panne_arrete_la_campagne_avant_toute_suite(self) -> None:
        for erreur in ("construction", "entree", "requete", "resultat", "sortie"):
            with self.subTest(erreur=erreur):
                contexte = ContextePreference(erreur=erreur)
                espace, _logger, suite = fonctions_reelles(contexte)
                try:
                    resultat = await espace["auto_purge_expired_contacts"]()
                except SuiteAtteinte as exc:
                    self.fail(str(exc))
                self.assertEqual(resultat, {"notifications": 0, "anonymisations": 0})
                self.assertEqual(contexte.factory.call_count, 1)
                suite.assert_not_awaited()

    async def test_desactivation_arrete_la_campagne(self) -> None:
        espace, _logger, suite = fonctions_reelles(ContextePreference(valeur="false"))
        self.assertEqual(await espace["auto_purge_expired_contacts"](),
                         {"notifications": 0, "anonymisations": 0})
        suite.assert_not_awaited()

    async def test_temoin_positif_le_chemin_active_atteint_la_suite(self) -> None:
        espace, _logger, suite = fonctions_reelles(ContextePreference(valeur="true"))
        with self.assertRaises(SuiteAtteinte):
            await espace["auto_purge_expired_contacts"]()
        suite.assert_awaited_once()

    async def test_annulation_n_est_pas_convertie_en_activation(self) -> None:
        import asyncio

        annulation = asyncio.CancelledError("annulation synthétique")
        espace, _logger, suite = fonctions_reelles(
            ContextePreference(erreur="requete", exception=annulation))
        with self.assertRaises(asyncio.CancelledError) as caught:
            await espace["auto_purge_expired_contacts"]()
        self.assertIs(caught.exception, annulation)
        suite.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
