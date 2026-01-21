# Story E3-08 : Ajouter l'extraction auto d'entités depuis conversations

## Description

En tant que **THÉRÈSE**,
Je veux **extraire automatiquement les informations importantes des conversations**,
Afin de **enrichir ma mémoire sans effort de l'utilisateur**.

## Contexte technique

- **Composants impactés** : Backend Python, Service LLM
- **Dépendances** : E2-02, E3-01, E3-03
- **Fichiers concernés** :
  - `src/backend/therese/services/entity_extractor.py` (nouveau)
  - `src/backend/therese/workers/extraction_worker.py` (nouveau)

## Critères d'acceptation

- [ ] Extraction de contacts (noms, entreprises, emails)
- [ ] Extraction de projets (noms, descriptions)
- [ ] Extraction de faits (informations factuelles)
- [ ] Extraction de préférences utilisateur
- [ ] Confidence score pour chaque extraction
- [ ] Validation humaine optionnelle avant stockage
- [ ] Extraction asynchrone (non bloquante)

## Notes techniques

### Service d'extraction

```python
# therese/services/entity_extractor.py
from dataclasses import dataclass
from typing import Literal
import json

from .llm import llm_service

EXTRACTION_PROMPT = """Tu es un assistant d'extraction d'entités. Analyse le message suivant et extrait :

1. **Contacts** : personnes mentionnées avec leur nom, entreprise, rôle si disponible
2. **Projets** : projets, missions ou tâches mentionnés
3. **Faits** : informations factuelles importantes à retenir
4. **Préférences** : préférences ou habitudes de l'utilisateur

Retourne UNIQUEMENT un JSON valide avec cette structure :
```json
{
  "contacts": [
    {"name": "...", "company": "...", "role": "...", "confidence": 0.0-1.0}
  ],
  "projects": [
    {"name": "...", "description": "...", "confidence": 0.0-1.0}
  ],
  "facts": [
    {"content": "...", "category": "work|personal|tech", "confidence": 0.0-1.0}
  ],
  "preferences": [
    {"key": "...", "value": "...", "confidence": 0.0-1.0}
  ]
}
```

Si rien n'est à extraire, retourne des listes vides.

Message à analyser :
{message}

Contexte de la conversation :
{context}
"""


@dataclass
class ExtractedContact:
    name: str
    company: str | None
    role: str | None
    confidence: float


@dataclass
class ExtractedProject:
    name: str
    description: str | None
    confidence: float


@dataclass
class ExtractedFact:
    content: str
    category: str
    confidence: float


@dataclass
class ExtractedPreference:
    key: str
    value: str
    confidence: float


@dataclass
class ExtractionResult:
    contacts: list[ExtractedContact]
    projects: list[ExtractedProject]
    facts: list[ExtractedFact]
    preferences: list[ExtractedPreference]


class EntityExtractor:
    CONFIDENCE_THRESHOLD = 0.7

    async def extract(
        self,
        message: str,
        context: str = ""
    ) -> ExtractionResult:
        """Extrait les entités d'un message"""
        prompt = EXTRACTION_PROMPT.format(
            message=message,
            context=context
        )

        response = await llm_service.complete(
            messages=[{"role": "user", "content": prompt}],
            system="Tu es un extracteur d'entités. Réponds uniquement en JSON valide."
        )

        return self._parse_response(response)

    def _parse_response(self, response: str) -> ExtractionResult:
        """Parse la réponse JSON du LLM"""
        try:
            # Extraire le JSON de la réponse
            start = response.find('{')
            end = response.rfind('}') + 1
            json_str = response[start:end]
            data = json.loads(json_str)

            return ExtractionResult(
                contacts=[
                    ExtractedContact(**c) for c in data.get("contacts", [])
                    if c.get("confidence", 0) >= self.CONFIDENCE_THRESHOLD
                ],
                projects=[
                    ExtractedProject(**p) for p in data.get("projects", [])
                    if p.get("confidence", 0) >= self.CONFIDENCE_THRESHOLD
                ],
                facts=[
                    ExtractedFact(**f) for f in data.get("facts", [])
                    if f.get("confidence", 0) >= self.CONFIDENCE_THRESHOLD
                ],
                preferences=[
                    ExtractedPreference(**p) for p in data.get("preferences", [])
                    if p.get("confidence", 0) >= self.CONFIDENCE_THRESHOLD
                ]
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse extraction: {e}")
            return ExtractionResult([], [], [], [])


# Singleton
entity_extractor = EntityExtractor()
```

### Worker d'extraction asynchrone

```python
# therese/workers/extraction_worker.py
import asyncio
from ..services.entity_extractor import entity_extractor, ExtractionResult
from ..services.memory_service import memory_service
from ..services.contact_service import contact_service
from ..services.project_service import project_service
from ..models.memory import Memory


class ExtractionWorker:
    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    async def start(self):
        """Démarre le worker"""
        self._running = True
        while self._running:
            try:
                message, conversation_id = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )
                await self._process(message, conversation_id)
            except asyncio.TimeoutError:
                continue

    async def stop(self):
        """Arrête le worker"""
        self._running = False

    async def enqueue(self, message: str, conversation_id: str):
        """Ajoute un message à la queue d'extraction"""
        await self._queue.put((message, conversation_id))

    async def _process(self, message: str, conversation_id: str):
        """Traite un message"""
        try:
            result = await entity_extractor.extract(message)
            await self._store_extractions(result, conversation_id)
        except Exception as e:
            logger.error(f"Extraction failed: {e}")

    async def _store_extractions(
        self,
        result: ExtractionResult,
        conversation_id: str
    ):
        """Stocke les entités extraites"""
        # Contacts
        for contact in result.contacts:
            existing = contact_service.find_by_name(contact.name)
            if not existing:
                contact_service.create(
                    first_name=contact.name.split()[0],
                    last_name=" ".join(contact.name.split()[1:]) or None,
                    company=contact.company,
                    role=contact.role
                )

        # Projets
        for project in result.projects:
            existing = project_service.find_by_name(project.name)
            if not existing:
                project_service.create(
                    name=project.name,
                    description=project.description
                )

        # Faits
        for fact in result.facts:
            memory_service.create(
                type="fact",
                category=fact.category,
                content=fact.content,
                source="extracted",
                confidence=fact.confidence,
                conversation_id=conversation_id
            )

        # Préférences
        for pref in result.preferences:
            memory_service.create(
                type="preference",
                content=f"{pref.key}: {pref.value}",
                source="extracted",
                confidence=pref.confidence,
                conversation_id=conversation_id
            )


# Singleton
extraction_worker = ExtractionWorker()
```

### Intégration dans le flux de chat

```python
# therese/api/routes/chat.py (màj)

@router.post("/message")
async def send_message(request: MessageRequest):
    # ... traitement normal ...

    # Lancer l'extraction en background
    if request.content:
        await extraction_worker.enqueue(
            message=request.content,
            conversation_id=request.conversation_id
        )

    return response
```

### Notification d'extraction (UI)

```tsx
// components/chat/ExtractionNotification.tsx
export function ExtractionNotification({ extraction }) {
  if (!extraction) return null;

  const count =
    extraction.contacts.length +
    extraction.projects.length +
    extraction.facts.length;

  if (count === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="px-4 py-2 bg-accent-cyan/10 border border-accent-cyan/30 rounded-lg text-sm"
    >
      <div className="flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-accent-cyan" />
        <span className="text-text">
          {count} élément{count > 1 ? 's' : ''} ajouté{count > 1 ? 's' : ''} à la mémoire
        </span>
        <button className="text-accent-cyan hover:underline ml-auto">
          Voir
        </button>
      </div>
    </motion.div>
  );
}
```

## Estimation

- **Complexité** : L
- **Points** : 8

## Definition of Done

- [ ] Extraction contacts fonctionne
- [ ] Extraction projets fonctionne
- [ ] Extraction faits fonctionne
- [ ] Confidence threshold respecté
- [ ] Worker async non bloquant
- [ ] Notification UI visible
- [ ] Tests avec exemples variés

---

*Sprint : 3-4*
*Assigné : Agent Dev Backend*
