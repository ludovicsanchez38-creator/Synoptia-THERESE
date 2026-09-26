"""B-1655 : si la lecture du mode cabinet échouait au démarrage, l'erreur
n'allait qu'au journal de débogage et le carnet redevenait partagé (ouvert),
alors que Paramètres affichait « actif ». Après une restauration, un échec
de relecture du profil empêchait aussi de relire le mode cabinet (bloc
d'erreur commun, B-1540). Un réglage illisible ferme désormais le
cloisonnement ; profil et mode cabinet ont chacun leur garde.
"""

from pathlib import Path

import pytest
from app.config import settings

PASSE = "Passphrase-Test-123"


@pytest.fixture(autouse=True)
def _neutre():
    from app.services.cloisonnement import poser_mode_cabinet

    yield
    poser_mode_cabinet(None)


@pytest.mark.asyncio
async def test_un_reglage_illisible_au_demarrage_ferme_le_cloisonnement(monkeypatch):
    from app import main
    from app.services import cloisonnement

    async def illisible():
        raise RuntimeError("base verrouillée")

    monkeypatch.setattr(cloisonnement, "charger_mode_cabinet_depuis_la_base", illisible)
    cloisonnement.poser_mode_cabinet(None)
    await main._load_brave_key()

    assert cloisonnement.mode_cabinet_actif() is True


@pytest.mark.asyncio
async def test_un_profil_illisible_n_empeche_pas_de_relire_le_mode_cabinet(client, monkeypatch):
    from app.services import user_profile
    from app.services.cloisonnement import mode_cabinet_actif

    assert (await client.post("/api/config/mode-cabinet?enabled=true&confirme=true")).status_code == 200
    sauvegarde = await client.post("/api/data/backup", json={"password": PASSE})
    assert sauvegarde.status_code == 200, sauvegarde.text
    assert (await client.post("/api/config/mode-cabinet?enabled=false")).status_code == 200

    async def profil_illisible():
        raise RuntimeError("profil illisible")

    monkeypatch.setattr(user_profile, "recharger_le_profil_en_cache", profil_illisible)
    reponse = await client.post(
        f"/api/data/restore/{sauvegarde.json()['backup_name']}?confirm=true", json={"password": PASSE},
    )
    assert reponse.status_code == 200, reponse.text
    assert mode_cabinet_actif() is True
    assert Path(settings.data_dir).exists()
