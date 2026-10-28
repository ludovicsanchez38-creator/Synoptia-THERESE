"""Copie automatique de la base avant que le moteur l'ouvre (B-1341).

Chaque démarrage réécrit des données par conception (réparations idempotentes
d'init_db, migrations d'une nouvelle version). Avant cela, une copie de
therese.db, de son journal WAL et de .encryption_key part dans
``backups/auto/<horodatage>-v<version>/`` :

- quand la version change (une mise à jour vient d'être installée) ;
- ou quand la dernière copie a plus d'un jour.

Trois copies sont conservées. La copie se fait fichier par fichier AVANT toute
connexion : rien n'écrit la base à ce moment, l'ensemble base + WAL est donc
cohérent. Elle ne lève jamais : un démarrage ne doit pas échouer parce qu'une
copie de précaution n'a pas pu se faire.

Ces copies ne remplacent pas les sauvegardes manuelles (chiffrées par phrase
de passe, rangées où l'utilisateur veut) : elles vivent avec les données
qu'elles protègent et servent à revenir en arrière après un démarrage raté.
« Effacer toutes mes données » les emporte (purger_copies_auto).
"""

from __future__ import annotations

import logging
import os
import re
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

COPIES_CONSERVEES = 3
INTERVALLE = timedelta(days=1)
_FORMAT = "%Y%m%dT%H%M%SZ"
_NOM = re.compile(r"^(\d{8}T\d{6}Z)-v(.+)$")


def dossier_copies(dossier_donnees: Path) -> Path:
    return Path(dossier_donnees) / "backups" / "auto"


def _copies_existantes(auto: Path) -> list[tuple[datetime, str, Path]]:
    """Les copies reconnues, de la plus ancienne à la plus récente.

    Un dossier qui ne suit pas le motif n'est ni compté ni effacé.
    """
    if not auto.is_dir():
        return []
    trouvees = []
    for entree in auto.iterdir():
        correspondance = _NOM.match(entree.name)
        if not (entree.is_dir() and correspondance):
            continue
        try:
            quand = datetime.strptime(correspondance.group(1), _FORMAT).replace(tzinfo=UTC)
        except ValueError:
            continue
        trouvees.append((quand, correspondance.group(2), entree))
    return sorted(trouvees, key=lambda t: t[0])


def _copie_utile(auto: Path, version: str, maintenant: datetime) -> bool:
    existantes = _copies_existantes(auto)
    if not existantes:
        return True
    quand, version_precedente, _ = existantes[-1]
    return version_precedente != version or maintenant - quand >= INTERVALLE


def _elaguer(auto: Path) -> None:
    existantes = _copies_existantes(auto)
    for _, _, ancienne in existantes[:-COPIES_CONSERVEES]:
        shutil.rmtree(ancienne, ignore_errors=True)


def copier_avant_demarrage(
    dossier_donnees: Path,
    version: str,
    *,
    base: Path | None = None,
    maintenant: datetime | None = None,
) -> Path | None:
    """Copie la base si c'est utile ; rend le dossier de la copie, sinon None."""
    dossier_donnees = Path(dossier_donnees)
    base = Path(base) if base is not None else dossier_donnees / "therese.db"
    maintenant = maintenant or datetime.now(UTC)
    auto = dossier_copies(dossier_donnees)
    cible: Path | None = None
    try:
        if not base.is_file() or base.stat().st_size == 0:
            return None
        if not _copie_utile(auto, version, maintenant):
            return None

        # Noms fixes dans la copie : un chemin de base personnalisé se restaure
        # sous le nom attendu.
        paires = [
            (base, "therese.db"),
            (base.with_name(base.name + "-wal"), "therese.db-wal"),
            (dossier_donnees / ".encryption_key", ".encryption_key"),
        ]
        paires = [(s, nom) for s, nom in paires if s.is_file()]
        taille = sum(s.stat().st_size for s, _ in paires)
        auto.mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(auto).free < 2 * taille:
            logger.warning(
                "B-1341 : place insuffisante pour la copie automatique (%s octets à copier)", taille
            )
            return None

        nouvelle = auto / f"{maintenant.strftime(_FORMAT)}-v{version}"
        # Le nom n'est retenu qu'une fois le dossier créé par CE démarrage :
        # en cas de collision, le nettoyage d'échec ne doit pas effacer la
        # copie d'un autre.
        nouvelle.mkdir(mode=0o700)
        cible = nouvelle
        os.chmod(cible, 0o700)
        for source, nom in paires:
            destination = cible / nom
            shutil.copy2(source, destination)
            os.chmod(destination, 0o600)
        _elaguer(auto)
        logger.info("B-1341 : copie automatique de la base dans %s", cible.name)
        return cible
    except Exception:
        logger.exception("B-1341 : copie automatique impossible, démarrage poursuivi")
        if cible is not None:
            shutil.rmtree(cible, ignore_errors=True)
        return None


def purger_copies_auto(dossier_donnees: Path) -> None:
    """« Effacer toutes mes données » : les copies automatiques partent aussi."""
    for _, _, copie in _copies_existantes(dossier_copies(dossier_donnees)):
        shutil.rmtree(copie, ignore_errors=True)

    # Les abris de reprise contiennent eux aussi des données personnelles.
    # Ils ne sont jamais élagués automatiquement, seulement sur cet effacement.
    reprises = Path(dossier_donnees) / "backups" / "reprises"
    if reprises.is_dir() and not reprises.is_symlink():
        for abri in reprises.iterdir():
            if re.fullmatch(r"[0-9a-f]{32}", abri.name) and not abri.is_symlink():
                shutil.rmtree(abri, ignore_errors=True)
