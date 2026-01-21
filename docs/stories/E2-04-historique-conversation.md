# Story E2-04 : Gérer l'historique de conversation (session)

## Description

En tant que **utilisateur**,
Je veux **que mes conversations soient sauvegardées**,
Afin de **pouvoir reprendre où j'en étais**.

## Contexte technique

- **Composants impactés** : Backend Python, Frontend React, SQLite
- **Dépendances** : E1-03, E2-02
- **Fichiers concernés** :
  - `src/backend/therese/services/conversation.py` (nouveau)
  - `src/backend/therese/api/routes/conversations.py` (nouveau)
  - `src/frontend/src/components/sidebar/` (nouveau)

## Critères d'acceptation

- [ ] Conversations sauvegardées en SQLite
- [ ] Liste des conversations dans une sidebar
- [ ] Clic sur une conversation la charge
- [ ] Nouvelle conversation via bouton ou ⌘N
- [ ] Titre auto-généré depuis le premier message
- [ ] Conversations triées par date (récentes en haut)
- [ ] Suppression d'une conversation possible

## Notes techniques

### Service Conversation

```python
# therese/services/conversation.py
from sqlmodel import Session, select
from ..models.conversation import Conversation, Message

class ConversationService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, title: str | None = None) -> Conversation:
        conversation = Conversation(title=title)
        self.session.add(conversation)
        self.session.commit()
        return conversation

    def get(self, conversation_id: str) -> Conversation | None:
        return self.session.get(Conversation, conversation_id)

    def list_all(self, limit: int = 50) -> list[Conversation]:
        statement = (
            select(Conversation)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return self.session.exec(statement).all()

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        self.session.add(message)

        # Update conversation title if first user message
        conv = self.get(conversation_id)
        if conv and not conv.title and role == "user":
            conv.title = content[:50] + ("..." if len(content) > 50 else "")

        self.session.commit()
        return message

    def get_messages(self, conversation_id: str) -> list[Message]:
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        return self.session.exec(statement).all()

    def delete(self, conversation_id: str):
        conversation = self.get(conversation_id)
        if conversation:
            self.session.delete(conversation)
            self.session.commit()
```

### Routes API

```python
# therese/api/routes/conversations.py
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.get("/")
async def list_conversations():
    return conversation_service.list_all()

@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    conv = conversation_service.get(conversation_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return {
        "conversation": conv,
        "messages": conversation_service.get_messages(conversation_id)
    }

@router.post("/")
async def create_conversation():
    return conversation_service.create()

@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    conversation_service.delete(conversation_id)
    return {"status": "deleted"}
```

### Sidebar component

```tsx
// components/sidebar/ConversationList.tsx
export function ConversationList() {
  const { conversations, currentId, loadConversation, createNew } = useChatStore();

  return (
    <div className="w-64 bg-surface border-r border-border flex flex-col">
      <div className="p-4">
        <button
          onClick={createNew}
          className="w-full px-4 py-2 bg-accent-cyan text-bg rounded-lg font-medium"
        >
          + Nouvelle conversation
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {conversations.map((conv) => (
          <button
            key={conv.id}
            onClick={() => loadConversation(conv.id)}
            className={cn(
              "w-full px-4 py-3 text-left hover:bg-surface-elevated",
              currentId === conv.id && "bg-surface-elevated"
            )}
          >
            <div className="text-sm font-medium text-text truncate">
              {conv.title || "Nouvelle conversation"}
            </div>
            <div className="text-xs text-text-muted">
              {formatRelativeTime(conv.updated_at)}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
```

### Store mise à jour

```typescript
// stores/chatStore.ts
interface ChatStore {
  conversations: Conversation[];
  currentId: string | null;
  fetchConversations: () => Promise<void>;
  loadConversation: (id: string) => Promise<void>;
  createNew: () => Promise<void>;
  deleteConversation: (id: string) => Promise<void>;
}
```

## Estimation

- **Complexité** : S
- **Points** : 3

## Maquette

```
┌────────────────┬────────────────────────────────────────┐
│ [+ Nouvelle]   │                                        │
├────────────────┤  Messages de la conversation active    │
│ Projet THÉRÈSE │                                        │
│ il y a 2h      │                                        │
├────────────────┤                                        │
│ Budget 2026    │                                        │
│ hier           │                                        │
├────────────────┤                                        │
│ Idées article  │                                        │
│ 3 janv.        │                                        │
└────────────────┴────────────────────────────────────────┘
```

## Definition of Done

- [ ] Conversations sauvegardées en DB
- [ ] Sidebar affiche la liste
- [ ] Navigation entre conversations
- [ ] ⌘N crée une nouvelle conversation
- [ ] Suppression fonctionne

---

*Sprint : 2*
*Assigné : Agent Dev*
