"""
THERESE v2 - PDF Theme System

Systeme de theming PDF reutilisable pour factures, devis, rapports.
Palette Synoptia : background #0B1226, primary #2451FF, cyan #22D3EE,
magenta #E11D8D, text #E6EDF7.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

logger = logging.getLogger(__name__)

# =====================================================================
# Polices : fallback sur Helvetica si une police custom est absente
# =====================================================================

_FONT_REGISTERED = False


def _ensure_fonts() -> tuple[str, str]:
    """Enregistre les polices custom si disponibles, sinon Helvetica.

    Returns:
        (font_regular, font_bold)
    """
    global _FONT_REGISTERED  # noqa: PLW0603
    if _FONT_REGISTERED:
        return _get_registered_fonts()

    _FONT_REGISTERED = True

    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # Tenter d'enregistrer des polices si elles existent dans le systeme
        # Priorite : Inter > Roboto > Helvetica (fallback natif)
        for family, regular, bold in [
            ("Inter", "Inter-Regular.ttf", "Inter-Bold.ttf"),
            ("Roboto", "Roboto-Regular.ttf", "Roboto-Bold.ttf"),
        ]:
            try:
                pdfmetrics.registerFont(TTFont(family, regular))
                pdfmetrics.registerFont(TTFont(f"{family}-Bold", bold))
                logger.info("Police PDF enregistree : %s", family)
                return family, f"{family}-Bold"
            except Exception:
                continue
    except Exception as exc:
        logger.debug("Echec enregistrement polices custom : %s", exc)

    logger.debug("Fallback sur Helvetica")
    return "Helvetica", "Helvetica-Bold"


def _get_registered_fonts() -> tuple[str, str]:
    """Retourne les polices actuellement enregistrees."""
    try:
        from reportlab.pdfbase import pdfmetrics

        for family in ("Inter", "Roboto"):
            if family in pdfmetrics.getRegisteredFontNames():
                return family, f"{family}-Bold"
    except Exception:
        pass
    return "Helvetica", "Helvetica-Bold"


# =====================================================================
# PDFTheme : configuration visuelle reutilisable
# =====================================================================


@dataclass(frozen=True)
class PDFTheme:
    """Theme PDF reutilisable.

    Contient les couleurs, polices et dimensions pour generer
    des documents PDF homogenes (factures, devis, rapports).
    """

    # -- Couleurs principales --
    primary: str = "#2451FF"
    primary_dark: str = "#0B1226"
    accent_cyan: str = "#22D3EE"
    accent_magenta: str = "#E11D8D"
    text_dark: str = "#1A1A2E"
    text_light: str = "#E6EDF7"
    bg_light: str = "#F7F8FC"
    bg_stripe: str = "#EEF1F8"
    border: str = "#D1D5E0"
    success: str = "#10B981"

    # -- Polices (resolues au runtime) --
    font_regular: str = ""
    font_bold: str = ""

    # -- Dimensions (en mm) --
    margin_top: float = 15.0
    margin_bottom: float = 15.0
    margin_left: float = 18.0
    margin_right: float = 18.0
    header_height: float = 28.0

    # -- Infos societe (optionnelles, injectees a la generation) --
    company_name: str = ""
    company_tagline: str = ""

    def __post_init__(self) -> None:
        """Resout les polices si non specifiees."""
        if not self.font_regular or not self.font_bold:
            regular, bold = _ensure_fonts()
            # frozen=True => on passe par __dict__ pour initialiser
            object.__setattr__(self, "font_regular", regular)
            object.__setattr__(self, "font_bold", bold)

    # -- Couleurs reportlab --

    @property
    def c_primary(self) -> colors.Color:
        return HexColor(self.primary)

    @property
    def c_primary_dark(self) -> colors.Color:
        return HexColor(self.primary_dark)

    @property
    def c_accent_cyan(self) -> colors.Color:
        return HexColor(self.accent_cyan)

    @property
    def c_accent_magenta(self) -> colors.Color:
        return HexColor(self.accent_magenta)

    @property
    def c_text_dark(self) -> colors.Color:
        return HexColor(self.text_dark)

    @property
    def c_text_light(self) -> colors.Color:
        return HexColor(self.text_light)

    @property
    def c_bg_light(self) -> colors.Color:
        return HexColor(self.bg_light)

    @property
    def c_bg_stripe(self) -> colors.Color:
        return HexColor(self.bg_stripe)

    @property
    def c_border(self) -> colors.Color:
        return HexColor(self.border)

    @property
    def c_success(self) -> colors.Color:
        return HexColor(self.success)

    # -- Styles paragraphe --

    def get_styles(self) -> dict[str, ParagraphStyle]:
        """Retourne un dictionnaire de styles paragraphe thematises."""
        base = getSampleStyleSheet()

        return {
            "title": ParagraphStyle(
                "ThemeTitle",
                parent=base["Heading1"],
                fontName=self.font_bold,
                fontSize=22,
                textColor=self.c_primary_dark,
                spaceAfter=4,
                leading=26,
            ),
            "subtitle": ParagraphStyle(
                "ThemeSubtitle",
                parent=base["Normal"],
                fontName=self.font_regular,
                fontSize=11,
                textColor=HexColor("#6B7280"),
                spaceAfter=10,
            ),
            "heading": ParagraphStyle(
                "ThemeHeading",
                parent=base["Heading2"],
                fontName=self.font_bold,
                fontSize=11,
                textColor=self.c_primary,
                spaceBefore=8,
                spaceAfter=4,
            ),
            "normal": ParagraphStyle(
                "ThemeNormal",
                parent=base["Normal"],
                fontName=self.font_regular,
                fontSize=9,
                textColor=self.c_text_dark,
                leading=13,
            ),
            "normal_bold": ParagraphStyle(
                "ThemeNormalBold",
                parent=base["Normal"],
                fontName=self.font_bold,
                fontSize=9,
                textColor=self.c_text_dark,
                leading=13,
            ),
            "small": ParagraphStyle(
                "ThemeSmall",
                parent=base["Normal"],
                fontName=self.font_regular,
                fontSize=7.5,
                textColor=HexColor("#6B7280"),
                leading=10,
            ),
            "footer": ParagraphStyle(
                "ThemeFooter",
                parent=base["Normal"],
                fontName=self.font_regular,
                fontSize=7,
                textColor=HexColor("#9CA3AF"),
                alignment=TA_CENTER,
                leading=9,
            ),
            "cell": ParagraphStyle(
                "ThemeCell",
                parent=base["Normal"],
                fontName=self.font_regular,
                fontSize=8.5,
                textColor=self.c_text_dark,
                leading=11,
            ),
            "cell_bold": ParagraphStyle(
                "ThemeCellBold",
                parent=base["Normal"],
                fontName=self.font_bold,
                fontSize=8.5,
                textColor=self.c_text_dark,
                leading=11,
            ),
            "cell_header": ParagraphStyle(
                "ThemeCellHeader",
                parent=base["Normal"],
                fontName=self.font_bold,
                fontSize=8.5,
                textColor=colors.white,
                leading=11,
            ),
            "total_label": ParagraphStyle(
                "ThemeTotalLabel",
                parent=base["Normal"],
                fontName=self.font_bold,
                fontSize=10,
                textColor=self.c_text_dark,
                alignment=TA_RIGHT,
            ),
            "total_value": ParagraphStyle(
                "ThemeTotalValue",
                parent=base["Normal"],
                fontName=self.font_bold,
                fontSize=10,
                textColor=self.c_text_dark,
                alignment=TA_RIGHT,
            ),
            "total_ttc_label": ParagraphStyle(
                "ThemeTTCLabel",
                parent=base["Normal"],
                fontName=self.font_bold,
                fontSize=12,
                textColor=colors.white,
                alignment=TA_RIGHT,
            ),
            "total_ttc_value": ParagraphStyle(
                "ThemeTTCValue",
                parent=base["Normal"],
                fontName=self.font_bold,
                fontSize=12,
                textColor=colors.white,
                alignment=TA_RIGHT,
            ),
        }


# =====================================================================
# Theme par defaut Synoptia
# =====================================================================

SYNOPTIA_THEME = PDFTheme(
    primary="#2451FF",
    primary_dark="#0B1226",
    accent_cyan="#22D3EE",
    accent_magenta="#E11D8D",
)
