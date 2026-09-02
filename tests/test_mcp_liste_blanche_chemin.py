"""
B-142 : la liste blanche des commandes MCP ne portait que sur le NOM DE BASE.

`validate_mcp_command` résolvait la commande puis comparait `Path(resolved).name`
aux commandes autorisées. Un binaire arbitraire déposé sous le nom `npx` et
désigné par son chemin satisfaisait donc la liste blanche : reproduit le
02/09/2026 par un POST /api/mcp/servers avec `command=/tmp/rb-faux-bin/npx`,
qui a répondu 200 et démarré le binaire (status « running »), alors que les
témoins `/bin/sh` et `curl` étaient bien refusés.

L'invariant posé ici : la commande se donne par son NOM SEUL. C'est le PATH
enrichi de THÉRÈSE (`build_mcp_enriched_path`, consommé par `start_server`) qui
désigne le binaire réellement lancé. Un chemin explicite court-circuite cette
résolution, donc la liste blanche.
"""

import pytest
from app.services.mcp_service import validate_mcp_command


def _faux_binaire(dossier, nom: str):
    """Dépose un exécutable arbitraire portant un nom de la liste blanche."""
    chemin = dossier / nom
    chemin.write_text("#!/bin/sh\necho arbitraire >&2\n")
    chemin.chmod(0o755)
    return chemin


class TestUnCheminNeContournePasLaListeBlanche:
    def test_binaire_arbitraire_nomme_npx_refuse(self, tmp_path):
        """Le cas exact de la reproduction : /tmp/<...>/npx n'est pas npx."""
        faux = _faux_binaire(tmp_path, "npx")
        with pytest.raises(ValueError, match="Commande MCP non autorisée"):
            validate_mcp_command(str(faux))

    def test_binaire_arbitraire_nomme_node_refuse(self, tmp_path):
        faux = _faux_binaire(tmp_path, "node")
        with pytest.raises(ValueError, match="Commande MCP non autorisée"):
            validate_mcp_command(str(faux))

    def test_le_message_dit_quoi_faire(self, tmp_path):
        """Un refus qui n'indique pas la forme attendue se lit comme une panne."""
        faux = _faux_binaire(tmp_path, "npx")
        with pytest.raises(ValueError) as erreur:
            validate_mcp_command(str(faux))
        assert "nom seul" in str(erreur.value)

    def test_chemin_relatif_refuse(self):
        """`./node` désigne un fichier du dossier courant, pas le node du PATH."""
        with pytest.raises(ValueError, match="Commande MCP non autorisée"):
            validate_mcp_command("./node")

    def test_chemin_windows_refuse(self):
        with pytest.raises(ValueError, match="Commande MCP non autorisée"):
            validate_mcp_command(r"C:\Users\public\npx.cmd")

    def test_le_nom_seul_reste_accepte(self):
        """La correction ne doit pas fermer l'usage normal : les 19 presets
        déclarent tous `npx` nu (routers/mcp.py)."""
        validate_mcp_command("npx", ["-y", "@modelcontextprotocol/server-fetch"])
        validate_mcp_command("python3")

    def test_une_commande_bloquee_avec_chemin_reste_bloquee(self):
        """L'ordre des contrôles compte : /bin/rm doit dire « bloquée »,
        message sur lequel s'appuie le refus affiché à l'utilisateur."""
        with pytest.raises(ValueError, match="Commande MCP bloquée"):
            validate_mcp_command("/bin/rm")
