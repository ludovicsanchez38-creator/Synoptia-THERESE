"""B-087 — les bornes de la création doivent tenir à la mise à jour.

POST /api/v3/commands/user refuse un nom vide (422) ; PUT sur la même
commande l'acceptait en 200 et le persistait. Une commande au nom vide
devenait ensuite injoignable : `update_user_command` retrouve le fichier par
le NOM courant, donc plus aucun PUT ni DELETE ne la désignait (404), alors
que GET la rendait toujours en 200.
"""

import pytest
from httpx import AsyncClient


@pytest.fixture
def dossier_de_commandes(tmp_path, monkeypatch):
    """`UserCommandsService` et `CommandRegistry` sont des singletons de
    processus : sans isolation, les commandes écrites ici fuiraient dans les
    autres fichiers de tests (et inversement)."""
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


COMMANDE_VALIDE = {
    "name": "b087cmd",
    "description": "description d'origine",
    "icon": "*",
    "category": "production",
    "prompt_template": "bonjour",
}

# Chaque valeur est refusée par CreateUserCommandRequest ; elle doit l'être
# aussi par UpdateUserCommandRequest.
HORS_BORNES = [
    ("name", ""),
    ("name", "n" * 51),
    ("description", "d" * 201),
    ("icon", "i" * 11),
    ("category", "c" * 51),
]


class TestB087BornesDeMiseAJour:
    @pytest.mark.asyncio
    async def test_la_creation_refuse_bien_ces_valeurs(
        self, client: AsyncClient, dossier_de_commandes
    ) -> None:
        """Contrôle de l'instrument : c'est bien la création qui fait référence."""
        for champ, valeur in HORS_BORNES:
            charge = dict(COMMANDE_VALIDE) | {champ: valeur}
            refus = await client.post("/api/v3/commands/user", json=charge)
            assert refus.status_code == 422, f"{champ}={valeur!r} : {refus.status_code}"

    @pytest.mark.parametrize("champ,valeur", HORS_BORNES)
    @pytest.mark.asyncio
    async def test_la_mise_a_jour_applique_les_memes_bornes(
        self, client: AsyncClient, dossier_de_commandes, champ: str, valeur: str
    ) -> None:
        creee = await client.post("/api/v3/commands/user", json=COMMANDE_VALIDE)
        assert creee.status_code == 201, creee.text
        identifiant = creee.json()["id"]

        refus = await client.put(f"/api/v3/commands/user/{identifiant}", json={champ: valeur})
        assert refus.status_code == 422, (
            f"PUT {champ}={valeur!r} rendu en {refus.status_code} : "
            "la mise à jour accepte ce que la création refuse"
        )

        relue = await client.get(f"/api/v3/commands/user/{identifiant}".replace("/user/", "/"))
        assert relue.status_code == 200, relue.text
        assert relue.json()[champ] == COMMANDE_VALIDE[champ], "la valeur hors bornes a été persistée"

    @pytest.mark.asyncio
    async def test_une_mise_a_jour_dans_les_bornes_passe_toujours(
        self, client: AsyncClient, dossier_de_commandes
    ) -> None:
        """Contrôle négatif : le durcissement ne ferme pas le cas légitime."""
        creee = await client.post("/api/v3/commands/user", json=COMMANDE_VALIDE)
        assert creee.status_code == 201, creee.text
        identifiant = creee.json()["id"]

        modifiee = await client.put(
            f"/api/v3/commands/user/{identifiant}",
            json={"description": "description modifiée", "show_on_home": False},
        )
        assert modifiee.status_code == 200, modifiee.text
        assert modifiee.json()["description"] == "description modifiée"
