# Story E4-06 : Indexer les fichiers dans la mémoire

## Description

En tant que **utilisateur**,
Je veux **que mes fichiers soient indexés dans la mémoire de THÉRÈSE**,
Afin de **retrouver leur contenu lors de conversations futures**.

## Contexte technique

- **Composants impactés** : Backend Python, Qdrant
- **Dépendances** : E3-02, E3-03, E4-02, E4-03, E4-04
- **Fichiers concernés** :
  - `src/backend/therese/services/file_indexer.py` (nouveau)
  - `src/backend/therese/models/file_memory.py` (nouveau)
  - `src/backend/therese/api/routes/files.py` (màj)

## Critères d'acceptation

- [ ] Indexation automatique après parsing
- [ ] Chunking intelligent (par paragraphe/section)
- [ ] Métadonnées fichier stockées (nom, chemin, date)
- [ ] Recherche dans les fichiers indexés
- [ ] Mise à jour si fichier modifié
- [ ] Suppression de l'index si fichier supprimé

## Notes techniques

### Modèle FileMemory

```python
# therese/models/file_memory.py
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
import hashlib


class FileMemory(SQLModel, table=True):
    """Représente un fichier indexé en mémoire"""
    __tablename__ = "file_memories"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    file_path: str = Field(index=True, unique=True)
    file_name: str
    file_type: str  # pdf, docx, txt, md
    file_hash: str  # Pour détecter les modifications
    file_size: int

    # Métadonnées extraites
    title: Optional[str] = None
    author: Optional[str] = None
    page_count: Optional[int] = None

    # Stats
    chunk_count: int = 0
    total_chars: int = 0

    # Timestamps
    indexed_at: datetime = Field(default_factory=datetime.utcnow)
    file_modified_at: Optional[datetime] = None

    @classmethod
    def compute_hash(cls, file_path: str) -> str:
        """Calcule le hash SHA256 du fichier"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()


class FileChunk(SQLModel, table=True):
    """Chunk d'un fichier pour l'indexation vectorielle"""
    __tablename__ = "file_chunks"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    file_memory_id: str = Field(foreign_key="file_memories.id", index=True)

    chunk_index: int  # Position dans le fichier
    content: str
    char_start: int  # Position de début dans le texte original
    char_end: int

    # Contexte
    section_title: Optional[str] = None  # Titre de section si disponible
    page_number: Optional[int] = None  # Numéro de page si disponible

    # Embedding
    embedding_id: Optional[str] = None  # ID dans Qdrant
```

### Service d'indexation

```python
# therese/services/file_indexer.py
from pathlib import Path
from datetime import datetime
import re

from ..models.file_memory import FileMemory, FileChunk
from .embedding_service import embedding_service
from .vector_service import vector_service
from .file_parser import pdf_parser, docx_parser, text_parser, markdown_parser

CHUNK_SIZE = 1000  # Caractères par chunk
CHUNK_OVERLAP = 200  # Chevauchement entre chunks


class FileIndexer:
    def __init__(self, db_session):
        self.db = db_session

    async def index_file(self, file_path: str) -> FileMemory:
        """Indexe un fichier dans la mémoire"""
        path = Path(file_path)

        # Vérifier si déjà indexé
        existing = self.db.query(FileMemory).filter(
            FileMemory.file_path == str(path)
        ).first()

        current_hash = FileMemory.compute_hash(file_path)

        if existing:
            if existing.file_hash == current_hash:
                # Pas de modification
                return existing
            # Fichier modifié - réindexer
            await self.remove_file(file_path)

        # Parser le fichier
        parsed = await self._parse_file(path)

        # Créer l'entrée FileMemory
        file_memory = FileMemory(
            file_path=str(path),
            file_name=path.name,
            file_type=parsed.file_type,
            file_hash=current_hash,
            file_size=path.stat().st_size,
            title=parsed.metadata.get("title"),
            author=parsed.metadata.get("author"),
            page_count=parsed.page_count,
            total_chars=len(parsed.text),
            file_modified_at=datetime.fromtimestamp(path.stat().st_mtime),
        )

        # Chunker le texte
        chunks = self._chunk_text(parsed.text, parsed.metadata)
        file_memory.chunk_count = len(chunks)

        # Sauvegarder en base
        self.db.add(file_memory)
        self.db.commit()

        # Indexer les chunks dans Qdrant
        await self._index_chunks(file_memory, chunks)

        return file_memory

    async def _parse_file(self, path: Path):
        """Parse un fichier selon son type"""
        ext = path.suffix.lower()
        parsers = {
            '.pdf': pdf_parser,
            '.docx': docx_parser,
            '.doc': docx_parser,
            '.txt': text_parser,
            '.md': markdown_parser,
        }
        parser = parsers.get(ext)
        if not parser:
            raise ValueError(f"Type de fichier non supporté: {ext}")
        return parser.parse(path)

    def _chunk_text(
        self,
        text: str,
        metadata: dict,
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP
    ) -> list[dict]:
        """Découpe le texte en chunks avec chevauchement"""
        chunks = []

        # Essayer de découper par sections (titres markdown)
        sections = re.split(r'\n(?=#{1,6}\s)', text)

        if len(sections) > 1:
            # Découpage par sections
            current_pos = 0
            for section in sections:
                if len(section) > chunk_size:
                    # Section trop longue - sous-découper
                    sub_chunks = self._split_by_size(section, chunk_size, overlap)
                    for sub in sub_chunks:
                        chunks.append({
                            "content": sub["content"],
                            "char_start": current_pos + sub["start"],
                            "char_end": current_pos + sub["end"],
                            "section_title": self._extract_title(section),
                        })
                else:
                    chunks.append({
                        "content": section.strip(),
                        "char_start": current_pos,
                        "char_end": current_pos + len(section),
                        "section_title": self._extract_title(section),
                    })
                current_pos += len(section)
        else:
            # Pas de sections - découpage par taille
            raw_chunks = self._split_by_size(text, chunk_size, overlap)
            for chunk in raw_chunks:
                chunks.append({
                    "content": chunk["content"],
                    "char_start": chunk["start"],
                    "char_end": chunk["end"],
                    "section_title": None,
                })

        return chunks

    def _split_by_size(
        self,
        text: str,
        size: int,
        overlap: int
    ) -> list[dict]:
        """Découpe un texte par taille avec chevauchement"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + size

            # Essayer de couper sur une fin de phrase
            if end < len(text):
                # Chercher le dernier point ou saut de ligne
                last_break = text.rfind('.', start, end)
                if last_break == -1:
                    last_break = text.rfind('\n', start, end)
                if last_break > start + size // 2:
                    end = last_break + 1

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "start": start,
                    "end": end,
                })

            start = end - overlap

        return chunks

    def _extract_title(self, section: str) -> str | None:
        """Extrait le titre d'une section markdown"""
        match = re.match(r'^#{1,6}\s+(.+)$', section, re.MULTILINE)
        return match.group(1).strip() if match else None

    async def _index_chunks(
        self,
        file_memory: FileMemory,
        chunks: list[dict]
    ):
        """Indexe les chunks dans Qdrant"""
        for i, chunk_data in enumerate(chunks):
            # Créer le chunk en base
            file_chunk = FileChunk(
                file_memory_id=file_memory.id,
                chunk_index=i,
                content=chunk_data["content"],
                char_start=chunk_data["char_start"],
                char_end=chunk_data["char_end"],
                section_title=chunk_data.get("section_title"),
            )
            self.db.add(file_chunk)

            # Générer l'embedding
            embedding = await embedding_service.embed(chunk_data["content"])

            # Indexer dans Qdrant
            point_id = await vector_service.upsert(
                collection="file_chunks",
                id=file_chunk.id,
                vector=embedding,
                payload={
                    "file_memory_id": file_memory.id,
                    "file_path": file_memory.file_path,
                    "file_name": file_memory.file_name,
                    "chunk_index": i,
                    "section_title": chunk_data.get("section_title"),
                    "content": chunk_data["content"][:500],  # Preview
                }
            )
            file_chunk.embedding_id = point_id

        self.db.commit()

    async def remove_file(self, file_path: str):
        """Supprime un fichier de l'index"""
        file_memory = self.db.query(FileMemory).filter(
            FileMemory.file_path == file_path
        ).first()

        if not file_memory:
            return

        # Supprimer les chunks de Qdrant
        chunks = self.db.query(FileChunk).filter(
            FileChunk.file_memory_id == file_memory.id
        ).all()

        for chunk in chunks:
            if chunk.embedding_id:
                await vector_service.delete(
                    collection="file_chunks",
                    id=chunk.embedding_id
                )
            self.db.delete(chunk)

        self.db.delete(file_memory)
        self.db.commit()

    async def search_files(
        self,
        query: str,
        limit: int = 5
    ) -> list[dict]:
        """Recherche dans les fichiers indexés"""
        # Générer l'embedding de la requête
        query_embedding = await embedding_service.embed(query)

        # Recherche vectorielle
        results = await vector_service.search(
            collection="file_chunks",
            vector=query_embedding,
            limit=limit
        )

        # Enrichir avec les infos du fichier
        enriched = []
        for result in results:
            file_memory = self.db.query(FileMemory).filter(
                FileMemory.id == result.payload["file_memory_id"]
            ).first()

            enriched.append({
                "file_name": file_memory.file_name,
                "file_path": file_memory.file_path,
                "section_title": result.payload.get("section_title"),
                "content_preview": result.payload["content"],
                "score": result.score,
            })

        return enriched


# Factory
def get_file_indexer(db_session) -> FileIndexer:
    return FileIndexer(db_session)
```

### Route API

```python
# therese/api/routes/files.py (ajout)

@router.post("/index")
async def index_file(file_path: str, db: Session = Depends(get_db)):
    """Indexe un fichier dans la mémoire"""
    indexer = get_file_indexer(db)
    try:
        file_memory = await indexer.index_file(file_path)
        return {
            "id": file_memory.id,
            "file_name": file_memory.file_name,
            "chunk_count": file_memory.chunk_count,
            "total_chars": file_memory.total_chars,
        }
    except FileNotFoundError:
        raise HTTPException(404, "File not found")
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/index/{file_path:path}")
async def remove_from_index(file_path: str, db: Session = Depends(get_db)):
    """Supprime un fichier de l'index"""
    indexer = get_file_indexer(db)
    await indexer.remove_file(file_path)
    return {"status": "removed"}


@router.get("/search")
async def search_files(
    query: str,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Recherche dans les fichiers indexés"""
    indexer = get_file_indexer(db)
    results = await indexer.search_files(query, limit)
    return {"results": results}


@router.get("/indexed")
async def list_indexed_files(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Liste les fichiers indexés"""
    offset = (page - 1) * limit
    files = db.query(FileMemory).offset(offset).limit(limit).all()
    total = db.query(FileMemory).count()
    return {
        "items": files,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }
```

### Tests

```python
# tests/test_file_indexer.py

@pytest.fixture
def indexer(db_session):
    return FileIndexer(db_session)


async def test_index_pdf(indexer, tmp_path):
    # Créer un PDF de test
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), "Contenu du document PDF pour test.")
    pdf_path = tmp_path / "test.pdf"
    doc.save(str(pdf_path))
    doc.close()

    # Indexer
    file_memory = await indexer.index_file(str(pdf_path))

    assert file_memory.file_name == "test.pdf"
    assert file_memory.file_type == "pdf"
    assert file_memory.chunk_count >= 1


async def test_search_indexed_files(indexer, tmp_path):
    # Créer et indexer un fichier
    txt_path = tmp_path / "searchable.txt"
    txt_path.write_text("Machine learning et intelligence artificielle.")
    await indexer.index_file(str(txt_path))

    # Rechercher
    results = await indexer.search_files("IA et ML")
    assert len(results) >= 1
    assert "searchable.txt" in results[0]["file_name"]


async def test_reindex_modified_file(indexer, tmp_path):
    txt_path = tmp_path / "evolving.txt"
    txt_path.write_text("Version 1")
    file_memory_v1 = await indexer.index_file(str(txt_path))

    # Modifier le fichier
    txt_path.write_text("Version 2 avec plus de contenu")
    file_memory_v2 = await indexer.index_file(str(txt_path))

    # Nouveau hash = nouvelle indexation
    assert file_memory_v1.file_hash != file_memory_v2.file_hash
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Definition of Done

- [ ] Indexation automatique fonctionne
- [ ] Chunking intelligent
- [ ] Recherche dans les fichiers
- [ ] Mise à jour sur modification
- [ ] Suppression de l'index
- [ ] Tests passent

---

*Sprint : 4*
*Assigné : Agent Dev Backend*
