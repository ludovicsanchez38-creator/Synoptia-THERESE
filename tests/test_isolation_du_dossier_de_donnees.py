"""
`THERESE_DATA_DIR` isole VRAIMENT, journaux et consignes compris.

Démontré en conditions réelles pendant la campagne dix personas : chaque
persona tournait sur une installation jetable, et pourtant trois PDF sont
apparus dans l'installation RÉELLE (`~/.therese/invoices/`). Ces trois-là ont
été corrigés ; deux chemins sont restés.

- `core/logging_config.py` écrit dans `~/.therese/logs`, avec les arguments
  COMPLETS des outils - donc des noms de contacts, des objets de mails, des
  montants.
- `services/llm.py` lit `~/.therese/THERESE.md`, les consignes de
  personnalisation de l'utilisateur réel.

C'était O1, classé dans le chantier « fondations », jamais livré. Le lot A de
la 0.54 a corrigé ce que l'écran AFFIRMAIT sur l'isolation ; celui-ci corrige
ce que l'application FAIT.

Ces tests exercent le vrai code, avec un dossier de données déplacé, et
vérifient qu'aucun des deux chemins ne pointe vers le dossier de l'utilisateur.
"""

from pathlib import Path

import pytest


@pytest.fixture
def dossier_isole(tmp_path, monkeypatch):
    """Un dossier de données jetable, posé comme le ferait un testeur."""
    dossier = tmp_path / "installation-jetable"
    dossier.mkdir()
    monkeypatch.setenv("THERESE_DATA_DIR", str(dossier))

    from app.config import Settings

    reglages = Settings()
    import app.config as module_config

    monkeypatch.setattr(module_config, "settings", reglages)
    return dossier


class TestLesJournauxSuiventLeDossierDeDonnees:
    def test_le_dossier_de_journaux_est_dans_l_installation_jetable(self, dossier_isole):
        from app.core.logging_config import dossier_des_journaux

        obtenu = dossier_des_journaux()

        assert dossier_isole in obtenu.parents or obtenu.parent == dossier_isole, (
            f"journaux écrits dans {obtenu}, hors de {dossier_isole}"
        )

    def test_il_ne_pointe_pas_vers_le_dossier_de_l_utilisateur(self, dossier_isole):
        from app.core.logging_config import dossier_des_journaux

        reel = Path.home() / ".therese"
        obtenu = dossier_des_journaux()

        assert reel not in obtenu.parents and obtenu != reel, (
            "les journaux d'une instance jetable atterrissent dans "
            f"l'installation réelle : {obtenu}"
        )


class TestLesConsignesSuiventLeDossierDeDonnees:
    def test_therese_md_est_cherche_dans_l_installation_jetable(self, dossier_isole):
        from app.services.llm import chemins_de_recherche_therese_md

        chemins = chemins_de_recherche_therese_md()

        assert any(dossier_isole in c.parents for c in chemins), (
            f"THERESE.md cherché dans {chemins}, jamais dans {dossier_isole}"
        )

    def test_il_ne_lit_pas_les_consignes_de_l_utilisateur_reel(self, dossier_isole):
        from app.services.llm import chemins_de_recherche_therese_md

        reel = Path.home() / ".therese" / "THERESE.md"
        assert reel not in chemins_de_recherche_therese_md(), (
            "une instance jetable lirait les consignes de personnalisation de "
            "l'utilisateur réel"
        )

    def test_sans_override_le_comportement_habituel_est_intact(self, monkeypatch):
        """La correction ne doit pas déplacer les fichiers d'une vraie installation."""
        monkeypatch.delenv("THERESE_DATA_DIR", raising=False)

        import app.config as module_config
        from app.config import Settings

        monkeypatch.setattr(module_config, "settings", Settings())
        from app.services.llm import chemins_de_recherche_therese_md

        chemins = chemins_de_recherche_therese_md()
        assert Path.home() / "THERESE.md" in chemins, (
            "le chemin de courtoisie à la racine du dossier personnel reste"
        )


class TestLaConfigurationDesJournauxEcritAuBonEndroit:
    """
    Le test précédent appelait l'aide, pas le chemin.

    Remettre `Path.home() / ".therese" / "logs"` dans `setup_logging` ne
    cassait RIEN : `dossier_des_journaux()` restait juste, et le sabotage
    passait. C'est la troisième fois de la journée que je teste une fonction
    au lieu du parcours qui l'emploie.

    Celui-ci configure vraiment les journaux, puis lit où le gestionnaire de
    fichiers écrit.
    """

    def test_le_gestionnaire_de_fichiers_pointe_dans_l_installation_jetable(
        self, dossier_isole
    ):
        import logging

        from app.core.logging_config import setup_logging

        racine = logging.getLogger()
        anciens = list(racine.handlers)
        try:
            setup_logging()
            fichiers = [
                Path(h.baseFilename)
                for h in logging.getLogger().handlers
                if hasattr(h, "baseFilename")
            ]
            assert fichiers, "aucun journal sur fichier configuré"
            for chemin in fichiers:
                assert dossier_isole in chemin.parents, (
                    f"journal écrit dans {chemin}, hors de {dossier_isole}"
                )
                assert Path.home() / ".therese" not in chemin.parents, (
                    "une instance jetable écrit ses journaux - avec les "
                    "arguments complets des outils - dans l'installation réelle"
                )
        finally:
            for h in list(logging.getLogger().handlers):
                if h not in anciens:
                    h.close()
                    logging.getLogger().removeHandler(h)
            for h in anciens:
                if h not in logging.getLogger().handlers:
                    logging.getLogger().addHandler(h)
