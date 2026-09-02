"""B-034 : le secret client Google ne sort pas par la route de statut.

Le secret est bien chiffré au repos dans `mcp_servers.json`, mais
`GET /api/email/setup/status` le déchiffrait et le renvoyait en clair dans son
JSON, systématiquement, sans opt-in — alors que Tauri interdit au renderer de
lire `.encryption_key`. Le préremplissage du wizard n'a pas besoin du secret :
il a besoin que l'autorisation aboutisse, ce que le serveur peut faire seul,
comme il le fait déjà pour la synchronisation Google Sheets.
"""

import pytest
from app.services.encryption import encrypt_value
from httpx import AsyncClient

TEMOIN = "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IR"
CLIENT_ID = "123456-abc.apps.googleusercontent.com"


@pytest.fixture
def serveur_mcp_google(tmp_path, monkeypatch):
    """Un serveur MCP google-workspace porteur d'un secret témoin chiffré."""
    from app.services import mcp_service as module

    monkeypatch.setattr(
        module, "get_config_path", lambda: tmp_path / "mcp.json", raising=False
    )
    service = module.MCPService()
    # `add_server` planifie une sauvegarde par asyncio.create_task : on pose
    # directement l'entrée, en chiffrant comme il le fait.
    service.servers = {
        "rp03": module.MCPServer(
            id="rp03",
            name="google-workspace RP03",
            command="npx",
            args=["-y", "google-workspace-mcp"],
            env=module._chiffrer_variables(
                {
                    "GOOGLE_OAUTH_CLIENT_ID": CLIENT_ID,
                    "GOOGLE_OAUTH_CLIENT_SECRET": TEMOIN,
                }
            ),
            enabled=False,
        )
    }
    monkeypatch.setattr(module, "get_mcp_service", lambda: service)
    return service


def _valeurs(objet):
    """Toutes les valeurs scalaires d'une réponse JSON, à plat."""
    if isinstance(objet, dict):
        for valeur in objet.values():
            yield from _valeurs(valeur)
    elif isinstance(objet, list):
        for valeur in objet:
            yield from _valeurs(valeur)
    else:
        yield objet


@pytest.mark.asyncio
async def test_statut_setup_ne_rend_jamais_le_secret(
    client: AsyncClient, serveur_mcp_google
):
    reponse = await client.get("/api/email/setup/status")
    assert reponse.status_code == 200, reponse.text
    statut = reponse.json()

    assert TEMOIN not in reponse.text, (
        "le secret client Google déchiffré sort par la route de statut"
    )
    for valeur in _valeurs(statut):
        assert valeur != TEMOIN

    identifiants = statut["google_credentials"]
    assert identifiants is not None, (
        "le statut doit continuer d'annoncer que des identifiants existent"
    )
    assert identifiants["client_id"] == CLIENT_ID
    assert identifiants["has_client_secret"] is True


@pytest.mark.asyncio
async def test_autorisation_google_reutilise_le_secret_cote_serveur(
    client: AsyncClient, serveur_mcp_google, monkeypatch
):
    """Le flux de mise en route survit : le serveur retrouve le secret seul."""
    from app.routers import email as module_email

    vu: dict[str, str] = {}
    vrai = module_email.get_gmail_oauth_config

    def _capture(client_id: str, client_secret: str):
        vu["client_id"] = client_id
        vu["client_secret"] = client_secret
        return vrai(client_id, client_secret)

    monkeypatch.setattr(module_email, "get_gmail_oauth_config", _capture)

    reponse = await client.post(
        "/api/email/auth/initiate",
        json={"client_id": CLIENT_ID, "client_secret": ""},
    )
    assert reponse.status_code == 200, reponse.text
    assert vu["client_secret"] == TEMOIN, (
        "sans le secret dans le corps, l'autorisation doit le retrouver "
        "côté serveur au lieu d'échouer"
    )


@pytest.mark.asyncio
async def test_autorisation_refuse_un_secret_introuvable(client: AsyncClient):
    """Aucun identifiant enregistré : refus explicite, pas un flux muet."""
    reponse = await client.post(
        "/api/email/auth/initiate",
        json={"client_id": "inconnu.apps.googleusercontent.com", "client_secret": ""},
    )
    assert reponse.status_code == 400, reponse.text


@pytest.mark.asyncio
async def test_secret_fourni_dans_le_corps_reste_prioritaire(
    client: AsyncClient, serveur_mcp_google, monkeypatch
):
    """Une saisie manuelle (import credentials.json) n'est pas écrasée."""
    from app.routers import email as module_email

    vu: dict[str, str] = {}
    vrai = module_email.get_gmail_oauth_config

    def _capture(client_id: str, client_secret: str):
        vu["client_secret"] = client_secret
        return vrai(client_id, client_secret)

    monkeypatch.setattr(module_email, "get_gmail_oauth_config", _capture)

    reponse = await client.post(
        "/api/email/auth/initiate",
        json={"client_id": CLIENT_ID, "client_secret": "GOCSPX-SAISIE-MANUELLE"},
    )
    assert reponse.status_code == 200, reponse.text
    assert vu["client_secret"] == "GOCSPX-SAISIE-MANUELLE"


def test_le_secret_reste_chiffre_au_repos():
    """Rappel : le défaut n'était pas le stockage, mais la restitution."""
    assert encrypt_value(TEMOIN) != TEMOIN
