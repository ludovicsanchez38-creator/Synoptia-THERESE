"""B-1540 et B-1541 (RFC P-107 et P-108 V4, jumeaux de B-1505 et B-1522) :
après une restauration, le profil, THERESE.md et le mode cabinet d'avant
restaient servis jusqu'au redémarrage (un PDF de facture produit entre-temps
portait l'émetteur d'avant) ; après « Effacer toutes mes données », le mode
cabinet restait actif en mémoire.
"""

from pathlib import Path

import pytest
from app.config import settings

PASSE = "Passphrase-Test-123"


@pytest.fixture(autouse=True)
def _caches_neutres():
    from app.services.cloisonnement import poser_mode_cabinet
    from app.services.llm import reload_therese_md
    from app.services.user_profile import set_cached_profile

    yield
    poser_mode_cabinet(None)
    set_cached_profile(None)
    (Path(settings.data_dir) / "THERESE.md").unlink(missing_ok=True)
    reload_therese_md()


@pytest.mark.asyncio
async def test_la_purge_remet_le_mode_cabinet_au_defaut(client):
    from app.services.cloisonnement import mode_cabinet_actif

    assert (await client.post("/api/config/mode-cabinet?enabled=true&confirme=true")).status_code == 200
    assert mode_cabinet_actif() is True

    assert (await client.delete("/api/data/all?confirm=true")).status_code == 200
    assert mode_cabinet_actif() is False


@pytest.mark.asyncio
async def test_la_restauration_remet_profil_consignes_et_mode_cabinet_de_la_sauvegarde(client):
    from app.services.cloisonnement import mode_cabinet_actif
    from app.services.llm import load_therese_md, reload_therese_md
    from app.services.user_profile import get_cached_profile

    consignes = Path(settings.data_dir) / "THERESE.md"
    assert (await client.post("/api/config/profile", json={"name": "Hélène Avant"})).status_code == 200
    assert (await client.post("/api/config/mode-cabinet?enabled=true&confirme=true")).status_code == 200
    consignes.write_text("Consignes de la sauvegarde", encoding="utf-8")
    reload_therese_md()
    sauvegarde = await client.post("/api/data/backup", json={"password": PASSE})
    assert sauvegarde.status_code == 200, sauvegarde.text

    assert (await client.post("/api/config/profile", json={"name": "Bruno Après"})).status_code == 200
    assert (await client.post("/api/config/mode-cabinet?enabled=false")).status_code == 200
    consignes.write_text("Consignes d'après", encoding="utf-8")
    reload_therese_md()

    reponse = await client.post(
        f"/api/data/restore/{sauvegarde.json()['backup_name']}?confirm=true", json={"password": PASSE},
    )
    assert reponse.status_code == 200, reponse.text

    # Un profil chiffré n'est pas relu sans trousseau (comme au démarrage) :
    # le cache est alors vide, et ses lecteurs relisent la base à la demande.
    # Le défaut était le cache PÉRIMÉ, qui servait « Bruno Après ».
    profil = get_cached_profile()
    assert profil is None or profil.name == "Hélène Avant", profil
    assert (await client.get("/api/config/profile")).json()["name"] == "Hélène Avant"
    assert load_therese_md() == "Consignes de la sauvegarde"
    assert mode_cabinet_actif() is True
