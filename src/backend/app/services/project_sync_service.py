"""Orchestration de project.sync : racine, plan, apply, reprise (0.45).

Design V2.1 challengé deux fois. Les règles qui structurent ce module :

- **verrou par projet étendu** : `plan`, `apply` et tout changement de racine
  passent par le même verrou - un plan ne peut pas devenir caduc pendant
  qu'un apply court sur lui ;
- **fail-closed** : un scan en erreur (racine absente, volume changé, parcours
  incomplet) ne produit AUCUN plan, donc jamais un retrait massif ;
- **at-least-once** : une opération n'est `fait` qu'après le succès COMPLET
  (vecteurs + métadonnée + entrée de référence), `a_faire` ET `echec` se
  rejouent, les gestes sont idempotents ;
- **l'état de référence naît des opérations réussies**, jamais du
  rattachement : `project_sync_entries` dit le dernier snapshot APPLIQUÉ,
  `files` dit l'identité et le périmètre réellement indexés ;
- **un `ProcessingTask` par run d'apply**, lié au plan par `entity_id` - et
  un récupérateur spécifique relance les plans `en_cours` orphelins, car
  `recuperer_taches_orphelines()` ne fait que marquer `interrupted`.
"""
import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from app.models.database import get_session_context
from app.models.entities import FileMetadata
from app.models.entities_sync import (
    EtatOperation,
    EtatPlan,
    ProjectSyncEntry,
    ProjectSyncRoot,
    SyncOperation,
    SyncPlan,
    TypeOperation,
)
from app.models.processing import EtatTache as EtatTacheTraitement
from app.models.processing import ProcessingTask
from app.services import indexation, retrait_index, task_registry
from app.services.project_sync import calculer_diff, scanner_racine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)


def _volume_id(chemin: Path) -> int:
    """Témoin d'identité du volume, borné à l'INTEGER signé de SQLite.

    BUG-172 (Windows) : `st_dev` y est le volume serial, un entier non
    signé qui peut dépasser 2^63-1 - le commit explosait en OverflowError.
    Conversion BIJECTIVE non signé -> signé 64 bits (complément à deux) :
    tous les bits sont conservés, deux volumes distincts restent distincts
    (P5-3), et la valeur tient dans l'INTEGER SQLite.
    """
    brut = chemin.stat().st_dev & 0xFFFF_FFFF_FFFF_FFFF
    return brut - 0x1_0000_0000_0000_0000 if brut > 0x7FFF_FFFF_FFFF_FFFF else brut


class ErreurRacine(Exception):
    """Racine invalide : inexistante, partagée ou imbriquée."""


class OperationRefusee(Exception):
    """Un apply court déjà, ou le plan n'est plus applicable."""


# Verrou global des racines (exclusivité et non-imbrication se vérifient dans
# la même section critique) et verrous par projet (plan/apply/racine).
_verrou_racines = asyncio.Lock()
_verrous_projet: dict[str, asyncio.Lock] = {}
# Références fortes des applies en cours : sans elles, le ramasse-miettes
# peut annuler une tâche de fond (leçon 0.43.4, indexation du profil).
_applies_en_cours: set["asyncio.Task[None]"] = set()


def _verrou(project_id: str) -> asyncio.Lock:
    return _verrous_projet.setdefault(project_id, asyncio.Lock())


@asynccontextmanager
async def _verrou_du_projet(project_id: str) -> "AsyncIterator[None]":
    verrou = _verrou(project_id)
    if verrou.locked():
        raise OperationRefusee(
            "Une synchronisation est déjà en cours sur ce projet."
        )
    async with verrou:
        yield


# ---------------------------------------------------------------------------
# Racine
# ---------------------------------------------------------------------------

def _resoudre_racine(chemin: str) -> Path:
    """Résolution et contrôle d'existence — travail DISQUE, jamais sur la boucle.

    D5 : sur Windows, avec un antivirus ou un volume réseau qui se réveille,
    `resolve()` et `is_dir()` prennent des secondes. Sur la boucle asyncio, ce
    sont TOUTES les requêtes de l'application qui attendent, et le client finit
    par abandonner au bout de ses trente secondes.
    """
    racine = Path(chemin).expanduser().resolve()
    if not racine.is_dir():
        raise ErreurRacine(f"Le dossier n'existe pas : {racine}")
    return racine


def _verifier_conflits(racine: Path, autres: list[str]) -> None:
    """Aucune racine ne doit en recouvrir une autre — travail DISQUE lui aussi.

    `exists()` et `samefile()` interrogent le système de fichiers une fois par
    racine déjà connue : sur un partage réseau injoignable, chacun peut durer.
    """
    for chemin_autre in autres:
        autre_racine = Path(chemin_autre)
        if autre_racine == racine:
            raise ErreurRacine("Cette racine appartient déjà à un autre projet.")
        if racine.is_relative_to(autre_racine) or autre_racine.is_relative_to(racine):
            raise ErreurRacine(
                f"Racine imbriquée avec celle d'un autre projet : {autre_racine}"
            )
        try:
            if autre_racine.exists() and racine.samefile(autre_racine):
                raise ErreurRacine(
                    "Cette racine désigne le même dossier qu'un autre projet."
                )
        except OSError:
            pass


async def definir_racine(project_id: str, chemin: str) -> ProjectSyncRoot:
    racine = await asyncio.to_thread(_resoudre_racine, chemin)

    # B1 (revue jalon) : la racine ne change JAMAIS pendant un plan ou un
    # apply - même verrou projet d'abord, puis le verrou global des racines.
    async with _verrou_du_projet(project_id), _verrou_racines, \
            get_session_context() as session:
        resultat = await session.execute(select(ProjectSyncRoot))
        existantes = list(resultat.scalars().all())

        # Les comparaisons touchent le disque : elles sortent de la boucle, et
        # la liste des chemins est prélevée avant pour n'y emporter que du texte.
        concurrentes = [
            autre.racine
            for autre in existantes
            if autre.project_id != project_id and not autre.detachee
        ]
        await asyncio.to_thread(_verifier_conflits, racine, concurrentes)
        # `_volume_id` fait un stat() : même raison, il sort de la boucle, et
        # une seule fois pour les deux branches ci-dessous.
        volume = await asyncio.to_thread(_volume_id, racine)

        actuelle = next(
            (r for r in existantes if r.project_id == project_id), None
        )
        if actuelle is None:
            root = ProjectSyncRoot(
                project_id=project_id,
                racine=str(racine),
                volume_id=volume,
            )
            session.add(root)
            await session.commit()
            await session.refresh(root)
            return root

        # D5 : réattacher le MÊME dossier encore actif est sans effet. Quand le
        # client abandonne au bout de ses trente secondes, le serveur poursuit
        # et pose la racine ; l'utilisateur relance, et cette relance
        # incrémentait la génération — invalidant en silence le plan qu'il
        # venait de préparer. Une racine déliée, elle, avance toujours : le
        # dossier a pu changer sans que personne ne l'observe.
        if actuelle.racine == str(racine) and not actuelle.detachee:
            return actuelle

        # Remplacement OU ré-attachement d'une racine déliée : la génération
        # ne repart JAMAIS - un ancien plan partiel de génération 1
        # redeviendrait compatible (revue jalon, B1).
        actuelle.racine = str(racine)
        actuelle.volume_id = volume
        actuelle.generation += 1
        actuelle.detachee = False
        await _invalider_generation(session, project_id)
        await session.commit()
        await session.refresh(actuelle)
        return actuelle


async def retirer_racine(project_id: str) -> None:
    """Délie la racine. Ne retire RIEN de l'index : ça, c'est un plan."""
    async with _verrou_du_projet(project_id), _verrou_racines, \
            get_session_context() as session:
        resultat = await session.execute(
            select(ProjectSyncRoot).where(
                ProjectSyncRoot.project_id == project_id
            )
        )
        root = resultat.scalar_one_or_none()
        if root is None or root.detachee:
            return
        # Tombeau, pas suppression : la génération survit à un retrait puis
        # rattachement (revue jalon, B1).
        root.detachee = True
        root.generation += 1
        await _invalider_generation(session, project_id)
        await session.commit()


async def _invalider_generation(session: AsyncSession, project_id: str) -> None:
    """Plans caducs et entrées purgées : l'ancienne génération est finie.
    Les FK SQLite ne sont pas activées - le ménage est explicite."""
    resultat = await session.execute(
        select(SyncPlan).where(
            SyncPlan.project_id == project_id,
            SyncPlan.etat.in_((EtatPlan.PROPOSE, EtatPlan.EN_COURS)),
        )
    )
    for plan in resultat.scalars():
        plan.etat = EtatPlan.CADUC
    resultat = await session.execute(
        select(ProjectSyncEntry).where(ProjectSyncEntry.project_id == project_id)
    )
    for entree in resultat.scalars():
        await session.delete(entree)


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

def _racine_encore_valide(racine: Path, volume_attendu: int) -> bool:
    """La racine est-elle toujours là, sur le même volume ? Travail DISQUE."""
    return racine.is_dir() and _volume_id(racine) == volume_attendu


async def preparer_plan(project_id: str) -> SyncPlan:
    async with _verrou_du_projet(project_id):
        root = await _racine_de(project_id)
        racine = Path(root.racine)
        # Contrôle DISQUE avant le scan : hors de la boucle, comme le scan
        # lui-même. Sur un volume réseau qui se réveille, ces deux appels
        # figeaient toute l'application avant même d'avoir commencé.
        racine_valide = await asyncio.to_thread(_racine_encore_valide, racine, root.volume_id)
        if not racine_valide:
            from app.services.project_sync import ErreurDeScan

            raise ErreurDeScan(
                "Racine introuvable ou volume changé : aucun plan ne sera "
                "produit (un montage débranché ne vide jamais un index)."
            )

        scan = await scanner_racine(racine)
        scannees = scan.entrees
        referentiel = await lire_referentiel(project_id)

        # Chemins possédés par un AUTRE périmètre voulu : conflit montré.
        proprietaires: dict[str, tuple[str, str | None]] = {}
        async with get_session_context() as session:
            chemins = [e.chemin for e in scannees]
            if chemins:
                resultat = await session.execute(
                    select(FileMetadata).where(FileMetadata.path.in_(chemins))
                )
                for meta in resultat.scalars():
                    if meta.scope_provisoire:
                        continue
                    if (meta.scope, meta.scope_id) != ("project", project_id):
                        proprietaires[meta.path] = (meta.scope, meta.scope_id)

        diff = calculer_diff(
            scannees, referentiel,
            proprietaires=proprietaires, instables=scan.instables,
        )

        async with get_session_context() as session:
            resultat = await session.execute(
                select(SyncPlan).where(
                    SyncPlan.project_id == project_id,
                    SyncPlan.etat == EtatPlan.PROPOSE,
                )
            )
            for ancien in resultat.scalars():
                ancien.etat = EtatPlan.CADUC

            plan = SyncPlan(
                project_id=project_id,
                generation_racine=root.generation,
                nb_indexer=len(diff.indexer),
                nb_reindexer=len(diff.reindexer),
                nb_retirer=len(diff.retirer),
                nb_conflits=len(diff.conflits),
                nb_inchanges=diff.inchanges,
            )
            session.add(plan)
            await session.flush()
            for type_op, operations in (
                (TypeOperation.INDEXER, diff.indexer),
                (TypeOperation.REINDEXER, diff.reindexer),
                (TypeOperation.RETIRER, diff.retirer),
                (TypeOperation.CONFLIT, diff.conflits),
            ):
                for op in operations:
                    session.add(SyncOperation(
                        plan_id=plan.id,
                        type=type_op,
                        chemin=op.chemin,
                        file_id_prevu=op.file_id_prevu,
                        empreinte_prevue=op.empreinte_prevue,
                    ))
            await session.commit()
            await session.refresh(plan)
            return plan


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------

async def appliquer_plan(project_id: str, plan_id: str) -> None:
    """Exécute le plan, opération par opération. Bloquant : la route passe
    par `reserver_apply` + `executer_reservation` pour répondre 202 APRÈS
    la validation, jamais avant."""
    async with _verrou_du_projet(project_id):
        await _appliquer_sous_verrou(project_id, plan_id)


class ReservationApply:
    """Un apply validé et verrouillé, pas encore exécuté.

    B3 (revue jalon) : le 202 couvrait un échec immédiat - la route testait
    `locked()` puis lançait une tâche qui validait APRÈS coup ; deux requêtes
    pouvaient aussi franchir le test avant la première acquisition. La
    réservation acquiert le verrou et valide AVANT que la route ne réponde ;
    l'exécution différée libère le verrou quoi qu'il arrive.
    """

    def __init__(self, project_id: str, plan_id: str) -> None:
        self.project_id = project_id
        self.plan_id = plan_id


async def reserver_apply(project_id: str, plan_id: str) -> ReservationApply:
    verrou = _verrou(project_id)
    if verrou.locked():
        raise OperationRefusee(
            "Une synchronisation est déjà en cours sur ce projet."
        )
    await verrou.acquire()
    try:
        await _valider_plan_applicable(project_id, plan_id)
    except BaseException:
        verrou.release()
        raise
    return ReservationApply(project_id, plan_id)


async def executer_reservation(reservation: ReservationApply) -> None:
    try:
        await _appliquer_sous_verrou(
            reservation.project_id, reservation.plan_id, deja_valide=True
        )
    finally:
        _verrou(reservation.project_id).release()


def lancer_apply_reserve(reservation: ReservationApply) -> "asyncio.Task[None]":
    """Exécution différée d'une réservation, référence forte conservée."""
    tache = asyncio.get_running_loop().create_task(
        executer_reservation(reservation)
    )
    _applies_en_cours.add(tache)
    tache.add_done_callback(_applies_en_cours.discard)
    return tache


async def _valider_plan_applicable(project_id: str, plan_id: str) -> ProjectSyncRoot:
    plan = await lire_plan(plan_id)
    if plan is None or plan.project_id != project_id:
        raise OperationRefusee("Plan inconnu pour ce projet.")
    if plan.etat not in (EtatPlan.PROPOSE, EtatPlan.EN_COURS, EtatPlan.APPLIQUE_PARTIEL):
        raise OperationRefusee(f"Ce plan n'est plus applicable ({plan.etat}).")
    root = await _racine_de(project_id)
    if plan.generation_racine != root.generation:
        raise OperationRefusee("La racine a changé depuis ce plan : refais un plan.")
    # Seul le DERNIER plan proposé s'applique - un plan en_cours (reprise)
    # reste prioritaire et aucun nouveau plan ne peut naître pendant l'apply
    # (même verrou).
    async with get_session_context() as session:
        resultat = await session.execute(
            select(SyncPlan).where(
                SyncPlan.project_id == project_id,
                SyncPlan.etat == EtatPlan.PROPOSE,
                SyncPlan.created_at > plan.created_at,
            )
        )
        if resultat.scalars().first() is not None:
            raise OperationRefusee("Un plan plus récent existe : applique-le, lui.")
    return root


async def _appliquer_sous_verrou(
    project_id: str, plan_id: str, *, deja_valide: bool = False
) -> None:
    from app.services import traitements

    root = await _valider_plan_applicable(project_id, plan_id)

    await _marquer_plan(plan_id, EtatPlan.EN_COURS)
    # 0.46 : le run est un TraitementHandle - banc d'essai du patron
    # (finding 5 : sans try/finally, une exception hors boucle laissait la
    # ligne `running` fantôme jusqu'au prochain redémarrage).
    handle = await traitements.creer_traitement(
        type="project_sync",
        label=f"Synchronisation de {Path(root.racine).name}",
        project_id=project_id,
        entity_id=plan_id,
    )

    interrompu = False
    # 0.47 : l'arrêt coupe aussi l'opération EN VOL, plus seulement entre
    # deux opérations - le cœur d'indexation consulte ce drapeau à ses
    # points d'abandon et lève IndexationAbandonnee avant toute écriture.
    arret = asyncio.Event()

    async def _abandonnee() -> bool:
        return arret.is_set()

    try:
        await handle.demarrer()
        await handle.lier_adaptateur(
            task_registry.AnnulationCooperative(poser_drapeau=arret.set)
        )
        operations = [
            o for o in await lire_operations(plan_id)
            if o.etat in (EtatOperation.A_FAIRE, EtatOperation.ECHEC)
            and o.type != TypeOperation.CONFLIT
        ]
        faites = 0
        echecs = 0
        for operation in operations:
            if arret.is_set() or await handle.annulation_demandee():
                # Ce qui est fait reste fait ; le reste attend un nouvel
                # apply. Le producteur pose cancelled APRÈS sa sortie réelle.
                interrompu = True
                break
            try:
                await _executer_operation(
                    project_id, root, operation, est_abandonnee=_abandonnee
                )
                faites += 1
            except indexation.IndexationAbandonnee:
                # L'utilisateur a demandé l'arrêt pendant CETTE opération :
                # rien n'a été écrit, elle reste à_faire - pas un échec.
                interrompu = True
                break
            except Exception as e:  # l'échec d'une opération n'arrête pas le plan
                echecs += 1
                await _consigner_operation(
                    operation.id, EtatOperation.ECHEC, erreur=str(e)[:500]
                )
                logger.warning(
                    "Opération sync en échec (%s): %s", operation.chemin, e
                )
            await handle.progresser(
                progress=(faites + echecs) / max(len(operations), 1)
            )
        # Revue jalon (F3) : les lectures finales et _finaliser_plan vivaient
        # HORS du try - une panne à cet endroit laissait la ligne running.
        finales = [
            o for o in await lire_operations(plan_id)
            if o.type != TypeOperation.CONFLIT
        ]
        tout_est_fait = all(o.etat == EtatOperation.FAIT for o in finales)
        plan_final = await lire_plan(plan_id)
        conflits = (plan_final.nb_conflits if plan_final else 0) or 0
        etat_final = (
            EtatPlan.APPLIQUE if tout_est_fait and not conflits
            else EtatPlan.APPLIQUE_PARTIEL
        )
        restantes = [o for o in finales if o.etat == EtatOperation.ECHEC]
        await _finaliser_plan(plan_id, etat_final)
        if interrompu:
            await handle.terminer(EtatTacheTraitement.CANCELLED)
        elif restantes:
            await handle.terminer(
                EtatTacheTraitement.FAILED,
                error=f"{len(restantes)} opération(s) en échec, réessayables",
            )
        else:
            await handle.terminer(EtatTacheTraitement.DONE)
    except asyncio.CancelledError:
        # Shutdown ou annulation de la tâche de fond : c'est un ARRÊT, pas
        # une panne inventée (revue jalon, F3). Le plan reste en_cours, la
        # reprise du prochain démarrage termine le travail.
        await handle.terminer(EtatTacheTraitement.CANCELLED)
        raise
    except BaseException as e:
        await handle.terminer(EtatTacheTraitement.FAILED, error=str(e)[:200])
        raise




async def _executer_operation(
    project_id: str,
    root: ProjectSyncRoot,
    operation: SyncOperation,
    est_abandonnee: Callable[[], Awaitable[bool]] | None = None,
) -> None:
    if operation.type == TypeOperation.RETIRER:
        # B2 (revue jalon) : revalider le DISQUE - un fichier revenu entre le
        # plan et l'apply ne doit JAMAIS être retiré.
        if Path(operation.chemin).exists():
            await _consigner_operation(
                operation.id, EtatOperation.OBSOLETE,
                erreur="Le fichier est réapparu depuis le plan : refais un plan.",
            )
            return
        resultat = await retrait_index.retirer_par_chemin(
            operation.chemin, file_id_attendu=operation.file_id_prevu
        )
        if resultat.conflit:
            await _consigner_operation(
                operation.id, EtatOperation.OBSOLETE,
                erreur="Le chemin a changé d'identité depuis le plan.",
            )
            return
        await _supprimer_entree(project_id, operation.chemin)
        await _consigner_operation(operation.id, EtatOperation.FAIT)
        return

    # indexer / reindexer : les attendus se vérifient dans le cœur, sous le
    # verrou du chemin, avant toute écriture.
    try:
        reponse = await indexation.index_payload(
            operation.chemin,
            est_abandonnee=est_abandonnee,
            scope="project",
            scope_id=project_id,
            sha256_attendu=operation.empreinte_prevue,
            file_id_attendu=operation.file_id_prevu,
        )
    except indexation.ContenuModifieDepuisLePlan:
        await _consigner_operation(
            operation.id, EtatOperation.OBSOLETE,
            erreur="Le contenu a changé depuis le plan : refais un plan.",
        )
        return
    except indexation.ConflitDePerimetre as e:
        await _consigner_operation(
            operation.id, EtatOperation.OBSOLETE, erreur=str(e)[:500]
        )
        return
    except Exception as e:
        # HTTPException 404 = fichier disparu depuis le plan : obsolète aussi.
        from fastapi import HTTPException

        if isinstance(e, HTTPException) and e.status_code == 404:
            await _consigner_operation(
                operation.id, EtatOperation.OBSOLETE,
                erreur="Le fichier a disparu depuis le plan.",
            )
            return
        raise

    if (reponse.scope, reponse.scope_id) != ("project", project_id):
        await _consigner_operation(
            operation.id, EtatOperation.OBSOLETE,
            erreur=f"Le périmètre effectif est {reponse.scope}/{reponse.scope_id}.",
        )
        return

    await _etablir_entree(project_id, root, operation, reponse.id)
    etat, cause = etat_pour_une_indexation(getattr(reponse, "chunk_count", 0))
    await _consigner_operation(
        operation.id, etat,
        empreinte_reelle=operation.empreinte_prevue,
        erreur=cause,
    )


def etat_pour_une_indexation(chunk_count: int) -> tuple[EtatOperation, str | None]:
    """L'etat a consigner apres une indexation, selon ce qu'elle a REELLEMENT produit.

    0.56, finding d'Aude (campagne cinq personas) : le journal consignait FAIT
    des que `index_payload` ne levait pas. Les trois fichiers du dossier
    Vermeer etaient donc « faits » avec `chunk_count: 0`, et `search_files`
    rendait `found: false` sur leur nom exact.

    On ne touche PAS au filtre `chunk_count > 0` du catalogue : un fichier sans
    chunk n'est pas lisible, le cacher est honnete. C'est le JOURNAL qui
    mentait - il disait « fait » pour un fichier que le catalogue allait
    refuser.
    """
    if chunk_count > 0:
        return EtatOperation.FAIT, None
    return (
        EtatOperation.OBSOLETE,
        "Fichier enregistre mais AUCUN chunk indexe : il n'apparaitra pas dans "
        "les recherches. Format non extractible, fichier vide ou protege ?",
    )


# ---------------------------------------------------------------------------
# Reprise des applies orphelins (après un crash ou une fermeture)
# ---------------------------------------------------------------------------

async def reprendre_applies_orphelins() -> int:
    """Relance les plans restés `en_cours` sans exécution vivante.

    `recuperer_taches_orphelines()` marque les ProcessingTask `interrupted`
    mais ne relance RIEN - challenge V2.1, correction 3. À appeler APRÈS
    l'initialisation de Qdrant.
    """
    async with get_session_context() as session:
        resultat = await session.execute(
            select(SyncPlan).where(SyncPlan.etat == EtatPlan.EN_COURS)
        )
        orphelins = list(resultat.scalars().all())

    repris = 0
    for plan in orphelins:
        try:
            await appliquer_plan(plan.project_id, plan.id)
            repris += 1
        except Exception:
            logger.warning(
                "Reprise du plan %s impossible", plan.id, exc_info=True
            )
    return repris


# ---------------------------------------------------------------------------
# Lectures et écritures unitaires (transactions courtes)
# ---------------------------------------------------------------------------

async def _racine_de(project_id: str) -> ProjectSyncRoot:
    async with get_session_context() as session:
        resultat = await session.execute(
            select(ProjectSyncRoot).where(ProjectSyncRoot.project_id == project_id)
        )
        root = resultat.scalar_one_or_none()
    if root is None or root.detachee:
        raise ErreurRacine("Ce projet n'a pas de dossier synchronisé.")
    return root


async def lire_plan(plan_id: str) -> SyncPlan | None:
    async with get_session_context() as session:
        resultat = await session.execute(
            select(SyncPlan).where(SyncPlan.id == plan_id)
        )
        return resultat.scalar_one_or_none()


async def lire_operations(plan_id: str) -> list[SyncOperation]:
    async with get_session_context() as session:
        resultat = await session.execute(
            select(SyncOperation).where(SyncOperation.plan_id == plan_id)
        )
        return list(resultat.scalars().all())


async def lire_referentiel(project_id: str) -> dict[str, tuple[str, str]]:
    """chemin -> (file_id, sha256) du dernier snapshot appliqué."""
    async with get_session_context() as session:
        resultat = await session.execute(
            select(ProjectSyncEntry).where(
                ProjectSyncEntry.project_id == project_id
            )
        )
        return {
            e.chemin: (e.file_id, e.sha256) for e in resultat.scalars()
        }


async def etat_sync(project_id: str) -> dict[str, object]:
    async with get_session_context() as session:
        resultat = await session.execute(
            select(ProjectSyncRoot).where(ProjectSyncRoot.project_id == project_id)
        )
        root = resultat.scalar_one_or_none()
        if root is not None and root.detachee:
            root = None
        resultat = await session.execute(
            select(SyncPlan)
            .where(SyncPlan.project_id == project_id)
            .where(SyncPlan.etat != EtatPlan.CADUC)
            .order_by(SyncPlan.created_at.desc())
            .limit(1)
        )
        plan = resultat.scalars().first()
    return {
        "racine": root.racine if root else None,
        "generation": root.generation if root else None,
        "dernier_plan": plan,
    }


async def _finaliser_plan(plan_id: str, etat: str) -> None:
    """Écrit l'état FINAL d'un apply, seulement si le plan est encore à lui.

    Revue jalon (B1) : un changement de racine pendant l'apply passait le
    plan à `caduc`, puis la fin de l'apply le réécrivait `applique` - et les
    entrées de l'ancienne génération renaissaient. Un plan qui n'est plus
    `en_cours` n'appartient plus à ce run.
    """
    async with get_session_context() as session:
        resultat = await session.execute(
            select(SyncPlan).where(SyncPlan.id == plan_id)
        )
        plan = resultat.scalar_one_or_none()
        if plan is not None and plan.etat == EtatPlan.EN_COURS:
            plan.etat = etat
            await session.commit()


async def lire_run(plan_id: str) -> ProcessingTask | None:
    """Le dernier run d'apply d'un plan - c'est lui qui porte la progression."""
    async with get_session_context() as session:
        resultat = await session.execute(
            select(ProcessingTask)
            .where(
                ProcessingTask.type == "project_sync",
                ProcessingTask.entity_id == plan_id,
            )
            .order_by(ProcessingTask.created_at.desc())
            .limit(1)
        )
        return resultat.scalars().first()


async def lire_journal(project_id: str) -> list[SyncOperation]:
    """Toutes les opérations du projet, tous plans confondus - l'HISTORIQUE,
    pas seulement le dernier plan (revue jalon, B7)."""
    async with get_session_context() as session:
        resultat = await session.execute(
            select(SyncPlan.id).where(SyncPlan.project_id == project_id)
        )
        plan_ids = [r for r in resultat.scalars().all()]
        if not plan_ids:
            return []
        resultat = await session.execute(
            select(SyncOperation).where(SyncOperation.plan_id.in_(plan_ids))
        )
        operations = list(resultat.scalars().all())
    operations.sort(
        key=lambda o: (o.last_attempt_at or o.created_at), reverse=True
    )
    return operations


async def _marquer_plan(plan_id: str, etat: str) -> None:
    async with get_session_context() as session:
        resultat = await session.execute(
            select(SyncPlan).where(SyncPlan.id == plan_id)
        )
        plan = resultat.scalar_one_or_none()
        if plan is not None:
            plan.etat = etat
            await session.commit()


async def _consigner_operation(
    operation_id: str, etat: str, *, erreur: str | None = None,
    empreinte_reelle: str | None = None,
) -> None:
    async with get_session_context() as session:
        resultat = await session.execute(
            select(SyncOperation).where(SyncOperation.id == operation_id)
        )
        operation = resultat.scalar_one_or_none()
        if operation is None:
            return
        operation.etat = etat
        operation.erreur = erreur
        if empreinte_reelle is not None:
            operation.empreinte_reelle = empreinte_reelle
        operation.attempt_count += 1
        operation.last_attempt_at = datetime.now(UTC)
        await session.commit()


async def _etablir_entree(
    project_id: str, root: ProjectSyncRoot, operation: SyncOperation, file_id: str
) -> None:
    try:
        stat = Path(operation.chemin).stat()
        taille, mtime_ns = stat.st_size, stat.st_mtime_ns
    except OSError:
        taille, mtime_ns = 0, 0
    async with get_session_context() as session:
        resultat = await session.execute(
            select(ProjectSyncEntry).where(
                ProjectSyncEntry.project_id == project_id,
                ProjectSyncEntry.chemin == operation.chemin,
            )
        )
        entree = resultat.scalar_one_or_none()
        if entree is None:
            entree = ProjectSyncEntry(
                project_id=project_id,
                chemin=operation.chemin,
                file_id=file_id,
                taille=taille,
                mtime_ns=mtime_ns,
                sha256=operation.empreinte_prevue or "",
                generation_racine=root.generation,
            )
            session.add(entree)
        else:
            entree.file_id = file_id
            entree.taille = taille
            entree.mtime_ns = mtime_ns
            entree.sha256 = operation.empreinte_prevue or ""
            entree.generation_racine = root.generation
            entree.updated_at = datetime.now(UTC)
        await session.commit()


async def _supprimer_entree(project_id: str, chemin: str) -> None:
    async with get_session_context() as session:
        resultat = await session.execute(
            select(ProjectSyncEntry).where(
                ProjectSyncEntry.project_id == project_id,
                ProjectSyncEntry.chemin == chemin,
            )
        )
        entree = resultat.scalar_one_or_none()
        if entree is not None:
            await session.delete(entree)
            await session.commit()


