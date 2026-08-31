"""Les variables d'un serveur MCP sont chiffrees, quel que soit le chemin.

Trouve le 31/08/2026 par la boucle d'amelioration, confirme dans le code.
`create_server` chiffrait chaque valeur avant de la ranger, mais
`install_preset` transmettait `env_vars` tel quel. `add_server` rangeait sans
rien faire et `_save_config` ecrivait le dictionnaire directement en JSON.
Installer un serveur MCP par un prereglage ecrivait donc ses cles d'API en
clair sur le disque.

La lecture, elle, teste `is_value_encrypted` avant de dechiffrer : elle
tolerait ce clair sans jamais s'en plaindre.

Le chiffrement descend au point de passage unique, `add_server`, pour que
tout appelant present et futur en beneficie sans avoir a y penser.
"""

import pytest
from app.services.encryption import is_value_encrypted


@pytest.fixture
def service(tmp_path, monkeypatch):
    from app.services import mcp_service as module

    monkeypatch.setattr(module, "get_config_path", lambda: tmp_path / "mcp.json", raising=False)
    svc = module.MCPService()
    svc.servers = {}
    return svc


@pytest.mark.asyncio
async def test_les_variables_sont_chiffrees_par_add_server(service):
    """Le point de passage unique : peu importe qui appelle."""
    serveur = service.add_server(
        name="stripe", command="npx", args=["-y", "stripe-mcp"],
        env={"STRIPE_API_KEY": "sk_live_valeur_secrete"},
    )
    rangee = serveur.env["STRIPE_API_KEY"]
    assert rangee != "sk_live_valeur_secrete", "la valeur a ete rangee en clair"
    assert is_value_encrypted(rangee)


@pytest.mark.asyncio
async def test_une_valeur_deja_chiffree_n_est_pas_chiffree_deux_fois(service):
    from app.services.encryption import encrypt_value

    deja = encrypt_value("sk_live_valeur_secrete")
    serveur = service.add_server(
        name="stripe2", command="npx", args=["-y", "autre"], env={"K": deja},
    )
    assert serveur.env["K"] == deja


@pytest.mark.asyncio
async def test_sans_variable_rien_ne_casse(service):
    serveur = service.add_server(name="simple", command="echo", args=["ok"], env=None)
    assert serveur.env == {}
