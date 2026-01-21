# Story E5-02 : Créer la command palette (⌘K)

## Description

En tant que **utilisateur power-user**,
Je veux **une command palette pour accéder rapidement aux actions**,
Afin de **naviguer et agir sans quitter le clavier**.

## Contexte technique

- **Composants impactés** : Frontend React
- **Dépendances** : E1-01, E5-03
- **Fichiers concernés** :
  - `src/frontend/src/components/CommandPalette.tsx` (nouveau)
  - `src/frontend/src/stores/commandStore.ts` (nouveau)
  - `src/frontend/src/hooks/useCommands.ts` (nouveau)

## Critères d'acceptation

- [ ] Ouverture avec ⌘K (macOS) / Ctrl+K (Windows)
- [ ] Recherche fuzzy dans les commandes
- [ ] Navigation clavier (↑↓ Enter Escape)
- [ ] Catégories de commandes (Actions, Navigation, Fichiers)
- [ ] Raccourcis affichés pour chaque commande
- [ ] Historique des commandes récentes
- [ ] Animation fluide d'ouverture/fermeture

## Notes techniques

### Store des commandes

```typescript
// stores/commandStore.ts
import { create } from 'zustand';
import Fuse from 'fuse.js';

interface Command {
  id: string;
  label: string;
  description?: string;
  category: 'action' | 'navigation' | 'file' | 'settings';
  shortcut?: string;
  icon?: React.ComponentType;
  action: () => void | Promise<void>;
  keywords?: string[];
}

interface CommandStore {
  isOpen: boolean;
  query: string;
  selectedIndex: number;
  commands: Command[];
  recentCommandIds: string[];

  open: () => void;
  close: () => void;
  toggle: () => void;
  setQuery: (query: string) => void;
  setSelectedIndex: (index: number) => void;
  executeCommand: (id: string) => void;
  registerCommand: (command: Command) => void;
  unregisterCommand: (id: string) => void;
}

export const useCommandStore = create<CommandStore>((set, get) => ({
  isOpen: false,
  query: '',
  selectedIndex: 0,
  commands: [],
  recentCommandIds: JSON.parse(localStorage.getItem('recentCommands') || '[]'),

  open: () => set({ isOpen: true, query: '', selectedIndex: 0 }),
  close: () => set({ isOpen: false }),
  toggle: () => set((state) => ({
    isOpen: !state.isOpen,
    query: '',
    selectedIndex: 0
  })),

  setQuery: (query) => set({ query, selectedIndex: 0 }),
  setSelectedIndex: (selectedIndex) => set({ selectedIndex }),

  executeCommand: (id) => {
    const command = get().commands.find((c) => c.id === id);
    if (command) {
      command.action();
      // Ajouter aux récents
      const recent = [id, ...get().recentCommandIds.filter((r) => r !== id)].slice(0, 5);
      localStorage.setItem('recentCommands', JSON.stringify(recent));
      set({ recentCommandIds: recent, isOpen: false });
    }
  },

  registerCommand: (command) => {
    set((state) => ({
      commands: [...state.commands.filter((c) => c.id !== command.id), command],
    }));
  },

  unregisterCommand: (id) => {
    set((state) => ({
      commands: state.commands.filter((c) => c.id !== id),
    }));
  },
}));

// Hook pour filtrer les commandes
export function useFilteredCommands() {
  const { query, commands, recentCommandIds } = useCommandStore();

  if (!query) {
    // Sans recherche : récents + toutes par catégorie
    const recent = recentCommandIds
      .map((id) => commands.find((c) => c.id === id))
      .filter(Boolean) as Command[];
    return { recent, all: commands };
  }

  // Recherche fuzzy
  const fuse = new Fuse(commands, {
    keys: ['label', 'description', 'keywords'],
    threshold: 0.3,
  });

  const results = fuse.search(query).map((r) => r.item);
  return { recent: [], all: results };
}
```

### Composant CommandPalette

```tsx
// components/CommandPalette.tsx
import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ArrowRight } from 'lucide-react';
import { useCommandStore, useFilteredCommands } from '../stores/commandStore';

export function CommandPalette() {
  const { isOpen, query, selectedIndex, setQuery, setSelectedIndex, executeCommand, close } =
    useCommandStore();
  const { recent, all } = useFilteredCommands();
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input quand ouvert
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Raccourci clavier global
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        useCommandStore.getState().toggle();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Navigation clavier
  const handleKeyDown = (e: React.KeyboardEvent) => {
    const commands = query ? all : [...recent, ...all];

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(Math.min(selectedIndex + 1, commands.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(Math.max(selectedIndex - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (commands[selectedIndex]) {
          executeCommand(commands[selectedIndex].id);
        }
        break;
      case 'Escape':
        e.preventDefault();
        close();
        break;
    }
  };

  const displayCommands = query ? all : [...recent, ...all];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={close}
            className="fixed inset-0 bg-bg/80 backdrop-blur-sm z-50"
          />

          {/* Palette */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ duration: 0.15 }}
            className="fixed top-[20%] left-1/2 -translate-x-1/2 w-full max-w-xl z-50"
          >
            <div className="bg-surface border border-border rounded-xl shadow-2xl overflow-hidden">
              {/* Input */}
              <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
                <Search className="w-5 h-5 text-text-muted" />
                <input
                  ref={inputRef}
                  type="text"
                  placeholder="Rechercher une commande..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="flex-1 bg-transparent text-text placeholder:text-text-muted focus:outline-none"
                />
                <kbd className="px-2 py-0.5 bg-surface-elevated rounded text-xs text-text-muted">
                  esc
                </kbd>
              </div>

              {/* Résultats */}
              <div className="max-h-[400px] overflow-y-auto">
                {/* Récents (si pas de recherche) */}
                {!query && recent.length > 0 && (
                  <div className="py-2">
                    <div className="px-4 py-1 text-xs text-text-muted uppercase tracking-wider">
                      Récents
                    </div>
                    {recent.map((cmd, i) => (
                      <CommandItem
                        key={cmd.id}
                        command={cmd}
                        isSelected={selectedIndex === i}
                        onClick={() => executeCommand(cmd.id)}
                      />
                    ))}
                  </div>
                )}

                {/* Toutes les commandes */}
                {all.length > 0 && (
                  <div className="py-2">
                    {!query && (
                      <div className="px-4 py-1 text-xs text-text-muted uppercase tracking-wider">
                        Commandes
                      </div>
                    )}
                    {all.map((cmd, i) => {
                      const idx = query ? i : recent.length + i;
                      return (
                        <CommandItem
                          key={cmd.id}
                          command={cmd}
                          isSelected={selectedIndex === idx}
                          onClick={() => executeCommand(cmd.id)}
                        />
                      );
                    })}
                  </div>
                )}

                {/* Aucun résultat */}
                {query && all.length === 0 && (
                  <div className="px-4 py-8 text-center text-text-muted">
                    Aucune commande trouvée
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between px-4 py-2 border-t border-border text-xs text-text-muted">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1">
                    <kbd className="px-1.5 py-0.5 bg-surface-elevated rounded">↑↓</kbd>
                    naviguer
                  </span>
                  <span className="flex items-center gap-1">
                    <kbd className="px-1.5 py-0.5 bg-surface-elevated rounded">↵</kbd>
                    sélectionner
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function CommandItem({
  command,
  isSelected,
  onClick,
}: {
  command: Command;
  isSelected: boolean;
  onClick: () => void;
}) {
  const Icon = command.icon;

  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors',
        isSelected ? 'bg-accent-cyan/10 text-text' : 'text-text-muted hover:bg-surface-elevated'
      )}
    >
      {Icon && <Icon className="w-4 h-4" />}
      <div className="flex-1 min-w-0">
        <div className="text-sm truncate">{command.label}</div>
        {command.description && (
          <div className="text-xs text-text-muted truncate">{command.description}</div>
        )}
      </div>
      {command.shortcut && (
        <kbd className="px-2 py-0.5 bg-surface-elevated rounded text-xs text-text-muted">
          {command.shortcut}
        </kbd>
      )}
      {isSelected && <ArrowRight className="w-4 h-4 text-accent-cyan" />}
    </button>
  );
}
```

### Hook d'enregistrement

```typescript
// hooks/useCommands.ts
import { useEffect } from 'react';
import { useCommandStore } from '../stores/commandStore';
import {
  MessageSquare,
  Folder,
  Search,
  Settings,
  Moon,
  Plus,
  History,
  Brain,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function useRegisterCommands() {
  const navigate = useNavigate();
  const { registerCommand, unregisterCommand } = useCommandStore();

  useEffect(() => {
    const commands = [
      // Actions
      {
        id: 'new-chat',
        label: 'Nouvelle conversation',
        category: 'action',
        shortcut: '⌘N',
        icon: Plus,
        action: () => navigate('/chat/new'),
      },
      {
        id: 'search-memory',
        label: 'Rechercher dans la mémoire',
        category: 'action',
        shortcut: '⌘⇧F',
        icon: Search,
        action: () => useCommandStore.getState().close(),
      },

      // Navigation
      {
        id: 'nav-chat',
        label: 'Aller au Chat',
        category: 'navigation',
        icon: MessageSquare,
        action: () => navigate('/chat'),
      },
      {
        id: 'nav-files',
        label: 'Aller aux Fichiers',
        category: 'navigation',
        icon: Folder,
        action: () => navigate('/files'),
      },
      {
        id: 'nav-memory',
        label: 'Aller à la Mémoire',
        category: 'navigation',
        icon: Brain,
        action: () => navigate('/memory'),
      },
      {
        id: 'nav-history',
        label: 'Voir l\'historique',
        category: 'navigation',
        icon: History,
        action: () => navigate('/history'),
      },

      // Settings
      {
        id: 'settings',
        label: 'Paramètres',
        category: 'settings',
        shortcut: '⌘,',
        icon: Settings,
        action: () => navigate('/settings'),
      },
    ];

    commands.forEach(registerCommand);

    return () => {
      commands.forEach((c) => unregisterCommand(c.id));
    };
  }, [navigate, registerCommand, unregisterCommand]);
}
```

### Intégration dans l'app

```tsx
// App.tsx
import { CommandPalette } from './components/CommandPalette';
import { useRegisterCommands } from './hooks/useCommands';

function App() {
  useRegisterCommands();

  return (
    <>
      <CommandPalette />
      {/* ... reste de l'app */}
    </>
  );
}
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Maquette

```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Rechercher une commande...                          esc  │
├─────────────────────────────────────────────────────────────┤
│ RÉCENTS                                                     │
│ ▶ 📝 Nouvelle conversation                            ⌘N    │
│   🔍 Rechercher dans la mémoire                       ⌘⇧F   │
├─────────────────────────────────────────────────────────────┤
│ COMMANDES                                                   │
│   💬 Aller au Chat                                          │
│   📁 Aller aux Fichiers                                     │
│   🧠 Aller à la Mémoire                                     │
│   📜 Voir l'historique                                      │
│   ⚙️ Paramètres                                        ⌘,    │
├─────────────────────────────────────────────────────────────┤
│ ↑↓ naviguer    ↵ sélectionner                               │
└─────────────────────────────────────────────────────────────┘
```

## Definition of Done

- [ ] ⌘K / Ctrl+K ouvre la palette
- [ ] Recherche fuzzy fonctionne
- [ ] Navigation clavier complète
- [ ] Récents persistés
- [ ] Animation fluide
- [ ] Tests unitaires

---

*Sprint : 2*
*Assigné : Agent Dev Frontend*
