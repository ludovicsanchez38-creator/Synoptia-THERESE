"""B-021 — « 3 fichiers supprimés », et les trois fichiers étaient toujours là.

02/09/2026, reproduction RB2-008. `DELETE /api/memory/projects/{id}` répond
`{"cascade_deleted": {"files": 3}}` et `GET /api/files/` ne rend plus rien,
mais les trois fichiers restent sur le disque, dans
`<data_dir>/projects/<id>/files/`. `_nettoyer_et_supprimer_projet` ne fait que
`session.delete(file)` : la ligne SQLite part, l'octet reste. Un compteur qui
s'appelle « cascade » promet plus qu'il ne tient.

CONTRAINTE qui commande tout le correctif : `FileMetadata.scope == "project"`
couvre AUSSI les fichiers indexés SUR PLACE depuis la racine de synchronisation
de l'utilisateur (`project_sync_service`). Effacer sans discernement tout ce
qui porte le périmètre du dossier détruirait ses propres documents. La purge
ne touche donc QUE le dossier de dépôt de THÉRÈSE,
`<data_dir>/projects/<id>/` — jamais un chemin hors de là.

La purge vient APRÈS le commit : un fichier effacé avant un commit qui échoue
laisserait une ligne promettant un contenu introuvable, exactement le faux
succès que la fonction dit refuser.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlmodel import select


async def _dossier_avec_deux_fichiers(db_session, tmp_path, monkeypatch):
    """Un dépôt THÉRÈSE (à purger) et un fichier de l'utilisateur (à épargner)."""
    from app.config import settings
    from app.models.entities import FileMetadata, Project

    monkeypatch.setattr(settings, "data_dir", tmp_path / "therese-data")

    projet = Project(id="proj-b021", name="Dossier B-021")
    db_session.add(projet)

    depot = Path(settings.data_dir) / "projects" / projet.id / "files"
    depot.mkdir(parents=True, exist_ok=True)
    fichier_depose = depot / "devis.md"
    fichier_depose.write_text("# Devis client", encoding="utf-8")

    ailleurs = tmp_path / "documents-de-l-utilisateur"
    ailleurs.mkdir(parents=True, exist_ok=True)
    fichier_sur_place = ailleurs / "notes-perso.md"
    fichier_sur_place.write_text("# Mes notes", encoding="utf-8")

    for chemin in (fichier_depose, fichier_sur_place):
        db_session.add(
            FileMetadata(
                path=str(chemin),
                name=chemin.name,
                extension=chemin.suffix,
                size=chemin.stat().st_size,
                scope="project",
                scope_id=projet.id,
                indexed_at=datetime.now(UTC),
            )
        )
    await db_session.commit()
    return projet, fichier_depose, fichier_sur_place


@pytest.mark.asyncio
async def test_supprimer_un_dossier_retire_ses_fichiers_du_disque(
    db_session, tmp_path, monkeypatch
):
    """Le défaut reproduit : le compteur disait 2, le disque en gardait 2."""
    from app.routers import memory as routeur

    projet, depose, _ = await _dossier_avec_deux_fichiers(
        db_session, tmp_path, monkeypatch
    )

    reponse = await routeur.delete_project(projet.id, cascade=True, session=db_session)

    assert reponse["deleted"] is True
    assert reponse["cascade_deleted"]["files"] == 2, reponse["cascade_deleted"]
    assert not depose.exists(), (
        f"la ligne SQLite est partie, le fichier reste : {depose} — le compteur "
        "« cascade » promet une suppression qui n'a pas eu lieu"
    )
    assert not depose.parent.parent.exists(), (
        f"le dossier de dépôt du projet survit à sa suppression : {depose.parent.parent}"
    )


@pytest.mark.asyncio
async def test_un_fichier_indexe_sur_place_n_est_jamais_efface(
    db_session, tmp_path, monkeypatch
):
    """Le garde-fou : les documents de l'utilisateur ne sont PAS à nous."""
    from app.routers import memory as routeur

    projet, _, sur_place = await _dossier_avec_deux_fichiers(
        db_session, tmp_path, monkeypatch
    )

    await routeur.delete_project(projet.id, cascade=True, session=db_session)

    assert sur_place.exists(), (
        f"un document de l'utilisateur, indexé sur place hors du dossier de "
        f"dépôt, a été effacé : {sur_place}"
    )
    assert sur_place.read_text(encoding="utf-8") == "# Mes notes"


@pytest.mark.asyncio
async def test_les_lignes_disparaissent_toujours(db_session, tmp_path, monkeypatch):
    """Verrou : fermer le trou disque ne doit rien changer au ménage en base."""
    from app.models.entities import FileMetadata, Project
    from app.routers import memory as routeur

    projet, _, _ = await _dossier_avec_deux_fichiers(db_session, tmp_path, monkeypatch)

    await routeur.delete_project(projet.id, cascade=True, session=db_session)

    restants = (
        await db_session.execute(
            select(FileMetadata).where(FileMetadata.scope_id == projet.id)
        )
    ).scalars().all()
    assert restants == [], restants
    assert (
        await db_session.execute(select(Project).where(Project.id == projet.id))
    ).scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_un_identifiant_porteur_de_separateur_ne_purge_rien(
    tmp_path, monkeypatch
):
    """`a/../b` se RÉSOUT dans la racine, sur le dépôt d'un autre dossier.

    Injoignable aujourd'hui — l'identifiant vient d'une ligne `Project` — mais
    `is_relative_to` seul ne l'attrape pas : il regarde le chemin résolu, qui
    est bien sous la racine. Le contrôle porte donc sur la FORME.
    """
    from app.config import settings
    from app.routers.memory import _purger_le_depot_du_dossier

    monkeypatch.setattr(settings, "data_dir", tmp_path / "therese-data")
    voisin = Path(settings.data_dir) / "projects" / "dossier-voisin"
    voisin.mkdir(parents=True, exist_ok=True)
    (voisin / "contrat.md").write_text("# Contrat du voisin", encoding="utf-8")

    for identifiant in ("proj-a/../dossier-voisin", "", "..", "../projects/dossier-voisin"):
        await _purger_le_depot_du_dossier(identifiant)
        assert voisin.exists(), (
            f"l'identifiant {identifiant!r} a fait sortir la purge de son dépôt"
        )
        assert (voisin / "contrat.md").exists()
