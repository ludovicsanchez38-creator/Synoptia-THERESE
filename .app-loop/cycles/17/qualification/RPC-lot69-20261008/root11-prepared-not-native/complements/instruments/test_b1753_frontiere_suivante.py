"""Sentinelle de frontière suivante préparée, sans restauration ni HTTP.

À placer après le témoin delete durable, sous le plugin de trace et dans une
copie/profil privé validé root. Aucune nouvelle fonctionnalité n'est testée.
"""
def test_frontiere_suivante_ne_recoit_aucune_tache_du_temoin():
    from app.services import task_registry
    from app.services.action_agents import ActionRunner
    assert task_registry.vivantes() == []
    assert not ActionRunner._taches_de_fond
