"""B-170 (P-004, décision de Ludo) : dès qu'un dossier de travail est choisi,
l'indexation reste dans les dossiers choisis (travail, synchronisés) et dans le
dossier de données de THÉRÈSE. Sans dossier choisi, rien ne borne encore."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


@pytest.fixture(autouse=True)
def _sans_encodage_ni_qdrant(monkeypatch):
    """Comme les tests voisins : l'indexation ne parle ni au modèle ni à Qdrant."""
    from app.services import indexation

    monkeypatch.setattr(indexation, "get_qdrant_service", lambda: AsyncMock())


@pytest.mark.asyncio
async def test_hors_des_dossiers_choisis_l_indexation_est_refusee(client, tmp_path):
    choisi = tmp_path / "choisi"
    choisi.mkdir()
    ailleurs = tmp_path / "ailleurs"
    ailleurs.mkdir()
    (ailleurs / "doc.txt").write_text("Texte hors périmètre", encoding="utf-8")
    (choisi / "doc.txt").write_text("Texte dans le dossier choisi", encoding="utf-8")

    reponse = await client.post("/api/config/working-directory", json={"path": str(choisi)})
    assert reponse.status_code == 200, reponse.text

    dehors = await client.post("/api/files/index", json={"path": str(ailleurs / "doc.txt")})
    assert dehors.status_code == 403, dehors.text
    assert "dossiers choisis" in dehors.text

    dedans = await client.post("/api/files/index", json={"path": str(choisi / "doc.txt")})
    assert dedans.status_code == 200, dedans.text


@pytest.mark.asyncio
async def test_sans_dossier_choisi_rien_ne_borne(client, tmp_path):
    (tmp_path / "doc.txt").write_text("Texte sans périmètre", encoding="utf-8")
    reponse = await client.post("/api/files/index", json={"path": str(tmp_path / "doc.txt")})
    assert reponse.status_code == 200, reponse.text
