"""B-1186 : les tests de B-1130 et B-1157 prouvent ce qu'ils annoncent.

- test_b1130 restait vert quand la purge n'effaçait plus aucun vecteur
  (aucun point posé avant la purge) ;
- test_b1157 écrivait dans le dossier de données de la session
  (THERESE.md écrasé, trois fichiers laissés) sans nettoyer.

Les mutants et la mesure en sous-processus viennent du reproducteur c13b.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from app.config import settings
from app.services import qdrant as module_qdrant

RACINE = Path(__file__).resolve().parents[1]


@pytest.fixture
def vrai_qdrant(tmp_path, monkeypatch):
    """Même montage que tests/test_b1130_qdrant_apres_purge.py."""
    monkeypatch.setattr(settings, "qdrant_path", str(tmp_path / "qdrant"))
    service = module_qdrant.QdrantService()
    _ = service.client
    monkeypatch.setattr(module_qdrant, "_qdrant_service", service)
    monkeypatch.setattr(module_qdrant, "get_qdrant_service", lambda: service)
    yield service
    service.close()


def _purge_sabotee(service, monkeypatch) -> None:
    # Mutant : « la purge n'efface plus la mémoire vectorielle ».
    monkeypatch.setattr(service.client, "delete_collection", lambda *a, **k: True)


def _poser_un_point(service) -> None:
    from qdrant_client.models import PointStruct

    service.client.upsert(
        collection_name=settings.qdrant_collection,
        points=[PointStruct(id=1, vector=[0.1] * settings.embedding_dimensions,
                            payload={"entity_id": "contact-x", "type": "contact"})],
    )
    assert service.client.count(settings.qdrant_collection).count == 1


@pytest.mark.asyncio
async def test_le_test_b1130_rougit_quand_la_purge_n_efface_plus_les_vecteurs(
    client, vrai_qdrant, monkeypatch
):
    from tests import test_b1130_qdrant_apres_purge as original

    _purge_sabotee(vrai_qdrant, monkeypatch)
    try:
        await original.test_la_collection_existe_toujours_apres_la_purge(client, vrai_qdrant)
    except AssertionError:
        return
    pytest.fail(
        "purge sabotée (delete_collection neutralisé, aucun vecteur effacé) : "
        "test_la_collection_existe_toujours_apres_la_purge reste VERT"
    )


@pytest.mark.asyncio
async def test_temoin_avec_un_point_pose_le_sabotage_est_vu(client, vrai_qdrant, monkeypatch):
    """Témoin : la même assertion, précédée d'un point, voit le sabotage."""
    _poser_un_point(vrai_qdrant)
    _purge_sabotee(vrai_qdrant, monkeypatch)

    resp = await client.delete("/api/data/all?confirm=true")

    assert resp.status_code == 200, resp.text
    assert vrai_qdrant.client.count(settings.qdrant_collection).count == 1


@pytest.mark.asyncio
async def test_temoin_avec_un_point_pose_la_vraie_purge_efface(client, vrai_qdrant):
    _poser_un_point(vrai_qdrant)

    resp = await client.delete("/api/data/all?confirm=true")

    assert resp.status_code == 200, resp.text
    assert vrai_qdrant.client.count(settings.qdrant_collection).count == 0


def test_le_test_b1157_ne_laisse_rien_dans_le_dossier_de_donnees(tmp_path):
    donnees = tmp_path / "donnees-de-session"
    donnees.mkdir()
    (donnees / "THERESE.md").write_text("SENTINELLE : consignes réelles", encoding="utf-8")

    env = {**os.environ, "THERESE_DATA_DIR": str(donnees), "OLLAMA_BASE_URL": "http://127.0.0.1:1"}
    rendu = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_b1157_sauvegarde_ce_que_la_purge_efface.py",
         "-q", "-p", "no:cacheprovider"],
        cwd=RACINE, env=env, capture_output=True, text=True, timeout=240,
    )
    assert rendu.returncode == 0, rendu.stdout[-2000:] + rendu.stderr[-2000:]

    sentinelle = (donnees / "THERESE.md").read_text(encoding="utf-8")
    residus = sorted(
        str(p.relative_to(donnees)) for p in donnees.rglob("*")
        if p.is_file() and p.parts[len(donnees.parts)] in {"projects", "invoices", "commands"}
    )
    assert sentinelle == "SENTINELLE : consignes réelles" and not residus, (
        f"après test_b1157 : THERESE.md = {sentinelle!r} ; résidus = {residus}"
    )
