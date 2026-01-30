"""
THÉRÈSE v2 - Invoice PDF Generator

Service de génération de factures PDF conformes à la réglementation française.
Phase 4 - Invoicing
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

# Taux TVA français
TVA_RATES = {
    20.0: "TVA normale 20%",
    10.0: "TVA intermédiaire 10%",
    5.5: "TVA réduite 5,5%",
    2.1: "TVA super réduite 2,1%",
    0.0: "TVA à 0%",
}


class InvoicePDFGenerator:
    """Générateur de factures PDF conformes France."""

    def __init__(self, output_dir: str = "~/.therese/invoices"):
        """
        Initialise le générateur.

        Args:
            output_dir: Répertoire de sortie des PDFs
        """
        self.output_dir = Path(output_dir).expanduser()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_invoice_pdf(
        self,
        invoice_data: Dict[str, Any],
        contact_data: Dict[str, Any],
        user_profile: Dict[str, Any],
    ) -> str:
        """
        Génère une facture PDF.

        Args:
            invoice_data: Données de la facture (invoice_number, lines, totals, etc.)
            contact_data: Données du client (name, email, company, address, etc.)
            user_profile: Données du profil utilisateur (nom, entreprise, SIREN, adresse)

        Returns:
            Chemin absolu du fichier PDF généré
        """
        invoice_number = invoice_data["invoice_number"]
        filename = f"{invoice_number}.pdf"
        filepath = self.output_dir / filename

        # Create PDF
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        # Build content
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#0B1226"),
            spaceAfter=12,
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#22D3EE"),
            spaceAfter=6,
        )

        normal_style = styles["Normal"]

        # =====================================================================
        # HEADER: Émetteur et Destinataire
        # =====================================================================

        # Title
        story.append(Paragraph("FACTURE", title_style))
        story.append(Spacer(1, 10 * mm))

        # Émetteur (left) et Destinataire (right)
        header_data = [
            [
                Paragraph("<b>Émetteur</b>", heading_style),
                Paragraph("<b>Destinataire</b>", heading_style),
            ],
            [
                Paragraph(
                    f"<b>{user_profile.get('company', user_profile.get('name', ''))}</b><br/>"
                    f"{user_profile.get('name', '')}<br/>"
                    f"{user_profile.get('address', '')}<br/>"
                    f"SIREN: {user_profile.get('siren', 'N/A')}<br/>"
                    f"TVA: {user_profile.get('tva_intra', 'N/A')}",
                    normal_style,
                ),
                Paragraph(
                    f"<b>{contact_data.get('company', contact_data.get('name', ''))}</b><br/>"
                    f"{contact_data.get('name', '')}<br/>"
                    f"{contact_data.get('email', '')}<br/>"
                    f"{contact_data.get('phone', '')}",
                    normal_style,
                ),
            ],
        ]

        header_table = Table(header_data, colWidths=[90 * mm, 90 * mm])
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ]
            )
        )
        story.append(header_table)
        story.append(Spacer(1, 10 * mm))

        # =====================================================================
        # INFO FACTURE
        # =====================================================================

        info_data = [
            ["Facture N°", invoice_number],
            [
                "Date d'émission",
                datetime.fromisoformat(invoice_data["issue_date"].replace("Z", "")).strftime(
                    "%d/%m/%Y"
                ),
            ],
            [
                "Date d'échéance",
                datetime.fromisoformat(invoice_data["due_date"].replace("Z", "")).strftime(
                    "%d/%m/%Y"
                ),
            ],
            ["Statut", invoice_data["status"].upper()],
        ]

        info_table = Table(info_data, colWidths=[60 * mm, 120 * mm])
        info_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0F0F0")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        story.append(info_table)
        story.append(Spacer(1, 10 * mm))

        # =====================================================================
        # LIGNES DE FACTURATION
        # =====================================================================

        story.append(Paragraph("<b>Détail des prestations</b>", heading_style))
        story.append(Spacer(1, 3 * mm))

        # Table header
        lines_data = [
            ["Description", "Qté", "Prix HT", "TVA", "Total HT", "Total TTC"]
        ]

        # Lines
        for line in invoice_data["lines"]:
            lines_data.append(
                [
                    line["description"],
                    str(line["quantity"]),
                    f"{line['unit_price_ht']:.2f} €",
                    f"{line['tva_rate']:.1f}%",
                    f"{line['total_ht']:.2f} €",
                    f"{line['total_ttc']:.2f} €",
                ]
            )

        lines_table = Table(
            lines_data,
            colWidths=[60 * mm, 15 * mm, 25 * mm, 20 * mm, 25 * mm, 25 * mm],
        )
        lines_table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#22D3EE")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ALIGN", (0, 1), (0, -1), "LEFT"),  # Description left-aligned
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    # Body rows
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    # Alternating row colors
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9F9F9")]),
                ]
            )
        )
        story.append(lines_table)
        story.append(Spacer(1, 10 * mm))

        # =====================================================================
        # TOTAUX
        # =====================================================================

        totals_data = [
            ["Total HT", f"{invoice_data['subtotal_ht']:.2f} €"],
            ["Total TVA", f"{invoice_data['total_tax']:.2f} €"],
            ["Total TTC", f"{invoice_data['total_ttc']:.2f} €"],
        ]

        totals_table = Table(totals_data, colWidths=[140 * mm, 30 * mm])
        totals_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    # Total TTC emphasized
                    ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#22D3EE")),
                    ("TEXTCOLOR", (0, 2), (-1, 2), colors.white),
                    ("FONTSIZE", (0, 2), (-1, 2), 14),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(totals_table)
        story.append(Spacer(1, 10 * mm))

        # =====================================================================
        # NOTES & CONDITIONS
        # =====================================================================

        if invoice_data.get("notes"):
            story.append(Paragraph("<b>Notes</b>", heading_style))
            story.append(Paragraph(invoice_data["notes"], normal_style))
            story.append(Spacer(1, 5 * mm))

        # Conditions de paiement (mentions obligatoires France)
        conditions = """
        <b>Conditions de paiement :</b><br/>
        Paiement à réception de facture, net à 30 jours.<br/>
        En cas de retard de paiement, application d'intérêts de retard au taux légal.<br/>
        Indemnité forfaitaire pour frais de recouvrement : 40 €.<br/>
        <br/>
        <b>Mentions légales obligatoires :</b><br/>
        TVA non applicable, art. 293 B du CGI (si micro-entreprise).<br/>
        Pas de TVA facturée (art. 293 B du CGI).<br/>
        """
        story.append(Paragraph(conditions, normal_style))

        # Build PDF
        doc.build(story)

        logger.info(f"Invoice PDF generated: {filepath}")
        return str(filepath.absolute())

    def delete_invoice_pdf(self, invoice_number: str) -> bool:
        """
        Supprime un fichier PDF de facture.

        Args:
            invoice_number: Numéro de facture

        Returns:
            True si supprimé, False sinon
        """
        filename = f"{invoice_number}.pdf"
        filepath = self.output_dir / filename

        if filepath.exists():
            filepath.unlink()
            logger.info(f"Invoice PDF deleted: {filepath}")
            return True

        logger.warning(f"Invoice PDF not found: {filepath}")
        return False
