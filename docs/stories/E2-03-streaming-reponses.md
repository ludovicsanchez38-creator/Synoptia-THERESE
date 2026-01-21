# Story E2-03 : Implémenter le streaming des réponses

## Description

En tant que **utilisateur**,
Je veux **voir les réponses s'afficher progressivement**,
Afin de **avoir un feedback immédiat et ne pas attendre**.

## Contexte technique

- **Composants impactés** : Backend Python, Frontend React
- **Dépendances** : E2-02
- **Fichiers concernés** :
  - `src/backend/therese/services/llm.py` (màj)
  - `src/backend/therese/api/routes/chat.py` (màj)
  - `src/frontend/src/components/chat/MessageItem.tsx` (màj)
  - `src/frontend/src/stores/chatStore.ts` (màj)

## Critères d'acceptation

- [ ] Endpoint SSE `/chat/stream` envoie les tokens un par un
- [ ] Frontend affiche les caractères au fur et à mesure
- [ ] Indicateur "THÉRÈSE réfléchit..." pendant le début
- [ ] Bouton stop pour annuler le streaming
- [ ] Curseur clignotant pendant le streaming
- [ ] Performance fluide (pas de lag visuel)

## Notes techniques

### Backend SSE

```python
# therese/api/routes/chat.py
from fastapi.responses import StreamingResponse
import asyncio

@router.post("/stream")
async def stream_message(request: MessageRequest):
    async def generate():
        async for chunk in llm_service.stream(
            messages=[{"role": "user", "content": request.content}]
        ):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

### Service LLM streaming

```python
# therese/services/llm.py
from typing import AsyncIterator

async def stream(
    self,
    messages: list[dict],
    system: str | None = None
) -> AsyncIterator[str]:
    with self.client.messages.stream(
        model=self.settings.model,
        max_tokens=self.settings.max_tokens,
        system=system or SYSTEM_PROMPT,
        messages=messages
    ) as stream:
        for text in stream.text_stream:
            yield text
```

### Frontend EventSource

```typescript
// lib/api.ts
export function streamMessage(
  content: string,
  onChunk: (chunk: string) => void,
  onDone: () => void,
  onError: (error: Error) => void
): () => void {
  const controller = new AbortController();

  fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
    signal: controller.signal,
  })
    .then(async (response) => {
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              onDone();
            } else {
              const { content } = JSON.parse(data);
              onChunk(content);
            }
          }
        }
      }
    })
    .catch(onError);

  return () => controller.abort();
}
```

### Store avec streaming

```typescript
// stores/chatStore.ts
interface ChatStore {
  // ... existing
  streamingContent: string;
  isStreaming: boolean;
  abortStream: (() => void) | null;
}

const streamMessage = async (content: string) => {
  set({ isLoading: true, isStreaming: true, streamingContent: '' });

  // Add user message
  get().addMessage({ role: 'user', content });

  // Create placeholder for assistant message
  const assistantId = crypto.randomUUID();

  const abort = streamMessage(
    content,
    (chunk) => {
      set((state) => ({
        streamingContent: state.streamingContent + chunk,
      }));
    },
    () => {
      // Finalize message
      get().addMessage({
        role: 'assistant',
        content: get().streamingContent,
      });
      set({ isStreaming: false, streamingContent: '', isLoading: false });
    },
    (error) => {
      console.error(error);
      set({ isStreaming: false, isLoading: false });
    }
  );

  set({ abortStream: abort });
};
```

### Composant avec curseur

```tsx
// components/chat/StreamingMessage.tsx
export function StreamingMessage({ content }: { content: string }) {
  return (
    <div className="text-text-muted whitespace-pre-wrap">
      {content}
      <span className="inline-block w-2 h-4 bg-accent-cyan animate-pulse ml-1" />
    </div>
  );
}
```

### Bouton Stop

```tsx
// components/chat/ChatInput.tsx
const { isStreaming, abortStream } = useChatStore();

{isStreaming && (
  <button
    onClick={() => abortStream?.()}
    className="px-4 py-3 bg-error text-white rounded-lg"
  >
    Stop
  </button>
)}
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Definition of Done

- [ ] Streaming fonctionne end-to-end
- [ ] Curseur visible pendant le streaming
- [ ] Stop annule effectivement la requête
- [ ] Pas de lag visuel
- [ ] Tests E2E streaming

---

*Sprint : 2*
*Assigné : Agent Dev*
