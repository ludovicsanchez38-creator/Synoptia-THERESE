"""P-104 : documents PDF du chat avec le moteur et le thème des factures."""

import asyncio
import re
import unicodedata
from io import BytesIO
from typing import Any

from app.services.invoice_pdf import _draw_footer, _texte_pdf
from app.services.pdf_theme import SYNOPTIA_THEME
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, HRFlowable, Paragraph, SimpleDocTemplate, Table, TableStyle

from .base import BaseSkill, FileFormat, SkillParams, SkillResult


def _texte(texte: str) -> str:
    """Emphases équilibrées ; tout passage ambigu reste du texte échappé."""
    texte = _texte_pdf(unicodedata.normalize("NFC", texte))
    # Le code déjà échappé reste littéral, même dans une emphase. Les entités
    # protègent ses astérisques de la pile et ses espaces du repli de Paragraph.
    texte = re.sub(
        r"(?<!`)`([^`]+)`(?!`)",
        lambda code: '<font name="Courier">'
        + code[1].replace("*", "&#42;").replace(" ", "&#160;")
        + "</font>",
        texte,
    )
    balises = {1: "i", 2: "b"}
    ouvertures = {1: [1], 2: [2], 3: [2, 1]}
    pile: list[int] = []
    resultat: list[str] = []
    position = 0
    for marqueur in re.finditer(r"\*+", texte):
        taille = len(marqueur[0])
        avant = texte[position:marqueur.start()]
        apres = texte[marqueur.end():marqueur.end() + 1]
        if taille not in ouvertures or avant.endswith("\\"):
            return texte
        resultat.append(avant)
        fermeture = 0
        nombre = 0
        for ouverture in reversed(pile):
            fermeture += ouverture
            nombre += 1
            if fermeture >= taille:
                break
        if fermeture == taille and avant and not avant[-1].isspace():
            for _ in range(nombre):
                resultat.append(f"</{balises[pile.pop()]}>")
        elif (
            apres and not apres.isspace()
            and not any(o in pile for o in ouvertures[taille])
        ):
            for ouverture in ouvertures[taille]:
                pile.append(ouverture)
                resultat.append(f"<{balises[ouverture]}>")
        else:
            return texte
        position = marqueur.end()
    if pile:
        return texte
    resultat.append(texte[position:])
    return "".join(resultat)


def _cellules(ligne: str) -> list[str]:
    return [cellule.strip() for cellule in ligne.strip().strip("|").split("|")]


class PdfSkill(BaseSkill):
    """Le contenu reste du texte : aucun code ni ressource externe exécutés."""

    skill_id = "pdf-pro"
    name = "Document PDF"
    description = "Génère un PDF structuré et paginé avec le style Synoptia"
    output_format = FileFormat.PDF

    def get_system_prompt_addition(self) -> str:
        return (
            "Rédige le contenu du PDF en texte ou Markdown : titres (#, ##, ###), "
            "paragraphes, listes (- ou 1.), gras, italique et tableaux simples "
            "avec une ligne d'en-tête et une ligne de séparation. "
            "Ne fournis ni code Python ni HTML."
        )

    async def execute(self, params: SkillParams) -> SkillResult:
        if not params.content.strip():
            raise ValueError("Le contenu du PDF est vide.")
        file_id = self.generate_file_id()
        output_path = self.get_output_path(file_id, params.title).resolve()
        if not output_path.is_relative_to(self.output_dir.resolve()):
            raise ValueError("Chemin du PDF hors du dossier de sortie autorisé.")

        # Comme les autres documents, la génération ne bloque pas le chat.
        # Le rendu en mémoire évite de laisser un fichier incomplet en cas d'erreur.
        contenu = await asyncio.to_thread(self._construire, params)
        with output_path.open("xb") as fichier:
            fichier.write(contenu)
        return SkillResult(
            file_id=file_id,
            file_path=output_path,
            file_name=output_path.name,
            file_size=len(contenu),
            mime_type=self.get_mime_type(),
            format=self.output_format,
        )

    def _construire(self, params: SkillParams) -> bytes:
        theme = SYNOPTIA_THEME
        styles = theme.get_styles()
        corps = ParagraphStyle(
            "DocumentCorps", parent=styles["normal"], fontSize=10, leading=14,
            spaceAfter=7, splitLongWords=1,
        )
        liste = ParagraphStyle(
            "DocumentListe", parent=corps, leftIndent=14, firstLineIndent=0,
            bulletFontName=theme.font_regular, bulletFontSize=10, spaceAfter=4,
        )
        citation = ParagraphStyle("DocumentCitation", parent=corps, leftIndent=14)
        titres = {
            niveau: ParagraphStyle(
                f"DocumentTitre{niveau}", parent=styles["heading"],
                fontSize=taille, leading=taille + 4, keepWithNext=True,
            )
            for niveau, taille in ((1, 16), (2, 13), (3, 11))
        }
        tampon = BytesIO()
        document = SimpleDocTemplate(
            tampon, pagesize=A4, title=params.title, author="THÉRÈSE",
            leftMargin=theme.margin_left * mm, rightMargin=theme.margin_right * mm,
            topMargin=20 * mm, bottomMargin=28 * mm,
        )
        elements: list[Flowable] = [Paragraph(_texte(params.title), styles["title"])]
        lignes = unicodedata.normalize("NFC", params.content).strip().splitlines()
        paragraphe: list[str] = []

        def terminer_paragraphe() -> None:
            if paragraphe:
                elements.append(Paragraph(_texte("\n".join(paragraphe)).replace("\n", "<br/>"), corps))
                paragraphe.clear()

        i = 0
        while i < len(lignes):
            ligne = lignes[i].strip()
            titre = re.match(r"^(#{1,6})\s+(.+)$", ligne)
            puce = re.match(r"^(?:([-*+])|([0-9]+)[.)])\s+(.+)$", ligne)
            if not ligne:
                terminer_paragraphe()
            elif re.fullmatch(r"-{3,}|\*{3,}|_{3,}", ligne):
                terminer_paragraphe()
                elements.append(HRFlowable(
                    width="100%", color=theme.c_border, thickness=0.5,
                    spaceBefore=7, spaceAfter=7,
                ))
            elif ligne.startswith("> "):
                terminer_paragraphe()
                elements.append(Paragraph(f"<i>{_texte(ligne[2:])}</i>", citation))
            elif titre:
                terminer_paragraphe()
                # Le registre reprend souvent le premier titre du contenu.
                if not (i == 0 and titre[2] == unicodedata.normalize("NFC", params.title)):
                    elements.append(Paragraph(_texte(titre[2]), titres[min(len(titre[1]), 3)]))
            elif puce:
                terminer_paragraphe()
                elements.append(Paragraph(
                    _texte(puce[3]), liste, bulletText=f"{puce[2]}." if puce[2] else "•",
                ))
            elif (
                "|" in ligne and i + 1 < len(lignes)
                and 1 <= len(_cellules(ligne)) <= 12
                and len(_cellules(lignes[i + 1])) == len(_cellules(ligne))
                and all(re.fullmatch(r":?-{3,}:?", c) for c in _cellules(lignes[i + 1]))
            ):
                terminer_paragraphe()
                entete = _cellules(ligne)
                donnees = [[Paragraph(_texte(c), styles["cell_header"]) for c in entete]]
                i += 2
                while i < len(lignes) and "|" in lignes[i]:
                    cellules = _cellules(lignes[i])
                    if len(cellules) != len(entete):
                        break
                    donnees.append([Paragraph(_texte(c), styles["cell"]) for c in cellules])
                    i += 1
                largeur_cellule = document.width / len(entete) - 12
                if any(
                    cellule.wrap(largeur_cellule, document.height)[1] > document.height / 2
                    for rang in donnees for cellule in rang
                ):
                    # Une cellule géante (notamment l'en-tête répété) peut empêcher
                    # Table de se scinder. Les paragraphes gardent chaque cellule
                    # dans l'ordre et coupent les mots longs sur autant de pages
                    # que nécessaire, sans répétition ni suppression de texte.
                    elements.extend(
                        Paragraph(cellule.text, corps) for rang in donnees for cellule in rang
                    )
                    continue
                tableau = Table(
                    donnees, colWidths=[document.width / len(entete)] * len(entete),
                    repeatRows=1, splitByRow=1, splitInRow=1, spaceAfter=8,
                )
                tableau.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), theme.c_primary_dark),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [theme.c_bg_light, theme.c_bg_stripe]),
                    ("GRID", (0, 0), (-1, -1), 0.4, theme.c_border),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                elements.append(tableau)
                continue
            else:
                paragraphe.append(ligne)
            i += 1
        terminer_paragraphe()

        def pied_de_page(canvas: Any, doc: Any) -> None:
            _draw_footer(canvas, doc, theme, ["Généré par THÉRÈSE - Synoptïa"])

        document.build(elements, onFirstPage=pied_de_page, onLaterPages=pied_de_page)
        return tampon.getvalue()
