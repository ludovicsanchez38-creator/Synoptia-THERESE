# Architecture Technique - THÉRÈSE v2

> Document généré par l'agent Architect (BMAD)
> Date : 21 janvier 2026

## Statut

🟢 Complété

---

## 1. Vue d'ensemble

### 1.1 Contexte

THÉRÈSE est une application desktop cross-platform (macOS, Windows, Linux) avec les caractéristiques suivantes :
- **100% données locales** (sauf appels API LLM)
- **Mémoire persistante** (SQLite + Qdrant)
- **Performance** : réponse mémoire < 200ms, startup < 2s
- **Bundle léger** : < 50 Mo

### 1.2 Diagramme de composants

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           THÉRÈSE Desktop App                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│   ┌─────────────────────────────────────────────────────────────────┐    │
│   │                        Tauri 2.0 Shell (Rust)                    │    │
│   │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐     │    │
│   │  │ System Tray  │  │   Window     │  │  Global Shortcuts  │     │    │
│   │  │   Manager    │  │   Manager    │  │     (Ctrl+Space)   │     │    │
│   │  └──────────────┘  └──────────────┘  └────────────────────┘     │    │
│   │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐     │    │
│   │  │ File System  │  │   Updater    │  │   IPC Bridge       │     │    │
│   │  │   Access     │  │              │  │   (localhost:8765) │     │    │
│   │  └──────────────┘  └──────────────┘  └────────────────────┘     │    │
│   └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                      │
│                                    │ IPC                                  │
│                                    ▼                                      │
│   ┌─────────────────────────────────────────────────────────────────┐    │
│   │                    React 19 Frontend (WebView)                   │    │
│   │  ┌───────────────────────────────────────────────────────────┐  │    │
│   │  │  Components                                                │  │    │
│   │  │  ├── ChatView (messages, input, streaming)                 │  │    │
│   │  │  ├── MemoryPanel (context, entities, search)               │  │    │
│   │  │  ├── FileBrowser (navigation, preview)                     │  │    │
│   │  │  ├── CommandPalette (⌘K, search, actions)                  │  │    │
│   │  │  ├── Settings (API key, preferences)                       │  │    │
│   │  │  └── Onboarding (first-time setup)                         │  │    │
│   │  └───────────────────────────────────────────────────────────┘  │    │
│   │  ┌───────────────────────────────────────────────────────────┐  │    │
│   │  │  State (Zustand)                                           │  │    │
│   │  │  ├── chatStore (messages, conversations)                   │  │    │
│   │  │  ├── memoryStore (entities, active context)                │  │    │
│   │  │  ├── fileStore (recent files, current file)                │  │    │
│   │  │  └── uiStore (theme, panels, modals)                       │  │    │
│   │  └───────────────────────────────────────────────────────────┘  │    │
│   └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                      │
│                                    │ HTTP + SSE                           │
│                                    ▼                                      │
│   ┌─────────────────────────────────────────────────────────────────┐    │
│   │                  Python FastAPI Backend (Sidecar)                │    │
│   │  ┌───────────────────────────────────────────────────────────┐  │    │
│   │  │  Services                                                  │  │    │
│   │  │  ├── ChatService (conversation, streaming, history)        │  │    │
│   │  │  ├── MemoryService (CRUD, search, extraction)              │  │    │
│   │  │  ├── FileService (read, parse, index)                      │  │    │
│   │  │  ├── LLMService (Claude, Mistral, Ollama)                  │  │    │
│   │  │  └── EmbeddingService (nomic-embed-text)                   │  │    │
│   │  └───────────────────────────────────────────────────────────┘  │    │
│   │  ┌───────────────────────────────────────────────────────────┐  │    │
│   │  │  Routers (API Endpoints)                                   │  │    │
│   │  │  ├── /api/chat/* (send, history, stream)                   │  │    │
│   │  │  ├── /api/memory/* (search, create, update, delete)        │  │    │
│   │  │  ├── /api/files/* (list, read, analyze, index)             │  │    │
│   │  │  └── /api/config/* (settings, export, import)              │  │    │
│   │  └───────────────────────────────────────────────────────────┘  │    │
│   └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                      │
│              ┌─────────────────────┼─────────────────────┐               │
│              │                     │                     │               │
│              ▼                     ▼                     ▼               │
│   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│   │     SQLite       │  │     Qdrant       │  │    LLM API       │      │
│   │  (structured)    │  │   (vectors)      │  │  (Claude/        │      │
│   │                  │  │                  │  │   Mistral/       │      │
│   │  - contacts      │  │  - embeddings    │  │   Ollama)        │      │
│   │  - projects      │  │  - conversations │  │                  │      │
│   │  - preferences   │  │  - file chunks   │  │  EXTERNAL        │      │
│   │  - conversations │  │                  │  │                  │      │
│   │  - files meta    │  │  LOCAL           │  │                  │      │
│   │                  │  │                  │  │                  │      │
│   │  LOCAL           │  │                  │  │                  │      │
│   └──────────────────┘  └──────────────────┘  └──────────────────┘      │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Stack technique validée

### 2.1 Décisions finales

| Couche | Technologie | Version | Justification |
|--------|-------------|---------|---------------|
| **Desktop Shell** | Tauri | 2.0 | Bundle léger (5-10 Mo), Rust perf, accès FS natif |
| **Frontend** | React | 19 | Écosystème riche, Server Components, concurrent features |
| **Language** | TypeScript | 5.x | Type safety, DX, refactoring |
| **Styling** | TailwindCSS | 4.0 | JIT, dark mode natif, design tokens |
| **State** | Zustand | 5.x | Minimal boilerplate, performant, devtools |
| **Components** | Radix UI | 1.x | Accessible, unstyled, composable |
| **Animations** | Framer Motion | 11.x | Declarative, performant, gestures |
| **Icons** | Lucide React | 0.x | Tree-shakeable, cohérent |
| **Backend** | FastAPI | 0.115+ | Async, type hints, OpenAPI auto |
| **Python** | Python | 3.12+ | Performance, typing, match statements |
| **Package Manager** | UV | 0.5+ | 10x faster than pip, lockfile |
| **DB Structured** | SQLite | 3.45+ | Embedded, WAL mode, JSON support |
| **ORM** | SQLModel | 0.0.22+ | SQLAlchemy + Pydantic, type safety |
| **DB Vectors** | Qdrant | 1.12+ | Rust, hybrid search, quantization |
| **Embeddings** | nomic-embed-text | 1.5 | 768 dims, via Ollama ou API |
| **LLM Primary** | Claude API | 2024-10 | Quality, streaming, tool use |
| **LLM Fallback** | Mistral API | v1 | EU-based, cost effective |
| **LLM Local** | Ollama | 0.5+ | Mistral 7B, offline mode (v2) |

### 2.2 Contraintes techniques

| Contrainte | Valeur | Raison |
|------------|--------|--------|
| Bundle size | < 50 Mo | UX download rapide |
| Cold start | < 2s | Perception performance |
| Memory footprint | < 300 Mo RAM | Machines modestes |
| Latence mémoire | < 200ms P95 | Feedback instantané |
| Latence chat (hors LLM) | < 500ms P95 | Fluidité UX |
| Taille max fichier | 10 Mo | Éviter OOM |
| Nb entités mémoire | 10 000+ | Usage long terme |

---

## 3. Composants détaillés

### 3.1 Tauri Shell (Rust)

```
src-tauri/
├── src/
│   ├── main.rs              # Entry point, window setup
│   ├── commands/
│   │   ├── mod.rs
│   │   ├── files.rs         # open_file_dialog, read_file
│   │   ├── system.rs        # get_data_dir, get_system_info
│   │   └── window.rs        # toggle_window, set_tray
│   ├── tray.rs              # System tray menu
│   └── shortcuts.rs         # Global shortcuts (Ctrl+Space)
├── tauri.conf.json          # App config, permissions
├── Cargo.toml
└── icons/                   # App icons
```

**Responsabilités** :
- Gestion fenêtre (resize, fullscreen, minimize to tray)
- Raccourcis globaux (activation depuis n'importe où)
- Accès filesystem sandboxé
- Spawning du backend Python (sidecar)
- Auto-update

**Configuration Tauri** :

```json
{
  "build": {
    "beforeBuildCommand": "npm run build",
    "beforeDevCommand": "npm run dev",
    "devPath": "http://localhost:5173",
    "distDir": "../dist"
  },
  "bundle": {
    "active": true,
    "targets": ["dmg", "msi", "deb", "appimage"],
    "identifier": "fr.synoptia.therese",
    "icon": ["icons/32x32.png", "icons/128x128.png", "icons/icon.icns"]
  },
  "security": {
    "csp": "default-src 'self'; connect-src 'self' http://localhost:8765 https://api.anthropic.com https://api.mistral.ai"
  },
  "allowlist": {
    "fs": {
      "readFile": true,
      "writeFile": true,
      "readDir": true,
      "scope": ["$HOME/.therese/**", "$DOCUMENT/**", "$DOWNLOAD/**"]
    },
    "dialog": { "open": true, "save": true },
    "notification": { "all": true },
    "globalShortcut": { "all": true },
    "shell": { "sidecar": true }
  }
}
```

### 3.2 React Frontend

```
src/
├── components/
│   ├── chat/
│   │   ├── ChatView.tsx        # Main chat container
│   │   ├── MessageList.tsx     # Virtualized message list
│   │   ├── MessageItem.tsx     # Single message (user/assistant)
│   │   ├── ChatInput.tsx       # Input with markdown preview
│   │   └── StreamingIndicator.tsx
│   ├── memory/
│   │   ├── MemoryPanel.tsx     # Right sidebar
│   │   ├── EntityCard.tsx      # Contact/project card
│   │   ├── ContextBadge.tsx    # Inline entity mention
│   │   └── MemorySearch.tsx    # Search within memory
│   ├── files/
│   │   ├── FileBrowser.tsx     # Directory navigation
│   │   ├── FilePreview.tsx     # Preview pane
│   │   └── FileDropZone.tsx    # Drag & drop
│   ├── command/
│   │   ├── CommandPalette.tsx  # ⌘K modal
│   │   └── CommandItem.tsx     # Single command row
│   ├── settings/
│   │   ├── SettingsModal.tsx   # Settings container
│   │   ├── ApiKeyForm.tsx      # API key input
│   │   └── PreferencesForm.tsx # User preferences
│   ├── onboarding/
│   │   └── OnboardingWizard.tsx
│   └── ui/
│       ├── Button.tsx
│       ├── Input.tsx
│       ├── Modal.tsx
│       ├── Tooltip.tsx
│       └── ...
├── stores/
│   ├── chatStore.ts           # Messages, conversations
│   ├── memoryStore.ts         # Entities, active context
│   ├── fileStore.ts           # Recent files, current
│   └── uiStore.ts             # Theme, panels, modals
├── hooks/
│   ├── useChat.ts             # Chat operations
│   ├── useMemory.ts           # Memory CRUD + search
│   ├── useFiles.ts            # File operations
│   ├── useKeyboard.ts         # Keyboard shortcuts
│   └── useSSE.ts              # Server-sent events
├── lib/
│   ├── api.ts                 # API client (fetch wrapper)
│   ├── tauri.ts               # Tauri commands wrapper
│   ├── markdown.ts            # Markdown rendering
│   └── utils.ts               # Helpers
├── styles/
│   ├── globals.css            # Tailwind imports
│   └── tokens.css             # Design tokens
├── App.tsx                    # Root component
└── main.tsx                   # Entry point
```

**Design Tokens** (tokens.css) :

```css
:root {
  /* Colors */
  --color-bg: #0B1226;
  --color-bg-subtle: #0F1730;
  --color-surface: #131B35;
  --color-surface-hover: #1A2444;
  --color-border: rgba(255, 255, 255, 0.1);
  --color-border-focus: rgba(34, 211, 238, 0.5);

  --color-text: #E6EDF7;
  --color-text-muted: #B6C7DA;
  --color-text-subtle: #7A8BA8;

  --color-accent-cyan: #22D3EE;
  --color-accent-cyan-hover: #06B6D4;
  --color-accent-magenta: #E11D8D;
  --color-accent-magenta-hover: #BE185D;

  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-error: #EF4444;

  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */

  /* Spacing */
  --space-1: 0.25rem;    /* 4px */
  --space-2: 0.5rem;     /* 8px */
  --space-3: 0.75rem;    /* 12px */
  --space-4: 1rem;       /* 16px */
  --space-6: 1.5rem;     /* 24px */
  --space-8: 2rem;       /* 32px */

  /* Border radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.3);
  --shadow-glow-cyan: 0 0 20px rgba(34, 211, 238, 0.15);
  --shadow-glow-magenta: 0 0 20px rgba(225, 29, 141, 0.15);

  /* Effects */
  --blur-glass: 12px;
  --bg-glass: rgba(19, 27, 53, 0.8);

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 200ms ease;
  --transition-slow: 300ms ease;
}
```

### 3.3 Python FastAPI Backend

```
src/backend/
├── app/
│   ├── main.py                 # FastAPI app, lifespan
│   ├── config.py               # Settings (pydantic-settings)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py             # /api/chat/*
│   │   ├── memory.py           # /api/memory/*
│   │   ├── files.py            # /api/files/*
│   │   └── config.py           # /api/config/*
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat_service.py     # Conversation logic
│   │   ├── memory_service.py   # Memory CRUD + search
│   │   ├── file_service.py     # File parsing
│   │   ├── llm_service.py      # LLM abstraction
│   │   └── embedding_service.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py         # SQLite connection
│   │   ├── entities.py         # SQLModel models
│   │   └── schemas.py          # Pydantic request/response
│   ├── core/
│   │   ├── __init__.py
│   │   ├── prompts.py          # System prompts
│   │   ├── extraction.py       # Entity extraction
│   │   └── context.py          # Context assembly
│   └── utils/
│       ├── __init__.py
│       ├── parsers.py          # PDF, DOCX parsers
│       └── chunking.py         # Text chunking
├── tests/
│   ├── test_chat.py
│   ├── test_memory.py
│   └── test_files.py
├── pyproject.toml              # UV config
└── .python-version             # 3.12
```

**Main FastAPI App** (main.py) :

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.database import init_db, close_db
from app.routers import chat, memory, files, config

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()

app = FastAPI(
    title="THÉRÈSE API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(config.router, prefix="/api/config", tags=["config"])

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
```

### 3.4 Module Mémoire

#### Architecture mémoire

```
┌─────────────────────────────────────────────────────────────────┐
│                      Memory Manager                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │ SQLite Store   │  │  Qdrant Store  │  │ Context Cache  │    │
│  │                │  │                │  │                │    │
│  │ Contacts       │  │ Conversation   │  │ Active         │    │
│  │ Projects       │  │ embeddings     │  │ entities       │    │
│  │ Preferences    │  │                │  │                │    │
│  │ Conversations  │  │ File chunks    │  │ Recent         │    │
│  │ Files metadata │  │                │  │ mentions       │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             │                                   │
│                    ┌────────▼────────┐                          │
│                    │  Hybrid Search  │                          │
│                    │  - Keyword (FTS)│                          │
│                    │  - Semantic     │                          │
│                    │  - Reranking    │                          │
│                    └────────┬────────┘                          │
│                             │                                   │
│                    ┌────────▼────────┐                          │
│                    │ Context Builder │                          │
│                    │ → LLM prompt    │                          │
│                    └─────────────────┘                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Schéma SQLite

```sql
-- Contacts
CREATE TABLE contacts (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    first_name TEXT,
    last_name TEXT,
    company TEXT,
    email TEXT,
    phone TEXT,
    notes TEXT,
    tags TEXT,  -- JSON array
    metadata TEXT,  -- JSON object
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects
CREATE TABLE projects (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name TEXT NOT NULL,
    description TEXT,
    contact_id TEXT REFERENCES contacts(id),
    status TEXT DEFAULT 'active',  -- active, completed, on_hold
    budget REAL,
    notes TEXT,
    tags TEXT,  -- JSON array
    metadata TEXT,  -- JSON object
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversations
CREATE TABLE conversations (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages
CREATE TABLE messages (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    conversation_id TEXT REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,  -- user, assistant
    content TEXT NOT NULL,
    tokens_in INTEGER,
    tokens_out INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Files metadata
CREATE TABLE files (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    path TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    mime_type TEXT,
    size_bytes INTEGER,
    content_hash TEXT,
    indexed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Preferences
CREATE TABLE preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,  -- JSON
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Full-text search index
CREATE VIRTUAL TABLE search_index USING fts5(
    content,
    entity_type,
    entity_id,
    tokenize='porter unicode61'
);

-- Indexes
CREATE INDEX idx_contacts_company ON contacts(company);
CREATE INDEX idx_projects_contact ON projects(contact_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_files_path ON files(path);
```

#### Collection Qdrant

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

COLLECTION_NAME = "therese_memory"
VECTOR_SIZE = 768  # nomic-embed-text

client = QdrantClient(path="~/.therese/qdrant_data")

# Create collection
client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(
        size=VECTOR_SIZE,
        distance=Distance.COSINE
    )
)

# Point structure
{
    "id": "uuid",
    "vector": [0.1, 0.2, ...],  # 768 dims
    "payload": {
        "type": "conversation" | "file_chunk" | "note",
        "entity_id": "uuid",
        "text": "chunk text",
        "metadata": {
            "conversation_id": "uuid",
            "message_id": "uuid",
            "file_path": "/path/to/file",
            "chunk_index": 0
        },
        "created_at": "2026-01-21T10:00:00Z"
    }
}
```

### 3.5 Module LLM

#### Architecture LLM-agnostic

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator
from pydantic import BaseModel

class Message(BaseModel):
    role: str  # system, user, assistant
    content: str

class LLMConfig(BaseModel):
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = True

class LLMProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        config: LLMConfig
    ) -> str:
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        config: LLMConfig
    ) -> AsyncIterator[str]:
        pass

class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def stream(self, messages, config):
        async with self.client.messages.stream(
            model=config.model,
            max_tokens=config.max_tokens,
            messages=[m.model_dump() for m in messages]
        ) as stream:
            async for text in stream.text_stream:
                yield text

class MistralProvider(LLMProvider):
    # Similar implementation

class OllamaProvider(LLMProvider):
    # Local LLM via Ollama API

class LLMService:
    def __init__(self):
        self.providers: dict[str, LLMProvider] = {}
        self.default_provider = "claude"

    def register(self, name: str, provider: LLMProvider):
        self.providers[name] = provider

    async def chat(self, messages, config, provider=None):
        p = self.providers.get(provider or self.default_provider)
        if config.stream:
            async for token in p.stream(messages, config):
                yield token
        else:
            yield await p.complete(messages, config)
```

### 3.6 Module Fichiers

```python
from pathlib import Path
from typing import Protocol

class FileParser(Protocol):
    def parse(self, path: Path) -> str:
        """Extract text content from file"""
        ...

class PDFParser:
    def parse(self, path: Path) -> str:
        import pypdf
        reader = pypdf.PdfReader(path)
        return "\n\n".join(page.extract_text() for page in reader.pages)

class DocxParser:
    def parse(self, path: Path) -> str:
        from docx import Document
        doc = Document(path)
        return "\n\n".join(p.text for p in doc.paragraphs)

class TextParser:
    def parse(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

class FileService:
    PARSERS = {
        ".pdf": PDFParser(),
        ".docx": DocxParser(),
        ".doc": DocxParser(),
        ".txt": TextParser(),
        ".md": TextParser(),
    }
    MAX_SIZE = 10 * 1024 * 1024  # 10 MB

    def get_parser(self, path: Path) -> FileParser | None:
        return self.PARSERS.get(path.suffix.lower())

    def parse_file(self, path: Path) -> str | None:
        if path.stat().st_size > self.MAX_SIZE:
            raise ValueError(f"File too large: {path}")
        parser = self.get_parser(path)
        if parser:
            return parser.parse(path)
        return None
```

---

## 4. Flux de données

### 4.1 Flux 1 : Conversation simple

```
┌─────────┐    ┌──────────┐    ┌───────────┐    ┌─────────┐
│  User   │───►│ Frontend │───►│  Backend  │───►│ LLM API │
│  Input  │    │          │    │           │    │         │
└─────────┘    └──────────┘    └───────────┘    └────┬────┘
                                                      │
                                                      │ Stream
                                                      ▼
┌─────────┐    ┌──────────┐    ┌───────────┐    ┌─────────┐
│  User   │◄───│ Frontend │◄───│  Backend  │◄───│Response │
│  Sees   │ SSE│          │    │   (SSE)   │    │ Tokens  │
└─────────┘    └──────────┘    └───────────┘    └─────────┘
```

**Séquence** :
1. User tape message dans `ChatInput`
2. `chatStore.sendMessage()` → POST /api/chat/send
3. Backend construit le prompt avec contexte
4. Backend appelle LLM API en streaming
5. Backend forward les tokens via SSE
6. Frontend affiche les tokens en temps réel
7. Backend sauvegarde message complet en SQLite
8. Frontend met à jour `chatStore`

### 4.2 Flux 2 : Conversation avec mémoire

```
┌─────────┐
│  User   │
│  Input  │
└────┬────┘
     │
     ▼
┌───────────────────────────────────────────────────────────────┐
│                         Backend                                │
│                                                                │
│  1. Parse input                                                │
│     │                                                          │
│     ▼                                                          │
│  2. ┌─────────────────────────────────────────────────────┐   │
│     │              Memory Query                            │   │
│     │  ┌───────────────┐  ┌───────────────┐              │   │
│     │  │ Qdrant Search │  │  SQLite FTS   │              │   │
│     │  │ (semantic)    │  │  (keyword)    │              │   │
│     │  └───────┬───────┘  └───────┬───────┘              │   │
│     │          │                  │                       │   │
│     │          └──────┬───────────┘                       │   │
│     │                 ▼                                   │   │
│     │         ┌──────────────┐                           │   │
│     │         │   Reranker   │                           │   │
│     │         │  (optional)  │                           │   │
│     │         └──────┬───────┘                           │   │
│     │                │                                   │   │
│     └────────────────┼───────────────────────────────────┘   │
│                      ▼                                        │
│  3. Build context (relevant memories + conversation history)  │
│     │                                                          │
│     ▼                                                          │
│  4. Call LLM with enriched prompt                             │
│     │                                                          │
│     ▼                                                          │
│  5. Stream response                                            │
│     │                                                          │
│     ▼                                                          │
│  6. Extract entities (async, background)                      │
│     │                                                          │
│     ▼                                                          │
│  7. Update memory if new info detected                        │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

### 4.3 Flux 3 : Indexation fichier

```
┌─────────────────┐
│ File Drop/Select│
└────────┬────────┘
         │
         ▼
┌───────────────────────────────────────────────────────────────┐
│                         Backend                                │
│                                                                │
│  1. Validate file (size, type)                                │
│     │                                                          │
│     ▼                                                          │
│  2. Parse content (PDF/DOCX/TXT)                              │
│     │                                                          │
│     ▼                                                          │
│  3. Chunk text (500 tokens, 50 overlap)                       │
│     │                                                          │
│     ▼                                                          │
│  4. ┌─────────────────────────────────────────────────────┐   │
│     │                 For each chunk:                      │   │
│     │  a. Generate embedding (nomic-embed-text)           │   │
│     │  b. Store in Qdrant with metadata                   │   │
│     └─────────────────────────────────────────────────────┘   │
│     │                                                          │
│     ▼                                                          │
│  5. Store file metadata in SQLite                             │
│     │                                                          │
│     ▼                                                          │
│  6. Update FTS index                                          │
│     │                                                          │
│     ▼                                                          │
│  7. Return confirmation + summary                             │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

---

## 5. Sécurité et données

### 5.1 Stockage des données

```
$HOME/.therese/           # macOS/Linux
%APPDATA%\therese\        # Windows
│
├── config.toml           # Configuration (non sensible)
├── therese.db            # SQLite database
├── qdrant_data/          # Qdrant vector storage
├── logs/                 # Application logs
│   └── therese.log
└── cache/                # Temporary files
    └── embeddings/
```

### 5.2 Gestion des secrets

```toml
# config.toml
[llm]
provider = "claude"  # claude, mistral, ollama

[llm.claude]
# API key stored in OS keychain, not in file
# macOS: Keychain Access
# Windows: Credential Manager
# Linux: libsecret

[privacy]
telemetry = false
crash_reports = false
```

**Stockage API key** :
- macOS : Keychain via `security` CLI
- Windows : Credential Manager via `wincred`
- Linux : libsecret via `secret-tool`

```python
import keyring

def get_api_key(provider: str) -> str | None:
    return keyring.get_password("therese", f"{provider}_api_key")

def set_api_key(provider: str, key: str):
    keyring.set_password("therese", f"{provider}_api_key", key)
```

### 5.3 Données envoyées au LLM

**Ce qui est envoyé** :
- Message utilisateur
- Contexte mémoire pertinent (contacts, projets mentionnés)
- Historique conversation (limité aux N derniers messages)

**Ce qui n'est PAS envoyé** :
- Clé API (header only)
- Fichiers complets (seulement chunks pertinents)
- Logs système
- Métadonnées techniques

### 5.4 RGPD Compliance

| Droit | Implémentation |
|-------|----------------|
| **Accès** | Export JSON/SQLite complet via Settings |
| **Rectification** | CRUD sur toutes les entités |
| **Effacement** | Suppression dossier `.therese/` |
| **Portabilité** | Export JSON standard |
| **Limitation** | Pause indexation possible |

### 5.5 Logging

```python
import structlog

logger = structlog.get_logger()

# Log levels
# - ERROR: Errors requiring attention
# - WARNING: Unusual but recoverable
# - INFO: Key operations (file indexed, conversation created)
# - DEBUG: Detailed trace (disabled in prod)

# What we log
logger.info("file_indexed", path=path, chunks=len(chunks))
logger.info("conversation_created", id=conv_id)
logger.warning("llm_rate_limited", provider="claude", retry_after=60)
logger.error("file_parse_failed", path=path, error=str(e))

# What we DON'T log
# - Message content
# - API keys
# - Personal data (names, emails)
# - File contents
```

---

## 6. Performance

### 6.1 Cibles

| Opération | Cible | Mesure |
|-----------|-------|--------|
| Cold start | < 2s | Time to interactive |
| Memory search | < 200ms | P95 latency |
| File indexing | < 5s/MB | PDF processing |
| Embedding generation | < 100ms | Per chunk |
| Context assembly | < 50ms | Memory retrieval |

### 6.2 Stratégies d'optimisation

**Frontend** :
- Virtualized lists (react-window) pour historique
- Code splitting par route
- Lazy loading composants lourds
- Debounce search (300ms)

**Backend** :
- Connection pool SQLite (WAL mode)
- Qdrant quantization (scalar)
- Embedding batch processing
- LRU cache pour embeddings fréquents

**Tauri** :
- Sidecar warmup au startup
- Lazy backend launch (first request)
- Background indexing

### 6.3 Monitoring local

```python
import time
from functools import wraps

metrics = {}

def timed(name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                if name not in metrics:
                    metrics[name] = []
                metrics[name].append(duration)
                if len(metrics[name]) > 1000:
                    metrics[name] = metrics[name][-1000:]
        return wrapper
    return decorator

@timed("memory_search")
async def search_memory(query: str):
    ...
```

---

## 7. Évolutivité

### 7.1 Ajouter un provider LLM

1. Créer `app/services/llm/providers/new_provider.py`
2. Implémenter `LLMProvider` interface
3. Enregistrer dans `LLMService`
4. Ajouter config dans `config.toml`
5. UI: nouveau choix dans Settings

### 7.2 Ajouter un type de fichier

1. Créer parser dans `app/utils/parsers/`
2. Implémenter `FileParser` protocol
3. Enregistrer extension dans `FileService.PARSERS`
4. Tests unitaires

### 7.3 Ajouter une intégration (Google Drive)

```
src/backend/app/
├── integrations/
│   ├── __init__.py
│   ├── base.py              # Integration protocol
│   ├── google_drive.py      # OAuth + API
│   └── notion.py            # Future
```

**Interface** :
```python
class Integration(Protocol):
    name: str

    async def connect(self, credentials: dict) -> bool
    async def list_files(self, folder: str | None) -> list[File]
    async def read_file(self, file_id: str) -> bytes
    async def disconnect(self) -> None
```

### 7.4 Plugin system (v2.0)

```
~/.therese/plugins/
├── my-plugin/
│   ├── manifest.json
│   ├── main.py          # Python entrypoint
│   └── ui/              # Optional React components
```

**Manifest** :
```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Description",
  "entrypoint": "main.py",
  "permissions": ["memory:read", "files:read"],
  "hooks": ["on_message", "on_file_indexed"]
}
```

---

## 8. ADRs (Architecture Decision Records)

### ADR-001: Tauri vs Electron

**Contexte** : Besoin d'une app desktop cross-platform avec accès filesystem.

**Options considérées** :
1. **Electron** : Mature, large ecosystem, mais bundle 150+ Mo, RAM hungry
2. **Tauri** : Bundle léger (5-10 Mo), Rust perf, mais écosystème plus jeune
3. **Flutter** : Single codebase, mais UI non-native feel, moins adapté desktop

**Décision** : **Tauri 2.0**

**Justification** :
- Bundle 15x plus léger qu'Electron
- Meilleure performance (Rust backend)
- Accès filesystem natif sécurisé
- Tauri 2.0 stable depuis 2024
- Roadmap active (mobile support)

**Conséquences** :
- Nécessite Rust installé pour le dev
- Moins de libs JS natives (workaround via Tauri commands)
- Équipe doit apprendre les bases Rust

**Status** : Accepted

---

### ADR-002: SQLite vs PostgreSQL

**Contexte** : Besoin d'une base de données pour les données structurées (contacts, projets).

**Options considérées** :
1. **PostgreSQL** : Robuste, features avancées, mais requiert serveur
2. **SQLite** : Embedded, zero config, mais single-writer
3. **DuckDB** : Analytics-oriented, embedded, mais moins mature pour OLTP

**Décision** : **SQLite en mode WAL**

**Justification** :
- Zero config, embedded dans l'app
- Backup = copier un fichier
- Performance suffisante pour 10K+ entités
- WAL mode permet concurrent reads
- JSON functions pour données semi-structurées

**Conséquences** :
- Single writer (ok pour app desktop mono-user)
- Pas de replication native
- Migration vers PostgreSQL possible si besoin multi-device

**Status** : Accepted

---

### ADR-003: Qdrant embedded vs server

**Contexte** : Besoin d'une base vectorielle pour la recherche sémantique.

**Options considérées** :
1. **Qdrant server** : Scalable, mais overhead process séparé
2. **Qdrant embedded** : In-process, mais moins features
3. **Chroma** : Simple, mais moins performant
4. **pgvector** : Via SQLite extension, mais immature

**Décision** : **Qdrant embedded mode**

**Justification** :
- In-process, pas de serveur séparé
- Performance native (Rust)
- Hybrid search (dense + sparse)
- Quantization pour réduire RAM
- Migration vers server mode triviale si besoin

**Conséquences** :
- Limité à ~1M vectors (suffisant pour usage perso)
- Pas de distributed search
- Backup: copier le dossier data

**Status** : Accepted

---

### ADR-004: UV vs pip/poetry

**Contexte** : Besoin d'un package manager Python moderne.

**Options considérées** :
1. **pip** : Standard, mais lent, pas de lockfile natif
2. **poetry** : Lockfile, virtual env, mais lent
3. **UV** : Rust-based, 10-100x faster, lockfile

**Décision** : **UV**

**Justification** :
- 10-100x plus rapide que pip/poetry
- Lockfile natif (uv.lock)
- Compatible pyproject.toml standard
- Remplace virtualenv
- Développé par Astral (créateurs de Ruff)

**Conséquences** :
- Tooling plus récent (docs moins fournies)
- Équipe doit migrer de pip/poetry
- CI/CD à adapter

**Status** : Accepted

---

### ADR-005: FastAPI sidecar vs Tauri Rust backend

**Contexte** : Où mettre la logique métier (memory, LLM, files)?

**Options considérées** :
1. **Tauri Rust backend** : Tout en Rust, mais écosystème IA limité
2. **FastAPI sidecar** : Python pour IA, communication HTTP
3. **Hybrid** : Rust pour perf-critical, Python pour IA

**Décision** : **FastAPI sidecar**

**Justification** :
- Écosystème Python IA riche (anthropic, qdrant-client, pypdf)
- Ludo connaît Python
- Prototypage rapide
- Sidecar spawné par Tauri
- Communication localhost (latence négligeable)

**Conséquences** :
- Bundle légèrement plus gros (Python runtime)
- Deux processes à gérer
- IPC overhead (~1-5ms)

**Alternatives futures** :
- Migrer vers Rust pour fonctions perf-critical
- PyO3 pour binding Python-Rust

**Status** : Accepted

---

## 9. Questions ouvertes

| Question | Options | Décision requise |
|----------|---------|------------------|
| **Embedding model** | nomic-embed-text (768) vs mxbai (1024) | Benchmark à faire |
| **Chunking strategy** | Fixed 500 tokens vs semantic | À tester avec vrais docs |
| **Context window usage** | 8K vs 16K vs 32K | Dépend du plan API |
| **Auto-update mechanism** | Tauri updater vs custom | À décider en v1.1 |
| **Crash reporting** | Sentry local vs none | Privacy considerations |
| **Analytics** | Opt-in local vs none | User research needed |
| **Backup format** | SQLite dump vs JSON export | UX consideration |
| **Multi-language** | French only vs i18n | v1.0 = FR, v2.0 = i18n |

---

## 10. Diagramme de déploiement

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            User Machine                                  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     THÉRÈSE.app / THÉRÈSE.exe                       │ │
│  │                                                                      │ │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────────┐ │ │
│  │  │ Tauri Binary │   │ WebView      │   │ Python Sidecar (bundled) │ │ │
│  │  │ (5 Mo)       │   │ (system)     │   │ (~30 Mo with deps)       │ │ │
│  │  └──────────────┘   └──────────────┘   └──────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                          ~/.therese/                                │ │
│  │  ┌──────────┐  ┌────────────┐  ┌────────┐  ┌───────────────────┐  │ │
│  │  │config.toml│ │therese.db │  │qdrant/ │  │ logs/            │  │ │
│  │  │ (1 Ko)    │ │ (SQLite)  │  │ (data) │  │ therese.log      │  │ │
│  │  └──────────┘  └────────────┘  └────────┘  └───────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
           │                                              │
           │ HTTPS (API calls only)                       │ OS Keychain
           │                                              │ (API keys)
           ▼                                              │
┌─────────────────────────┐                              │
│     External APIs       │◄─────────────────────────────┘
│  ┌───────────────────┐  │
│  │ api.anthropic.com │  │  Claude API
│  └───────────────────┘  │
│  ┌───────────────────┐  │
│  │ api.mistral.ai    │  │  Mistral API (fallback)
│  └───────────────────┘  │
│  ┌───────────────────┐  │
│  │ localhost:11434   │  │  Ollama (optional, v2)
│  └───────────────────┘  │
└─────────────────────────┘
```

---

## 11. Checklist de validation

### Pré-développement

- [ ] Stack validée par l'équipe
- [ ] Machines de dev configurées (Rust, Node, Python, UV)
- [ ] Repo Git créé avec structure de base
- [ ] CI/CD pipeline configuré (GitHub Actions)
- [ ] Environnements de test (macOS, Windows, Linux)

### MVP Ready

- [ ] Tous les ADRs documentés et acceptés
- [ ] Schémas de données finalisés
- [ ] API endpoints documentés (OpenAPI)
- [ ] Design system tokens validés
- [ ] Tests unitaires scaffold
- [ ] Documentation développeur

### Production Ready

- [ ] Tests end-to-end
- [ ] Performance benchmarks
- [ ] Security audit (basic)
- [ ] Auto-update mechanism
- [ ] Crash reporting (opt-in)
- [ ] Documentation utilisateur

---

*Document généré le 21 janvier 2026*
*THÉRÈSE v2 - Synoptïa*
