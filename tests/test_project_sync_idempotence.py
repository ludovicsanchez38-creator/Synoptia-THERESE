"""D5 : réessayer d'attacher le même dossier ne doit rien détruire.

Quand le client abandonne au bout de ses trente secondes, le serveur, lui,
poursuit : un `stat()` ne s'annule pas. La racine peut donc être posée alors
que l'écran affiche un échec. L'utilisateur relance — « ho, en le relançant,
il passe » — et cette seconde tentative incrémentait la génération.

Or la génération est ce qui rend un plan applicable. La relancer invalide un
plan que l'utilisateur venait de préparer, sans que rien ne le dise. Réattacher
le MÊME dossier ne change rien : ce doit être sans effet.

Changer de dossier, en revanche, doit toujours incrémenter — un ancien plan
partiel ne doit jamais redevenir compatible (revue jalon, B1).
"""
import pytest
from pathlib import Path

from app.services import project_sync_service as svc


async def _projet(client, nom: str) -> str:
    reponse = await client.post("/api/memory/projects", json={"name": nom})
    return reponse.json()["id"]


@pytest.mark.asyncio
async def test_reattacher_le_meme_dossier_ne_change_pas_la_generation(
    client, tmp_path: Path
):
    dossier = tmp_path / "site"
    dossier.mkdir()
    projet = await _projet(client, "Site egrenne")

    premier = await svc.definir_racine(projet, str(dossier))
    second = await svc.definir_racine(projet, str(dossier))

    assert second.generation == premier.generation
    assert second.racine == premier.racine


@pytest.mark.asyncio
async def test_changer_de_dossier_incremente_toujours(client, tmp_path: Path):
    un = tmp_path / "un"
    deux = tmp_path / "deux"
    un.mkdir()
    deux.mkdir()
    projet = await _projet(client, "Chantier")

    premier = await svc.definir_racine(projet, str(un))
    second = await svc.definir_racine(projet, str(deux))

    assert second.generation == premier.generation + 1


@pytest.mark.asyncio
async def test_reattacher_une_racine_deliee_la_reprend(client, tmp_path: Path):
    """Un dossier délié puis repris redevient actif, sans repartir de zéro."""
    dossier = tmp_path / "reprise"
    dossier.mkdir()
    projet = await _projet(client, "Reprise")

    premier = await svc.definir_racine(projet, str(dossier))
    await svc.retirer_racine(projet)
    repris = await svc.definir_racine(projet, str(dossier))

    assert repris.detachee is False
    # Deux avancées : le détachement, puis la reprise. L'idempotence ne
    # s'applique QU'À une racine identique ET toujours active — pendant un
    # détachement, le dossier a pu changer sans que personne ne l'observe,
    # et un ancien plan ne doit pas redevenir applicable.
    assert repris.generation == premier.generation + 2
