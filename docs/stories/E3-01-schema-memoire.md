# Story E3-01 : Définir le schéma mémoire (entités, relations)

## Description

En tant que **développeur**,
Je veux **avoir un schéma de données robuste pour la mémoire**,
Afin de **stocker efficacement contacts, projets et faits**.

## Contexte technique

- **Composants impactés** : Backend Python, SQLite
- **Dépendances** : E1-03
- **Fichiers concernés** :
  - `src/backend/therese/models/memory.py` (nouveau)
  - `src/backend/therese/models/__init__.py` (màj)

## Critères d'acceptation

- [ ] Modèles SQLModel pour Contact, Project, Memory, Preference
- [ ] Relations définies (Project → Contact)
- [ ] Champs JSON pour tags et metadata
- [ ] Index sur les champs fréquemment requêtés
- [ ] Timestamps automatiques (created_at, updated_at)
- [ ] Migration Alembic générée

## Notes techniques

### Modèles complets

```python
# therese/models/memory.py
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
import uuid

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Contact(SQLModel, table=True):
    """Représente un contact (client, partenaire, etc.)"""
    __tablename__ = "contacts"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    first_name: str = Field(index=True)
    last_name: Optional[str] = Field(default=None, index=True)
    company: Optional[str] = Field(default=None, index=True)
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    role: Optional[str] = Field(default=None)  # "client", "partenaire", etc.
    notes: Optional[str] = Field(default=None)
    tags: list[str] = Field(default=[], sa_column=Column(JSON))
    metadata: dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relations
    projects: list["Project"] = Relationship(back_populates="client")

    @property
    def full_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name


class Project(SQLModel, table=True):
    """Représente un projet ou mission"""
    __tablename__ = "projects"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    status: str = Field(default="active", index=True)  # active, done, archived, paused
    budget: Optional[float] = Field(default=None)
    deadline: Optional[datetime] = Field(default=None)
    client_id: Optional[str] = Field(default=None, foreign_key="contacts.id")
    tags: list[str] = Field(default=[], sa_column=Column(JSON))
    metadata: dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relations
    client: Optional[Contact] = Relationship(back_populates="projects")
    memories: list["Memory"] = Relationship(back_populates="project")


class Memory(SQLModel, table=True):
    """Représente un fait, une information mémorisée"""
    __tablename__ = "memories"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    type: str = Field(index=True)  # fact, preference, note, skill
    category: Optional[str] = Field(default=None, index=True)  # work, personal, tech
    content: str
    source: str = Field(default="extracted")  # extracted, manual, imported
    confidence: float = Field(default=1.0)  # 0.0 to 1.0

    # Relations optionnelles
    conversation_id: Optional[str] = Field(default=None, foreign_key="conversations.id")
    contact_id: Optional[str] = Field(default=None, foreign_key="contacts.id")
    project_id: Optional[str] = Field(default=None, foreign_key="projects.id")

    # Qdrant
    embedding_id: Optional[str] = Field(default=None, index=True)

    # Metadata
    tags: list[str] = Field(default=[], sa_column=Column(JSON))
    metadata: dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)  # Pour mémoire temporaire

    # Relations
    project: Optional[Project] = Relationship(back_populates="memories")


class Preference(SQLModel, table=True):
    """Préférences utilisateur"""
    __tablename__ = "preferences"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    key: str = Field(index=True, unique=True)
    value: str
    type: str = Field(default="string")  # string, number, boolean, json
    category: str = Field(default="general")  # general, ui, llm, memory
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Énumérations

```python
# therese/models/enums.py
from enum import Enum

class MemoryType(str, Enum):
    FACT = "fact"           # Information factuelle
    PREFERENCE = "preference"  # Préférence utilisateur
    NOTE = "note"           # Note libre
    SKILL = "skill"         # Compétence/savoir-faire

class MemorySource(str, Enum):
    EXTRACTED = "extracted"  # Extrait auto d'une conversation
    MANUAL = "manual"        # Ajouté manuellement
    IMPORTED = "imported"    # Importé d'un fichier

class ProjectStatus(str, Enum):
    ACTIVE = "active"
    DONE = "done"
    ARCHIVED = "archived"
    PAUSED = "paused"
```

### Index SQL

```sql
-- Optimisation des recherches
CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company);
CREATE INDEX IF NOT EXISTS idx_memories_type_category ON memories(type, category);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
```

## Estimation

- **Complexité** : S
- **Points** : 3

## Definition of Done

- [ ] Modèles créés et validés
- [ ] Migration Alembic générée
- [ ] Relations testées
- [ ] Index créés
- [ ] Documentation des champs

---

*Sprint : 3*
*Assigné : Agent Dev Backend*
