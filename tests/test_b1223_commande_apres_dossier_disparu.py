"""B-1223 : le service des commandes utilisateur ne crée son dossier qu'une
fois, à sa naissance. Si `commands/user/` disparaît ensuite (restauration dont
le retour arrière a échoué, ménage manuel), créer une commande échouait
(FileNotFoundError) jusqu'au redémarrage.
"""

import shutil


def test_une_commande_se_cree_meme_si_le_dossier_a_disparu():
    from app.services.user_commands import UserCommandsService

    service = UserCommandsService.get_instance()
    shutil.rmtree(service._commands_dir, ignore_errors=True)

    service.create_command(name="b1223cmd", description="test", content="Bonjour")

    assert (service._commands_dir / "b1223cmd.md").exists()
    service.delete_command("b1223cmd")
