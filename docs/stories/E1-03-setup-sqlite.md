# Story E1-03 : Mettre en place SQLite avec schéma initial

## Description

En tant que **développeur**,
Je veux **avoir une base SQLite configurée avec le schéma initial**,
Afin de **stocker les données de THÉRÈSE localement**.

## Contexte technique

- **Composants impactés** : Backend Python, Module mémoire
- **Dépendances** : E1-02 (Backend FastAPI)
- **Fichiers concernés** :
  - `src/backend/therese/database/` (nouveau)
  - `src/backend/therese/models/` (màj)

## Critères d'acceptation

- [ ] SQLModel installé et configuré
- [ ] Fichier DB créé dans `~/.therese/data/therese.db`
- [ ] Tables initiales créées (conversations, messages, contacts, projects, memories)
- [ ] Migration Alembic fonctionnelle
- [ ] CRUD basique testé
- [ ] Backup automatique possible

## Notes techniques

### Dépendances

```bash
uv add sqlmodel aiosqlite alembic
```

### Schéma initial

```python
# therese/models/base.py
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
import uuid

def generate_uuid() -> str:
    return str(uuid.uuid4())

class BaseModel(SQLModel):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

```python
# therese/models/conversation.py
from sqlmodel import Field, Relationship
from .base import BaseModel

class Conversation(BaseModel, table=True):
    __tablename__ = "conversations"

    title: str | None = None
    messages: list["Message"] = Relationship(back_populates="conversation")

class Message(BaseModel, table=True):
    __tablename__ = "messages"

    role: str  # "user" | "assistant"
    content: str
    conversation_id: str = Field(foreign_key="conversations.id")
    conversation: Conversation = Relationship(back_populates="messages")
```

```python
# therese/models/memory.py
class Contact(BaseModel, table=True):
    __tablename__ = "contacts"

    first_name: str
    last_name: str | None = None
    company: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None
    tags: str | None = None  # JSON array

class Project(BaseModel, table=True):
    __tablename__ = "projects"

    name: str
    description: str | None = None
    status: str = "active"  # active, done, archived
    client_id: str | None = Field(foreign_key="contacts.id")
    tags: str | None = None

class Memory(BaseModel, table=True):
    __tablename__ = "memories"

    type: str  # fact, preference, note
    content: str
    source: str = "extracted"  # extracted, manual
    conversation_id: str | None = Field(foreign_key="conversations.id")
    embedding_id: str | None = None  # Qdrant point ID
```

### Configuration DB

```python
# therese/database/connection.py
from pathlib import Path
from sqlmodel import create_engine, SQLModel

def get_db_path() -> Path:
    db_dir = Path.home() / ".therese" / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "therese.db"

def get_engine():
    db_path = get_db_path()
    return create_engine(f"sqlite:///{db_path}", echo=False)

def init_db():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
```

## Estimation

- **Complexité** : S
- **Points** : 3

## Definition of Done

- [ ] DB créée au démarrage si absente
- [ ] Tables visibles avec `sqlite3`
- [ ] CRUD conversations testé
- [ ] Migration Alembic initiale créée

---

*Sprint : 1*
*Assigné : Agent Dev*
