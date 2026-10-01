"""
THÉRÈSE v2 - Invoices Router

REST API pour la gestion de facturation.
Phase 4 - Invoicing
"""

import logging
import re
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from app.models.database import get_session
from app.models.entities import Contact, Invoice, InvoiceLine, Preference
from app.models.schemas import (
    ConvertDevisRequest,
    CreateInvoiceRequest,
    InvoiceLineRequest,
    InvoiceLineResponse,
    InvoiceResponse,
    MarkPaidRequest,
    UpdateInvoiceRequest,
)
from app.services.civil_time import date_civile_paris
from app.services.error_handler import message_pour_ecran
from app.services.invoice_pdf import InvoicePDFGenerator
from app.services.invoice_status import statut_effectif_facture
from app.services.user_profile import get_cached_profile
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

logger = logging.getLogger(__name__)

router = APIRouter(tags=["invoices"])

# B-160 : nombre de numéros essayés avant de rendre la main (409). Large
# devant le nombre de créations qu'un poste unique lance en parallèle.
_REPRISES_DE_NUMERO = 10


async def _get_invoice_output_dir(session: AsyncSession) -> str:
    """Résout le répertoire de sortie des PDFs factures (dossier de travail ou défaut).

    Priorité : dossier de travail configuré + sous-dossier 'factures'.
    Fallback : {data_dir}/invoices (suit THERESE_DATA_DIR).
    """
    import os
    from pathlib import Path

    from app.config import settings

    result = await session.execute(
        select(Preference).where(Preference.key == "working_directory")
    )
    pref = result.scalar_one_or_none()
    if pref and pref.value:
        output_dir = os.path.join(pref.value, "factures")
        logger.info("Répertoire factures résolu depuis les préférences : %s", output_dir)
        return output_dir
    # Finding 9 (30/08) : le fallback ignorait THERESE_DATA_DIR et écrivait
    # toujours dans ~/.therese/invoices, y compris pour un second profil.
    fallback = str(Path(settings.data_dir) / "invoices")
    logger.info("Répertoire factures : aucun dossier de travail configuré, fallback %s", fallback)
    return fallback


async def _verrouiller_emission(session: AsyncSession) -> None:
    """B-1746 : réserve l'écriture SQLite avant la première lecture de la pièce.

    PUT et mark-paid doivent lire l'état issu du commit précédent, même dans
    deux processus. La contrainte unique ne protège pas deux UPDATE de la même
    ligne. Un verrou pris après lecture laisserait les dates et le booléen de
    première émission calculés sur une instance périmée. Le commit/rollback
    de la session libère cette réservation ; busy_timeout borne l'attente.
    """
    try:
        await session.execute(text("BEGIN IMMEDIATE"))
    except OperationalError as erreur:
        if "database is locked" not in str(erreur.orig).casefold():
            raise
        raise HTTPException(
            status_code=409,
            detail="La base de facturation est occupée. Réessaie dans quelques secondes.",
        ) from erreur


async def _get_invoice_with_lines(session: AsyncSession, invoice_id: str) -> Invoice | None:
    """Load an invoice with its lines eagerly loaded (async-safe)."""
    statement = (
        select(Invoice)
        .where(Invoice.id == invoice_id)
        .options(selectinload(Invoice.lines), selectinload(Invoice.contact))
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def _generate_invoice_number(
    session: AsyncSession, document_type: str = "facture", *, emission: datetime | None = None,
) -> str:
    """
    Génère le prochain numéro de document.

    Format selon le type :
    - devis : DEV-YYYY-NNN
    - facture et avoir : FACT-YYYY-NNN, séquence commune à l'émission

    B-159 (02/09/2026) : le rang se compare en NOMBRE, pas en texte.
    `invoice_number` est une colonne texte, et `MAX()` y range
    « DEV-2026-1000 » AVANT « DEV-2026-999 ». Passé le millième document de
    l'année, le maximum restait donc bloqué sur 999, le numéro calculé valait
    toujours 1000 — déjà pris — et la création tombait en erreur
    définitivement. Les suffixes sont désormais relus et comparés en entier.

    Ce numéro reste une LECTURE : deux requêtes simultanées peuvent calculer
    le même (B-160). C'est l'insertion qui tranche, par la contrainte
    d'unicité et la reprise de `create_invoice`.
    """
    prefix_map = {
        "devis": "DEV",
        "facture": "FACT",
        "avoir": "FACT",
    }
    prefix = prefix_map.get(document_type, "FACT")
    # B-1757 : l'année et la date imprimée viennent du même instant, même
    # lorsqu'une première émission traverse minuit le 31 décembre.
    current_year = (emission if emission is not None else datetime.now(UTC)).year

    statement = select(Invoice.invoice_number).where(
        Invoice.invoice_number.like(f"{prefix}-{current_year}-%")
    )
    result = await session.execute(statement)

    next_number = 1
    for numero in result.scalars().all():
        try:
            rang = int(numero.rsplit("-", 1)[-1])
        except (ValueError, AttributeError):
            # Numéro d'une autre convention (import, saisie manuelle) : ignoré
            # plutôt que de faire échouer toute la série.
            continue
        next_number = max(next_number, rang + 1)

    return f"{prefix}-{current_year}-{next_number:03d}"


async def _inserer_avec_numero_frais(
    session: AsyncSession,
    document_type: str,
    fabrique: Callable[[str], Invoice],
) -> Invoice:
    """Lit un numéro, insère la pièce, et reprend avec un numéro frais si un
    concurrent a pris celui-ci entre la lecture et l'insertion.

    B-160 (02/09/2026) : le numéro se LIT puis s'INSÈRE, sans transaction
    verrouillante entre les deux. Huit créations simultanées lisaient le même
    maximum, calculaient le même numéro, et six sur huit finissaient en 500
    « erreur inattendue » sur la contrainte d'unicité. La lecture ne peut pas
    trancher ; l'insertion, elle, tranche pour de bon.

    B-338 (05/09/2026) : cette reprise vivait dans `create_invoice` seulement.
    La conversion de type et la conversion d'un devis en facture inséraient
    sans reprise, et rendaient 500 sur le même défaut. Les trois chemins
    passent ici. `fabrique` ne doit lire que des valeurs déjà en mémoire : le
    rollback d'une reprise expire les objets chargés, et une session async
    interdit de les recharger paresseusement.
    """
    for _ in range(_REPRISES_DE_NUMERO):
        invoice_number = await _generate_invoice_number(session, document_type)
        candidat = fabrique(invoice_number)
        session.add(candidat)
        try:
            await session.flush()  # Pour avoir l'ID de la pièce
        except IntegrityError as collision:
            await session.rollback()
            if "invoice_number" not in str(collision.orig):
                # Une autre contrainte : ce n'est pas la course au numéro, et
                # la reprise n'y changerait rien.
                raise
            logger.warning("Numéro %s pris par un concurrent, reprise", invoice_number)
            continue
        return candidat

    raise HTTPException(
        status_code=409,
        detail="Numérotation occupée par d'autres créations simultanées, réessaie.",
    )


# B-1615 : ces statuts quittent le brouillon et émettent la pièce. `cancelled`
# ne le fait pas : un brouillon annulé ne consomme pas de numéro.
_STATUTS_QUI_EMETTENT = frozenset({"sent", "paid", "overdue"})


def _jeton_provisoire() -> str:
    """Hors série FACT. La colonne est NOT NULL et unique."""
    return f"PROV-{uuid.uuid4().hex}"


def _numero_provisoire(numero: str) -> bool:
    return numero.startswith("PROV-")


async def _inserer_piece(
    session: AsyncSession,
    document_type: str,
    fabrique: Callable[[str], Invoice],
) -> Invoice:
    """Devis : numéro DEV dès la création. Facture et avoir : jeton PROV.

    Le 7° du I de l'article 242 nonies A et le § 90 du
    BOI-TVA-DECLA-30-20-20-10 numérotent la facture au fur et à mesure de
    l'émission. Supprimer un brouillon ne doit pas retirer un numéro de la
    série. Ces textes ne visent pas le devis.
    """
    if document_type == "devis":
        return await _inserer_avec_numero_frais(session, document_type, fabrique)

    for _ in range(_REPRISES_DE_NUMERO):
        jeton = _jeton_provisoire()
        candidat = fabrique(jeton)
        session.add(candidat)
        try:
            await session.flush()
        except IntegrityError as collision:
            await session.rollback()
            if "invoice_number" not in str(collision.orig):
                raise
            logger.warning("Jeton %s déjà pris, reprise", jeton)
            continue
        return candidat

    raise HTTPException(
        status_code=409,
        detail="Numérotation occupée par d'autres créations simultanées, réessaie.",
    )


def _rang_de_numero(numero: str) -> int | None:
    try:
        return int(numero.rsplit("-", 1)[-1])
    except (ValueError, AttributeError):
        return None


async def _est_le_dernier_de_sa_serie(session: AsyncSession, numero: str) -> bool:
    """Vrai si ce numéro est le plus haut de son préfixe et de son année.

    Une convention illisible est laissée en place : on ne la renumérote pas.
    """
    morceaux = numero.split("-")
    rang = _rang_de_numero(numero)
    if rang is None or len(morceaux) < 3:
        return True
    prefixe = "-".join(morceaux[:-1])
    statement = select(Invoice.invoice_number).where(Invoice.invoice_number.like(f"{prefixe}-%"))
    maximum = rang
    for autre in (await session.execute(statement)).scalars().all():
        autre_rang = _rang_de_numero(autre)
        if autre_rang is not None:
            maximum = max(maximum, autre_rang)
    return rang == maximum


def _numero_de_la_serie_courante(numero: str, emission: datetime) -> bool:
    """Seul un FACT de l'année d'émission peut conserver son rang au brouillon.

    P160 : les anciens AV et les conventions importées ne sont plus prolongés.
    Une pièce déjà émise reste conservée avant que cette règle soit consultée.
    """
    reconnu = re.fullmatch(rf"FACT-{emission.year}-([0-9]+)", numero)
    if reconnu is None:
        return False
    rang = int(reconnu.group(1))
    return rang > 0 and reconnu.group(1) == f"{rang:03d}"


async def _attribuer_numero_definitif(
    session: AsyncSession,
    invoice: Invoice,
    nouveau_statut: str | None,
    *, emission: datetime | None = None,
) -> Invoice:
    """Pose un FACT commun aux factures et avoirs à la première émission.

    Un brouillon annulé n'est plus « draft », mais son jeton PROV- n'a jamais
    été émis : cette première sortie le numérote. Un brouillon qui porte déjà
    un numéro définitif hérité le garde s'il est un FACT de l'année courante,
    encore dernier de sa série. Sinon il en reçoit un nouveau, à la suite : l'émettre tel quel
    après un numéro plus haut casserait l'ordre du § 90. L'ancien numéro,
    inférieur au maximum, n'est pas réattribué.

    Appelé avant les autres écritures. Une collision annule seulement son
    SAVEPOINT, pour conserver la réservation SQLite jusqu’au commit final.
    Le numéro proposé est journalisé avant le flush, parce que l'objet expire
    si l'insertion est refusée.
    """
    if nouveau_statut is None or nouveau_statut not in _STATUTS_QUI_EMETTENT:
        return invoice
    if invoice.document_type not in ("facture", "avoir"):
        return invoice
    if _facture_emise(invoice):
        return invoice
    if emission is None:
        emission = datetime.now(UTC)
    if _numero_de_la_serie_courante(invoice.invoice_number, emission) and await _est_le_dernier_de_sa_serie(
        session, invoice.invoice_number
    ):
        return invoice

    identifiant = invoice.id
    type_document = invoice.document_type
    for _ in range(_REPRISES_DE_NUMERO):
        numero = await _generate_invoice_number(session, type_document, emission=emission)
        logger.info("Numéro définitif proposé %s pour %s", numero, identifiant)
        try:
            async with session.begin_nested():
                invoice.invoice_number = numero
                await session.flush()
        except IntegrityError as collision:
            if "invoice_number" not in str(collision.orig):
                raise
            logger.warning("Numéro %s pris par un concurrent, reprise", numero)
            rechargee = await _get_invoice_with_lines(session, identifiant)
            if rechargee is None:
                raise HTTPException(status_code=404, detail="Invoice not found") from collision
            invoice = rechargee
            if _facture_emise(invoice):
                return invoice
            if _numero_de_la_serie_courante(invoice.invoice_number, emission) and await _est_le_dernier_de_sa_serie(
                session, invoice.invoice_number
            ):
                return invoice
            type_document = invoice.document_type
            continue
        return invoice

    raise HTTPException(
        status_code=409,
        detail="Numérotation occupée par d'autres créations simultanées, réessaie.",
    )


def _poser_echeance(invoice: Invoice, echeance: datetime) -> None:
    """B-1760 : garder la date auto-générée cohérente avec l'échéance.

    Seule la première ligne reconnue est remplacée. Les conditions négociées
    et les mentions personnalisées restent intactes, sans recalcul du taux.
    """
    mentions = invoice.legal_mentions
    ancienne_ligne = f"Date d'échéance : {invoice.due_date:%d/%m/%Y}."
    if mentions and (mentions == ancienne_ligne or mentions.startswith(ancienne_ligne + "\n")):
        nouvelle_ligne = f"Date d'échéance : {echeance:%d/%m/%Y}."
        invoice.legal_mentions = nouvelle_ligne + mentions[len(ancienne_ligne):]
    invoice.due_date = echeance


def _poser_dates_demission(invoice: Invoice, emission: datetime) -> None:
    """La date imprimée est celle de la délivrance (BOFiP § 140).

    L'échéance se décale du même nombre de jours, pour garder le délai
    convenu. Appelé après la copie des champs : une date ancienne envoyée
    avec le changement de statut ne reste pas sur la pièce émise.
    """
    maintenant = emission
    ancienne = invoice.issue_date
    if ancienne.tzinfo is None:
        ancienne = ancienne.replace(tzinfo=UTC)
    else:
        ancienne = ancienne.astimezone(UTC)
    jours = (maintenant.date() - ancienne.date()).days
    invoice.issue_date = maintenant
    echeance = invoice.due_date
    if echeance.tzinfo is None:
        echeance = echeance.replace(tzinfo=UTC)
    else:
        echeance = echeance.astimezone(UTC)
    _poser_echeance(invoice, echeance + timedelta(days=jours))


def _premiere_emission(invoice: Invoice, nouveau_statut: str | None) -> bool:
    """Première sortie d'une facture ou d'un avoir vers un statut émis."""
    return (
        nouveau_statut in _STATUTS_QUI_EMETTENT
        and invoice.document_type in ("facture", "avoir")
        and not _facture_emise(invoice)
    )


def _date_du_client(valeur: str, champ: str) -> datetime:
    """B-558 (05/09/2026) : « 2026-02-30 » faisait lever ValueError jusqu'au 500.

    Les autres entités (contacts, tâches, agenda, planning) refusent déjà une
    date impossible en 422 ; la facturation était la seule à tomber en 500.
    """
    try:
        return datetime.fromisoformat(valeur.replace("Z", ""))
    except ValueError as invalide:
        raise HTTPException(
            status_code=422,
            detail=f"{champ} invalide : attendu une date au format AAAA-MM-JJ.",
        ) from invalide


def _au_centime(valeur: float) -> float:
    """B-1428 : arrondi commercial au centime, demi-centime vers le haut (en
    valeur absolue), comme l'écran. `round` de Python arrondit au pair sur la
    représentation binaire : 2,5 × 1,25 = 3,125 donnait 3,12 ici et 3,13 à
    l'écran. On passe par la représentation décimale courte du nombre."""
    return float(Decimal(repr(valeur)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _montants_de_ligne(
    ligne: InvoiceLineRequest, tva_applicable: bool = True
) -> tuple[float, float]:
    """Le HT et le TTC d'une ligne, arrondis au centime a la SOURCE.

    B-345 (05/09/2026) : l'exonération (art. 293 B du CGI) est un attribut de
    la PIÈCE. Le taux de la ligne était appliqué sans la regarder : une facture
    en franchise valait 120 en base, dans la liste et dans l'encours, pendant
    que le PDF remis au client imprimait 100. Le PDF est la pièce juridique :
    c'est la base qui mentait. En franchise, le TTC d'une ligne EST son HT.

    F1 (0.55) : `total_ttc` etait stocke non arrondi. Trois lignes de 33,33 EUR
    a 20 % donnaient 119.98799999999999 en base, pendant que le PDF imprimait
    119,99, que l'encours disait 119,99 et que la somme des lignes affichees
    faisait 119,99. Un client qui additionne les lignes de son PDF ne
    retrouvait pas le total du document.

    L'argent n'a pas de troisieme decimale : on arrondit ou le montant NAIT,
    pas a chaque affichage. Les totaux du document somment ensuite des lignes
    deja arrondies, donc la somme des parts egale toujours le tout.
    """
    total_ht = _au_centime(ligne.quantity * ligne.unit_price_ht)
    if not tva_applicable:
        return total_ht, total_ht
    total_ttc = _au_centime(total_ht * (1 + ligne.tva_rate / 100))
    return total_ht, total_ttc


def _calculate_invoice_totals(lines: list[InvoiceLine]) -> tuple[float, float, float]:
    """
    Calcule les totaux d'une facture, a partir de lignes DEJA arrondies.

    Returns:
        (subtotal_ht, total_tax, total_ttc)
    """
    subtotal_ht = _au_centime(sum(line.total_ht for line in lines))
    total_ttc = _au_centime(sum(line.total_ttc for line in lines))
    total_tax = _au_centime(total_ttc - subtotal_ht)

    return subtotal_ht, total_tax, total_ttc


def _invoice_to_response(invoice: Invoice) -> InvoiceResponse:
    """Convertit Invoice entity en InvoiceResponse schema."""
    lines = [
        InvoiceLineResponse(
            id=line.id,
            invoice_id=line.invoice_id,
            description=line.description,
            quantity=line.quantity,
            unit_price_ht=line.unit_price_ht,
            tva_rate=line.tva_rate,
            total_ht=line.total_ht,
            total_ttc=line.total_ttc,
        )
        for line in invoice.lines
    ]

    # Le contact n'est présent que si l'appelant a chargé la relation
    # (`selectinload`). On ne le force pas ici : un accès paresseux dans un
    # contexte async lèverait.
    nom_du_client = invoice.client_name
    contact = invoice.__dict__.get("contact")
    if nom_du_client is None and contact is not None:
        nom_du_client = (
            getattr(contact, "display_name", None)
            or " ".join(
                filter(None, [getattr(contact, "first_name", None),
                              getattr(contact, "last_name", None)])
            ).strip()
            or getattr(contact, "company", None)
        )

    return InvoiceResponse(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        contact_id=invoice.contact_id,
        contact_name=nom_du_client,
        document_type=invoice.document_type,
        tva_applicable=invoice.tva_applicable,
        currency=invoice.currency,
        issue_date=invoice.issue_date.isoformat(),
        due_date=invoice.due_date.isoformat(),
        status=statut_effectif_facture(
            invoice.status, invoice.document_type, invoice.due_date
        ),
        subtotal_ht=invoice.subtotal_ht,
        total_tax=invoice.total_tax,
        total_ttc=invoice.total_ttc,
        notes=invoice.notes,
        payment_terms=invoice.payment_terms,
        payment_method=invoice.payment_method,
        late_penalty_rate=invoice.late_penalty_rate,
        legal_mentions=invoice.legal_mentions,
        converted_from_id=invoice.converted_from_id,
        validite_jours=invoice.validite_jours,
        payment_date=invoice.payment_date.isoformat() if invoice.payment_date else None,
        # P-139 : toujours en UTC explicite (relue de SQLite, la date perd son fuseau).
        sent_at=(invoice.sent_at if invoice.sent_at.tzinfo else invoice.sent_at.replace(tzinfo=UTC)).isoformat() if invoice.sent_at else None,
        created_at=invoice.created_at.isoformat(),
        updated_at=invoice.updated_at.isoformat(),
        lines=lines,
    )


def _snapshot_du_contact(contact: Contact) -> dict[str, str | None]:
    """Copie l'identité utilisée par une pièce, une seule fois."""
    return {
        "client_name": contact.display_name,
        "client_company": contact.company,
        "client_email": contact.email,
        "client_phone": contact.phone,
        "client_address": contact.address,
    }


def _snapshot_de_la_piece(invoice: Invoice) -> dict[str, str | None]:
    """Refuse de fabriquer un document quand son destinataire n'est pas figé."""
    if not invoice.client_name:
        raise HTTPException(
            status_code=409,
            detail=(
                "Destinataire historique absent : génération refusée pour ne pas "
                "produire une pièce comptable fausse."
            ),
        )
    return {
        "name": invoice.client_name,
        "company": invoice.client_company or "",
        "email": invoice.client_email or "",
        "phone": invoice.client_phone or "",
        "address": invoice.client_address or "",
    }


def _snapshot_de_ligne(line: InvoiceLine) -> dict[str, str | float]:
    """Les valeurs d'une ligne, copiées avant qu'un rollback ne l'expire."""
    return {
        "description": line.description,
        "quantity": line.quantity,
        "unit_price_ht": line.unit_price_ht,
        "tva_rate": line.tva_rate,
        "total_ht": line.total_ht,
        "total_ttc": line.total_ttc,
    }


# Routes "collection" exposees avec ET sans slash final pour eviter la
# redirection 307 (le frontend appelle sans slash, les tests avec slash).
@router.get("", response_model=list[InvoiceResponse], include_in_schema=False)
@router.get("/", response_model=list[InvoiceResponse])
async def list_invoices(
    status: str | None = Query(None, description="Filtrer par status (draft, sent, paid, overdue, cancelled)"),
    contact_id: str | None = Query(None, description="Filtrer par contact"),
    document_type: str | None = Query(None, description="Filtrer par type (devis, facture, avoir)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """
    Liste les factures avec pagination et filtres.
    """
    statement = select(Invoice).options(selectinload(Invoice.lines), selectinload(Invoice.contact))

    # Filtres
    if status:
        # B-315 : « en retard » est un état calendaire, pas seulement une
        # valeur qu'un scheduler aurait eu le temps d'écrire en base.
        aujourd_hui = date_civile_paris(datetime.now(UTC))
        debut_du_jour = datetime.combine(aujourd_hui, datetime.min.time())
        if status == "overdue":
            statement = statement.where(
                Invoice.document_type == "facture",
                or_(
                    Invoice.status == "overdue",
                    and_(Invoice.status == "sent", Invoice.due_date < debut_du_jour),
                ),
            )
        elif status == "sent":
            statement = statement.where(
                Invoice.status == "sent",
                or_(
                    Invoice.document_type != "facture",
                    Invoice.due_date >= debut_du_jour,
                ),
            )
        else:
            statement = statement.where(Invoice.status == status)
    if contact_id:
        statement = statement.where(Invoice.contact_id == contact_id)
    if document_type:
        statement = statement.where(Invoice.document_type == document_type)

    # Ordre anti-chronologique
    statement = statement.order_by(Invoice.created_at.desc())

    # Pagination
    statement = statement.offset(skip).limit(limit)

    result = await session.execute(statement)
    invoices = result.scalars().all()

    return [_invoice_to_response(invoice) for invoice in invoices]


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Récupère une facture par ID.
    """
    invoice = await _get_invoice_with_lines(session, invoice_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return _invoice_to_response(invoice)


# Les statuts, par type de document. Un devis s'accepte ou se refuse ; une
# facture s'envoie, se paie ou tombe en retard. Melanger les deux fait sortir
# une creance de l'encours (`sent`/`overdue` seulement).
STATUTS_DE_DEVIS = frozenset(
    {"draft", "sent", "accepted", "refused", "expired", "converted", "cancelled"}
)
STATUTS_DE_FACTURE = frozenset({"draft", "sent", "paid", "overdue", "cancelled"})


def _facture_citee_emise(origine: Invoice) -> bool:
    """Une facture déjà émise, avec un numéro définitif. Le § 220 cite
    la facture initiale, pas un brouillon PROV-."""
    return (
        origine.document_type == "facture"
        and _facture_emise(origine)
        and not _numero_provisoire(origine.invoice_number)
    )


async def _verifier_la_facture_d_origine(
    session: AsyncSession, document_type: str, origine_id: str | None,
    *, obligatoire: bool = False,
) -> None:
    """P-154 : un avoir peut désigner la facture qu'il corrige ; la pièce
    désignée doit exister, être une facture, et être déjà émise."""
    if origine_id is None:
        if obligatoire and document_type == "avoir":
            raise HTTPException(
                status_code=409,
                detail="Sélectionne la facture d'origine avant d'émettre cet avoir.",
            )
        return
    if document_type != "avoir":
        raise HTTPException(status_code=400, detail="La facture d'origine est réservée aux avoirs.")
    origine = await session.get(Invoice, origine_id)
    if origine is None or origine.document_type != "facture":
        raise HTTPException(status_code=400, detail="La pièce d'origine d'un avoir doit être une facture existante.")
    if not _facture_citee_emise(origine):
        raise HTTPException(status_code=400, detail="Un avoir ne peut citer qu'une facture déjà émise.")


@router.post("", response_model=InvoiceResponse, include_in_schema=False)
@router.post("/", response_model=InvoiceResponse)
async def create_invoice(
    request: CreateInvoiceRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Crée une nouvelle facture.

    - Facture et avoir : jeton provisoire, numéro définitif à l'émission
    - Devis : numéro DEV-YYYY-NNN dès la création
    - Calcule les totaux automatiquement
    - Dates par défaut: issue_date=aujourd'hui, due_date=+30 jours
    """
    # Vérifier que le contact existe
    contact = await session.get(Contact,request.contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Valider le type de document
    document_type = request.document_type
    if document_type not in ("devis", "facture", "avoir"):
        raise HTTPException(status_code=400, detail="document_type doit être : devis, facture ou avoir")
    await _verifier_la_facture_d_origine(session, document_type, request.converted_from_id)

    # Dates par défaut
    issue_date = _date_du_client(request.issue_date, "Date d'émission") if request.issue_date else datetime.now(UTC)
    due_date = _date_du_client(request.due_date, "Date d'échéance") if request.due_date else issue_date + timedelta(days=30)

    # Validité par défaut pour les devis
    validite_jours = request.validite_jours
    if document_type == "devis" and validite_jours is None:
        validite_jours = 30

    # Le rollback d'une reprise expire les objets chargés : le contact serait
    # relu paresseusement au tour suivant, ce qu'une session async interdit.
    snapshot_client = _snapshot_du_contact(contact)

    invoice = await _inserer_piece(
        session,
        document_type,
        lambda numero: Invoice(
            invoice_number=numero,
            contact_id=request.contact_id,
            **snapshot_client,
            document_type=document_type,
            tva_applicable=request.tva_applicable,
            currency=request.currency,
            issue_date=issue_date,
            due_date=due_date,
            status="draft",
            notes=request.notes,
            validite_jours=validite_jours,
            converted_from_id=request.converted_from_id,
        ),
    )
    invoice_number = invoice.invoice_number

    # Créer les lignes
    db_lines = []
    for line_req in request.lines:
        total_ht, total_ttc = _montants_de_ligne(line_req, invoice.tva_applicable)

        line = InvoiceLine(
            invoice_id=invoice.id,
            description=line_req.description,
            quantity=line_req.quantity,
            unit_price_ht=line_req.unit_price_ht,
            tva_rate=line_req.tva_rate,
            total_ht=total_ht,
            total_ttc=total_ttc,
        )
        session.add(line)
        db_lines.append(line)

    # Calculer les totaux a partir des lignes en memoire (evite lazy load)
    subtotal_ht, total_tax, total_ttc = _calculate_invoice_totals(db_lines)
    invoice.subtotal_ht = subtotal_ht
    invoice.total_tax = total_tax
    invoice.total_ttc = total_ttc
    invoice.updated_at = datetime.now(UTC)

    session.add(invoice)
    await session.commit()

    # Recharger avec eager loading
    invoice = await _get_invoice_with_lines(session, invoice.id)

    logger.info(f"Invoice created: {invoice_number}")

    return _invoice_to_response(invoice)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    request: UpdateInvoiceRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Met à jour une facture.

    - Si les lignes sont modifiées, recalcule les totaux
    """
    await _verrouiller_emission(session)
    invoice = await _get_invoice_with_lines(session, invoice_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # 0.55 : `status` etait une chaine LIBRE sur cette route generique. Poser
    # « accepted » (un statut de DEVIS) sur une facture la sortait de l'encours,
    # qui ne regarde que `sent` et `overdue` : une creance de 1 200 EUR
    # disparaissait par un clic de menu, sans passer par le chat. La route
    # dediee `/devis-status` etait deja protegee ; c'est la porte generique qui
    # manquait. Un statut invente passait aussi - exactement ce que THERESE
    # avait halluciné en 0.53 (« en attente », « partiellement paye »).
    if request.status is not None:
        autorises = (
            STATUTS_DE_DEVIS if invoice.document_type == "devis" else STATUTS_DE_FACTURE
        )
        if request.status not in autorises:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Statut « {request.status} » invalide pour un document de type "
                    f"« {invoice.document_type} ». Valeurs acceptées : "
                    f"{', '.join(sorted(autorises))}"
                ),
            )
        if request.status == "draft" and _facture_emise(invoice):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Une pièce émise ne repasse pas en brouillon. "
                    + _conseil_pour_rectifier(invoice)
                ),
            )
        # B-1671 : un statut « Annulée » sort la créance de l'encours sans
        # document nouveau. Le § 210 du BOI-TVA-DECLA-30-20-20-20 rectifie
        # par une facture de remplacement ou une note d'avoir. L'article 289,
        # I, 5 assimile l'avoir émis à une facture : même garde.
        if (
            request.status == "cancelled"
            and invoice.document_type in ("facture", "avoir")
            and _facture_emise(invoice)
        ):
            detail = (
                "Un avoir émis ne s'annule pas. Demande à ton expert-comptable "
                "comment établir le document rectificatif adapté."
                if invoice.document_type == "avoir"
                else "Une facture émise ne s'annule pas. Pour l'annuler, émets un avoir."
            )
            raise HTTPException(status_code=409, detail=detail)

    # B-1744 : l’immuabilité se décide sur la pièce chargée, avant qu’un
    # PROV annulé reçoive son premier numéro définitif.
    deja_emise = _facture_emise(invoice)

    # B-1615 : le numéro définitif naît ici, avant toute autre écriture.
    # La date du jour se pose après la copie des champs (plus bas).
    emet_maintenant = _premiere_emission(invoice, request.status)
    instant_emission = datetime.now(UTC) if emet_maintenant else None
    if emet_maintenant and invoice.document_type == "avoir":
        origine_id = (
            request.converted_from_id
            if "converted_from_id" in request.model_fields_set
            else invoice.converted_from_id
        )
        await _verifier_la_facture_d_origine(session, "avoir", origine_id, obligatoire=True)
    invoice = await _attribuer_numero_definitif(
        session, invoice, request.status, emission=instant_emission,
    )

    # Mise à jour des champs
    # B-1614 : une pièce émise est figée (B-1506, numérotation continue) ;
    # seul son statut change encore, jamais vers le brouillon.
    if deja_emise:
        champs = {
            champ for champ in request.model_fields_set
            if champ != "status" and (getattr(request, champ) is not None or champ == "converted_from_id")
        }
        if champs:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Une pièce émise ne se modifie pas : seul son statut change. "
                    + _conseil_pour_rectifier(invoice)
                ),
            )

    if request.contact_id is not None:
        # Vérifier que le nouveau contact existe
        contact = await session.get(Contact, request.contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        invoice.contact_id = request.contact_id
        for field, value in _snapshot_du_contact(contact).items():
            setattr(invoice, field, value)

    if request.currency is not None:
        invoice.currency = request.currency

    if request.issue_date is not None:
        invoice.issue_date = _date_du_client(request.issue_date, "Date d'émission")

    if request.due_date is not None:
        _poser_echeance(invoice, _date_du_client(request.due_date, "Date d'échéance"))

    if request.status is not None:
        _dater_le_premier_envoi(invoice, request.status, emission=instant_emission)
        invoice.status = request.status

    if "converted_from_id" in request.model_fields_set:
        await _verifier_la_facture_d_origine(session, invoice.document_type, request.converted_from_id)
        invoice.converted_from_id = request.converted_from_id

    if request.notes is not None:
        invoice.notes = request.notes

    if request.validite_jours is not None:
        invoice.validite_jours = request.validite_jours

    # Mise à jour des lignes
    if request.lines is not None:
        # BUG-147 : détacher la collection AVANT la suppression. Sinon
        # invoice.lines garde les instances en état « deleted » et le
        # session.add(invoice) plus bas re-cascade dessus ->
        # InvalidRequestError « Instance '<InvoiceLine ...>' has been
        # deleted » (500 « Failed to fetch » côté UI).
        old_lines = list(invoice.lines)
        invoice.lines = []
        for line in old_lines:
            await session.delete(line)
        await session.flush()

        # Créer les nouvelles lignes
        db_lines = []
        for line_req in request.lines:
            total_ht, total_ttc = _montants_de_ligne(line_req, invoice.tva_applicable)

            line = InvoiceLine(
                invoice_id=invoice.id,
                description=line_req.description,
                quantity=line_req.quantity,
                unit_price_ht=line_req.unit_price_ht,
                tva_rate=line_req.tva_rate,
                total_ht=total_ht,
                total_ttc=total_ttc,
            )
            session.add(line)
            db_lines.append(line)

        # La session tourne en expire_on_commit=False : la relecture finale
        # repasse par l'identity map et ne repeuple PAS une relation déjà
        # chargée. La collection en mémoire doit donc refléter les nouvelles
        # lignes, sinon la réponse renvoie une facture sans lignes.
        invoice.lines = db_lines

        # Recalculer les totaux a partir des lignes en memoire
        subtotal_ht, total_tax, total_ttc = _calculate_invoice_totals(db_lines)
        invoice.subtotal_ht = subtotal_ht
        invoice.total_tax = total_tax
        invoice.total_ttc = total_ttc

    if instant_emission is not None:
        _poser_dates_demission(invoice, instant_emission)

    invoice.updated_at = datetime.now(UTC)

    session.add(invoice)
    await session.commit()

    # Recharger avec eager loading
    invoice = await _get_invoice_with_lines(session, invoice.id)

    logger.info(f"Invoice updated: {invoice.invoice_number}")

    return _invoice_to_response(invoice)


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Supprime une facture et son PDF associé.
    """
    await _verrouiller_emission(session)
    invoice = await _get_invoice_with_lines(session, invoice_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if _facture_emise(invoice):
        raise HTTPException(
            status_code=409,
            detail=(
                "Une pièce émise ne se supprime pas : sa numérotation doit "
                "rester continue. " + _conseil_pour_rectifier(invoice)
            ),
        )

    # Un brouillon hérité porte déjà FACT- ou AV-. L'effacer sortirait ce
    # numéro du maximum, et la prochaine émission le reprendrait.
    if invoice.document_type in ("facture", "avoir") and not _numero_provisoire(invoice.invoice_number):
        raise HTTPException(
            status_code=409,
            detail=(
                "Ce brouillon porte déjà un numéro de la série. Le supprimer "
                "permettrait de le donner à une autre pièce. Annule-le si tu "
                "ne veux plus l'émettre."
            ),
        )

    invoice_number = invoice.invoice_number

    # Supprimer le PDF si existant
    output_dir = await _get_invoice_output_dir(session)
    pdf_generator = InvoicePDFGenerator(output_dir=output_dir)
    pdf_generator.delete_invoice_pdf(invoice_number)

    # Supprimer la facture (cascade sur lignes)
    await session.delete(invoice)
    await session.commit()

    logger.info(f"Invoice deleted: {invoice_number}")

    return {"message": "Invoice deleted successfully"}


def _conseil_pour_rectifier(invoice: Invoice) -> str:
    """Le formulaire référence une facture, pas encore un avoir antérieur."""
    if invoice.document_type == "avoir":
        return "Demande à ton expert-comptable comment établir le document rectificatif adapté."
    return "Pour la corriger, émets un avoir."


def _facture_emise(invoice: Invoice) -> bool:
    """Une pièce réellement émise reste figée, quel que soit son statut.

    Sa numérotation appartient à une séquence chronologique et continue
    (BOFiP, BOI-TVA-DECLA-30-20-20-10) : on ne le supprime pas et il ne
    repasse pas en brouillon, on l'annule par un avoir. Un devis n'entre pas
    dans cette séquence.

    B-1743/B-1744 : un PROV- annulé sans envoi n'a jamais été émis.
    Une ancienne pièce annulée avec numéro définitif reste conservée comme
    émise, même si son horodatage d'envoi n'avait pas été enregistré.
    """
    return invoice.document_type in ("facture", "avoir") and (
        invoice.sent_at is not None
        or invoice.status in _STATUTS_QUI_EMETTENT
        or (invoice.status == "cancelled" and not _numero_provisoire(invoice.invoice_number))
    )


def _dater_le_premier_envoi(
    invoice: Invoice, nouveau_statut: str, *, emission: datetime | None = None,
) -> None:
    """P-139 : la date du premier passage à « envoyé » est gardée, jamais
    réécrite (un renvoi ou un aller-retour de statut ne la déplace pas)."""
    if nouveau_statut == "sent" and invoice.sent_at is None:
        invoice.sent_at = emission if emission is not None else datetime.now(UTC)


@router.patch("/{invoice_id}/mark-paid", response_model=InvoiceResponse)
async def mark_invoice_paid(
    invoice_id: str,
    request: MarkPaidRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Marque une facture comme payée.
    """
    await _verrouiller_emission(session)
    invoice = await _get_invoice_with_lines(session, invoice_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # B-162 (02/09/2026) : la porte generique `PUT` refuse « paid » sur un
    # devis depuis la 0.55 ; cette porte laterale posait le meme statut sans
    # jamais regarder le type de document. Un devis marque paye sortait des
    # filtres de devis par statut tout en restant compte dans la liste des
    # devis. Meme garde, meme table de reference.
    autorises = (
        STATUTS_DE_DEVIS if invoice.document_type == "devis" else STATUTS_DE_FACTURE
    )
    if "paid" not in autorises:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Statut « paid » invalide pour un document de type "
                f"« {invoice.document_type} ». Valeurs acceptées : "
                f"{', '.join(sorted(autorises))}"
            ),
        )

    # Date de paiement
    payment_date = datetime.fromisoformat(request.payment_date.replace("Z", "")) if request.payment_date else datetime.now(UTC)
    # P-155 : la date réelle se saisit ; une date future ferait passer la
    # facture pour payée avant de l'être (tableau de bord, relances).
    if payment_date.date() > datetime.now(UTC).date() + timedelta(days=1):
        raise HTTPException(
            status_code=400,
            detail="La date du paiement ne peut pas être dans le futur.",
        )

    # B-1615 : marquer payé un brouillon, c'est l'émettre.
    emet_maintenant = _premiere_emission(invoice, "paid")
    instant_emission = datetime.now(UTC) if emet_maintenant else None
    if emet_maintenant and invoice.document_type == "avoir":
        await _verifier_la_facture_d_origine(session, "avoir", invoice.converted_from_id, obligatoire=True)
    invoice = await _attribuer_numero_definitif(session, invoice, "paid", emission=instant_emission)
    if instant_emission is not None:
        _poser_dates_demission(invoice, instant_emission)
    invoice.status = "paid"
    invoice.payment_date = payment_date
    invoice.updated_at = datetime.now(UTC)

    session.add(invoice)
    await session.commit()

    # Recharger avec eager loading
    invoice = await _get_invoice_with_lines(session, invoice.id)

    logger.info(f"Invoice marked as paid: {invoice.invoice_number}")

    return _invoice_to_response(invoice)


@router.post("/{invoice_id}/convert")
async def convert_invoice(
    invoice_id: str,
    request: dict,
    session: AsyncSession = Depends(get_session),
):
    """
    Convertit un document (ex: devis → facture).

    Crée une copie du document avec le nouveau type et un nouveau numéro.
    Le document original est conservé.
    """
    target_type = request.get("target_type", "")
    if target_type not in ("devis", "facture", "avoir"):
        raise HTTPException(status_code=400, detail="target_type doit être 'devis', 'facture' ou 'avoir'")

    source = await _get_invoice_with_lines(session, invoice_id)
    if not source:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if source.document_type == target_type:
        raise HTTPException(status_code=400, detail=f"Le document est déjà de type '{target_type}'")

    # Le rollback d'une reprise de numéro expire la pièce source : tout ce
    # qu'on relit après l'insertion est copié ici, en valeurs.
    source_numero, source_type = source.invoice_number, source.document_type
    emission = datetime.now(UTC)
    copie = {
        "document_type": target_type,
        "contact_id": source.contact_id,
        "client_name": source.client_name,
        "client_company": source.client_company,
        "client_email": source.client_email,
        "client_phone": source.client_phone,
        "client_address": source.client_address,
        "currency": source.currency,
        "issue_date": emission,
        # B-545 (05/09/2026) : recopier l'échéance du devis donnait une facture
        # échue avant d'être émise (-218 jours). Même règle que la conversion
        # devis -> facture : émission + délai de paiement (30 jours par défaut).
        "due_date": emission + timedelta(days=_parse_payment_terms_days(source.payment_terms or "")),
        "status": "draft",
        "subtotal_ht": source.subtotal_ht,
        "total_tax": source.total_tax,
        "total_ttc": source.total_ttc,
        "tva_applicable": source.tva_applicable,
        "notes": source.notes or "",
        # P-154 : un avoir tiré d'une facture déjà émise la garde comme origine.
        "converted_from_id": None,
    }
    if target_type == "avoir" and source_type == "facture":
        if not _facture_citee_emise(source):
            raise HTTPException(status_code=400, detail="Un avoir ne peut citer qu'une facture déjà émise.")
        copie["converted_from_id"] = source.id
    lignes_source = [_snapshot_de_ligne(line) for line in source.lines]

    # B-1615 : facture et avoir naissent provisoires ; le devis est numéroté.
    # La reprise d'un numéro double (B-338) a lieu à l'émission.
    new_invoice = await _inserer_piece(
        session, target_type, lambda numero: Invoice(invoice_number=numero, **copie)
    )

    # Copier les lignes
    for ligne in lignes_source:
        session.add(InvoiceLine(invoice_id=new_invoice.id, **ligne))

    await session.commit()

    # Recharger avec eager loading
    new_invoice = await _get_invoice_with_lines(session, new_invoice.id)

    logger.info(f"Converted {source_numero} ({source_type}) → {new_invoice.invoice_number} ({target_type})")

    return _invoice_to_response(new_invoice)


@router.get("/billing/profile-status")
async def billing_profile_status(session: AsyncSession = Depends(get_session)):
    """Statut de complétude du profil émetteur (P0-PROD-2).

    Permet à l'UI de poser un garde-fou avant la 1re facture : raison sociale (ou
    nom), SIRET et adresse sont requis pour une facture conforme et opposable.
    """
    profile = get_cached_profile()
    if profile is None:
        # Cache vide après un démarrage avec profil chiffré : lecture de
        # secours en session (déchiffre et répare le cache au passage).
        from app.services.user_profile import get_user_profile

        profile = await get_user_profile(session)
    if profile is None:
        return {
            "is_complete": False,
            "missing": ["raison sociale ou nom", "SIRET", "adresse"],
            "tva_intra_renseigne": False,
        }
    return {
        "is_complete": profile.is_billing_complete(),
        "missing": profile.missing_billing_fields(),
        # P-136 : le formulaire avertit (sans bloquer) d'une facture avec TVA
        # de plus de 150 € HT sans numéro de TVA de l'émetteur (F31808).
        "tva_intra_renseigne": bool((profile.tva_intra or "").strip()),
    }


async def _facture_d_origine_pour_le_pdf(session: AsyncSession, invoice: Invoice) -> dict[str, str] | None:
    """P-154 : numéro et date de la facture qu'un avoir corrige."""
    if invoice.document_type != "avoir" or not invoice.converted_from_id:
        return None
    origine = await session.get(Invoice, invoice.converted_from_id)
    if origine is None or not _facture_citee_emise(origine):
        return None
    return {"numero": origine.invoice_number, "date": origine.issue_date.strftime("%d/%m/%Y")}


@router.get("/{invoice_id}/pdf")
async def generate_invoice_pdf(
    invoice_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Génère et retourne le chemin du PDF de la facture.

    - Utilise les données du profil utilisateur pour l'émetteur
    - Récupère les données du contact pour le destinataire
    - Génère un PDF conforme à la réglementation française
    """
    invoice = await _get_invoice_with_lines(session, invoice_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Récupérer le profil utilisateur (dataclass → dict pour .get())
    _profile = get_cached_profile()
    if _profile is None:
        # B-1616 : cache vide après un démarrage ou une restauration avec un
        # profil chiffré (relu sans trousseau) ; lecture de secours en base,
        # qui déchiffre et répare le cache, comme billing_profile_status.
        from app.services.user_profile import get_user_profile

        _profile = await get_user_profile(session)

    # P0-PROD-2 : garde-fou émetteur. Un document de facturation sans identité
    # émetteur (raison sociale + SIRET + adresse) n'est pas conforme ni opposable
    # (constat C7 : factures sans SIRET, NDA inventé faute de profil).
    if _profile is None or not _profile.is_billing_complete():
        missing = (
            _profile.missing_billing_fields()
            if _profile
            else ["raison sociale ou nom", "SIRET", "adresse"]
        )
        raise HTTPException(
            status_code=400,
            detail=(
                "Profil émetteur incomplet : renseigne "
                + ", ".join(missing)
                + " dans Paramètres > Profil avant de générer un document de facturation."
            ),
        )

    user_profile = _profile.to_dict() if _profile else {}

    # Préparer les données pour le PDF
    invoice_data = {
        "invoice_number": invoice.invoice_number,
        "document_type": invoice.document_type,
        "tva_applicable": invoice.tva_applicable,
        "validite_jours": invoice.validite_jours,
        "issue_date": invoice.issue_date.isoformat(),
        "due_date": invoice.due_date.isoformat(),
        # B-468 : le PDF porte le statut EFFECTIF (une facture envoyée et
        # échue est « En retard »), comme la liste et l'encours.
        "status": statut_effectif_facture(invoice.status, invoice.document_type, invoice.due_date),
        "subtotal_ht": invoice.subtotal_ht,
        "total_tax": invoice.total_tax,
        "total_ttc": invoice.total_ttc,
        "notes": invoice.notes or "",
        # B-339 : les conditions négociées à la conversion d'un devis (échéance,
        # mode de règlement, mentions calculées) n'arrivaient jamais au PDF, qui
        # imprimait « net à 30 jours » sous une échéance à 90 jours.
        "payment_terms": invoice.payment_terms,
        "payment_method": invoice.payment_method,
        "legal_mentions": invoice.legal_mentions,
        "facture_origine": await _facture_d_origine_pour_le_pdf(session, invoice),
        "lines": [
            {
                "description": line.description,
                "quantity": line.quantity,
                "unit_price_ht": line.unit_price_ht,
                "tva_rate": line.tva_rate,
                "total_ht": line.total_ht,
                "total_ttc": line.total_ttc,
            }
            for line in invoice.lines
        ],
    }

    contact_data = _snapshot_de_la_piece(invoice)

    user_profile_data = {
        "name": user_profile.get("name", ""),
        "company": user_profile.get("company", ""),
        "address": user_profile.get("address", ""),
        "siren": user_profile.get("siren", ""),
        "siret": user_profile.get("siret", ""),
        "code_ape": user_profile.get("code_ape", ""),
        "tva_intra": user_profile.get("tva_intra", ""),
        # B-1445 : le régime choisit la mention légale (P-119) ; la liste
        # blanche l'oubliait et le PDF sortait toujours « Aucune TVA facturée ».
        "regime_tva": user_profile.get("regime_tva", "normal"),
    }

    # Générer le PDF (dans le dossier de travail si configuré)
    try:
        output_dir = await _get_invoice_output_dir(session)
        pdf_generator = InvoicePDFGenerator(output_dir=output_dir)
        pdf_path = pdf_generator.generate_invoice_pdf(
            invoice_data=invoice_data,
            contact_data=contact_data,
            user_profile=user_profile_data,
            currency=invoice.currency,
        )
    except Exception as e:
        # B-334 (05/09/2026) : le détail HTTP recopiait l'exception brute
        # (adresses mémoire ReportLab, chemins du poste). À la limite de
        # l'écran, seuls les messages localisés passent.
        logger.error(f"Erreur génération PDF facture {invoice_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=message_pour_ecran(e, ou="pendant la génération du PDF de la facture"),
        ) from e

    logger.info(f"PDF generated for invoice: {invoice.invoice_number}")

    return {"pdf_path": pdf_path, "invoice_number": invoice.invoice_number}


def generate_legal_mentions(
    late_penalty_rate: float = 11.62,
    due_date_str: str = "",
    currency: str = "EUR",
) -> str:
    """
    Genere les mentions legales d'une facture.

    Args:
        late_penalty_rate: Taux de penalite de retard (defaut: 3x taux BCE ~3.87% = 11.62%)
        due_date_str: Date d'echeance formatee
        currency: Devise du document. Les mentions legales francaises (indemnite 40
            EUR, art. L441-10) ne s'appliquent qu'en EUR / droit FR : on ne les met
            pas sur une facture libellee en devise etrangere (test global : 40 EUR
            sur une facture CAD).
    """
    # B-1357 : ce texte est imprimé tel quel sur la facture remise au client,
    # il s'écrit donc en français correct (accents, virgule décimale).
    taux = f"{late_penalty_rate:.2f}".replace(".", ",")
    lines = [
        f"Date d'échéance : {due_date_str}." if due_date_str else "",
    ]
    if currency == "EUR":
        lines += [
            f"En cas de retard de paiement, une pénalité de {taux} % annuel sera appliquée "
            "(3 fois le taux d'intérêt légal en vigueur).",
            "Une indemnité forfaitaire de 40 EUR pour frais de recouvrement sera exigée "
            "(art. L441-10 du Code de commerce).",
            "Escompte pour paiement anticipé : néant.",
        ]
    else:
        lines.append(
            "En cas de retard de paiement, des pénalités pourront être appliquées "
            "conformément aux conditions convenues entre les parties."
        )
    return "\n".join(line for line in lines if line)


def _parse_payment_terms_days(payment_terms: str) -> int:
    """Extrait le nombre de jours depuis une chaine comme '30 jours'."""
    import re

    match = re.search(r"(\d+)", payment_terms)
    return int(match.group(1)) if match else 30


@router.post("/{invoice_id}/convert-to-invoice", response_model=InvoiceResponse)
async def convert_devis_to_invoice(
    invoice_id: str,
    request: ConvertDevisRequest | None = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Convertit un devis accepte en facture.

    - Copie toutes les lignes du devis
    - Crée un brouillon provisoire, numéroté dans FACT à sa première émission
    - Ajoute conditions de paiement et mentions legales
    - Marque le devis source comme "converted"
    """
    await _verrouiller_emission(session)
    # 1. Recuperer le devis
    devis = await _get_invoice_with_lines(session, invoice_id)
    if not devis:
        raise HTTPException(status_code=404, detail="Devis non trouvé")

    # 2. Verifier que c'est un devis
    if devis.document_type != "devis":
        raise HTTPException(
            status_code=400,
            detail=f"Ce document est un(e) {devis.document_type}, pas un devis",
        )

    # 3. Verifier le statut (accepted ou sent, pas deja converti)
    if devis.status == "converted":
        raise HTTPException(status_code=400, detail="Ce devis a déjà été converti en facture")
    if devis.status == "cancelled":
        raise HTTPException(status_code=400, detail="Impossible de convertir un devis annulé")

    # Parametres de conversion
    req = request or ConvertDevisRequest()
    payment_terms = req.payment_terms
    payment_method = req.payment_method
    payment_days = _parse_payment_terms_days(payment_terms)
    late_penalty_rate = 11.62  # 3x taux BCE approximatif

    # 4. Creer la facture
    issue_date = datetime.now(UTC)
    due_date = issue_date + timedelta(days=payment_days)

    legal_mentions = generate_legal_mentions(
        late_penalty_rate=late_penalty_rate,
        due_date_str=due_date.strftime("%d/%m/%Y"),
        currency=devis.currency,
    )

    # Le rollback d'une reprise de numéro expire le devis chargé : ses valeurs
    # sont copiées avant l'insertion, et le devis est relu après.
    facture = {
        "contact_id": devis.contact_id,
        "client_name": devis.client_name,
        "client_company": devis.client_company,
        "client_email": devis.client_email,
        "client_phone": devis.client_phone,
        "client_address": devis.client_address,
        "document_type": "facture",
        "tva_applicable": devis.tva_applicable,
        "currency": devis.currency,
        "issue_date": issue_date,
        "due_date": due_date,
        "status": "draft",
        "notes": devis.notes,
        "payment_terms": payment_terms,
        "payment_method": payment_method,
        "late_penalty_rate": late_penalty_rate,
        "legal_mentions": legal_mentions,
        "converted_from_id": devis.id,
    }
    lignes_devis = [_snapshot_de_ligne(line) for line in devis.lines]

    new_invoice = await _inserer_piece(
        session, "facture", lambda numero: Invoice(invoice_number=numero, **facture)
    )
    invoice_number = new_invoice.invoice_number
    devis = await _get_invoice_with_lines(session, invoice_id)
    if devis is None:
        raise HTTPException(status_code=404, detail="Devis non trouvé après la reprise de numéro")

    # 5. Copier les lignes
    db_lines = []
    for ligne in lignes_devis:
        new_line = InvoiceLine(invoice_id=new_invoice.id, **ligne)
        session.add(new_line)
        db_lines.append(new_line)

    # 6. Calculer les totaux
    subtotal_ht, total_tax, total_ttc = _calculate_invoice_totals(db_lines)
    new_invoice.subtotal_ht = subtotal_ht
    new_invoice.total_tax = total_tax
    new_invoice.total_ttc = total_ttc
    new_invoice.updated_at = datetime.now(UTC)

    # 7. Marquer le devis comme converti
    devis.status = "converted"
    devis.updated_at = datetime.now(UTC)

    session.add(new_invoice)
    session.add(devis)
    await session.commit()

    # Recharger avec eager loading
    new_invoice = await _get_invoice_with_lines(session, new_invoice.id)

    logger.info(f"Devis {devis.invoice_number} converti en facture {invoice_number}")

    return _invoice_to_response(new_invoice)


@router.patch("/{invoice_id}/devis-status", response_model=InvoiceResponse)
async def update_devis_status(
    invoice_id: str,
    request: dict,
    session: AsyncSession = Depends(get_session),
):
    """
    Met a jour le statut d'un devis (accepte, refuse, expire).

    Statuts valides pour un devis : draft, sent, accepted, refused, expired, converted, cancelled.
    """
    new_status = request.get("status", "")
    valid_devis_statuses = STATUTS_DE_DEVIS

    if new_status not in valid_devis_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Statut invalide pour un devis. Valeurs acceptées : {', '.join(sorted(valid_devis_statuses))}",
        )

    invoice = await _get_invoice_with_lines(session, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Devis non trouvé")

    if invoice.document_type != "devis":
        raise HTTPException(status_code=400, detail="Ce document n'est pas un devis")

    _dater_le_premier_envoi(invoice, new_status)
    invoice.status = new_status
    invoice.updated_at = datetime.now(UTC)

    session.add(invoice)
    await session.commit()

    invoice = await _get_invoice_with_lines(session, invoice.id)
    logger.info(f"Devis {invoice.invoice_number} : statut mis a jour -> {new_status}")

    return _invoice_to_response(invoice)


@router.post("/{invoice_id}/send")
async def send_invoice_by_email(
    invoice_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Envoie la facture par email au contact.

    Nécessite:
    - Un compte email configuré (Phase 1 - Email)
    - Une facture avec un contact ayant un email
    """
    invoice = await _get_invoice_with_lines(session, invoice_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Récupérer le contact
    contact = await session.get(Contact,invoice.contact_id)
    if not contact or not contact.email:
        raise HTTPException(status_code=400, detail="Contact has no email address")

    # TODO: Intégration avec le service email (Phase 1)
    # L'envoi par email n'est pas encore implémenté.
    # Ne PAS changer le statut de la facture tant que l'email n'est pas réellement envoyé.
    raise HTTPException(
        status_code=501,
        detail="L'envoi de factures par email n'est pas encore disponible. "
        "Télécharge le PDF et envoie-le manuellement.",
    )

    return {
        "message": "Invoice send functionality not yet implemented (Phase 1 - Email required)",
        "invoice_number": invoice.invoice_number,
        "recipient": contact.email,
        "pdf_path": str(invoice.id),
    }
