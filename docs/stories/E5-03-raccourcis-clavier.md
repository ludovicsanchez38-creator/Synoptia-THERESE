# Story E5-03 : Ajouter les raccourcis clavier globaux

## Description

En tant que **utilisateur**,
Je veux **utiliser des raccourcis clavier pour toutes les actions courantes**,
Afin de **être plus productif sans utiliser la souris**.

## Contexte technique

- **Composants impactés** : Frontend React
- **Dépendances** : E1-01, E5-02
- **Fichiers concernés** :
  - `src/frontend/src/hooks/useKeyboardShortcuts.ts` (nouveau)
  - `src/frontend/src/components/ShortcutsHelp.tsx` (nouveau)

## Critères d'acceptation

- [ ] Raccourcis navigation (⌘1-5 pour onglets)
- [ ] Raccourcis actions (⌘N, ⌘⇧F, ⌘K)
- [ ] Raccourcis chat (⌘Enter pour envoyer)
- [ ] Panel aide raccourcis (⌘/)
- [ ] Raccourcis désactivés dans les inputs (sauf Escape)
- [ ] Support macOS (⌘) et Windows/Linux (Ctrl)

## Notes techniques

### Hook de raccourcis

```typescript
// hooks/useKeyboardShortcuts.ts
import { useEffect, useCallback } from 'react';

type Modifier = 'meta' | 'ctrl' | 'alt' | 'shift';
type Key = string;

interface Shortcut {
  key: Key;
  modifiers?: Modifier[];
  action: () => void;
  description: string;
  category: string;
  allowInInput?: boolean;
}

const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;

export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      // Ignorer si dans un input (sauf exceptions)
      const target = e.target as HTMLElement;
      const isInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName);
      const isEditable = target.isContentEditable;

      for (const shortcut of shortcuts) {
        // Vérifier la touche
        if (e.key.toLowerCase() !== shortcut.key.toLowerCase()) continue;

        // Vérifier les modificateurs
        const mods = shortcut.modifiers || [];
        const wantsMeta = mods.includes('meta');
        const wantsCtrl = mods.includes('ctrl');
        const wantsAlt = mods.includes('alt');
        const wantsShift = mods.includes('shift');

        // ⌘ sur Mac = Ctrl sur Windows/Linux
        const hasMainMod = isMac ? e.metaKey : e.ctrlKey;
        const wantsMainMod = isMac ? wantsMeta : wantsCtrl;

        if (wantsMainMod !== hasMainMod) continue;
        if (wantsAlt !== e.altKey) continue;
        if (wantsShift !== e.shiftKey) continue;

        // Vérifier si autorisé dans les inputs
        if ((isInput || isEditable) && !shortcut.allowInInput) {
          // Toujours autoriser Escape
          if (e.key !== 'Escape') continue;
        }

        e.preventDefault();
        shortcut.action();
        return;
      }
    },
    [shortcuts]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}

// Format pour l'affichage
export function formatShortcut(modifiers: Modifier[], key: string): string {
  const symbols = {
    meta: isMac ? '⌘' : 'Ctrl',
    ctrl: 'Ctrl',
    alt: isMac ? '⌥' : 'Alt',
    shift: '⇧',
  };

  const parts = modifiers.map((m) => symbols[m]);
  parts.push(key.toUpperCase());
  return parts.join(isMac ? '' : '+');
}
```

### Définition des raccourcis globaux

```typescript
// config/shortcuts.ts
import { useNavigate } from 'react-router-dom';
import { useCommandStore } from '../stores/commandStore';
import { useChatStore } from '../stores/chatStore';
import { useFileStore } from '../stores/fileStore';

export function useGlobalShortcuts() {
  const navigate = useNavigate();
  const toggleCommandPalette = useCommandStore((s) => s.toggle);
  const createNewChat = useChatStore((s) => s.createNew);
  const toggleFilePanel = useFileStore((s) => s.togglePanel);

  const [showShortcutsHelp, setShowShortcutsHelp] = useState(false);

  const shortcuts: Shortcut[] = [
    // Command Palette
    {
      key: 'k',
      modifiers: ['meta'],
      action: toggleCommandPalette,
      description: 'Ouvrir la command palette',
      category: 'Général',
    },

    // Navigation
    {
      key: '1',
      modifiers: ['meta'],
      action: () => navigate('/chat'),
      description: 'Aller au Chat',
      category: 'Navigation',
    },
    {
      key: '2',
      modifiers: ['meta'],
      action: () => navigate('/memory'),
      description: 'Aller à la Mémoire',
      category: 'Navigation',
    },
    {
      key: '3',
      modifiers: ['meta'],
      action: () => navigate('/files'),
      description: 'Aller aux Fichiers',
      category: 'Navigation',
    },
    {
      key: '4',
      modifiers: ['meta'],
      action: () => navigate('/history'),
      description: 'Aller à l\'Historique',
      category: 'Navigation',
    },
    {
      key: ',',
      modifiers: ['meta'],
      action: () => navigate('/settings'),
      description: 'Paramètres',
      category: 'Navigation',
    },

    // Actions Chat
    {
      key: 'n',
      modifiers: ['meta'],
      action: createNewChat,
      description: 'Nouvelle conversation',
      category: 'Chat',
    },
    {
      key: 'Enter',
      modifiers: ['meta'],
      action: () => document.querySelector<HTMLButtonElement>('[data-send-button]')?.click(),
      description: 'Envoyer le message',
      category: 'Chat',
      allowInInput: true,
    },

    // Actions Fichiers
    {
      key: 'f',
      modifiers: ['meta', 'shift'],
      action: toggleFilePanel,
      description: 'Ouvrir le navigateur de fichiers',
      category: 'Fichiers',
    },
    {
      key: 'o',
      modifiers: ['meta'],
      action: () => {
        // Ouvrir dialogue fichier natif
        window.__TAURI__.dialog.open({
          multiple: true,
          filters: [{ name: 'Documents', extensions: ['pdf', 'docx', 'txt', 'md'] }],
        });
      },
      description: 'Ouvrir un fichier',
      category: 'Fichiers',
    },

    // Aide
    {
      key: '/',
      modifiers: ['meta'],
      action: () => setShowShortcutsHelp(true),
      description: 'Aide raccourcis clavier',
      category: 'Général',
    },
    {
      key: 'Escape',
      modifiers: [],
      action: () => {
        // Fermer tous les overlays
        useCommandStore.getState().close();
        setShowShortcutsHelp(false);
      },
      description: 'Fermer',
      category: 'Général',
      allowInInput: true,
    },
  ];

  useKeyboardShortcuts(shortcuts);

  return { shortcuts, showShortcutsHelp, setShowShortcutsHelp };
}
```

### Panel aide raccourcis

```tsx
// components/ShortcutsHelp.tsx
import { motion, AnimatePresence } from 'framer-motion';
import { X, Keyboard } from 'lucide-react';
import { formatShortcut } from '../hooks/useKeyboardShortcuts';

interface ShortcutsHelpProps {
  isOpen: boolean;
  onClose: () => void;
  shortcuts: Shortcut[];
}

export function ShortcutsHelp({ isOpen, onClose, shortcuts }: ShortcutsHelpProps) {
  // Grouper par catégorie
  const grouped = shortcuts.reduce((acc, shortcut) => {
    if (!acc[shortcut.category]) {
      acc[shortcut.category] = [];
    }
    acc[shortcut.category].push(shortcut);
    return acc;
  }, {} as Record<string, Shortcut[]>);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-bg/80 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl z-50"
          >
            <div className="bg-surface border border-border rounded-xl shadow-2xl overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                <div className="flex items-center gap-3">
                  <Keyboard className="w-5 h-5 text-accent-cyan" />
                  <h2 className="text-lg font-semibold text-text">Raccourcis clavier</h2>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-surface-elevated rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-text-muted" />
                </button>
              </div>

              {/* Content */}
              <div className="p-6 max-h-[60vh] overflow-y-auto">
                <div className="grid grid-cols-2 gap-8">
                  {Object.entries(grouped).map(([category, items]) => (
                    <div key={category}>
                      <h3 className="text-sm font-medium text-text-muted uppercase tracking-wider mb-3">
                        {category}
                      </h3>
                      <div className="space-y-2">
                        {items.map((shortcut) => (
                          <div
                            key={shortcut.key + shortcut.modifiers?.join('')}
                            className="flex items-center justify-between py-1.5"
                          >
                            <span className="text-sm text-text">{shortcut.description}</span>
                            <kbd className="px-2 py-1 bg-surface-elevated rounded text-xs text-text-muted font-mono">
                              {formatShortcut(shortcut.modifiers || [], shortcut.key)}
                            </kbd>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Footer */}
              <div className="px-6 py-3 border-t border-border bg-surface-elevated/50">
                <p className="text-xs text-text-muted text-center">
                  Appuie sur <kbd className="px-1.5 py-0.5 bg-surface rounded">Escape</kbd> pour fermer
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

### Intégration

```tsx
// App.tsx
import { useGlobalShortcuts } from './config/shortcuts';
import { ShortcutsHelp } from './components/ShortcutsHelp';

function App() {
  const { shortcuts, showShortcutsHelp, setShowShortcutsHelp } = useGlobalShortcuts();

  return (
    <>
      <ShortcutsHelp
        isOpen={showShortcutsHelp}
        onClose={() => setShowShortcutsHelp(false)}
        shortcuts={shortcuts}
      />
      {/* ... reste de l'app */}
    </>
  );
}
```

## Estimation

- **Complexité** : S
- **Points** : 3

## Liste des raccourcis

| Raccourci | Action | Catégorie |
|-----------|--------|-----------|
| ⌘K | Command palette | Général |
| ⌘/ | Aide raccourcis | Général |
| Escape | Fermer overlay | Général |
| ⌘1 | Aller au Chat | Navigation |
| ⌘2 | Aller à la Mémoire | Navigation |
| ⌘3 | Aller aux Fichiers | Navigation |
| ⌘4 | Aller à l'Historique | Navigation |
| ⌘, | Paramètres | Navigation |
| ⌘N | Nouvelle conversation | Chat |
| ⌘Enter | Envoyer message | Chat |
| ⌘⇧F | Navigateur fichiers | Fichiers |
| ⌘O | Ouvrir fichier | Fichiers |

## Definition of Done

- [ ] Tous les raccourcis fonctionnent
- [ ] Support macOS + Windows/Linux
- [ ] Panel aide accessible
- [ ] Raccourcis désactivés dans inputs
- [ ] Tests unitaires

---

*Sprint : 2*
*Assigné : Agent Dev Frontend*
