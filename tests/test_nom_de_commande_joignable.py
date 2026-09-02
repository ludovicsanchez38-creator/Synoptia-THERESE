"""B-187 (RB2-017) — une commande créée sous un nom injoignable est perdue.

Le nom n'est borné que par sa longueur (50 caractères). Un nom contenant une
barre oblique est accepté en 201, apparaît dans la liste et dans le menu des
commandes, mais GET, PUT et DELETE sur `/api/commands/user/{name}` rendent
tous 404 : le routeur découpe le chemin avant d'arriver à la fonction, et
`%2F` est décodé de la même façon. La commande reste donc affichée pour
toujours, sans moyen de la modifier ni de la supprimer.

Même cause côté V3, qui fabrique `id = f"user-{name}"` et le reprend en chemin.
"""

import pytest
from httpx import AsyncClient


@pytest.fixture
def dossier_de_commandes(tmp_path, monkeypatch):
    """`UserCommandsService` et `CommandRegistry` sont des singletons de
    processus : sans isolation, les noms écrits ici fuiraient dans les autres
    fichiers de tests (et inversement)."""
    from app.services.command_registry import CommandRegistry
    from app.services.user_commands import UserCommandsService

    service = UserCommandsService.get_instance()
    monkeypatch.setattr(service, "_commands_dir", tmp_path)

    registre = CommandRegistry.get_instance()
    memoire = dict(registre._commands)
    registre._commands.clear()
    yield tmp_path
    registre._commands.clear()
    registre._commands.update(memoire)


NOMS_INJOIGNABLES = ["a/b", "../rb2evade", "a\\b", ".cache"]


class TestB187NomJoignable:
    @pytest.mark.asyncio
    async def test_un_nom_ordinaire_reste_joignable(
        self, client: AsyncClient, dossier_de_commandes
    ) -> None:
        """Contrôle de l'instrument : le cycle complet marche sur un nom sain."""
        creee = await client.post(
            "/api/commands/user",
            json={"name": "rb2cmd", "description": "cmd test", "content": "bonjour"},
        )
        assert creee.status_code == 201, creee.text

        lue = await client.get("/api/commands/user/rb2cmd")
        assert lue.status_code == 200, lue.text

        modifiee = await client.put(
            "/api/commands/user/rb2cmd", json={"description": "autre"}
        )
        assert modifiee.status_code == 200, modifiee.text

        supprimee = await client.delete("/api/commands/user/rb2cmd")
        assert supprimee.status_code == 200, supprimee.text

    @pytest.mark.asyncio
    async def test_noms_injoignables_refuses(
        self, client: AsyncClient, dossier_de_commandes
    ) -> None:
        for nom in NOMS_INJOIGNABLES:
            reponse = await client.post(
                "/api/commands/user",
                json={"name": nom, "description": "x", "content": "y"},
            )
            assert reponse.status_code == 422, (
                f"nom {nom!r} accepte : {reponse.status_code} -> {reponse.text[:200]}"
            )
            assert "name" in reponse.text

        liste = await client.get("/api/commands/user")
        assert liste.json() == [], "un nom injoignable a quand meme ete ecrit"

    @pytest.mark.asyncio
    async def test_nom_fait_de_blancs_refuse(
        self, client: AsyncClient, dossier_de_commandes
    ) -> None:
        reponse = await client.post(
            "/api/commands/user", json={"name": "   ", "description": "x", "content": "y"}
        )
        assert reponse.status_code == 422, reponse.text

    @pytest.mark.asyncio
    async def test_v3_refuse_les_memes_noms(
        self, client: AsyncClient, dossier_de_commandes
    ) -> None:
        """V3 fabrique `user-{name}` et le reprend en chemin : même trou."""
        for nom in NOMS_INJOIGNABLES:
            reponse = await client.post(
                "/api/v3/commands/user",
                json={"name": nom, "description": "x", "prompt_template": "y"},
            )
            assert reponse.status_code == 422, (
                f"V3 accepte {nom!r} : {reponse.status_code} -> {reponse.text[:200]}"
            )
