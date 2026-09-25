"""B-1223 : le service des commandes utilisateur ne crée son dossier qu'une
fois, à sa naissance. Si `commands/user/` disparaît ensuite (restauration dont
le retour arrière a échoué, ménage manuel), créer une commande échouait
(FileNotFoundError) jusqu'au redémarrage.
"""

import shutil


def test_une_commande_se_cree_meme_si_le_dossier_a_disparu(tmp_path, monkeypatch):
    from app.services.user_commands import UserCommandsService

    service = UserCommandsService.get_instance()
    # B-1236 : on travaille dans un dossier du test, jamais dans celui de la
    # session (qui peut être un vrai dossier si THERESE_DATA_DIR est défini).
    dossier = tmp_path / "commands" / "user"
    dossier.mkdir(parents=True)
    monkeypatch.setattr(service, "_commands_dir", dossier)
    shutil.rmtree(dossier)

    service.create_command(name="b1223cmd", description="test", content="Bonjour")

    assert (dossier / "b1223cmd.md").exists()
