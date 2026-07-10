"""
THERESE v2 - Conversion Markdown -> DOCX déterministe (BUG-135).

Chemin d'export des documents de l'Atelier documentaire et des conversations.
Contrairement au pipeline LLM (CodeGenSkill/DocxSkill), ce convertisseur :
- ne supprime JAMAIS de contenu : les blocs ``` clôturés sont rendus en
  préformaté, une fence orpheline ne tronque pas la suite du document ;
- n'exécute jamais de code présent dans le document (un bloc ```python```
  est du contenu, pas un générateur) ;
- pose la langue de correction fr-FR (docDefaults + style Normal), au lieu
  du en-US hérité du template python-docx.
"""

import re
from pathlib import Path

from app.services.skills.docx_generator import SYNOPTIA_COLORS
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt

# Segments inline **gras**, *italique*, `code` - tout le reste (y compris les
# * ou ` non appariés) est ajouté tel quel, jamais jeté.
_INLINE_PATTERN = re.compile(r"(\*\*.+?\*\*|\*[^*\n]+?\*|`[^`\n]+?`)")
_TABLE_SEPARATOR = re.compile(r"^\|?[\s\-:|]+\|?\s*$")
_HR_PATTERN = re.compile(r"^(-{3,}|\*{3,}|_{3,})\s*$")


def render_markdown_docx(markdown: str, output_path: Path) -> None:
    """Rend un document Markdown complet en .docx stylé Synoptia, fr-FR."""
    doc = Document()
    _setup_styles(doc)
    _set_language(doc, "fr-FR")
    _render_blocks(doc, markdown)
    _add_footer(doc)
    doc.save(str(output_path))


def _set_language(doc: Document, lang: str) -> None:
    """Pose w:lang sur les docDefaults ET le style Normal (correction Word)."""
    rpr_defaults = doc.styles.element.findall(
        f"{qn('w:docDefaults')}/{qn('w:rPrDefault')}/{qn('w:rPr')}"
    )
    targets = list(rpr_defaults)
    targets.append(doc.styles["Normal"].element.get_or_add_rPr())
    for rpr in targets:
        for existing in rpr.findall(qn("w:lang")):
            rpr.remove(existing)
        lang_el = rpr.makeelement(qn("w:lang"), {})
        lang_el.set(qn("w:val"), lang)
        lang_el.set(qn("w:eastAsia"), lang)
        rpr.append(lang_el)


def _render_blocks(doc: Document, markdown: str) -> None:
    """Machine à états ligne par ligne - aucune branche ne jette de contenu."""
    in_code = False
    first_h1_done = False
    table_buffer: list[str] = []

    for raw in markdown.split("\n"):
        line = raw.strip()

        if in_code:
            if line.startswith("```"):
                in_code = False
            else:
                _add_preformatted(doc, raw)
            continue

        if not line.startswith("|"):
            _flush_table(doc, table_buffer)

        if line.startswith("```"):
            # Fence ouvrante : le contenu sera rendu préformaté. Si elle n'est
            # jamais refermée, TOUT le reste sort en préformaté (zéro perte).
            in_code = True
            continue

        if not line:
            continue

        if line.startswith("|"):
            table_buffer.append(line)
        elif line.startswith("#### "):
            doc.add_heading(line[5:], level=4)
        elif line.startswith("### "):
            doc.add_heading(line[4:], level=3)
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=2)
        elif line.startswith("# "):
            if first_h1_done:
                doc.add_heading(line[2:], level=1)
            else:
                # Premier # = titre principal du document (style hero), les
                # suivants redeviennent des Heading 1 ordinaires.
                para = doc.add_heading(line[2:], level=0)
                _style_title(para)
                first_h1_done = True
        elif _HR_PATTERN.match(line):
            continue  # séparateur horizontal : pas de texte littéral
        elif line.startswith("> "):
            para = doc.add_paragraph()
            _add_formatted_text(para, line[2:])
            for run in para.runs:
                run.italic = True
        elif line.startswith("- ") or line.startswith("* "):
            para = doc.add_paragraph(style="List Bullet")
            _add_formatted_text(para, line[2:])
        elif re.match(r"^\d+\.\s", line):
            para = doc.add_paragraph(style="List Number")
            _add_formatted_text(para, re.sub(r"^\d+\.\s", "", line))
        else:
            para = doc.add_paragraph()
            _add_formatted_text(para, line)

    _flush_table(doc, table_buffer)


def _flush_table(doc: Document, buffer: list[str]) -> None:
    """Rend un groupe de lignes `|...|`. Vrai tableau Word si la 2e ligne est
    un séparateur d'en-tête Markdown, sinon repli en paragraphes (les cellules
    jointes par tabulation - comportement historique, sans perte)."""
    if not buffer:
        return
    rows = list(buffer)
    buffer.clear()

    if len(rows) >= 2 and _TABLE_SEPARATOR.match(rows[1]):
        header = _split_row(rows[0])
        body = [_split_row(r) for r in rows[2:] if not _TABLE_SEPARATOR.match(r)]
        table = doc.add_table(rows=1, cols=len(header))
        table.style = "Table Grid"
        for j, cell_text in enumerate(header):
            run = table.rows[0].cells[j].paragraphs[0].add_run(cell_text)
            run.bold = True
        for row_cells in body:
            row = table.add_row()
            for j in range(len(header)):
                text = row_cells[j] if j < len(row_cells) else ""
                _add_formatted_text(row.cells[j].paragraphs[0], text)
        return

    for r in rows:
        if _TABLE_SEPARATOR.match(r):
            continue
        para = doc.add_paragraph()
        para.add_run("\t".join(_split_row(r)))


def _split_row(line: str) -> list[str]:
    """Cellules d'une ligne de tableau - tolère l'absence de pipe fermant
    (l'ancien split('|')[1:-1] perdait la dernière cellule)."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def _add_preformatted(doc: Document, text: str) -> None:
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(0)
    run = para.add_run(text)
    run.font.name = "Consolas"
    run.font.size = Pt(10)


def _add_formatted_text(para, text: str) -> None:
    """Inline **gras**/*italique*/`code`. Les segments hors motifs (dont les
    * et ` non appariés) sont ajoutés tels quels : rien n'est jeté."""
    pos = 0
    for m in _INLINE_PATTERN.finditer(text):
        if m.start() > pos:
            para.add_run(text[pos : m.start()])
        part = m.group(0)
        if part.startswith("**"):
            run = para.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("*"):
            run = para.add_run(part[1:-1])
            run.italic = True
        else:
            run = para.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(10)
        pos = m.end()
    if pos < len(text):
        para.add_run(text[pos:])


def _setup_styles(doc: Document) -> None:
    """Styles Synoptia (mêmes réglages que le chemin LLM DocxSkill)."""
    styles = doc.styles

    normal = styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.font.color.rgb = SYNOPTIA_COLORS["body"]
    normal.paragraph_format.space_after = Pt(10)
    normal.paragraph_format.line_spacing = 1.15

    heading_specs = {
        "Heading 1": (24, SYNOPTIA_COLORS["heading"], 24, 12),
        "Heading 2": (18, SYNOPTIA_COLORS["primary"], 18, 8),
        "Heading 3": (14, SYNOPTIA_COLORS["heading"], 14, 6),
        "Heading 4": (12, SYNOPTIA_COLORS["heading"], 12, 6),
    }
    for name, (size, color, before, after) in heading_specs.items():
        if name in styles:
            style = styles[name]
            style.font.name = "Outfit"
            style.font.size = Pt(size)
            style.font.bold = True
            style.font.color.rgb = color
            style.paragraph_format.space_before = Pt(before)
            style.paragraph_format.space_after = Pt(after)


def _style_title(para) -> None:
    for run in para.runs:
        run.font.name = "Outfit"
        run.font.size = Pt(28)
        run.font.bold = True
        run.font.color.rgb = SYNOPTIA_COLORS["heading"]


def _add_footer(doc: Document) -> None:
    section = doc.sections[-1]
    footer = section.footer
    footer.is_linked_to_previous = False
    para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run("Généré par THÉRÈSE - Synoptïa")
    run.font.size = Pt(9)
