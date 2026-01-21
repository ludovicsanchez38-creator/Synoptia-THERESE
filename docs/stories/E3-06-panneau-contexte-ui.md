# Story E3-06 : Créer le panneau "Contexte actif" (UI)

## Description

En tant que **utilisateur**,
Je veux **voir le contexte mémoire actif**,
Afin de **comprendre ce que THÉRÈSE sait de moi**.

## Contexte technique

- **Composants impactés** : Frontend React
- **Dépendances** : E3-04, E5-01
- **Fichiers concernés** :
  - `src/frontend/src/components/memory/ContextPanel.tsx` (nouveau)
  - `src/frontend/src/stores/memoryStore.ts` (nouveau)

## Critères d'acceptation

- [ ] Panneau latéral droit toggleable (⌘⇧M)
- [ ] Affiche : projet actif, contacts récents, préférences
- [ ] Items cliquables pour voir le détail
- [ ] Badge indiquant le nombre d'éléments en contexte
- [ ] Animation d'apparition fluide
- [ ] Responsive (se replie en modal sur petit écran)

## Notes techniques

### Store Memory

```typescript
// stores/memoryStore.ts
import { create } from 'zustand';

interface ContextItem {
  id: string;
  type: 'project' | 'contact' | 'preference' | 'memory';
  title: string;
  subtitle?: string;
  content: string;
}

interface MemoryStore {
  isPanelOpen: boolean;
  contextItems: ContextItem[];
  activeProject: ContextItem | null;
  recentContacts: ContextItem[];
  preferences: ContextItem[];

  togglePanel: () => void;
  setContextItems: (items: ContextItem[]) => void;
  fetchContext: () => Promise<void>;
}

export const useMemoryStore = create<MemoryStore>((set, get) => ({
  isPanelOpen: false,
  contextItems: [],
  activeProject: null,
  recentContacts: [],
  preferences: [],

  togglePanel: () => set((state) => ({ isPanelOpen: !state.isPanelOpen })),

  setContextItems: (items) => set({ contextItems: items }),

  fetchContext: async () => {
    const response = await api.get('/memory/context');
    set({
      activeProject: response.active_project,
      recentContacts: response.recent_contacts,
      preferences: response.preferences,
    });
  },
}));
```

### Composant ContextPanel

```tsx
// components/memory/ContextPanel.tsx
import { motion, AnimatePresence } from 'framer-motion';
import { X, Briefcase, User, Settings, Brain } from 'lucide-react';
import { useMemoryStore } from '../../stores/memoryStore';

export function ContextPanel() {
  const { isPanelOpen, togglePanel, activeProject, recentContacts, preferences } = useMemoryStore();

  return (
    <AnimatePresence>
      {isPanelOpen && (
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="w-80 bg-surface border-l border-border flex flex-col h-full"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border">
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-accent-cyan" />
              <h2 className="font-semibold text-text">Contexte actif</h2>
            </div>
            <button
              onClick={togglePanel}
              className="p-1 rounded hover:bg-surface-elevated text-text-muted"
            >
              <X size={18} />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            {/* Projet actif */}
            {activeProject && (
              <ContextSection
                icon={<Briefcase className="w-4 h-4" />}
                title="Projet actif"
              >
                <ContextCard
                  title={activeProject.title}
                  subtitle={activeProject.subtitle}
                  onClick={() => {/* Ouvrir détail */}}
                />
              </ContextSection>
            )}

            {/* Contacts récents */}
            {recentContacts.length > 0 && (
              <ContextSection
                icon={<User className="w-4 h-4" />}
                title="Contacts récents"
              >
                {recentContacts.map((contact) => (
                  <ContextCard
                    key={contact.id}
                    title={contact.title}
                    subtitle={contact.subtitle}
                    onClick={() => {/* Ouvrir détail */}}
                  />
                ))}
              </ContextSection>
            )}

            {/* Préférences */}
            {preferences.length > 0 && (
              <ContextSection
                icon={<Settings className="w-4 h-4" />}
                title="Préférences"
              >
                {preferences.map((pref) => (
                  <div key={pref.id} className="text-sm text-text-muted">
                    <span className="text-text">{pref.title}:</span> {pref.content}
                  </div>
                ))}
              </ContextSection>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-border">
            <button className="w-full text-sm text-accent-cyan hover:underline">
              Voir toute la mémoire →
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function ContextSection({
  icon,
  title,
  children
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-2 text-text-muted">
        {icon}
        <span className="text-xs font-medium uppercase tracking-wider">{title}</span>
      </div>
      <div className="space-y-2">
        {children}
      </div>
    </div>
  );
}

function ContextCard({
  title,
  subtitle,
  onClick
}: {
  title: string;
  subtitle?: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-3 rounded-lg bg-surface-elevated hover:bg-surface-elevated/80 transition-colors"
    >
      <div className="font-medium text-text text-sm">{title}</div>
      {subtitle && (
        <div className="text-xs text-text-muted mt-0.5">{subtitle}</div>
      )}
    </button>
  );
}
```

### Badge dans le header

```tsx
// components/layout/Header.tsx
function MemoryBadge() {
  const { contextItems, togglePanel } = useMemoryStore();
  const count = contextItems.length;

  return (
    <button
      onClick={togglePanel}
      className="relative p-2 rounded-lg hover:bg-surface-elevated"
      title="Contexte mémoire (⌘⇧M)"
    >
      <Brain className="w-5 h-5 text-text-muted" />
      {count > 0 && (
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-accent-cyan text-bg text-xs font-bold rounded-full flex items-center justify-center">
          {count}
        </span>
      )}
    </button>
  );
}
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Maquette

```
┌─────────────────────────────────────────┬──────────────────────────┐
│                                         │ 🧠 Contexte actif    [X] │
│          Zone de chat                   ├──────────────────────────┤
│                                         │ 📁 PROJET ACTIF          │
│                                         │ ┌────────────────────┐   │
│                                         │ │ THÉRÈSE v2         │   │
│                                         │ │ MVP en cours       │   │
│                                         │ └────────────────────┘   │
│                                         │                          │
│                                         │ 👤 CONTACTS RÉCENTS      │
│                                         │ ┌────────────────────┐   │
│                                         │ │ Pierre H.          │   │
│                                         │ │ DAF                 │   │
│                                         │ └────────────────────┘   │
│                                         │ ┌────────────────────┐   │
│                                         │ │ Célia G.           │   │
│                                         │ │ Consultant         │   │
│                                         │ └────────────────────┘   │
│                                         │                          │
│                                         │ ⚙️ PRÉFÉRENCES           │
│                                         │ • Ton: direct            │
│                                         │ • Langue: français       │
│                                         │                          │
│                                         │ [Voir toute la mémoire →]│
└─────────────────────────────────────────┴──────────────────────────┘
```

## Definition of Done

- [ ] Panneau s'ouvre/ferme avec animation
- [ ] ⌘⇧M toggle le panneau
- [ ] Données chargées depuis l'API
- [ ] Items cliquables
- [ ] Badge visible dans le header

---

*Sprint : 3*
*Assigné : Agent Dev Frontend*
