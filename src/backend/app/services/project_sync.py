"""Scanner et diff de project.sync - purs et fail-closed (0.45).

Le scan photographie une racine : chaque fichier indexable est hashé
SYSTÉMATIQUEMENT (le préfiltre taille+mtime a été retiré au challenge V2 -
hasher tout est plus simple et plus sûr ; taille et mtime_ns restent stockés
pour le diagnostic). Un stat avant/après la lecture écarte les fichiers en
cours d'écriture : on ne consigne jamais une empreinte dont on ne sait pas
ce qu'elle décrit.

Fail-closed : racine absente ou erreur de parcours lèvent `ErreurDeScan` -
un montage débranché ou un dossier illisible ne produisent JAMAIS un plan,
donc jamais un retrait massif. Les erreurs de parcours sont REMONTÉES,
pas ignorées.

Le diff est une fonction pure : scan + référentiel + propriétaires -> plan.
Un chemin possédé par un autre périmètre est un CONFLIT montré, jamais un
reclassement silencieux.
"""
import hashlib
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from app.services.path_security import INDEXABLE_EXTENSIONS
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

# Répertoires que personne ne veut indexer - et qui font exploser les scans.
REPERTOIRES_EXCLUS = {".git", "node_modules", "__pycache__", ".venv"}


class ErreurDeScan(Exception):
    """Le scan n'a pas pu produire une photographie fiable : pas de plan."""


@dataclass(frozen=True)
class EntreeScannee:
    chemin: str  # canonique
    taille: int
    mtime_ns: int
    sha256: str


@dataclass(frozen=True)
class OperationPrevue:
    chemin: str
    file_id_prevu: str | None = None
    empreinte_prevue: str | None = None


@dataclass
class Diff:
    indexer: list[OperationPrevue] = field(default_factory=list)
    reindexer: list[OperationPrevue] = field(default_factory=list)
    retirer: list[OperationPrevue] = field(default_factory=list)
    conflits: list[OperationPrevue] = field(default_factory=list)
    inchanges: int = 0


def _hacher(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def _scanner_sync(racine: Path) -> list[EntreeScannee]:
    racine = racine.resolve()
    if not racine.is_dir():
        raise ErreurDeScan(f"Racine introuvable ou illisible : {racine}")

    erreurs: list[str] = []

    def _sur_erreur(err: OSError) -> None:
        # Un scan partiel ferait conclure « disparu » à tort : tout se remonte.
        erreurs.append(f"{err.filename}: {err.strerror}")

    entrees: list[EntreeScannee] = []
    for dossier, sous_dossiers, fichiers in os.walk(racine, onerror=_sur_erreur):
        sous_dossiers[:] = [
            d for d in sous_dossiers
            if d not in REPERTOIRES_EXCLUS and not d.startswith(".")
        ]
        for nom in fichiers:
            if nom.startswith("."):
                continue
            chemin = Path(dossier) / nom
            if chemin.suffix.lower() not in INDEXABLE_EXTENSIONS:
                continue
            resolu = chemin.resolve()
            if not str(resolu).startswith(str(racine) + os.sep):
                # Lien symbolique qui sort de la racine : échappée refusée.
                logger.warning(
                    "Scan %s : %s pointe hors de la racine, ignoré", racine, chemin
                )
                continue
            try:
                avant = resolu.stat()
                empreinte = _hacher(resolu)
                apres = resolu.stat()
            except OSError as e:
                erreurs.append(f"{resolu}: {e}")
                continue
            if (avant.st_size, avant.st_mtime_ns) != (apres.st_size, apres.st_mtime_ns):
                # En cours d'écriture : on ne sait pas ce qu'on a hashé.
                logger.warning(
                    "Scan %s : %s a changé pendant la lecture, exclu du plan",
                    racine, resolu,
                )
                continue
            entrees.append(EntreeScannee(
                chemin=str(resolu),
                taille=apres.st_size,
                mtime_ns=apres.st_mtime_ns,
                sha256=empreinte,
            ))

    if erreurs:
        raise ErreurDeScan(
            "Parcours incomplet, aucun plan ne sera produit : " + " ; ".join(erreurs[:5])
        )
    return entrees


async def scanner_racine(racine: Path | str) -> list[EntreeScannee]:
    """Photographie la racine, hors boucle d'événements (hash = disque + CPU)."""
    return await run_in_threadpool(_scanner_sync, Path(racine))


def calculer_diff(
    scannees: list[EntreeScannee],
    referentiel: dict[str, tuple[str, str]],
    *,
    proprietaires: dict[str, tuple[str, str | None]],
) -> Diff:
    """Classe chaque chemin. Pur : aucune entrée-sortie.

    `referentiel` : chemin -> (file_id, sha256) du dernier snapshot appliqué
    (project_sync_entries). `proprietaires` : chemin -> (scope, scope_id) des
    fichiers déjà indexés par un AUTRE périmètre (files) - conflit montré,
    jamais exécuté.
    """
    diff = Diff()
    vus: set[str] = set()
    for entree in scannees:
        vus.add(entree.chemin)
        if entree.chemin in proprietaires:
            diff.conflits.append(OperationPrevue(chemin=entree.chemin))
            continue
        connu = referentiel.get(entree.chemin)
        if connu is None:
            diff.indexer.append(OperationPrevue(
                chemin=entree.chemin, empreinte_prevue=entree.sha256
            ))
        elif connu[1] != entree.sha256:
            diff.reindexer.append(OperationPrevue(
                chemin=entree.chemin, file_id_prevu=connu[0],
                empreinte_prevue=entree.sha256,
            ))
        else:
            diff.inchanges += 1
    for chemin, (file_id, sha) in referentiel.items():
        if chemin not in vus:
            diff.retirer.append(OperationPrevue(
                chemin=chemin, file_id_prevu=file_id, empreinte_prevue=sha
            ))
    return diff
