"""B-1157 (cycle 13) : la sauvegarde archive ce que la purge efface.

La purge totale efface `projects/`, `invoices/` (PDF des factures),
`THERESE.md` et les commandes utilisateur (`commands/`) ; la sauvegarde ne les
archivait pas. Sauvegarder, tout effacer puis restaurer les perdait.

Une restauration rend l'état sauvegardé : un élément couvert par l'archive est
vidé avant extraction (un fichier créé après la sauvegarde ne survit pas). Une
archive d'avant ce correctif ne couvre pas ces éléments : sa restauration ne
les touche pas. Le manifeste de l'archive dit ce qu'elle couvre.
"""

import io
import shutil
import tarfile
from pathlib import Path

import pytest
from app.config import settings
from app.routers import data as data_router

PASSE = "Passphrase-Test-123"

ELEMENTS = ("projects", "invoices", "THERESE.md", "commands")


@pytest.fixture(autouse=True)
def _dossier_de_donnees_rendu_intact(tmp_path):
    """B-1186 : ces tests écrivent dans le dossier de données de la session ;
    on met de côté ce qui y était et on le rend tel quel après le test."""
    data_dir = Path(settings.data_dir)
    cote = tmp_path / "mis-de-cote"
    cote.mkdir()
    for nom in ELEMENTS:
        if (data_dir / nom).exists():
            shutil.move(str(data_dir / nom), str(cote / nom))
    yield
    for nom in ELEMENTS:
        cible = data_dir / nom
        if cible.is_dir():
            shutil.rmtree(cible)
        elif cible.exists():
            cible.unlink()
        if (cote / nom).exists():
            shutil.move(str(cote / nom), str(cible))


def _poser(data_dir: Path) -> None:
    (data_dir / "projects" / "p1").mkdir(parents=True, exist_ok=True)
    (data_dir / "projects" / "p1" / "notes.md").write_text("projet", encoding="utf-8")
    (data_dir / "invoices").mkdir(parents=True, exist_ok=True)
    (data_dir / "invoices" / "F-2026-001.pdf").write_bytes(b"%PDF-1.4 facture")
    (data_dir / "THERESE.md").write_text("Mes consignes", encoding="utf-8")
    (data_dir / "commands" / "user").mkdir(parents=True, exist_ok=True)
    (data_dir / "commands" / "user" / "ma-commande.md").write_text("---\nname: ma-commande\n---\nFais ceci", encoding="utf-8")


@pytest.mark.asyncio
async def test_la_sauvegarde_archive_ce_que_la_purge_efface(client):
    _poser(Path(settings.data_dir))

    resp = await client.post("/api/data/backup", json={"password": PASSE})

    assert resp.status_code == 200, resp.text
    inclus = set(resp.json()["included"])
    assert {"projects", "invoices", "THERESE.md", "commands"} <= inclus, sorted(inclus)
    assert data_router.MANIFESTE_SAUVEGARDE not in inclus


@pytest.mark.asyncio
async def test_sauvegarder_effacer_restaurer_rend_l_etat_sauvegarde(client):
    data_dir = Path(settings.data_dir)
    _poser(data_dir)
    resp = await client.post("/api/data/backup", json={"password": PASSE})
    assert resp.status_code == 200, resp.text
    nom = resp.json()["backup_name"]

    shutil.rmtree(data_dir / "projects" / "p1")
    (data_dir / "invoices" / "F-2026-001.pdf").unlink()
    (data_dir / "THERESE.md").write_text("Consignes modifiées après", encoding="utf-8")
    (data_dir / "commands" / "user" / "ma-commande.md").unlink()
    (data_dir / "projects" / "p2").mkdir(parents=True)
    (data_dir / "projects" / "p2" / "orphelin.md").write_text("créé après", encoding="utf-8")

    resp = await client.post(f"/api/data/restore/{nom}?confirm=true", json={"password": PASSE})

    assert resp.status_code == 200, resp.text
    assert (data_dir / "projects" / "p1" / "notes.md").read_text(encoding="utf-8") == "projet"
    assert (data_dir / "invoices" / "F-2026-001.pdf").read_bytes() == b"%PDF-1.4 facture"
    assert (data_dir / "THERESE.md").read_text(encoding="utf-8") == "Mes consignes"
    assert (data_dir / "commands" / "user" / "ma-commande.md").exists()
    assert not (data_dir / "projects" / "p2").exists(), "un projet créé après la sauvegarde a survécu"
    assert not (data_dir / data_router.MANIFESTE_SAUVEGARDE).exists(), "le manifeste est resté dans les données"


def _archive(membres: dict[str, bytes]) -> tarfile.TarFile:
    tampon = io.BytesIO()
    with tarfile.open(fileobj=tampon, mode="w:gz") as tar:
        for nom, contenu in membres.items():
            info = tarfile.TarInfo(nom)
            info.size = len(contenu)
            tar.addfile(info, io.BytesIO(contenu))
    tampon.seek(0)
    return tarfile.open(fileobj=tampon, mode="r:gz")


def test_une_archive_d_avant_le_correctif_ne_couvre_rien_de_neuf():
    with _archive({"therese.db": b"base"}) as tar:
        assert data_router.elements_couverts(tar) == set()


def test_le_manifeste_ne_couvre_que_les_elements_connus():
    manifeste = b'{"version": 1, "couverts": ["projects", "THERESE.md", "../etc", "therese.db"]}'
    with _archive({data_router.MANIFESTE_SAUVEGARDE: manifeste}) as tar:
        assert data_router.elements_couverts(tar) == {"projects", "THERESE.md"}
