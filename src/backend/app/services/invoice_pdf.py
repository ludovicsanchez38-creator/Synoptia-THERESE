"""
THERESE v2 - Invoice PDF Generator

Service de generation de factures PDF conformes a la reglementation francaise.
Phase 4 - Invoicing

Refonte visuelle : utilise PDFTheme pour un rendu professionnel
avec la palette Synoptia (primary #2451FF, cyan #22D3EE, dark #0B1226).
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from app.services.pdf_theme import SYNOPTIA_THEME, PDFTheme
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

# Taux TVA francais
TVA_RATES = {
    20.0: "TVA normale 20%",
    10.0: "TVA intermediaire 10%",
    5.5: "TVA reduite 5,5%",
    2.1: "TVA super reduite 2,1%",
    0.0: "TVA a 0%",
}

# Mapping devise vers symbole d'affichage
CURRENCY_SYMBOLS: dict[str, str] = {
    "EUR": "\u20ac",
    "CHF": "CHF",
    "GBP": "\u00a3",
    "USD": "$",
}

# Fallback par defaut (utilise uniquement si aucun dossier de travail configure)
_DEFAULT_INVOICE_DIR = "~/.therese/invoices"


def resolve_invoice_output_dir() -> str:
    """
    Resout le repertoire de sortie des PDFs factures depuis la base de donnees.

    Utilise le dossier de travail configure (Preference working_directory) + sous-dossier
    'factures'. Fallback sur ~/.therese/invoices si pas de dossier configure.

    Returns:
        Chemin absolu du repertoire de sortie
    """
    try:
        from app.models.database import get_sync_session
        from app.models.entities import Preference
        from sqlmodel import select

        with get_sync_session() as session:
            result = session.execute(
                select(Preference).where(Preference.key == "working_directory")
            )
            pref = result.scalar_one_or_none()
            if pref and pref.value:
                resolved = os.path.join(pref.value, "factures")
                logger.debug("Repertoire factures resolu depuis les preferences : %s", resolved)
                return resolved
    except Exception as exc:
        logger.warning("Impossible de resoudre le dossier de travail depuis la DB : %s", exc)

    fallback = os.path.expanduser(_DEFAULT_INVOICE_DIR)
    logger.debug("Repertoire factures : fallback par defaut %s", fallback)
    return fallback


# =====================================================================
# Fonctions utilitaires de mise en page
# =====================================================================


def _draw_header_band(
    canvas: Any,
    doc: Any,
    theme: PDFTheme,
) -> None:
    """Dessine la bande de couleur en haut de page."""
    page_w, page_h = A4
    band_h = theme.header_height * mm
    canvas.saveState()
    canvas.setFillColor(theme.c_primary_dark)
    canvas.rect(0, page_h - band_h, page_w, band_h, fill=1, stroke=0)
    canvas.restoreState()


def _draw_footer(
    canvas: Any,
    doc: Any,
    theme: PDFTheme,
    footer_lines: list[str],
) -> None:
    """Dessine le pied de page avec mentions legales et numero de page."""
    page_w, _page_h = A4
    canvas.saveState()

    # Ligne de separation
    y_line = 22 * mm
    canvas.setStrokeColor(theme.c_border)
    canvas.setLineWidth(0.5)
    canvas.line(
        theme.margin_left * mm,
        y_line,
        page_w - theme.margin_right * mm,
        y_line,
    )

    # Texte du footer
    canvas.setFont(theme.font_regular, 7)
    canvas.setFillColor(HexColor("#9CA3AF"))
    y = 18 * mm
    for line in footer_lines:
        canvas.drawCentredString(page_w / 2, y, line)
        y -= 9

    # Numero de page
    canvas.setFont(theme.font_regular, 7)
    canvas.drawRightString(
        page_w - theme.margin_right * mm,
        8 * mm,
        f"Page {canvas.getPageNumber()}",
    )

    canvas.restoreState()


def _make_header_footer(
    theme: PDFTheme,
    footer_lines: list[str],
):
    """Fabrique les callbacks onFirstPage / onLaterPages pour SimpleDocTemplate."""

    def on_page(canvas: Any, doc: Any) -> None:
        _draw_header_band(canvas, doc, theme)
        _draw_footer(canvas, doc, theme, footer_lines)

    return on_page, on_page


# =====================================================================
# InvoicePDFGenerator
# =====================================================================


class InvoicePDFGenerator:
    """Generateur de factures PDF conformes France avec theming Synoptia."""

    def __init__(
        self,
        output_dir: str | None = None,
        theme: PDFTheme | None = None,
    ):
        """
        Initialise le generateur.

        Args:
            output_dir: Repertoire de sortie des PDFs. Si None, resolu automatiquement
                        depuis le dossier de travail configure (BUG-094).
            theme: Theme PDF a utiliser. Si None, theme Synoptia par defaut.
        """
        if output_dir is None:
            output_dir = resolve_invoice_output_dir()
        self.output_dir = Path(output_dir).expanduser()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.theme = theme or SYNOPTIA_THEME
        self.styles = self.theme.get_styles()
        logger.info("InvoicePDFGenerator initialise : output_dir=%s", self.output_dir)

    # -----------------------------------------------------------------
    # Construction des blocs
    # -----------------------------------------------------------------

    def _build_doc_title_block(
        self,
        document_type: str,
        invoice_number: str,
    ) -> list[Any]:
        """Construit le bloc titre du document (dans la bande sombre du header)."""
        title_map = {
            "devis": "DEVIS",
            "facture": "FACTURE",
            "avoir": "AVOIR",
        }
        doc_title = title_map.get(document_type, "FACTURE")

        # Le titre est affiche en blanc sur fond sombre via la bande header
        title_style = ParagraphStyle(
            "DocTitle",
            fontName=self.theme.font_bold,
            fontSize=22,
            textColor=colors.white,
            leading=26,
        )
        number_style = ParagraphStyle(
            "DocNumber",
            fontName=self.theme.font_regular,
            fontSize=11,
            textColor=HexColor("#93A3C0"),
            leading=14,
        )

        elements: list[Any] = []
        elements.append(Paragraph(doc_title, title_style))
        elements.append(Spacer(1, 1 * mm))
        elements.append(Paragraph(f"N. {invoice_number}", number_style))
        elements.append(Spacer(1, 8 * mm))
        return elements

    def _build_parties_block(
        self,
        user_profile: dict[str, Any],
        contact_data: dict[str, Any],
    ) -> list[Any]:
        """Construit le bloc emetteur / destinataire cote a cote."""
        s = self.styles
        theme = self.theme

        # -- Emetteur --
        emetteur_parts: list[str] = []
        company = user_profile.get("company") or user_profile.get("name", "")
        if company:
            emetteur_parts.append(
                f'<font name="{theme.font_bold}" size="10">{company}</font>'
            )
        name = user_profile.get("name", "")
        if name and name != company:
            emetteur_parts.append(name)
        address = user_profile.get("address", "")
        if address:
            emetteur_parts.append(address)
        siret = user_profile.get("siret") or user_profile.get("siren", "")
        if siret:
            emetteur_parts.append(f"SIRET : {siret}")
        code_ape = user_profile.get("code_ape", "")
        if code_ape:
            emetteur_parts.append(f"Code APE : {code_ape}")
        tva_intra = user_profile.get("tva_intra", "")
        if tva_intra:
            emetteur_parts.append(f"TVA intra : {tva_intra}")

        # -- Destinataire --
        dest_parts: list[str] = []
        dest_company = contact_data.get("company") or contact_data.get("name", "")
        if dest_company:
            dest_parts.append(
                f'<font name="{theme.font_bold}" size="10">{dest_company}</font>'
            )
        dest_name = contact_data.get("name", "")
        if dest_name and dest_name != dest_company:
            dest_parts.append(dest_name)
        dest_address = contact_data.get("address", "")
        if dest_address:
            dest_parts.append(dest_address)
        if contact_data.get("email"):
            dest_parts.append(contact_data["email"])
        if contact_data.get("phone"):
            dest_parts.append(contact_data["phone"])

        # Label
        label_style = ParagraphStyle(
            "PartyLabel",
            fontName=theme.font_bold,
            fontSize=8,
            textColor=theme.c_primary,
            spaceAfter=2,
        )

        header_data = [
            [
                Paragraph("EMETTEUR", label_style),
                Paragraph("DESTINATAIRE", label_style),
            ],
            [
                Paragraph("<br/>".join(emetteur_parts), s["normal"]),
                Paragraph("<br/>".join(dest_parts), s["normal"]),
            ],
        ]

        t = Table(header_data, colWidths=[85 * mm, 85 * mm])
        t.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )

        return [t, Spacer(1, 6 * mm)]

    def _build_info_block(
        self,
        invoice_data: dict[str, Any],
        document_type: str,
    ) -> list[Any]:
        """Construit le bloc d'informations (dates, statut) sous forme de pastilles."""
        theme = self.theme

        numero_label_map = {
            "devis": "Devis N.",
            "facture": "Facture N.",
            "avoir": "Avoir N.",
        }
        numero_label = numero_label_map.get(document_type, "Facture N.")

        issue_date = datetime.fromisoformat(
            invoice_data["issue_date"].replace("Z", "")
        ).strftime("%d/%m/%Y")
        due_date = datetime.fromisoformat(
            invoice_data["due_date"].replace("Z", "")
        ).strftime("%d/%m/%Y")

        status_raw = invoice_data["status"].upper()

        info_data = [
            [numero_label, invoice_data["invoice_number"]],
            ["Date d'emission", issue_date],
            ["Date d'echeance", due_date],
            ["Statut", status_raw],
        ]

        # Ajouter la duree de validite pour les devis
        validite = invoice_data.get("validite_jours")
        if document_type == "devis" and validite:
            info_data.insert(3, ["Validite", f"{validite} jours"])

        cell_label = ParagraphStyle(
            "InfoLabel",
            fontName=theme.font_bold,
            fontSize=8.5,
            textColor=theme.c_text_dark,
        )
        cell_value = ParagraphStyle(
            "InfoValue",
            fontName=theme.font_regular,
            fontSize=8.5,
            textColor=theme.c_text_dark,
        )

        rows = []
        for label, value in info_data:
            rows.append([
                Paragraph(label, cell_label),
                Paragraph(str(value), cell_value),
            ])

        t = Table(rows, colWidths=[45 * mm, 125 * mm])
        t.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), theme.c_bg_light),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, theme.c_border),
                ("LINEBELOW", (0, -1), (-1, -1), 0.4, theme.c_border),
                ("LINEBEFORE", (0, 0), (0, -1), 0.4, theme.c_border),
                ("LINEAFTER", (-1, 0), (-1, -1), 0.4, theme.c_border),
                ("LINEABOVE", (0, 0), (-1, 0), 0.4, theme.c_border),
            ])
        )

        return [t, Spacer(1, 8 * mm)]

    def _build_lines_table(
        self,
        lines: list[dict[str, Any]],
        tva_applicable: bool,
        currency_symbol: str,
    ) -> list[Any]:
        """Construit le tableau des lignes de facturation."""
        theme = self.theme
        s = self.styles

        # Section heading
        heading = Paragraph(
            "DETAIL DES PRESTATIONS",
            ParagraphStyle(
                "LinesHeading",
                fontName=theme.font_bold,
                fontSize=9,
                textColor=theme.c_primary,
                spaceBefore=0,
                spaceAfter=4,
            ),
        )

        # Header row
        headers = ["Description", "Qte", "Prix unit. HT", "TVA", "Total HT", "Total TTC"]
        header_cells = [Paragraph(h, s["cell_header"]) for h in headers]

        table_data = [header_cells]

        for line in lines:
            if tva_applicable:
                tva_display = f"{line['tva_rate']:.1f}%"
                ttc_display = f"{line['total_ttc']:.2f} {currency_symbol}"
            else:
                tva_display = "0,0%"
                ttc_display = f"{line['total_ht']:.2f} {currency_symbol}"

            row = [
                Paragraph(line["description"], s["cell"]),
                Paragraph(str(line["quantity"]), s["cell"]),
                Paragraph(f"{line['unit_price_ht']:.2f} {currency_symbol}", s["cell"]),
                Paragraph(tva_display, s["cell"]),
                Paragraph(f"{line['total_ht']:.2f} {currency_symbol}", s["cell"]),
                Paragraph(ttc_display, s["cell_bold"]),
            ]
            table_data.append(row)

        col_widths = [62 * mm, 14 * mm, 24 * mm, 18 * mm, 24 * mm, 28 * mm]
        t = Table(table_data, colWidths=col_widths)

        style_cmds: list[Any] = [
            # Header
            ("BACKGROUND", (0, 0), (-1, 0), theme.c_primary),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            # Body alignment
            ("ALIGN", (0, 1), (0, -1), "LEFT"),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            # Padding
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            # Borders
            ("LINEBELOW", (0, 0), (-1, 0), 1, theme.c_primary),
            ("LINEBELOW", (0, 1), (-1, -1), 0.3, theme.c_border),
            # Zebra striping
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, theme.c_bg_stripe]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        t.setStyle(TableStyle(style_cmds))

        return [heading, Spacer(1, 2 * mm), t, Spacer(1, 8 * mm)]

    def _build_totals_block(
        self,
        invoice_data: dict[str, Any],
        tva_applicable: bool,
        currency_symbol: str,
    ) -> list[Any]:
        """Construit le bloc des totaux, aligne a droite."""
        theme = self.theme
        s = self.styles

        if tva_applicable:
            rows_data = [
                ("Total HT", f"{invoice_data['subtotal_ht']:.2f} {currency_symbol}"),
                ("Total TVA", f"{invoice_data['total_tax']:.2f} {currency_symbol}"),
                ("Total TTC", f"{invoice_data['total_ttc']:.2f} {currency_symbol}"),
            ]
        else:
            rows_data = [
                ("Total HT", f"{invoice_data['subtotal_ht']:.2f} {currency_symbol}"),
                ("Total TVA", f"0,00 {currency_symbol}"),
                ("Total TTC", f"{invoice_data['subtotal_ht']:.2f} {currency_symbol}"),
            ]

        table_rows = []
        for i, (label, value) in enumerate(rows_data):
            is_ttc = i == len(rows_data) - 1
            if is_ttc:
                table_rows.append([
                    Paragraph(label, s["total_ttc_label"]),
                    Paragraph(value, s["total_ttc_value"]),
                ])
            else:
                table_rows.append([
                    Paragraph(label, s["total_label"]),
                    Paragraph(value, s["total_value"]),
                ])

        t = Table(table_rows, colWidths=[30 * mm, 35 * mm])
        t.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                # Ligne de separation sous les lignes HT/TVA
                ("LINEBELOW", (0, 0), (-1, -2), 0.3, theme.c_border),
                # Fond colore pour la ligne TTC
                ("BACKGROUND", (0, -1), (-1, -1), theme.c_primary),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
                # Bordure arrondie simulee par un contour
                ("BOX", (0, 0), (-1, -1), 0.5, theme.c_border),
            ])
        )

        # Wrapper pour aligner a droite
        wrapper = Table([[t]], colWidths=[170 * mm])
        wrapper.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ])
        )

        return [wrapper, Spacer(1, 8 * mm)]

    def _build_notes_block(
        self,
        notes: str,
    ) -> list[Any]:
        """Construit le bloc notes si present."""
        if not notes:
            return []
        s = self.styles
        theme = self.theme

        heading = Paragraph(
            "NOTES",
            ParagraphStyle(
                "NotesHeading",
                fontName=theme.font_bold,
                fontSize=9,
                textColor=theme.c_primary,
                spaceAfter=3,
            ),
        )
        body = Paragraph(notes, s["normal"])
        return [heading, body, Spacer(1, 6 * mm)]

    def _build_conditions_block(
        self,
        tva_applicable: bool,
        currency_symbol: str,
    ) -> list[Any]:
        """Construit le bloc conditions de paiement et mentions legales."""
        s = self.styles
        theme = self.theme

        if tva_applicable:
            tva_mention = "TVA incluse selon les taux en vigueur."
        else:
            tva_mention = "TVA non applicable, art. 293 B du CGI."

        heading = Paragraph(
            "CONDITIONS" if self._current_document_type == "devis" else "CONDITIONS DE PAIEMENT",
            ParagraphStyle(
                "ConditionsHeading",
                fontName=theme.font_bold,
                fontSize=9,
                textColor=theme.c_primary,
                spaceAfter=3,
            ),
        )

        conditions_text = (
            f"Paiement a reception de facture, net a 30 jours.<br/>"
            f"En cas de retard de paiement, application d'interets de retard au taux legal.<br/>"
            f"Indemnite forfaitaire pour frais de recouvrement : 40 {currency_symbol}.<br/>"
            f"<br/>"
            f"<b>Mentions legales :</b> {tva_mention}"
        )
        body = Paragraph(conditions_text, s["small"])

        return [heading, body]

    # -----------------------------------------------------------------
    # Generation principale
    # -----------------------------------------------------------------

    def generate_invoice_pdf(
        self,
        invoice_data: dict[str, Any],
        contact_data: dict[str, Any],
        user_profile: dict[str, Any],
        currency: str = "EUR",
    ) -> str:
        """
        Genere une facture PDF avec le theme Synoptia.

        Args:
            invoice_data: Donnees de la facture (invoice_number, lines, totals, etc.)
            contact_data: Donnees du client (name, email, company, address, etc.)
            user_profile: Donnees du profil utilisateur (nom, entreprise, SIREN, adresse)
            currency: Code devise (EUR, CHF, USD, GBP)

        Returns:
            Chemin absolu du fichier PDF genere
        """
        theme = self.theme
        currency_symbol = CURRENCY_SYMBOLS.get(currency, currency)
        invoice_number = invoice_data["invoice_number"]
        filename = f"{invoice_number}.pdf"
        filepath = self.output_dir / filename

        document_type = invoice_data.get("document_type", "facture")
        tva_applicable = invoice_data.get("tva_applicable", True)

        # Footer lines
        company = user_profile.get("company", "")
        siret = user_profile.get("siret") or user_profile.get("siren", "")
        tva_intra = user_profile.get("tva_intra", "")
        footer_parts = [p for p in [company, f"SIRET {siret}" if siret else "", f"TVA {tva_intra}" if tva_intra else ""] if p]
        footer_lines = [" - ".join(footer_parts)] if footer_parts else []
        footer_lines.append(f"Document genere par THERESE - {datetime.now().strftime('%d/%m/%Y')}")

        on_first, on_later = _make_header_footer(theme, footer_lines)

        # Document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=theme.margin_right * mm,
            leftMargin=theme.margin_left * mm,
            topMargin=(theme.margin_top + theme.header_height) * mm,
            bottomMargin=(theme.margin_bottom + 10) * mm,
        )

        # Store document_type for use in conditions block
        self._current_document_type = document_type

        # Story
        story: list[Any] = []

        # 1. Titre du document (dans l'espace sous la bande header)
        story.extend(self._build_doc_title_block(document_type, invoice_number))

        # 2. Emetteur / Destinataire
        story.extend(self._build_parties_block(user_profile, contact_data))

        # 3. Informations facture
        story.extend(self._build_info_block(invoice_data, document_type))

        # 4. Lignes de facturation
        story.extend(
            self._build_lines_table(
                invoice_data["lines"],
                tva_applicable,
                currency_symbol,
            )
        )

        # 5. Totaux
        story.extend(
            self._build_totals_block(invoice_data, tva_applicable, currency_symbol)
        )

        # 6. Notes
        story.extend(self._build_notes_block(invoice_data.get("notes", "")))

        # 7. Conditions de paiement
        story.extend(self._build_conditions_block(tva_applicable, currency_symbol))

        # Build PDF
        doc.build(story, onFirstPage=on_first, onLaterPages=on_later)

        logger.info("Invoice PDF generated: %s", filepath)
        return str(filepath.absolute())

    def delete_invoice_pdf(self, invoice_number: str) -> bool:
        """
        Supprime un fichier PDF de facture.

        Args:
            invoice_number: Numero de facture

        Returns:
            True si supprime, False sinon
        """
        filename = f"{invoice_number}.pdf"
        filepath = self.output_dir / filename

        if filepath.exists():
            filepath.unlink()
            logger.info("Invoice PDF deleted: %s", filepath)
            return True

        logger.warning("Invoice PDF not found: %s", filepath)
        return False
