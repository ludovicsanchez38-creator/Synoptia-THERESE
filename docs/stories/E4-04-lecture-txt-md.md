# Story E4-04 : Supporter les fichiers TXT et Markdown

## Description

En tant que **utilisateur**,
Je veux **que THÉRÈSE lise mes fichiers texte et Markdown**,
Afin de **travailler avec mes notes et documentation**.

## Contexte technique

- **Composants impactés** : Backend Python
- **Dépendances** : E1-02, E4-02
- **Fichiers concernés** :
  - `src/backend/therese/services/file_parser.py` (màj)

## Critères d'acceptation

- [ ] Lecture fichiers .txt (UTF-8, Latin-1)
- [ ] Lecture fichiers .md avec structure préservée
- [ ] Détection automatique de l'encodage
- [ ] Limite de taille : 10 Mo
- [ ] Extraction des métadonnées front matter YAML (optionnel)

## Notes techniques

### Parser TXT/Markdown

```python
# therese/services/file_parser.py (ajout)
import chardet
import yaml
import re

MAX_TEXT_SIZE = 10 * 1024 * 1024  # 10 Mo


class TextParser:
    def parse(self, file_path: str | Path) -> ParsedDocument:
        """Parse un fichier texte"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if path.stat().st_size > MAX_TEXT_SIZE:
            raise ValueError(f"File too large: {path.stat().st_size} bytes")

        # Détecter l'encodage
        raw_content = path.read_bytes()
        detected = chardet.detect(raw_content)
        encoding = detected.get('encoding', 'utf-8') or 'utf-8'

        try:
            text = raw_content.decode(encoding)
        except UnicodeDecodeError:
            # Fallback UTF-8 avec erreurs ignorées
            text = raw_content.decode('utf-8', errors='ignore')

        return ParsedDocument(
            text=text,
            metadata={
                "encoding": encoding,
                "confidence": detected.get('confidence', 0),
            },
            page_count=self._estimate_pages(text),
            file_path=str(path),
            file_type="txt"
        )

    def _estimate_pages(self, text: str) -> int:
        """Estime le nombre de pages"""
        chars_per_page = 3000
        return max(1, len(text) // chars_per_page)


class MarkdownParser:
    FRONT_MATTER_REGEX = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)

    def parse(self, file_path: str | Path) -> ParsedDocument:
        """Parse un fichier Markdown"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if path.stat().st_size > MAX_TEXT_SIZE:
            raise ValueError(f"File too large: {path.stat().st_size} bytes")

        text = path.read_text(encoding='utf-8')
        metadata = {}

        # Extraire le front matter YAML
        front_matter_match = self.FRONT_MATTER_REGEX.match(text)
        if front_matter_match:
            try:
                front_matter = yaml.safe_load(front_matter_match.group(1))
                metadata = front_matter if isinstance(front_matter, dict) else {}
                # Retirer le front matter du texte
                text = text[front_matter_match.end():]
            except yaml.YAMLError:
                pass

        # Extraire le titre (premier H1)
        title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        if title_match and 'title' not in metadata:
            metadata['title'] = title_match.group(1).strip()

        # Compter les sections
        headings = re.findall(r'^#{1,6}\s+.+$', text, re.MULTILINE)
        metadata['heading_count'] = len(headings)

        return ParsedDocument(
            text=text,
            metadata=metadata,
            page_count=self._estimate_pages(text),
            file_path=str(path),
            file_type="markdown"
        )

    def _estimate_pages(self, text: str) -> int:
        """Estime le nombre de pages"""
        chars_per_page = 3000
        return max(1, len(text) // chars_per_page)

    def extract_structure(self, file_path: str | Path) -> dict:
        """Extrait la structure du document (titres hiérarchiques)"""
        path = Path(file_path)
        text = path.read_text(encoding='utf-8')

        structure = []
        for match in re.finditer(r'^(#{1,6})\s+(.+)$', text, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            structure.append({
                "level": level,
                "title": title,
                "position": match.start()
            })

        return {"headings": structure}


# Singletons
text_parser = TextParser()
markdown_parser = MarkdownParser()
```

### Route API

```python
# therese/api/routes/files.py (ajout)

@router.post("/parse/text")
async def parse_text(file_path: str):
    """Parse un fichier texte"""
    try:
        result = text_parser.parse(file_path)
        return {
            "text": result.text[:10000],
            "text_length": len(result.text),
            "metadata": result.metadata,
        }
    except FileNotFoundError:
        raise HTTPException(404, "File not found")
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/parse/markdown")
async def parse_markdown(file_path: str):
    """Parse un fichier Markdown"""
    try:
        result = markdown_parser.parse(file_path)
        return {
            "text": result.text[:10000],
            "text_length": len(result.text),
            "metadata": result.metadata,
            "structure": markdown_parser.extract_structure(file_path)
        }
    except FileNotFoundError:
        raise HTTPException(404, "File not found")
    except ValueError as e:
        raise HTTPException(400, str(e))
```

### Tests

```python
# tests/test_text_parser.py

def test_parse_utf8_text(tmp_path):
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("Contenu en UTF-8 avec accents: é è à", encoding='utf-8')

    result = text_parser.parse(txt_path)
    assert "UTF-8" in result.text or "accents" in result.text
    assert result.file_type == "txt"


def test_parse_markdown_with_frontmatter(tmp_path):
    md_path = tmp_path / "test.md"
    content = """---
title: Mon Document
author: Ludo
---

# Introduction

Contenu du document.

## Section 1

Plus de contenu.
"""
    md_path.write_text(content, encoding='utf-8')

    result = markdown_parser.parse(md_path)
    assert result.metadata.get("title") == "Mon Document"
    assert result.metadata.get("author") == "Ludo"
    assert result.metadata.get("heading_count") == 2


def test_parse_markdown_structure(tmp_path):
    md_path = tmp_path / "structure.md"
    content = """# Titre Principal

## Section A

### Sous-section A1

## Section B
"""
    md_path.write_text(content, encoding='utf-8')

    structure = markdown_parser.extract_structure(md_path)
    assert len(structure["headings"]) == 4
    assert structure["headings"][0]["level"] == 1
    assert structure["headings"][1]["level"] == 2
```

## Estimation

- **Complexité** : XS
- **Points** : 2

## Definition of Done

- [ ] TXT parsés avec détection encodage
- [ ] Markdown parsés avec front matter
- [ ] Structure extraite (titres)
- [ ] Limites respectées
- [ ] Tests passent

---

*Sprint : 4*
*Assigné : Agent Dev Backend*
