"""
THÉRÈSE v2 - Invoices Router

REST API pour la gestion de facturation.
Phase 4 - Invoicing
"""

import logging
from datetime import UTC, datetime, timedelta

from app.models.database import get_session
from app.models.entities import Contact, Invoice, InvoiceLine
from app.models.schemas import (
    CreateInvoiceRequest,
    InvoiceLineResponse,
    InvoiceResponse,
    MarkPaidRequest,
    UpdateInvoiceRequest,
)
from app.services.invoice_pdf import InvoicePDFGenerator
from app.services.user_profile import get_cached_profile
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

logger = logging.getLogger(__name__)

router = APIRouter(tags=["invoices"])


async def _get_invoice_with_lines(session: AsyncSession, invoice_id: str) -> Invoice | None:
    """Load an invoice with its lines eagerly loaded (async-safe)."""
    statement = (
        select(Invoice)
        .where(Invoice.id == invoice_id)
        .options(selectinload(Invoice.lines))
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def _generate_invoice_number(session: AsyncSession) -> str:
    """
    Génère le prochain numéro de facture.
    Format: FACT-YYYY-NNN (ex: FACT-2026-001)
    """
    current_year = datetime.now(UTC).year

    # Trouver la dernière facture de l'année
    statement = (
        select(Invoice)
        .where(Invoice.invoice_number.startswith(f"FACT-{current_year}-"))
        .order_by(Invoice.created_at.desc())
    )
    result = await session.execute(statement)
    last_invoice = result.scalar_one_or_none()

    if last_invoice:
        # Extraire le numéro et incrémenter
        last_number = int(last_invoice.invoice_number.split("-")[-1])
        next_number = last_number + 1
    else:
        # Première facture de l'année
        next_number = 1

    return f"FACT-{current_year}-{next_number:03d}"


def _calculate_invoice_totals(lines: list[InvoiceLine]) -> tuple[float, float, float]:
    """
    Calcule les totaux d'une facture.

    Returns:
        (subtotal_ht, total_tax, total_ttc)
    """
    subtotal_ht = sum(line.total_ht for line in lines)
    total_tax = sum(line.total_ttc - line.total_ht for line in lines)
    total_ttc = sum(line.total_ttc for line in lines)

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

    return InvoiceResponse(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        contact_id=invoice.contact_id,
        issue_date=invoice.issue_date.isoformat(),
        due_date=invoice.due_date.isoformat(),
        status=invoice.status,
        subtotal_ht=invoice.subtotal_ht,
        total_tax=invoice.total_tax,
        total_ttc=invoice.total_ttc,
        notes=invoice.notes,
        payment_date=invoice.payment_date.isoformat() if invoice.payment_date else None,
        created_at=invoice.created_at.isoformat(),
        updated_at=invoice.updated_at.isoformat(),
        lines=lines,
    )


@router.get("/", response_model=list[InvoiceResponse])
async def list_invoices(
    status: str | None = Query(None, description="Filtrer par status (draft, sent, paid, overdue, cancelled)"),
    contact_id: str | None = Query(None, description="Filtrer par contact"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """
    Liste les factures avec pagination et filtres.
    """
    statement = select(Invoice).options(selectinload(Invoice.lines))

    # Filtres
    if status:
        statement = statement.where(Invoice.status == status)
    if contact_id:
        statement = statement.where(Invoice.contact_id == contact_id)

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


@router.post("/", response_model=InvoiceResponse)
async def create_invoice(
    request: CreateInvoiceRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Crée une nouvelle facture.

    - Génère automatiquement le numéro de facture (FACT-YYYY-NNN)
    - Calcule les totaux automatiquement
    - Dates par défaut: issue_date=aujourd'hui, due_date=+30 jours
    """
    # Vérifier que le contact existe
    contact = await session.get(Contact,request.contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Générer le numéro de facture
    invoice_number = await _generate_invoice_number(session)

    # Dates par défaut
    issue_date = datetime.fromisoformat(request.issue_date.replace("Z", "")) if request.issue_date else datetime.now(UTC)
    due_date = datetime.fromisoformat(request.due_date.replace("Z", "")) if request.due_date else issue_date + timedelta(days=30)

    # Créer la facture
    invoice = Invoice(
        invoice_number=invoice_number,
        contact_id=request.contact_id,
        issue_date=issue_date,
        due_date=due_date,
        status="draft",
        notes=request.notes,
    )

    session.add(invoice)
    await session.flush()  # Pour avoir l'ID de la facture

    # Créer les lignes
    db_lines = []
    for line_req in request.lines:
        total_ht = line_req.quantity * line_req.unit_price_ht
        total_ttc = total_ht * (1 + line_req.tva_rate / 100)

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
    invoice = await _get_invoice_with_lines(session, invoice_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Mise à jour des champs
    if request.contact_id is not None:
        # Vérifier que le nouveau contact existe
        contact = await session.get(Contact, request.contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        invoice.contact_id = request.contact_id

    if request.issue_date is not None:
        invoice.issue_date = datetime.fromisoformat(request.issue_date.replace("Z", ""))

    if request.due_date is not None:
        invoice.due_date = datetime.fromisoformat(request.due_date.replace("Z", ""))

    if request.status is not None:
        invoice.status = request.status

    if request.notes is not None:
        invoice.notes = request.notes

    # Mise à jour des lignes
    if request.lines is not None:
        # Supprimer les anciennes lignes
        for line in invoice.lines:
            await session.delete(line)
        await session.flush()

        # Créer les nouvelles lignes
        db_lines = []
        for line_req in request.lines:
            total_ht = line_req.quantity * line_req.unit_price_ht
            total_ttc = total_ht * (1 + line_req.tva_rate / 100)

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

        # Recalculer les totaux a partir des lignes en memoire
        subtotal_ht, total_tax, total_ttc = _calculate_invoice_totals(db_lines)
        invoice.subtotal_ht = subtotal_ht
        invoice.total_tax = total_tax
        invoice.total_ttc = total_ttc

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
    invoice = await _get_invoice_with_lines(session, invoice_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice_number = invoice.invoice_number

    # Supprimer le PDF si existant
    pdf_generator = InvoicePDFGenerator()
    pdf_generator.delete_invoice_pdf(invoice_number)

    # Supprimer la facture (cascade sur lignes)
    await session.delete(invoice)
    await session.commit()

    logger.info(f"Invoice deleted: {invoice_number}")

    return {"message": "Invoice deleted successfully"}


@router.patch("/{invoice_id}/mark-paid", response_model=InvoiceResponse)
async def mark_invoice_paid(
    invoice_id: str,
    request: MarkPaidRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Marque une facture comme payée.
    """
    invoice = await _get_invoice_with_lines(session, invoice_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Date de paiement
    payment_date = datetime.fromisoformat(request.payment_date.replace("Z", "")) if request.payment_date else datetime.now(UTC)

    invoice.status = "paid"
    invoice.payment_date = payment_date
    invoice.updated_at = datetime.now(UTC)

    session.add(invoice)
    await session.commit()

    # Recharger avec eager loading
    invoice = await _get_invoice_with_lines(session, invoice.id)

    logger.info(f"Invoice marked as paid: {invoice.invoice_number}")

    return _invoice_to_response(invoice)


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

    # Récupérer le contact
    contact = await session.get(Contact,invoice.contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Récupérer le profil utilisateur
    user_profile = get_cached_profile()

    # Préparer les données pour le PDF
    invoice_data = {
        "invoice_number": invoice.invoice_number,
        "issue_date": invoice.issue_date.isoformat(),
        "due_date": invoice.due_date.isoformat(),
        "status": invoice.status,
        "subtotal_ht": invoice.subtotal_ht,
        "total_tax": invoice.total_tax,
        "total_ttc": invoice.total_ttc,
        "notes": invoice.notes or "",
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

    contact_data = {
        "name": contact.display_name,
        "company": contact.company or "",
        "email": contact.email or "",
        "phone": contact.phone or "",
    }

    user_profile_data = {
        "name": user_profile.get("name", ""),
        "company": user_profile.get("company", ""),
        "address": user_profile.get("address", ""),
        "siren": user_profile.get("siren", ""),
        "tva_intra": user_profile.get("tva_intra", ""),
    }

    # Générer le PDF
    pdf_generator = InvoicePDFGenerator()
    pdf_path = pdf_generator.generate_invoice_pdf(
        invoice_data=invoice_data,
        contact_data=contact_data,
        user_profile=user_profile_data,
    )

    logger.info(f"PDF generated for invoice: {invoice.invoice_number}")

    return {"pdf_path": pdf_path, "invoice_number": invoice.invoice_number}


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
        "Veuillez télécharger le PDF et l'envoyer manuellement.",
    )

    return {
        "message": "Invoice send functionality not yet implemented (Phase 1 - Email required)",
        "invoice_number": invoice.invoice_number,
        "recipient": contact.email,
        "pdf_path": pdf_path,
    }
