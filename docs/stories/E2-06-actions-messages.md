# Story E2-06 : Implémenter copier/coller et actions sur messages

## Description

En tant que **utilisateur**,
Je veux **pouvoir copier et interagir avec les messages**,
Afin de **réutiliser facilement les réponses de THÉRÈSE**.

## Contexte technique

- **Composants impactés** : Frontend React
- **Dépendances** : E2-01, E2-05
- **Fichiers concernés** :
  - `src/frontend/src/components/chat/MessageActions.tsx` (nouveau)
  - `src/frontend/src/hooks/useClipboard.ts` (nouveau)

## Critères d'acceptation

- [ ] Bouton copier sur chaque message assistant
- [ ] ⌘C copie le message sélectionné
- [ ] Feedback visuel "Copié !" temporaire
- [ ] Bouton régénérer sur le dernier message assistant
- [ ] Menu contextuel clic droit
- [ ] Sélection de texte fonctionne normalement

## Notes techniques

### Hook clipboard

```typescript
// hooks/useClipboard.ts
import { writeText } from '@tauri-apps/plugin-clipboard-manager';
import { useState, useCallback } from 'react';

export function useClipboard() {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(async (text: string) => {
    try {
      await writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      return true;
    } catch (error) {
      console.error('Failed to copy:', error);
      return false;
    }
  }, []);

  return { copy, copied };
}
```

### Composant MessageActions

```tsx
// components/chat/MessageActions.tsx
import { Copy, RefreshCw, MoreHorizontal } from 'lucide-react';
import { useClipboard } from '../../hooks/useClipboard';

interface MessageActionsProps {
  content: string;
  isLast: boolean;
  onRegenerate?: () => void;
}

export function MessageActions({ content, isLast, onRegenerate }: MessageActionsProps) {
  const { copy, copied } = useClipboard();

  return (
    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
      <button
        onClick={() => copy(content)}
        className="p-1.5 rounded hover:bg-surface-elevated text-text-muted hover:text-text"
        title="Copier"
      >
        {copied ? (
          <span className="text-xs text-success">Copié !</span>
        ) : (
          <Copy size={14} />
        )}
      </button>

      {isLast && onRegenerate && (
        <button
          onClick={onRegenerate}
          className="p-1.5 rounded hover:bg-surface-elevated text-text-muted hover:text-text"
          title="Régénérer"
        >
          <RefreshCw size={14} />
        </button>
      )}

      <ContextMenu content={content} />
    </div>
  );
}
```

### Menu contextuel

```tsx
// components/chat/ContextMenu.tsx
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';

export function ContextMenu({ content }: { content: string }) {
  const { copy } = useClipboard();

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button className="p-1.5 rounded hover:bg-surface-elevated text-text-muted hover:text-text">
          <MoreHorizontal size={14} />
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          className="bg-surface-elevated border border-border rounded-lg p-1 shadow-lg min-w-[160px]"
          sideOffset={5}
        >
          <DropdownMenu.Item
            onClick={() => copy(content)}
            className="px-3 py-2 text-sm text-text hover:bg-surface rounded cursor-pointer outline-none"
          >
            Copier le message
          </DropdownMenu.Item>
          <DropdownMenu.Item
            onClick={() => copy(`\`\`\`\n${content}\n\`\`\``)}
            className="px-3 py-2 text-sm text-text hover:bg-surface rounded cursor-pointer outline-none"
          >
            Copier comme code
          </DropdownMenu.Item>
          <DropdownMenu.Separator className="h-px bg-border my-1" />
          <DropdownMenu.Item
            className="px-3 py-2 text-sm text-text-muted hover:bg-surface rounded cursor-pointer outline-none"
          >
            Partager...
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
```

### Mise à jour MessageItem

```tsx
// components/chat/MessageItem.tsx
export function MessageItem({ message, isLast }: MessageItemProps) {
  const { regenerate } = useChatStore();
  const isAssistant = message.role === 'assistant';

  return (
    <div className="group relative flex gap-3 p-4 rounded-lg">
      {/* ... content ... */}

      {isAssistant && (
        <div className="absolute top-2 right-2">
          <MessageActions
            content={message.content}
            isLast={isLast}
            onRegenerate={isLast ? () => regenerate(message.id) : undefined}
          />
        </div>
      )}
    </div>
  );
}
```

### Raccourci clavier global

```tsx
// hooks/useKeyboardShortcuts.ts
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    // ⌘C avec message sélectionné
    if ((e.metaKey || e.ctrlKey) && e.key === 'c') {
      const selection = window.getSelection()?.toString();
      if (!selection && lastAssistantMessage) {
        e.preventDefault();
        copy(lastAssistantMessage.content);
      }
    }
  };

  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [lastAssistantMessage]);
```

## Estimation

- **Complexité** : XS
- **Points** : 2

## Definition of Done

- [ ] Copier fonctionne (bouton + ⌘C)
- [ ] Feedback "Copié !" visible
- [ ] Régénérer relance la requête
- [ ] Menu contextuel opérationnel
- [ ] Pas de conflit avec sélection native

---

*Sprint : 2*
*Assigné : Agent Dev Frontend*
