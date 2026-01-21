# Story E5-06 : Créer le panneau latéral multifonction

## Description

En tant que **utilisateur**,
Je veux **un panneau latéral pour accéder rapidement aux fonctions secondaires**,
Afin de **naviguer entre historique, mémoire et fichiers sans changer de vue**.

## Contexte technique

- **Composants impactés** : Frontend React
- **Dépendances** : E1-01, E2-04, E4-01
- **Fichiers concernés** :
  - `src/frontend/src/components/Sidebar.tsx` (nouveau)
  - `src/frontend/src/components/SidebarPanel.tsx` (nouveau)
  - `src/frontend/src/stores/sidebarStore.ts` (nouveau)

## Critères d'acceptation

- [ ] Panneau rétractable (ouvert/fermé)
- [ ] Onglets : Historique, Mémoire, Fichiers
- [ ] Animation fluide d'ouverture/fermeture
- [ ] État persisté (localStorage)
- [ ] Largeur ajustable (drag resize)
- [ ] Raccourci toggle (⌘B)

## Notes techniques

### Store sidebar

```typescript
// stores/sidebarStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type SidebarTab = 'history' | 'memory' | 'files';

interface SidebarStore {
  isOpen: boolean;
  activeTab: SidebarTab;
  width: number;
  minWidth: number;
  maxWidth: number;

  toggle: () => void;
  open: () => void;
  close: () => void;
  setTab: (tab: SidebarTab) => void;
  setWidth: (width: number) => void;
}

export const useSidebarStore = create<SidebarStore>()(
  persist(
    (set, get) => ({
      isOpen: true,
      activeTab: 'history',
      width: 320,
      minWidth: 280,
      maxWidth: 500,

      toggle: () => set((state) => ({ isOpen: !state.isOpen })),
      open: () => set({ isOpen: true }),
      close: () => set({ isOpen: false }),
      setTab: (activeTab) => set({ activeTab, isOpen: true }),
      setWidth: (width) => {
        const { minWidth, maxWidth } = get();
        set({ width: Math.min(Math.max(width, minWidth), maxWidth) });
      },
    }),
    {
      name: 'sidebar-state',
      partialize: (state) => ({
        isOpen: state.isOpen,
        activeTab: state.activeTab,
        width: state.width,
      }),
    }
  )
);
```

### Composant Sidebar

```tsx
// components/Sidebar.tsx
import { motion, AnimatePresence } from 'framer-motion';
import { History, Brain, Folder, ChevronLeft, ChevronRight } from 'lucide-react';
import { useSidebarStore } from '../stores/sidebarStore';
import { SidebarPanel } from './SidebarPanel';
import { useRef, useCallback } from 'react';

const tabs = [
  { id: 'history', label: 'Historique', icon: History },
  { id: 'memory', label: 'Mémoire', icon: Brain },
  { id: 'files', label: 'Fichiers', icon: Folder },
] as const;

export function Sidebar() {
  const { isOpen, activeTab, width, toggle, setTab, setWidth } = useSidebarStore();
  const resizeRef = useRef<HTMLDivElement>(null);
  const isResizing = useRef(false);

  // Gestion du resize
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    isResizing.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing.current) return;
      const newWidth = window.innerWidth - e.clientX;
      setWidth(newWidth);
    };

    const handleMouseUp = () => {
      isResizing.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [setWidth]);

  // Raccourci clavier
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
        e.preventDefault();
        toggle();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggle]);

  return (
    <div className="flex h-full">
      {/* Resize handle */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            ref={resizeRef}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onMouseDown={handleMouseDown}
            className="w-1 bg-transparent hover:bg-accent-cyan/50 cursor-col-resize transition-colors"
          />
        )}
      </AnimatePresence>

      {/* Sidebar panel */}
      <motion.div
        initial={false}
        animate={{ width: isOpen ? width : 0 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
        className="h-full overflow-hidden bg-surface border-l border-border"
      >
        <div style={{ width }} className="h-full flex flex-col">
          {/* Tabs */}
          <div className="flex items-center border-b border-border">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  onClick={() => setTab(tab.id)}
                  className={cn(
                    'flex-1 flex items-center justify-center gap-2 py-3 text-sm transition-colors',
                    isActive
                      ? 'text-accent-cyan border-b-2 border-accent-cyan'
                      : 'text-text-muted hover:text-text'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden md:inline">{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-hidden">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.15 }}
                className="h-full"
              >
                <SidebarPanel tab={activeTab} />
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </motion.div>

      {/* Toggle button */}
      <motion.button
        onClick={toggle}
        className="absolute right-0 top-1/2 -translate-y-1/2 z-10 p-1.5 bg-surface border border-border rounded-l-lg hover:bg-surface-elevated transition-colors"
        style={{ right: isOpen ? width : 0 }}
        animate={{ right: isOpen ? width : 0 }}
        transition={{ duration: 0.2 }}
      >
        {isOpen ? (
          <ChevronRight className="w-4 h-4 text-text-muted" />
        ) : (
          <ChevronLeft className="w-4 h-4 text-text-muted" />
        )}
      </motion.button>
    </div>
  );
}
```

### Panneau de contenu

```tsx
// components/SidebarPanel.tsx
import { HistoryPanel } from './panels/HistoryPanel';
import { MemoryPanel } from './panels/MemoryPanel';
import { FilesPanel } from './panels/FilesPanel';

interface SidebarPanelProps {
  tab: 'history' | 'memory' | 'files';
}

export function SidebarPanel({ tab }: SidebarPanelProps) {
  switch (tab) {
    case 'history':
      return <HistoryPanel />;
    case 'memory':
      return <MemoryPanel />;
    case 'files':
      return <FilesPanel />;
  }
}
```

### Panel Historique

```tsx
// components/panels/HistoryPanel.tsx
import { Search, MessageSquare, Trash2 } from 'lucide-react';
import { useChatStore } from '../../stores/chatStore';

export function HistoryPanel() {
  const { conversations, currentId, loadConversation, deleteConversation } = useChatStore();
  const [search, setSearch] = useState('');

  const filtered = conversations.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="p-3 border-b border-border">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Rechercher..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-surface-elevated rounded-lg text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-accent-cyan"
          />
        </div>
      </div>

      {/* Conversations list */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="p-4 text-center text-text-muted text-sm">
            Aucune conversation
          </div>
        ) : (
          <div className="py-2">
            {filtered.map((conversation) => (
              <button
                key={conversation.id}
                onClick={() => loadConversation(conversation.id)}
                className={cn(
                  'w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-surface-elevated transition-colors group',
                  currentId === conversation.id && 'bg-accent-cyan/10'
                )}
              >
                <MessageSquare className="w-4 h-4 text-text-muted flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-text truncate">{conversation.title}</p>
                  <p className="text-xs text-text-muted mt-0.5">
                    {formatRelativeDate(conversation.updated_at)}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation(conversation.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-error/10 rounded transition-opacity"
                >
                  <Trash2 className="w-3.5 h-3.5 text-error" />
                </button>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

### Panel Mémoire (compact)

```tsx
// components/panels/MemoryPanel.tsx
import { Brain, Plus, Search } from 'lucide-react';
import { useMemoryStore } from '../../stores/memoryStore';

export function MemoryPanel() {
  const { memories, searchMemories, createMemory } = useMemoryStore();
  const [search, setSearch] = useState('');

  const filtered = search ? searchMemories(search) : memories.slice(0, 20);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-border">
        <div className="flex items-center gap-2 mb-3">
          <Brain className="w-4 h-4 text-accent-cyan" />
          <span className="text-sm font-medium text-text">{memories.length} éléments</span>
          <button
            onClick={() => createMemory()}
            className="ml-auto p-1.5 hover:bg-surface-elevated rounded"
          >
            <Plus className="w-4 h-4 text-text-muted" />
          </button>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Rechercher dans la mémoire..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-surface-elevated rounded-lg text-sm"
          />
        </div>
      </div>

      {/* Memory items */}
      <div className="flex-1 overflow-y-auto py-2">
        {filtered.map((memory) => (
          <div
            key={memory.id}
            className="px-4 py-2 hover:bg-surface-elevated cursor-pointer"
          >
            <div className="flex items-center gap-2 mb-1">
              <span className={cn(
                'px-1.5 py-0.5 rounded text-xs',
                memory.type === 'fact' && 'bg-info/20 text-info',
                memory.type === 'preference' && 'bg-accent-magenta/20 text-accent-magenta',
                memory.type === 'note' && 'bg-success/20 text-success'
              )}>
                {memory.type}
              </span>
            </div>
            <p className="text-sm text-text line-clamp-2">{memory.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Panel Fichiers (compact)

```tsx
// components/panels/FilesPanel.tsx
import { Folder, File, ArrowUp, RefreshCw } from 'lucide-react';
import { useFileStore } from '../../stores/fileStore';

export function FilesPanel() {
  const { currentPath, files, isLoading, setPath, navigateUp, refresh } = useFileStore();

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-border">
        <div className="flex items-center gap-2">
          <button
            onClick={navigateUp}
            disabled={!currentPath}
            className="p-1.5 hover:bg-surface-elevated rounded disabled:opacity-50"
          >
            <ArrowUp className="w-4 h-4 text-text-muted" />
          </button>
          <span className="flex-1 text-sm text-text-muted truncate">
            {currentPath || '/'}
          </span>
          <button
            onClick={refresh}
            className="p-1.5 hover:bg-surface-elevated rounded"
          >
            <RefreshCw className={cn('w-4 h-4 text-text-muted', isLoading && 'animate-spin')} />
          </button>
        </div>
      </div>

      {/* Files list */}
      <div className="flex-1 overflow-y-auto">
        {files.map((file) => (
          <button
            key={file.path}
            onClick={() => file.isDirectory && setPath(file.path)}
            className="w-full flex items-center gap-3 px-4 py-2 hover:bg-surface-elevated text-left"
          >
            {file.isDirectory ? (
              <Folder className="w-4 h-4 text-accent-cyan" />
            ) : (
              <File className="w-4 h-4 text-text-muted" />
            )}
            <span className="flex-1 text-sm text-text truncate">{file.name}</span>
          </button>
        ))}
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
┌────────────────────────────────────────┬─────────────────────┐
│                                        │ [Hist] [Mém] [Fich] │
│                                        ├─────────────────────┤
│                                        │ 🔍 Rechercher...     │
│                                        ├─────────────────────┤
│             Chat Area                  │ 💬 Comment optimiser │
│                                        │    Il y a 2h        │
│                                        │ 💬 Analyse du PDF    │
│                                        │    Hier             │
│                                        │ 💬 Projet THÉRÈSE    │
│                                        │    Lundi            │
│                                        │ ...                 │
├────────────────────────────────────────┼─────────────────────┤
│ 💬 Message...                     [→]  │                     │
└────────────────────────────────────────┴─────────────────────┘
                                         ◀ (toggle)
```

## Definition of Done

- [ ] 3 onglets fonctionnels
- [ ] Resize par drag
- [ ] Raccourci ⌘B fonctionne
- [ ] État persisté
- [ ] Animation fluide
- [ ] Tests unitaires

---

*Sprint : 3*
*Assigné : Agent Dev Frontend*
