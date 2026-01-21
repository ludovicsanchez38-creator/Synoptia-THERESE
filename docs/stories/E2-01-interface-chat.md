# Story E2-01 : Créer l'interface chat (input + messages)

## Description

En tant que **utilisateur**,
Je veux **avoir une interface de chat épurée**,
Afin de **converser avec THÉRÈSE de manière naturelle**.

## Contexte technique

- **Composants impactés** : React frontend
- **Dépendances** : E1-01 (Tauri + React)
- **Fichiers concernés** :
  - `src/frontend/src/components/chat/` (nouveau)
  - `src/frontend/src/stores/chatStore.ts` (nouveau)

## Critères d'acceptation

- [ ] Zone de saisie avec auto-resize
- [ ] Liste de messages scrollable
- [ ] Distinction visuelle user vs assistant
- [ ] Timestamp discret sur chaque message
- [ ] Enter pour envoyer, Shift+Enter pour newline
- [ ] Placeholder "Message THÉRÈSE..."
- [ ] Scroll auto vers le bas sur nouveau message

## Notes techniques

### Composants

```
components/chat/
├── ChatContainer.tsx    # Layout principal
├── MessageList.tsx      # Liste scrollable
├── MessageItem.tsx      # Un message
├── ChatInput.tsx        # Zone de saisie
└── index.ts
```

### Store Zustand

```typescript
// stores/chatStore.ts
import { create } from 'zustand';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatStore {
  messages: Message[];
  isLoading: boolean;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isLoading: false,
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: crypto.randomUUID(),
          timestamp: new Date(),
        },
      ],
    })),
  clearMessages: () => set({ messages: [] }),
  setLoading: (isLoading) => set({ isLoading }),
}));
```

### Composant MessageItem

```tsx
// components/chat/MessageItem.tsx
interface MessageItemProps {
  message: Message;
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user';

  return (
    <div className={cn(
      "flex gap-3 p-4 rounded-lg",
      isUser ? "bg-surface" : "bg-surface-elevated"
    )}>
      <div className="shrink-0">
        {isUser ? (
          <div className="w-8 h-8 rounded-full bg-accent-cyan flex items-center justify-center text-sm font-medium">
            L
          </div>
        ) : (
          <div className="w-8 h-8 rounded-full bg-accent-magenta flex items-center justify-center">
            🤖
          </div>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium text-text">
            {isUser ? 'Vous' : 'THÉRÈSE'}
          </span>
          <span className="text-xs text-text-muted">
            {formatTime(message.timestamp)}
          </span>
        </div>
        <div className="text-text-muted whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    </div>
  );
}
```

### Composant ChatInput

```tsx
// components/chat/ChatInput.tsx
export function ChatInput() {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { addMessage, setLoading } = useChatStore();

  const handleSubmit = () => {
    if (!value.trim()) return;
    addMessage({ role: 'user', content: value });
    setValue('');
    // TODO: Call API in E2-02
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Auto-resize
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [value]);

  return (
    <div className="border-t border-border p-4">
      <div className="flex gap-2 items-end">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Message THÉRÈSE..."
          className="flex-1 resize-none bg-surface-elevated rounded-lg p-3 text-text placeholder:text-text-subtle focus:outline-none focus:ring-2 focus:ring-accent-cyan"
          rows={1}
        />
        <button
          onClick={handleSubmit}
          disabled={!value.trim()}
          className="px-4 py-3 bg-accent-cyan text-bg rounded-lg font-medium hover:opacity-90 disabled:opacity-50"
        >
          Envoyer
        </button>
      </div>
    </div>
  );
}
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Maquette

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ [L] Vous                              14:32      │   │
│  │ Bonjour THÉRÈSE !                               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ [🤖] THÉRÈSE                          14:32      │   │
│  │ Bonjour ! Comment puis-je t'aider               │   │
│  │ aujourd'hui ?                                   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Message THÉRÈSE...                    [Envoyer] │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Definition of Done

- [ ] Composants créés et stylés
- [ ] Store Zustand fonctionnel
- [ ] Envoi de message fonctionne (UI only)
- [ ] Auto-scroll actif
- [ ] Accessible au clavier

---

*Sprint : 1*
*Assigné : Agent Dev Frontend*
