# Story E4-02 : Implémenter la lecture PDF

## Description

En tant que **utilisateur**,
Je veux **que THÉRÈSE lise mes fichiers PDF**,
Afin de **analyser et résumer des documents**.

## Contexte technique

- **Composants impactés** : Backend Python
- **Dépendances** : E1-02, E1-05
- **Fichiers concernés** :
  - `src/backend/therese/services/file_parser.py` (nouveau)
  - `pyproject.toml` (màj)

## Critères d'acceptation

- [ ] Extraction du texte de PDFs
- [ ] Support des PDFs scannés (OCR optionnel)
- [ ] Limite de taille : 50 Mo
- [ ] Limite de pages : 500 pages
- [ ] Extraction des métadonnées (titre, auteur, date)
- [ ] Performance < 5s pour un PDF de 50 pages

## Notes techniques

### Installation

```bash
uv add pymupdf pytesseract
```

### Parser PDF

```python
# therese/services/file_parser.py
from pathlib import Path
from dataclasses import dataclass
import fitz  # PyMuPDF

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 Mo
MAX_PAGES = 500


@dataclass
class ParsedDocument:
    text: str
    metadata: dict
    page_count: int
    file_path: str
    file_type: str


class PDFParser:
    def parse(self, file_path: str | Path) -> ParsedDocument:
        """Parse un fichier PDF et extrait le texte"""
        path = Path(file_path)

        # Vérifications
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if path.stat().st_size > MAX_FILE_SIZE:
            raise ValueError(f"File too large: {path.stat().st_size} bytes")

        doc = fitz.open(str(path))

        if doc.page_count > MAX_PAGES:
            raise ValueError(f"Too many pages: {doc.page_count}")

        # Extraire le texte
        text_parts = []
        for page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
            else:
                # Page sans texte (probablement scannée)
                # TODO: OCR si configuré
                pass

        # Métadonnées
        metadata = {
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
            "creator": doc.metadata.get("creator", ""),
            "creation_date": doc.metadata.get("creationDate", ""),
            "modification_date": doc.metadata.get("modDate", ""),
        }

        doc.close()

        return ParsedDocument(
            text="\n\n".join(text_parts),
            metadata=metadata,
            page_count=doc.page_count,
            file_path=str(path),
            file_type="pdf"
        )

    def extract_images(self, file_path: str | Path) -> list[bytes]:
        """Extrait les images d'un PDF"""
        path = Path(file_path)
        doc = fitz.open(str(path))
        images = []

        for page in doc:
            image_list = page.get_images()
            for img_info in image_list:
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                images.append(base_image["image"])

        doc.close()
        return images


class PDFParserWithOCR(PDFParser):
    """Parser PDF avec support OCR pour les pages scannées"""

    def __init__(self):
        super().__init__()
        self.ocr_enabled = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        """Vérifie si Tesseract est disponible"""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def parse(self, file_path: str | Path) -> ParsedDocument:
        """Parse avec OCR si nécessaire"""
        path = Path(file_path)
        doc = fitz.open(str(path))

        if doc.page_count > MAX_PAGES:
            raise ValueError(f"Too many pages: {doc.page_count}")

        text_parts = []
        for page_num, page in enumerate(doc):
            text = page.get_text()

            # Si page vide et OCR disponible
            if not text.strip() and self.ocr_enabled:
                text = self._ocr_page(page)

            if text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

        metadata = {
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "ocr_used": self.ocr_enabled,
        }

        doc.close()

        return ParsedDocument(
            text="\n\n".join(text_parts),
            metadata=metadata,
            page_count=doc.page_count,
            file_path=str(path),
            file_type="pdf"
        )

    def _ocr_page(self, page) -> str:
        """Applique l'OCR sur une page"""
        import pytesseract
        from PIL import Image
        import io

        # Convertir la page en image
        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes()))

        # OCR
        text = pytesseract.image_to_string(img, lang='fra+eng')
        return text


# Factory
def get_pdf_parser() -> PDFParser:
    """Retourne le parser PDF approprié"""
    try:
        return PDFParserWithOCR()
    except Exception:
        return PDFParser()


pdf_parser = get_pdf_parser()
```

### Route API

```python
# therese/api/routes/files.py
from fastapi import APIRouter, UploadFile, HTTPException
from pathlib import Path

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/parse/pdf")
async def parse_pdf(file_path: str):
    """Parse un fichier PDF local"""
    try:
        result = pdf_parser.parse(file_path)
        return {
            "text": result.text[:10000],  # Limiter la réponse
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
# tests/test_pdf_parser.py
import pytest
from therese.services.file_parser import pdf_parser

def test_parse_simple_pdf(tmp_path):
    # Créer un PDF de test avec PyMuPDF
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), "Hello THÉRÈSE!")
    pdf_path = tmp_path / "test.pdf"
    doc.save(str(pdf_path))
    doc.close()

    result = pdf_parser.parse(pdf_path)
    assert "Hello THÉRÈSE!" in result.text
    assert result.page_count == 1

def test_parse_large_pdf_rejected(tmp_path):
    # Simuler un fichier trop gros
    # ...
    pass
```

## Estimation

- **Complexité** : S
- **Points** : 3

## Definition of Done

- [ ] PDFs parsés correctement
- [ ] Métadonnées extraites
- [ ] Limites respectées
- [ ] OCR optionnel fonctionne
- [ ] Tests passent

---

*Sprint : 4*
*Assigné : Agent Dev Backend*
