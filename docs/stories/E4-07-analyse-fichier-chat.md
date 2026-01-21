# Story E4-07 : Permettre l'analyse d'un fichier via le chat

## Description

En tant que **utilisateur**,
Je veux **demander à THÉRÈSE d'analyser un fichier spécifique**,
Afin de **obtenir des résumés, extractions ou réponses basées sur son contenu**.

## Contexte technique

- **Composants impactés** : Backend Python, Frontend React
- **Dépendances** : E2-02, E4-02, E4-03, E4-06
- **Fichiers concernés** :
  - `src/backend/therese/services/file_analyzer.py` (nouveau)
  - `src/backend/therese/api/routes/chat.py` (màj)
  - `src/frontend/src/components/chat/FileAnalysisRequest.tsx` (nouveau)

## Critères d'acceptation

- [ ] Commande "/analyse [fichier]" reconnue
- [ ] Envoi du contenu au LLM avec le prompt
- [ ] Résumé automatique si demandé
- [ ] Extraction d'informations spécifiques
- [ ] Questions sur le contenu du fichier
- [ ] Affichage du fichier source dans la réponse

## Notes techniques

### Service d'analyse

```python
# therese/services/file_analyzer.py
from dataclasses import dataclass
from typing import Literal

from .llm import llm_service
from .file_parser import pdf_parser, docx_parser, text_parser, markdown_parser

AnalysisType = Literal["summary", "extract", "qa", "custom"]


@dataclass
class AnalysisRequest:
    file_path: str
    analysis_type: AnalysisType
    prompt: str | None = None
    extraction_fields: list[str] | None = None


@dataclass
class AnalysisResult:
    file_name: str
    file_path: str
    analysis_type: AnalysisType
    result: str
    tokens_used: int


PROMPTS = {
    "summary": """Résume le document suivant de manière concise mais complète.
Inclus les points clés, les conclusions principales et les informations importantes.

Document :
{content}

Résumé :""",

    "extract": """Extrais les informations suivantes du document :
{fields}

Document :
{content}

Extraction (format JSON) :""",

    "qa": """Réponds à la question suivante en te basant uniquement sur le document fourni.
Si l'information n'est pas dans le document, dis-le clairement.

Document :
{content}

Question : {question}

Réponse :""",
}


class FileAnalyzer:
    def __init__(self):
        self.parsers = {
            '.pdf': pdf_parser,
            '.docx': docx_parser,
            '.doc': docx_parser,
            '.txt': text_parser,
            '.md': markdown_parser,
        }

    async def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """Analyse un fichier selon le type demandé"""
        # Parser le fichier
        path = Path(request.file_path)
        ext = path.suffix.lower()
        parser = self.parsers.get(ext)

        if not parser:
            raise ValueError(f"Type de fichier non supporté: {ext}")

        parsed = parser.parse(path)
        content = parsed.text

        # Tronquer si trop long (limite tokens)
        max_content_chars = 50000  # ~12500 tokens
        if len(content) > max_content_chars:
            content = content[:max_content_chars] + "\n\n[Document tronqué...]"

        # Construire le prompt
        if request.analysis_type == "summary":
            prompt = PROMPTS["summary"].format(content=content)
        elif request.analysis_type == "extract":
            fields = "\n".join(f"- {f}" for f in (request.extraction_fields or []))
            prompt = PROMPTS["extract"].format(fields=fields, content=content)
        elif request.analysis_type == "qa":
            prompt = PROMPTS["qa"].format(content=content, question=request.prompt)
        else:
            # Custom prompt
            prompt = f"{request.prompt}\n\nDocument :\n{content}"

        # Appeler le LLM
        response = await llm_service.complete(
            messages=[{"role": "user", "content": prompt}],
            system="Tu es un assistant expert en analyse de documents."
        )

        return AnalysisResult(
            file_name=path.name,
            file_path=str(path),
            analysis_type=request.analysis_type,
            result=response.content,
            tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else 0
        )

    async def summarize(self, file_path: str) -> AnalysisResult:
        """Raccourci pour résumer un fichier"""
        return await self.analyze(AnalysisRequest(
            file_path=file_path,
            analysis_type="summary"
        ))

    async def extract(
        self,
        file_path: str,
        fields: list[str]
    ) -> AnalysisResult:
        """Raccourci pour extraire des champs"""
        return await self.analyze(AnalysisRequest(
            file_path=file_path,
            analysis_type="extract",
            extraction_fields=fields
        ))

    async def ask(
        self,
        file_path: str,
        question: str
    ) -> AnalysisResult:
        """Raccourci pour poser une question sur un fichier"""
        return await self.analyze(AnalysisRequest(
            file_path=file_path,
            analysis_type="qa",
            prompt=question
        ))


# Singleton
file_analyzer = FileAnalyzer()
```

### Détection de commandes

```python
# therese/services/command_parser.py
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedCommand:
    command: str
    file_path: Optional[str] = None
    args: Optional[str] = None


class CommandParser:
    PATTERNS = {
        "analyze": re.compile(
            r'^/(?:analyse|analyze|résume|resume|summarize)\s+["\']?([^"\']+)["\']?\s*(.*)$',
            re.IGNORECASE
        ),
        "extract": re.compile(
            r'^/(?:extrait|extract)\s+["\']?([^"\']+)["\']?\s+(.+)$',
            re.IGNORECASE
        ),
        "ask_file": re.compile(
            r'^/(?:demande|ask)\s+["\']?([^"\']+)["\']?\s+(.+)$',
            re.IGNORECASE
        ),
    }

    def parse(self, message: str) -> ParsedCommand | None:
        """Parse une commande depuis un message"""
        message = message.strip()

        if not message.startswith('/'):
            return None

        for cmd_type, pattern in self.PATTERNS.items():
            match = pattern.match(message)
            if match:
                return ParsedCommand(
                    command=cmd_type,
                    file_path=match.group(1).strip(),
                    args=match.group(2).strip() if len(match.groups()) > 1 else None
                )

        return None


command_parser = CommandParser()
```

### Intégration dans le chat

```python
# therese/api/routes/chat.py (màj)
from ..services.command_parser import command_parser
from ..services.file_analyzer import file_analyzer


@router.post("/message")
async def send_message(request: MessageRequest):
    """Envoie un message avec support des commandes fichier"""

    # Vérifier si c'est une commande
    parsed_cmd = command_parser.parse(request.content)

    if parsed_cmd:
        return await handle_file_command(parsed_cmd, request.conversation_id)

    # Traitement normal du message...
    # ...


async def handle_file_command(
    cmd: ParsedCommand,
    conversation_id: str
) -> dict:
    """Gère les commandes liées aux fichiers"""

    if cmd.command == "analyze":
        result = await file_analyzer.summarize(cmd.file_path)
    elif cmd.command == "extract":
        fields = [f.strip() for f in cmd.args.split(',')]
        result = await file_analyzer.extract(cmd.file_path, fields)
    elif cmd.command == "ask_file":
        result = await file_analyzer.ask(cmd.file_path, cmd.args)
    else:
        raise HTTPException(400, f"Commande inconnue: {cmd.command}")

    # Sauvegarder dans l'historique
    # ...

    return {
        "type": "file_analysis",
        "file_name": result.file_name,
        "file_path": result.file_path,
        "analysis_type": result.analysis_type,
        "content": result.result,
        "tokens_used": result.tokens_used,
    }
```

### Composant UI

```tsx
// components/chat/FileAnalysisRequest.tsx
import { FileText, Search, MessageSquare, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

interface FileAnalysisMessageProps {
  message: {
    file_name: string;
    file_path: string;
    analysis_type: string;
    content: string;
  };
}

export function FileAnalysisMessage({ message }: FileAnalysisMessageProps) {
  const icons = {
    summary: Sparkles,
    extract: Search,
    qa: MessageSquare,
    custom: FileText,
  };
  const Icon = icons[message.analysis_type] || FileText;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col gap-3"
    >
      {/* Header fichier */}
      <div className="flex items-center gap-2 px-3 py-2 bg-surface-elevated rounded-lg">
        <FileText className="w-4 h-4 text-accent-cyan" />
        <span className="text-sm text-text">{message.file_name}</span>
        <span className="ml-auto flex items-center gap-1 text-xs text-text-muted">
          <Icon className="w-3 h-3" />
          {message.analysis_type === 'summary' && 'Résumé'}
          {message.analysis_type === 'extract' && 'Extraction'}
          {message.analysis_type === 'qa' && 'Q&A'}
        </span>
      </div>

      {/* Contenu de l'analyse */}
      <div className="prose prose-invert prose-sm max-w-none">
        <ReactMarkdown>{message.content}</ReactMarkdown>
      </div>
    </motion.div>
  );
}
```

### Suggestions de commandes

```tsx
// components/chat/CommandSuggestions.tsx
export function CommandSuggestions({ input, onSelect }: CommandSuggestionsProps) {
  const commands = [
    {
      command: '/analyse',
      description: 'Résumer un fichier',
      example: '/analyse rapport.pdf',
    },
    {
      command: '/extrait',
      description: 'Extraire des informations',
      example: '/extrait contrat.pdf nom, date, montant',
    },
    {
      command: '/demande',
      description: 'Poser une question sur un fichier',
      example: '/demande notes.md Quels sont les points clés ?',
    },
  ];

  const filtered = commands.filter(
    (c) => c.command.startsWith(input) || input.startsWith(c.command)
  );

  if (filtered.length === 0 || !input.startsWith('/')) {
    return null;
  }

  return (
    <div className="absolute bottom-full left-0 w-full mb-2 bg-surface border border-border rounded-lg shadow-lg overflow-hidden">
      {filtered.map((cmd) => (
        <button
          key={cmd.command}
          onClick={() => onSelect(cmd.command + ' ')}
          className="w-full flex items-start gap-3 px-4 py-3 hover:bg-surface-elevated text-left"
        >
          <code className="text-accent-cyan text-sm">{cmd.command}</code>
          <div className="flex-1">
            <p className="text-sm text-text">{cmd.description}</p>
            <p className="text-xs text-text-muted mt-0.5">{cmd.example}</p>
          </div>
        </button>
      ))}
    </div>
  );
}
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Maquette

```
┌─────────────────────────────────────────────────────────────┐
│ 👤 /analyse rapport-annuel.pdf                              │
├─────────────────────────────────────────────────────────────┤
│ 🤖 ┌──────────────────────────────────────────────────────┐ │
│    │ 📄 rapport-annuel.pdf                    ✨ Résumé   │ │
│    └──────────────────────────────────────────────────────┘ │
│                                                             │
│    **Résumé du rapport annuel**                             │
│                                                             │
│    Le rapport présente les résultats de l'année 2025 :      │
│                                                             │
│    - Chiffre d'affaires : +15% vs N-1                       │
│    - Marge opérationnelle : 12%                             │
│    - 3 nouvelles acquisitions                               │
│    - Expansion marché EMEA                                  │
│                                                             │
│    Points clés pour 2026 :                                  │
│    - Objectif CA +20%                                       │
│    - Lancement nouveau produit Q2                           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ 💬 /demande rapport.pdf Quel est le budget R&D ?       [→]  │
└─────────────────────────────────────────────────────────────┘
```

## Definition of Done

- [ ] Commande /analyse fonctionne
- [ ] Commande /extrait fonctionne
- [ ] Commande /demande fonctionne
- [ ] Suggestions de commandes
- [ ] Affichage source fichier
- [ ] Tests passent

---

*Sprint : 4*
*Assigné : Agent Dev*
