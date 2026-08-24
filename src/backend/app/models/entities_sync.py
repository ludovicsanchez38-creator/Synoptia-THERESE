"""Tables de project.sync (0.45) - design V2.1 du 24/08/2026.

Quatre tables NOUVELLES, zéro colonne ajoutée aux tables existantes :
`create_all()` crée les tables manquantes au démarrage packagé mais n'ajoute
jamais de colonne, et les clés étrangères SQLite ne sont pas activées par les
PRAGMA actuels - le ménage (suppression d'un projet, changement de racine)
est explicite, dans le service.

Autorité formalisée (challenge V2, finding 6) :
- `project_sync_entries` fait foi sur le DERNIER SNAPSHOT APPLIQUÉ - une
  entrée naît d'une opération d'apply réussie, jamais du rattachement seul ;
- `files` (FileMetadata) fait foi sur l'identité et le périmètre réellement
  indexés ;
- leur divergence transitoire après un crash est réparée par la reprise
  (opérations idempotentes, at-least-once).
"""
from datetime import UTC, datetime

from app.models.entities import generate_uuid
from sqlalchemy import Index, UniqueConstraint, text
from sqlmodel import Field, SQLModel


class EtatPlan:
    PROPOSE = "propose"
    EN_COURS = "en_cours"
    APPLIQUE = "applique"
    APPLIQUE_PARTIEL = "applique_partiel"
    CADUC = "caduc"


class EtatOperation:
    A_FAIRE = "a_faire"
    FAIT = "fait"
    ECHEC = "echec"  # réessayable dans le même plan (at-least-once)
    OBSOLETE = "obsolete"  # l'état du disque a dérivé depuis le plan


class TypeOperation:
    INDEXER = "indexer"
    REINDEXER = "reindexer"
    RETIRER = "retirer"
    CONFLIT = "conflit"  # chemin possédé par un autre périmètre : montré, jamais exécuté


class ProjectSyncRoot(SQLModel, table=True):
    """La racine locale d'un projet. Une seule, exclusive, jamais imbriquée."""

    __tablename__ = "project_sync_roots"
    __table_args__ = (
        # Passe 2 de revue : le verrou global du service ne protège qu'UN
        # processus. L'invariant durable est SQL : une racine active (non
        # détachée) n'appartient qu'à un seul projet - index unique PARTIEL,
        # compatible avec les tombeaux qui gardent leur dernier chemin.
        Index(
            "uq_sync_root_racine_active",
            "racine",
            unique=True,
            sqlite_where=text("detachee = 0"),
        ),
    )

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    project_id: str = Field(unique=True, index=True)
    # Chemin CANONIQUE (resolve). L'exclusivité (unicité, non-imbrication,
    # samefile) se vérifie dans la section critique du service, sous le
    # verrou global - PAS par une contrainte SQL : un tombeau (`detachee`)
    # conserve son dernier chemin pour l'audit, et une contrainte unique
    # empêcherait un autre projet de reprendre un dossier délié.
    racine: str
    # Identité du volume (st_dev) au rattachement : un montage débranché ne
    # doit JAMAIS produire un plan de retrait massif (fail-closed).
    volume_id: int
    # Incrémentée à chaque changement ou retrait de racine : les plans d'une
    # génération précédente deviennent caducs, les entrées sont nettoyées.
    # Elle ne repart JAMAIS à 1 : au retrait, la ligne devient un tombeau
    # (`detachee`) plutôt que d'être supprimée (revue jalon, B1).
    generation: int = Field(default=1)
    detachee: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProjectSyncEntry(SQLModel, table=True):
    """L'état de référence d'un fichier synchronisé - le dernier snapshot
    APPLIQUÉ. `content_hash` de `files` n'est alimenté nulle part : cette
    table est le seul référentiel exploitable pour détecter les changements."""

    __tablename__ = "project_sync_entries"
    __table_args__ = (
        UniqueConstraint("project_id", "chemin", name="uq_sync_entry_projet_chemin"),
    )

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    project_id: str = Field(index=True)
    chemin: str = Field(index=True)  # canonique ; unique PAR PROJET (service)
    file_id: str  # l'entité FileMetadata réellement indexée
    taille: int
    # Entier epoch en nanosecondes, jamais une date locale (FAT à granularité
    # 2 s et fuseaux : le challenge V2 documente les pièges).
    mtime_ns: int
    sha256: str  # empreinte VALIDÉE (stat avant/après le hash au scan)
    generation_racine: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SyncPlan(SQLModel, table=True):
    """Une photographie proposée. Seul le DERNIER plan `propose` s'applique ;
    créer un plan pendant un apply est refusé (verrou projet étendu)."""

    __tablename__ = "sync_plans"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    project_id: str = Field(index=True)
    generation_racine: int
    etat: str = Field(default=EtatPlan.PROPOSE, index=True)
    # Compteurs figés au moment du plan (l'affichage n'a pas à recompter).
    nb_indexer: int = 0
    nb_reindexer: int = 0
    nb_retirer: int = 0
    nb_conflits: int = 0
    nb_inchanges: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SyncOperation(SQLModel, table=True):
    """Une opération d'un plan. Jamais supprimée : c'est le journal.

    At-least-once : `a_faire` jusqu'au succès COMPLET (vecteurs écrits +
    métadonnée + entrée de référence), puis un commit court la marque `fait`.
    `echec` est réessayable dans le même plan ; `attempt_count` et
    `last_attempt_at` portent la trace des tentatives (pas d'historique
    détaillé par tentative - promesse MVP réduite, assumée)."""

    __tablename__ = "sync_operations"
    __table_args__ = (
        Index("ix_sync_operations_plan_etat", "plan_id", "etat"),
    )

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    plan_id: str = Field(index=True)
    type: str  # TypeOperation
    chemin: str
    # L'identité prévue au moment du plan : un chemin réindexé entre-temps
    # désigne une autre entité, que l'apply ne doit jamais retirer.
    file_id_prevu: str | None = None
    empreinte_prevue: str | None = None
    empreinte_reelle: str | None = None
    etat: str = Field(default=EtatOperation.A_FAIRE, index=True)
    erreur: str | None = None
    attempt_count: int = 0
    last_attempt_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
