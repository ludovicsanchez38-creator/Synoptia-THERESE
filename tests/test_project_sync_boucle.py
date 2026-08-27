"""D5 : attacher un dossier ne doit pas figer l'application.

Dr_logic, 27/08 (v0.48.2, donc APRÈS le correctif BUG-172) : « il y a un délai
sur la synchronisation ? » puis « ho, en le relançant, il passe... ».

Trente secondes, c'est exactement le délai client par défaut. `definir_racine`
enchaîne des appels système — résolution du chemin, `is_dir`, `exists`,
`samefile`, `stat` — directement sur la boucle asyncio, sous deux verrous et
une session ouverte. Sur Windows, avec un antivirus ou un volume réseau qui se
réveille, ces appels durent : la boucle entière attend, tout le reste de
l'application avec elle, et le client abandonne.

Allonger le délai ne ferait que rallonger le gel. Le travail système doit
sortir de la boucle.
"""
import asyncio
import time

import pytest

from app.services import project_sync_service as svc


@pytest.mark.asyncio
async def test_un_systeme_de_fichiers_lent_ne_fige_pas_la_boucle(
    client, tmp_path, monkeypatch
):
    dossier = tmp_path / "site-egrenne"
    dossier.mkdir()

    lenteur = {"applique": False}
    vrai_is_dir = svc.Path.is_dir

    def _is_dir_lent(self):
        # Une seule fois : le temps que met un volume réseau à répondre.
        if not lenteur["applique"]:
            lenteur["applique"] = True
            time.sleep(0.6)
        return vrai_is_dir(self)

    monkeypatch.setattr(svc.Path, "is_dir", _is_dir_lent)

    battements = 0

    async def coeur():
        nonlocal battements
        while True:
            await asyncio.sleep(0.02)
            battements += 1

    pouls = asyncio.create_task(coeur())
    try:
        with __import__("contextlib").suppress(Exception):
            await svc.definir_racine("projet-boucle", str(dossier))
    finally:
        pouls.cancel()
        with __import__("contextlib").suppress(asyncio.CancelledError):
            await pouls

    # Sur la boucle, l'attente de 0,6 s bloque tout : le pouls reste à zéro.
    # Hors de la boucle, il bat une vingtaine de fois.
    assert battements >= 10, (
        f"la boucle est restée figée pendant l'accès disque ({battements} battements)"
    )


@pytest.mark.asyncio
async def test_preparer_un_plan_ne_fige_pas_non_plus_la_boucle(
    client, tmp_path, monkeypatch
):
    """Le contrôle de racine précède le scan, et il touche le disque lui aussi.

    Le scan, lui, tourne déjà hors de la boucle. Mais `is_dir()` et le témoin
    de volume s'exécutaient avant, sur la boucle : c'est le bouton
    « Préparer » qui gelait l'application le temps qu'un volume réseau réponde.
    """
    dossier = tmp_path / "site-egrenne-plan"
    dossier.mkdir()
    (dossier / "index.html").write_text("<html></html>", encoding="utf-8")

    projet = (
        await client.post("/api/memory/projects", json={"name": "Site egrenne"})
    ).json()["id"]
    await svc.definir_racine(projet, str(dossier))

    lenteur = {"applique": False}
    vrai_is_dir = svc.Path.is_dir

    def _is_dir_lent(self):
        if not lenteur["applique"]:
            lenteur["applique"] = True
            time.sleep(0.6)
        return vrai_is_dir(self)

    monkeypatch.setattr(svc.Path, "is_dir", _is_dir_lent)

    battements = 0

    async def coeur():
        nonlocal battements
        while True:
            await asyncio.sleep(0.02)
            battements += 1

    pouls = asyncio.create_task(coeur())
    try:
        with __import__("contextlib").suppress(Exception):
            await svc.preparer_plan(projet)
    finally:
        pouls.cancel()
        with __import__("contextlib").suppress(asyncio.CancelledError):
            await pouls

    assert battements >= 10, (
        f"la boucle est restée figée avant le scan ({battements} battements)"
    )
