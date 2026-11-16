"""Une extraction impossible reste un écart de synchronisation non réessayé."""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from app.models.database import get_session_context
from app.models.entities import FileMetadata
from app.models.entities_sync import EtatOperation, EtatPlan
from app.models.processing import EtatTache
from app.services import indexation, traitements
from app.services import project_sync_service as sync
from fastapi import HTTPException


class FauxIndex:
    def __init__(self):
        self.items = []
        self.retraits = []

    async def async_add_memories(self, items):
        self.items.extend(items)

    async def async_delete_by_entity(self, entity_id):
        self.retraits.append(entity_id)
        self.items = [item for item in self.items if item["entity_id"] != entity_id]


async def test_extraction_none_ecartee_du_plan_sans_rejouer_ni_effacer(
    client, tmp_path, monkeypatch
):
    racine = tmp_path / "projet"
    racine.mkdir()
    illisible = racine / "illisible.txt"
    illisible.write_text("ancienne version", encoding="utf-8")
    faux = FauxIndex()
    monkeypatch.setattr(indexation, "get_qdrant_service", lambda: faux)
    monkeypatch.setattr(indexation, "extract_text", lambda chemin: chemin.read_text(encoding="utf-8"))

    creation = await client.post("/api/memory/projects", json={"name": "Projet test"})
    assert creation.status_code in (200, 201)
    projet = creation.json()["id"]
    await sync.definir_racine(projet, str(racine))
    premier_plan = await sync.preparer_plan(projet)
    await sync.appliquer_plan(projet, premier_plan.id)
    ancien_ref = (await sync.lire_referentiel(projet))[str(illisible.resolve())]
    ancien_id = ancien_ref[0]
    anciens_items = list(faux.items)
    async with get_session_context() as session:
        ancienne_meta = await session.get(FileMetadata, ancien_id)
        anciens_compte_et_date = (ancienne_meta.chunk_count, ancienne_meta.indexed_at)

    illisible.write_text("version illisible", encoding="utf-8")
    lisible = racine / "lisible.txt"
    lisible.write_text("nouveau texte lisible", encoding="utf-8")
    plan = await sync.preparer_plan(projet)
    lectures = []

    def extraire(chemin):
        texte = chemin.read_text(encoding="utf-8")
        lectures.append(texte)
        return None if texte == "version illisible" else texte

    monkeypatch.setattr(indexation, "extract_text", extraire)
    await sync.appliquer_plan(projet, plan.id)

    operations = {Path(o.chemin).name: o for o in await sync.lire_operations(plan.id)}
    assert operations["illisible.txt"].etat == EtatOperation.OBSOLETE
    assert operations["illisible.txt"].erreur
    assert operations["illisible.txt"].attempt_count == 1
    assert operations["lisible.txt"].etat == EtatOperation.FAIT
    assert (await sync.lire_plan(plan.id)).etat == EtatPlan.APPLIQUE_PARTIEL
    run = await sync.lire_run(plan.id)
    assert run.state == EtatTache.DONE
    assert "partielle" in run.error and "1 fichier" in run.error
    referentiel = await sync.lire_referentiel(projet)
    assert referentiel[str(illisible.resolve())] == ancien_ref
    assert str(lisible.resolve()) in referentiel
    assert ancien_id not in faux.retraits
    assert [item for item in faux.items if item["entity_id"] == ancien_id] == anciens_items
    async with get_session_context() as session:
        meta = await session.get(FileMetadata, ancien_id)
        assert (meta.chunk_count, meta.indexed_at) == anciens_compte_et_date

    await sync.appliquer_plan(projet, plan.id)
    operation_reprise = next(
        o for o in await sync.lire_operations(plan.id) if o.chemin == str(illisible.resolve())
    )
    assert operation_reprise.etat == EtatOperation.OBSOLETE
    assert operation_reprise.attempt_count == 1
    assert lectures.count("version illisible") == 1
    assert ancien_id not in faux.retraits


async def test_extraction_none_est_un_signal_metier_sans_ecriture(db_session, tmp_path, monkeypatch):
    fichier = tmp_path / "illisible.txt"
    fichier.write_text("contenu", encoding="utf-8")
    ecrire = AsyncMock()
    monkeypatch.setattr(indexation, "extract_text", lambda _chemin: None)
    monkeypatch.setattr(indexation, "_ecrire_et_consigner", ecrire)

    with pytest.raises(indexation.ExtractionImpossible) as erreur:
        await indexation.index_payload(str(fichier))

    assert not isinstance(erreur.value, HTTPException)
    assert "Impossible d'extraire" in str(erreur.value)
    ecrire.assert_not_awaited()


async def test_extraction_none_du_nouveau_fichier_est_ecartee(client, tmp_path, monkeypatch):
    racine = tmp_path / "projet"
    racine.mkdir()
    (racine / "illisible.txt").write_text("contenu", encoding="utf-8")
    ecrire = AsyncMock()
    monkeypatch.setattr(indexation, "extract_text", lambda _chemin: None)
    monkeypatch.setattr(indexation, "_ecrire_et_consigner", ecrire)

    creation = await client.post("/api/memory/projects", json={"name": "Projet test"})
    assert creation.status_code in (200, 201)
    projet = creation.json()["id"]
    await sync.definir_racine(projet, str(racine))
    plan = await sync.preparer_plan(projet)
    await sync.appliquer_plan(projet, plan.id)

    operations = await sync.lire_operations(plan.id)
    assert len(operations) == 1
    assert operations[0].etat == EtatOperation.OBSOLETE
    assert operations[0].attempt_count == 1
    assert await sync.lire_referentiel(projet) == {}
    assert (await sync.lire_plan(plan.id)).etat == EtatPlan.APPLIQUE_PARTIEL
    assert (await sync.lire_run(plan.id)).state == EtatTache.DONE
    ecrire.assert_not_awaited()


@pytest.mark.parametrize("surface", ["index", "upload"])
async def test_extraction_none_est_traduite_en_422_par_les_routes(
    client, tmp_path, monkeypatch, surface
):
    fichier = tmp_path / "illisible.txt"
    fichier.write_text("contenu", encoding="utf-8")
    faux = FauxIndex()
    monkeypatch.setattr(indexation, "get_qdrant_service", lambda: faux)
    monkeypatch.setattr(indexation, "extract_text", lambda _chemin: None)

    if surface == "index":
        reponse = await client.post("/api/files/index", json={"path": str(fichier)})
    else:
        creation = await client.post("/api/memory/projects", json={"name": "Projet test"})
        assert creation.status_code in (200, 201)
        reponse = await client.post(
            "/api/files/upload",
            data={"project_id": creation.json()["id"]},
            files={"file": ("illisible.txt", b"contenu", "text/plain")},
        )

    assert reponse.status_code == 422
    assert "Impossible d'extraire" in reponse.json()["message"]
    assert faux.items == [] and faux.retraits == []
    lignes = [ligne for ligne in await traitements.lister() if ligne["type"] == "indexation"]
    assert len(lignes) == 1
    assert lignes[0]["state"] == EtatTache.FAILED
    assert "Impossible d'extraire" in lignes[0]["error"]
