"""B-798 (cycle 9) : une ligne JSON valide mais non-objet (`[]`, `"x"`, `42`)
levait AttributeError hors du try, et l'except de la boucle faisait `break` :
le pont MCP s'arrêtait au lieu de sauter la ligne."""
from __future__ import annotations

import pytest
from app.services.mcp_therese_server import decoder_requete


@pytest.mark.parametrize("ligne", ["[]", '"x"', "42", "null", "{pas du json"])
def test_une_ligne_qui_n_est_pas_un_objet_est_ignoree(ligne: str) -> None:
    assert decoder_requete(ligne) is None


def test_un_objet_json_rpc_est_accepte() -> None:
    assert decoder_requete('{"jsonrpc": "2.0", "id": 1, "method": "initialize"}') == {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
    }
