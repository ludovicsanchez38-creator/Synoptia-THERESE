"""B-188 (RB2-018) — le pont entre les deux registres ne va que dans un sens.

Deux routeurs servent les commandes utilisateur, et les deux clients existent
côté écran. `commands.py` écrit par `UserCommandsService` (clé = nom) ;
`commands_v3.py` lit le `CommandRegistry` (clé = identifiant, notion de
source). Le registre n'est chargé qu'au démarrage : une commande créée par le
client historique n'existe donc pas pour les surfaces servies par V3, alors
qu'une commande créée par V3 est visible des deux côtés.

Une commande utilisateur créée est une commande utilisateur, quel que soit le
registre interrogé.
"""

import pytest
from httpx import AsyncClient


@pytest.fixture
def dossier_de_commandes(tmp_path, monkeypatch):
    """Les deux services sont des singletons de processus (cf. B-187)."""
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


async def _noms_v3(client: AsyncClient) -> list[str]:
    reponse = await client.get("/api/v3/commands?source=user")
    assert reponse.status_code == 200, reponse.text
    return [cmd["name"] for cmd in reponse.json()]


async def _noms_historiques(client: AsyncClient) -> list[str]:
    reponse = await client.get("/api/commands/user")
    assert reponse.status_code == 200, reponse.text
    return [cmd["name"] for cmd in reponse.json()]


class TestB188LesDeuxRegistresSAccordent:
    @pytest.mark.asyncio
    async def test_sens_deja_bon_v3_vers_historique(
        self, client: AsyncClient, dossier_de_commandes
    ) -> None:
        """Contrôle de l'instrument : ce sens-là fonctionnait déjà."""
        creee = await client.post(
            "/api/v3/commands/user",
            json={"name": "rb2v3", "description": "cmd v3", "prompt_template": "bonjour"},
        )
        assert creee.status_code == 201, creee.text

        assert "rb2v3" in await _noms_v3(client)
        assert "rb2v3" in await _noms_historiques(client)

    @pytest.mark.asyncio
    async def test_creation_historique_visible_en_v3(
        self, client: AsyncClient, dossier_de_commandes
    ) -> None:
        creee = await client.post(
            "/api/commands/user",
            json={"name": "rb2cmd", "description": "cmd test", "content": "bonjour"},
        )
        assert creee.status_code == 201, creee.text

        assert "rb2cmd" in await _noms_historiques(client)
        assert "rb2cmd" in await _noms_v3(client), (
            "creee par /api/commands/user, absente de GET /api/v3/commands?source=user"
        )

        detail = await client.get("/api/v3/commands/user-rb2cmd")
        assert detail.status_code == 200, detail.text
        assert detail.json()["prompt_template"] == "bonjour"
        assert detail.json()["source"] == "user"

    @pytest.mark.asyncio
    async def test_modification_historique_repercutee_en_v3(
        self, client: AsyncClient, dossier_de_commandes
    ) -> None:
        await client.post(
            "/api/commands/user",
            json={"name": "rb2cmd", "description": "avant", "content": "bonjour"},
        )

        modifiee = await client.put(
            "/api/commands/user/rb2cmd",
            json={"description": "apres", "content": "bonsoir"},
        )
        assert modifiee.status_code == 200, modifiee.text

        detail = await client.get("/api/v3/commands/user-rb2cmd")
        assert detail.status_code == 200, detail.text
        assert detail.json()["description"] == "apres"
        assert detail.json()["prompt_template"] == "bonsoir"

    @pytest.mark.asyncio
    async def test_suppression_historique_repercutee_en_v3(
        self, client: AsyncClient, dossier_de_commandes
    ) -> None:
        await client.post(
            "/api/commands/user",
            json={"name": "rb2cmd", "description": "cmd test", "content": "bonjour"},
        )

        supprimee = await client.delete("/api/commands/user/rb2cmd")
        assert supprimee.status_code == 200, supprimee.text

        assert await _noms_historiques(client) == []
        assert "rb2cmd" not in await _noms_v3(client), (
            "supprimee du disque mais toujours proposee par V3"
        )
        detail = await client.get("/api/v3/commands/user-rb2cmd")
        assert detail.status_code == 404, detail.text


class TestB254LeDrapeauSlashEstPersiste:
    """B-254 — `show_in_slash` ne vivait qu'en mémoire.

    Le registre est repeuplé au démarrage depuis `~/.therese/commands/user/*.md`.
    Le drapeau n'existait ni dans le modèle de disque `UserCommand`, ni dans le
    frontmatter YAML écrit, ni dans le parseur ;
    `_definition_depuis_commande_utilisateur` le posait à `True` en dur. Une
    commande masquée du menu « / » y revenait donc au redémarrage suivant, par
    les DEUX chemins d'écriture (création V3 et mise à jour).

    `show_on_home`, persisté depuis toujours, sert de modèle exact.
    """

    @staticmethod
    async def _registre_neuf(command_id: str):
        """Le redémarrage : un registre neuf qui relit le disque."""
        from app.services.command_registry import CommandRegistry

        neuf = CommandRegistry()
        await neuf.init()
        return neuf.get(command_id)

    @pytest.mark.asyncio
    async def test_le_drapeau_show_in_slash_survit_au_redemarrage(
        self, client: AsyncClient, dossier_de_commandes
    ) -> None:
        creee = await client.post(
            "/api/v3/commands/user",
            json={
                "name": "b254-cachee",
                "description": "commande hors du menu slash",
                "icon": "",
                "category": "production",
                "prompt_template": "p",
                "show_on_home": True,
                "show_in_slash": False,
            },
        )
        assert creee.status_code == 201, creee.text
        assert creee.json()["show_in_slash"] is False, creee.text

        relue = await self._registre_neuf("user-b254-cachee")
        assert relue is not None, "la commande n'est pas relue du disque"
        assert relue.show_in_slash is False, (
            f"drapeau perdu au redémarrage : show_in_slash={relue.show_in_slash}"
        )
        assert relue.show_on_home is True, (
            "le drapeau voisin, lui, doit rester ce qu'il était"
        )

    @pytest.mark.asyncio
    async def test_le_drapeau_retire_par_une_mise_a_jour_survit_aussi(
        self, client: AsyncClient, dossier_de_commandes
    ) -> None:
        creee = await client.post(
            "/api/v3/commands/user",
            json={
                "name": "b254-visible",
                "description": "commande visible puis masquée",
                "icon": "",
                "category": "production",
                "prompt_template": "p",
                "show_on_home": True,
                "show_in_slash": True,
            },
        )
        assert creee.status_code == 201, creee.text

        modifiee = await client.put(
            "/api/v3/commands/user/user-b254-visible",
            json={"show_in_slash": False},
        )
        assert modifiee.status_code == 200, modifiee.text
        assert modifiee.json()["show_in_slash"] is False, modifiee.text

        relue = await self._registre_neuf("user-b254-visible")
        assert relue is not None, "la commande n'est pas relue du disque"
        assert relue.show_in_slash is False, (
            "la mise à jour n'a rien écrit sur le disque : "
            f"show_in_slash={relue.show_in_slash} après redémarrage"
        )

    @pytest.mark.asyncio
    async def test_un_fichier_ancien_sans_le_drapeau_reste_visible(
        self, dossier_de_commandes
    ) -> None:
        """Les `.md` déjà sur le disque n'ont pas la clé : leur comportement ne
        doit pas changer."""
        from app.services.user_commands import UserCommand

        ancien = (
            "---\nname: b254-ancienne\ndescription: d\ncategory: production\n"
            "icon: ''\nshow_on_home: true\n---\ncorps"
        )
        commande = UserCommand.from_markdown(ancien, "b254-ancienne.md")
        assert commande.show_in_slash is True
