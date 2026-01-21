# Story E4-03 : Implémenter la lecture DOCX

## Description

En tant que **utilisateur**,
Je veux **que THÉRÈSE lise mes fichiers Word**,
Afin de **analyser mes documents professionnels**.

## Contexte technique

- **Composants impactés** : Backend Python
- **Dépendances** : E1-02, E4-02
- **Fichiers concernés** :
  - `src/backend/therese/services/file_parser.py` (màj)
  - `pyproject.toml` (màj)

## Critères d'acceptation

- [ ] Extraction du texte des fichiers DOCX
- [ ] Conservation de la structure (titres, listes)
- [ ] Extraction des tableaux en texte
- [ ] Limite de taille : 20 Mo
- [ ] Support des commentaires et révisions (optionnel)

## Notes techniques

### Installation

```bash
uv add python-docx
```

### Parser DOCX

```python
# therese/services/file_parser.py (ajout)
from docx import Document
from docx.table import Table

MAX_DOCX_SIZE = 20 * 1024 * 1024  # 20 Mo


class DOCXParser:
    def parse(self, file_path: str | Path) -> ParsedDocument:
        """Parse un fichier DOCX"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if path.stat().st_size > MAX_DOCX_SIZE:
            raise ValueError(f"File too large: {path.stat().st_size} bytes")

        doc = Document(str(path))
        text_parts = []

        # Parcourir tous les éléments du document
        for element in doc.element.body:
            if element.tag.endswith('p'):
                # Paragraphe
                para = self._get_paragraph_text(doc, element)
                if para:
                    text_parts.append(para)
            elif element.tag.endswith('tbl'):
                # Tableau
                table_text = self._get_table_text(doc, element)
                if table_text:
                    text_parts.append(table_text)

        # Métadonnées
        core_props = doc.core_properties
        metadata = {
            "title": core_props.title or "",
            "author": core_props.author or "",
            "subject": core_props.subject or "",
            "created": str(core_props.created) if core_props.created else "",
            "modified": str(core_props.modified) if core_props.modified else "",
            "last_modified_by": core_props.last_modified_by or "",
        }

        return ParsedDocument(
            text="\n\n".join(text_parts),
            metadata=metadata,
            page_count=self._estimate_pages(text_parts),
            file_path=str(path),
            file_type="docx"
        )

    def _get_paragraph_text(self, doc: Document, element) -> str:
        """Extrait le texte d'un paragraphe avec formatage"""
        from docx.oxml.ns import qn

        paragraph = element
        text = ""

        # Détecter si c'est un titre
        style_element = paragraph.find(qn('w:pPr'))
        if style_element is not None:
            style = style_element.find(qn('w:pStyle'))
            if style is not None:
                style_name = style.get(qn('w:val'), '')
                if 'Heading' in style_name or 'Title' in style_name:
                    level = ''.join(filter(str.isdigit, style_name)) or '1'
                    prefix = '#' * int(level) + ' '
                    text = prefix

        # Extraire le texte
        for run in paragraph.iter():
            if run.tag.endswith('t'):
                text += run.text or ""

        return text.strip()

    def _get_table_text(self, doc: Document, element) -> str:
        """Convertit un tableau en texte markdown"""
        from docx.oxml.ns import qn

        rows = []
        for tr in element.iter():
            if tr.tag.endswith('tr'):
                cells = []
                for tc in tr.iter():
                    if tc.tag.endswith('tc'):
                        cell_text = ""
                        for p in tc.iter():
                            if p.tag.endswith('t'):
                                cell_text += p.text or ""
                        cells.append(cell_text.strip())
                if cells:
                    rows.append(cells)

        if not rows:
            return ""

        # Convertir en markdown
        lines = []
        for i, row in enumerate(rows):
            line = "| " + " | ".join(row) + " |"
            lines.append(line)
            if i == 0:
                # Ligne de séparation après le header
                sep = "| " + " | ".join(["---"] * len(row)) + " |"
                lines.append(sep)

        return "\n".join(lines)

    def _estimate_pages(self, text_parts: list[str]) -> int:
        """Estime le nombre de pages"""
        total_chars = sum(len(p) for p in text_parts)
        chars_per_page = 3000  # Approximation
        return max(1, total_chars // chars_per_page)

    def extract_comments(self, file_path: str | Path) -> list[dict]:
        """Extrait les commentaires du document"""
        path = Path(file_path)
        doc = Document(str(path))
        comments = []

        # Les commentaires sont stockés dans comments.xml
        # À implémenter si nécessaire
        return comments


docx_parser = DOCXParser()
```

### Route API

```python
# therese/api/routes/files.py (ajout)

@router.post("/parse/docx")
async def parse_docx(file_path: str):
    """Parse un fichier DOCX local"""
    try:
        result = docx_parser.parse(file_path)
        return {
            "text": result.text[:10000],
            "text_length": len(result.text),
            "metadata": result.metadata,
            "page_count": result.page_count
        }
    except FileNotFoundError:
        raise HTTPException(404, "File not found")
    except ValueError as e:
        raise HTTPException(400, str(e))
```

### Tests

```python
# tests/test_docx_parser.py
from docx import Document

def test_parse_simple_docx(tmp_path):
    # Créer un DOCX de test
    doc = Document()
    doc.add_heading('Titre du document', 0)
    doc.add_paragraph('Contenu du paragraphe.')
    doc.add_heading('Section 1', 1)
    doc.add_paragraph('Texte de la section.')

    docx_path = tmp_path / "test.docx"
    doc.save(str(docx_path))

    result = docx_parser.parse(docx_path)
    assert "Titre du document" in result.text
    assert "Contenu du paragraphe" in result.text

def test_parse_docx_with_table(tmp_path):
    doc = Document()
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "A"
    table.cell(0, 1).text = "B"
    table.cell(1, 0).text = "1"
    table.cell(1, 1).text = "2"

    docx_path = tmp_path / "table.docx"
    doc.save(str(docx_path))

    result = docx_parser.parse(docx_path)
    assert "| A | B |" in result.text
```

## Estimation

- **Complexité** : S
- **Points** : 3

## Definition of Done

- [ ] DOCX parsés correctement
- [ ] Structure conservée (titres)
- [ ] Tableaux en markdown
- [ ] Métadonnées extraites
- [ ] Tests passent

---

*Sprint : 4*
*Assigné : Agent Dev Backend*
