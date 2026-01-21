# Story E2-02 : Intégrer l'API Claude (envoi/réception)

## Description

En tant que **utilisateur**,
Je veux **recevoir des réponses intelligentes de Claude**,
Afin de **obtenir de l'aide sur mes tâches**.

## Contexte technique

- **Composants impactés** : Backend Python, Frontend React
- **Dépendances** : E1-02, E1-05, E2-01
- **Fichiers concernés** :
  - `src/backend/therese/services/llm.py` (nouveau)
  - `src/backend/therese/api/routes/chat.py` (nouveau)
  - `src/frontend/src/lib/api.ts` (màj)

## Critères d'acceptation

- [ ] Endpoint POST `/chat/message` accepte un message
- [ ] Backend appelle l'API Claude avec le message
- [ ] Réponse retournée au frontend
- [ ] Clé API stockée de manière sécurisée
- [ ] Gestion des erreurs API (rate limit, timeout)
- [ ] System prompt THÉRÈSE configuré

## Notes techniques

### Installation

```bash
uv add anthropic
```

### Service LLM

```python
# therese/services/llm.py
from anthropic import Anthropic
from pydantic_settings import BaseSettings

class LLMSettings(BaseSettings):
    anthropic_api_key: str
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096

    class Config:
        env_file = ".env"

SYSTEM_PROMPT = """Tu es THÉRÈSE, l'assistante IA de {user_name}.

Tu es :
- Efficace et directe
- Chaleureuse mais professionnelle
- Experte en productivité et automatisation

Tu connais :
- Le contexte du travail de l'utilisateur
- Ses projets en cours
- Ses contacts et clients

Réponds en français, de manière concise.
"""

class LLMService:
    def __init__(self, settings: LLMSettings):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.settings = settings

    async def complete(
        self,
        messages: list[dict],
        system: str | None = None
    ) -> str:
        response = self.client.messages.create(
            model=self.settings.model,
            max_tokens=self.settings.max_tokens,
            system=system or SYSTEM_PROMPT.format(user_name="Ludo"),
            messages=messages
        )
        return response.content[0].text
```

### Route Chat

```python
# therese/api/routes/chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])

class MessageRequest(BaseModel):
    content: str
    conversation_id: str | None = None

class MessageResponse(BaseModel):
    content: str
    conversation_id: str

@router.post("/message", response_model=MessageResponse)
async def send_message(request: MessageRequest):
    try:
        # Format messages for Claude
        messages = [{"role": "user", "content": request.content}]

        # Get response
        response = await llm_service.complete(messages)

        return MessageResponse(
            content=response,
            conversation_id=request.conversation_id or str(uuid.uuid4())
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Client API frontend

```typescript
// lib/api.ts
interface ChatMessage {
  content: string;
  conversation_id?: string;
}

interface ChatResponse {
  content: string;
  conversation_id: string;
}

export async function sendMessage(message: ChatMessage): Promise<ChatResponse> {
  return api.request('/chat/message', {
    method: 'POST',
    body: JSON.stringify(message),
  });
}
```

### Mise à jour du store

```typescript
// stores/chatStore.ts
const sendMessage = async (content: string) => {
  set({ isLoading: true });

  // Add user message
  const userMessage = { role: 'user' as const, content };
  get().addMessage(userMessage);

  try {
    const response = await api.sendMessage({
      content,
      conversation_id: get().conversationId,
    });

    // Add assistant message
    get().addMessage({ role: 'assistant', content: response.content });
    set({ conversationId: response.conversation_id });
  } catch (error) {
    // Handle error
    get().addMessage({
      role: 'assistant',
      content: 'Désolée, une erreur est survenue. Réessaie.',
    });
  } finally {
    set({ isLoading: false });
  }
};
```

### Gestion de la clé API

```python
# therese/config.py
from pathlib import Path
import keyring

def get_api_key() -> str | None:
    """Get API key from secure storage"""
    return keyring.get_password("therese", "anthropic_api_key")

def set_api_key(key: str):
    """Store API key securely"""
    keyring.set_password("therese", "anthropic_api_key", key)
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Definition of Done

- [ ] Message envoyé → réponse Claude reçue
- [ ] Clé API stockée dans keyring
- [ ] Erreurs gérées gracieusement
- [ ] Tests API passent

---

*Sprint : 1*
*Assigné : Agent Dev*
