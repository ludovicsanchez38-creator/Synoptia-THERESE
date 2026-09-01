"""Les agents actionnables doivent entrer au registre des commandes.

Trouvé par la boucle d'amélioration le 01/09/2026, confirmé par recherche
dans tout le serveur : `_register_action_agents` était écrite et n'était
appelée nulle part. Son unique occurrence était sa propre définition.

`init()` enregistrait les commandes intégrées, celles des skills et celles de
l'utilisateur, puis s'arrêtait. Les agents actionnables n'atteignaient donc ni
l'accueil ni le menu, alors que le code pour les brancher existait.
"""

import pytest


@pytest.mark.asyncio
async def test_les_agents_actionnables_sont_dans_le_registre():
    from app.services.command_registry import CommandRegistry

    registre = CommandRegistry()
    await registre.init()
    actionnables = [c for c in registre._commands.values() if c.id.startswith("action-")]
    assert actionnables, (
        "aucun agent actionnable enregistré : la méthode qui les branche "
        "existe mais n'est appelée nulle part"
    )


@pytest.mark.asyncio
async def test_ils_sont_annonces_a_l_accueil_et_au_menu():
    from app.services.command_registry import CommandRegistry

    registre = CommandRegistry()
    await registre.init()
    actionnables = [c for c in registre._commands.values() if c.id.startswith("action-")]
    assert all(c.show_on_home for c in actionnables)
    assert all(c.show_in_slash for c in actionnables)
