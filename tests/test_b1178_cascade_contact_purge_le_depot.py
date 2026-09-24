"""B-1178 : la suppression en cascade d'un contact purge aussi le dépôt disque
`<data_dir>/projects/<id>/` de ses projets (jumeau de B-021).

Attendu (B-021, memory.py:182-199 et :1252-1257) : quand un dossier disparaît,
son dépôt THÉRÈSE part du disque après le commit. `delete_project` le fait ;
la cascade de `delete_contact` passe par le même `_nettoyer_et_supprimer_projet`
mais n'appelle jamais `_purger_le_depot_du_dossier`.
Chemin servi : MemoryPanel.tsx:330 appelle `deleteContactWithCascade(id, true)`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest


async def _contact_avec_projet_et_depot(db_session, tmp_path, monkeypatch):
    from app.config import settings
    from app.models.entities import Contact, FileMetadata, Project

    monkeypatch.setattr(settings, "data_dir", tmp_path / "therese-data")

    contact = Contact(id="contact-b1178", first_name="Alice", last_name="Martin")
    projet = Project(id="proj-b1178", name="Chantier Martin", contact_id=contact.id)
    db_session.add(contact)
    db_session.add(projet)

    depot = Path(settings.data_dir) / "projects" / projet.id / "files"
    depot.mkdir(parents=True, exist_ok=True)
    fichier = depot / "devis.md"
    fichier.write_text("# Devis confidentiel", encoding="utf-8")
    db_session.add(
        FileMetadata(
            path=str(fichier),
            name=fichier.name,
            extension=fichier.suffix,
            size=fichier.stat().st_size,
            scope="project",
            scope_id=projet.id,
            indexed_at=datetime.now(UTC),
        )
    )
    await db_session.commit()
    return contact, projet, fichier


@pytest.mark.asyncio
async def test_la_cascade_d_un_contact_purge_le_depot_disque_de_ses_projets(
    db_session, tmp_path, monkeypatch
):
    from app.routers import memory as routeur

    contact, projet, fichier = await _contact_avec_projet_et_depot(
        db_session, tmp_path, monkeypatch
    )

    reponse = await routeur.delete_contact(contact.id, cascade=True, session=db_session)

    assert reponse["deleted"] is True
    assert reponse["cascade_deleted"]["projects"] == 1, reponse["cascade_deleted"]
    assert reponse["cascade_deleted"]["files"] == 1, reponse["cascade_deleted"]
    assert not fichier.exists(), (
        f"projet supprimé par la cascade du contact, compteur files=1, mais le "
        f"fichier reste sur le disque : {fichier}"
    )
    assert not fichier.parent.parent.exists(), (
        f"le dépôt du projet survit : {fichier.parent.parent}"
    )


@pytest.mark.asyncio
async def test_temoin_supprimer_le_projet_seul_purge_bien_son_depot(
    db_session, tmp_path, monkeypatch
):
    """Témoin B-021 : la même donnée, supprimée par delete_project, part du disque."""
    from app.routers import memory as routeur

    _, projet, fichier = await _contact_avec_projet_et_depot(
        db_session, tmp_path, monkeypatch
    )

    await routeur.delete_project(projet.id, cascade=True, session=db_session)

    assert not fichier.exists()
    assert not fichier.parent.parent.exists()
