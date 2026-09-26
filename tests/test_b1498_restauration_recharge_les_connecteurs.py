"""B-1498 : après une restauration, le moteur gardait en mémoire la liste de
connecteurs d'avant.

La restauration remet `mcp_servers.json`, mais le service MCP ne relit ce
fichier qu'au démarrage. Jusqu'au redémarrage, la liste en mémoire était
celle d'avant, et la première modification d'un connecteur la réécrivait
sur le disque : la configuration restaurée était perdue.
"""

import pytest

PASSE = "Passphrase-Test-123"


@pytest.mark.asyncio
async def test_apres_restauration_la_liste_en_memoire_est_celle_du_fichier(client):
    from app.services.mcp_service import MCPServer, get_mcp_service

    service = get_mcp_service()
    avant = dict(service.servers)
    try:
        service.servers = {"sauvegarde": MCPServer(id="sauvegarde", name="Connecteur sauvegardé", command="uvx", enabled=False)}
        service._ecrire_config()

        sauvegarde = await client.post("/api/data/backup", json={"password": PASSE})
        assert sauvegarde.status_code == 200, sauvegarde.text

        service.servers["ajoute"] = MCPServer(id="ajoute", name="Ajouté après", command="npx", enabled=False)
        service._ecrire_config()

        reponse = await client.post(
            f"/api/data/restore/{sauvegarde.json()['backup_name']}?confirm=true", json={"password": PASSE},
        )
        assert reponse.status_code == 200, reponse.text

        assert set(service.servers) == {"sauvegarde"}
    finally:
        service.servers = avant
        service._ecrire_config()
