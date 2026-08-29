"""
Le garde de path traversal accepte un chemin légitime, y compris sur Windows.

CI Windows du 29/08 : `test_pre_restore_retention_une_seule_archive` rendait
400 « Archive de backup non sûre » sur une archive que l'application venait
elle-même de produire. Vert le matin, rouge le soir : un test dépendant de
l'ordre et de la plateforme.

La cause est la méthode de comparaison :

    if not str(target).startswith(str(dest_resolved)):

Comparer des chemins par PRÉFIXE DE CHAÎNE est fragile. Sous Windows,
`Path.resolve()` peut rendre une forme courte (`RUNNER~1`) ou une casse
différente de celle du parent, et un membre parfaitement légitime échoue.
Le pire : `/data-autre` commence bien par `/data`, donc le garde laisse
passer un vrai voisin tout en refusant un enfant légitime.

`Path.is_relative_to` répond exactement à la question posée.
"""

from pathlib import Path


class TestLeGardeRepondALaBonneQuestion:
    def test_un_membre_legitime_passe(self, tmp_path):
        from app.routers.data import _membre_est_sur

        dest = tmp_path / "restauration"
        dest.mkdir()
        assert _membre_est_sur(dest, "therese.db") is True
        assert _membre_est_sur(dest, "qdrant/collection.bin") is True

    def test_une_sortie_du_dossier_est_refusee(self, tmp_path):
        from app.routers.data import _membre_est_sur

        dest = tmp_path / "restauration"
        dest.mkdir()
        assert _membre_est_sur(dest, "../evade.txt") is False
        assert _membre_est_sur(dest, "../../etc/passwd") is False

    def test_un_voisin_au_nom_proche_est_refuse(self, tmp_path):
        """« /data-autre » commence par « /data » : le préfixe de chaîne
        laissait passer un voisin, pas seulement un enfant."""
        from app.routers.data import _membre_est_sur

        dest = tmp_path / "data"
        dest.mkdir()
        (tmp_path / "data-autre").mkdir()

        assert _membre_est_sur(dest, "../data-autre/vol.txt") is False

    def test_le_chemin_absolu_est_refuse(self, tmp_path):
        from app.routers.data import _membre_est_sur

        dest = tmp_path / "restauration"
        dest.mkdir()
        assert _membre_est_sur(dest, str(Path.home() / "vol.txt")) is False
