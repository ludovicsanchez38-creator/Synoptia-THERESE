# Règles Frontend - THÉRÈSE V2

> Document de référence pour toutes les conventions, patterns et règles du frontend THÉRÈSE V2.
> Toute contribution doit respecter ces règles. En cas de doute, ce fichier fait autorité.

---

## Stack technique

| Technologie | Version | Rôle |
|-------------|---------|------|
| React | 19.0.0 | UI déclarative |
| TypeScript | 5.4 | Typage statique |
| Tauri | 2.0 | Shell desktop (Rust + WebView) |
| TailwindCSS | 4.0 | Styling utility-first |
| Framer Motion | 11 | Animations spring |
| Zustand | 5.0 | State management avec persistence |
| Vite | 5.4 | Bundler / dev server |
| lucide-react | - | Bibliothèque d'icônes |
| Vitest | - | Framework de tests |
| React Testing Library | - | Tests de composants |

---

## Architecture des fichiers

```
src/frontend/src/
├── App.tsx              # Composant racine (routing, onboarding, panels)
├── main.tsx             # Point d'entrée React
├── components/          # 40+ composants React
│   ├── chat/            # ChatLayout, MessageBubble, ChatInput, etc.
│   ├── sidebar/         # ConversationSidebar
│   ├── memory/          # MemoryPanel, ContactModal, ProjectModal
│   ├── settings/        # SettingsModal (6 onglets)
│   ├── board/           # BoardPanel (5 conseillers)
│   ├── guided/          # GuidedPrompts (3 actions x 24 options)
│   ├── onboarding/      # OnboardingWizard (6 étapes)
│   ├── panels/          # PanelWindow (Email, Calendar, Tasks, etc.)
│   └── ui/              # SideToggle, Notifications
├── stores/              # 6 stores Zustand
│   ├── chatStore.ts     # Conversations, messages, streaming
│   ├── statusStore.ts   # Connexion, activité
│   ├── emailStore.ts    # Comptes, messages email
│   ├── calendarStore.ts # Calendriers, événements
│   ├── taskStore.ts     # Tâches, filtres, vue kanban
│   ├── personalisationStore.ts  # Raccourcis, templates, comportement
│   └── accessibilityStore.ts    # Accessibilité
├── hooks/               # 13 hooks personnalisés
│   ├── useHealthCheck.ts       # Monitoring backend (30s)
│   ├── useKeyboardShortcuts.ts # Raccourcis globaux (14+)
│   ├── useVoiceRecorder.ts     # Enregistrement audio
│   ├── useConversationSync.ts  # Sync conversations backend
│   ├── useFileDrop.ts          # Drag & drop fichiers
│   └── useDemoMask.ts          # Masquage données sensibles
├── services/            # Couche API
│   ├── api/             # 14 modules API (core, chat, memory, etc.)
│   └── windowManager.ts # Gestion fenêtres Tauri
└── lib/                 # Utilitaires
    ├── utils.ts         # cn(), formatRelativeDate(), generateId()
    └── animations.ts    # Variants Framer Motion (30+)
```

### Règles d'organisation

- Chaque dossier dans `components/` correspond à un domaine fonctionnel.
- Un composant par fichier, nommé identiquement au composant qu'il exporte.
- Les fichiers utilitaires partagés vont dans `lib/`.
- Les hooks personnalisés vont dans `hooks/`, jamais dans les dossiers de composants.
- Les stores Zustand vont dans `stores/`, un fichier par domaine.
- Les modules API vont dans `services/api/`, un fichier par domaine.

---

## Conventions de composants

### Règles strictes

- **Composants fonctionnels uniquement** : pas de classes React, jamais.
- **Props typées avec interfaces TypeScript** : chaque composant déclare une interface pour ses props.
- **Un composant par fichier** : pas d'exception.
- **Nommage PascalCase** pour les composants (`ChatLayout`, `MessageBubble`).
- **Nommage camelCase** pour les hooks (`useHealthCheck`, `useFileDrop`).
- **Export par défaut** pour les composants principaux de chaque fichier.
- **Pas de prop drilling** : si une donnée traverse plus de 2 niveaux, utiliser Zustand.

### Structure type d'un composant

```tsx
import { useState } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { useChatStore } from '@/stores/chatStore';

interface MonComposantProps {
  titre: string;
  actif?: boolean;
  onAction: () => void;
}

export default function MonComposant({ titre, actif = false, onAction }: MonComposantProps) {
  const messages = useChatStore((state) => state.messages);

  return (
    <motion.div
      className={cn('p-4 rounded-lg', actif && 'bg-[#131B35]')}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <h2 className="text-[#E6EDF7] font-semibold">{titre}</h2>
    </motion.div>
  );
}
```

### Taille maximale

- Un composant ne doit **jamais dépasser 300 lignes**.
- Au-delà, découper en sous-composants ou extraire la logique dans un hook.

---

## State Management (Zustand)

### Principes fondamentaux

- **Un store par domaine fonctionnel** : chat, status, email, calendar, tasks, personnalisation, accessibilité.
- **Actions définies dans le store** : pas de reducers séparés, pas de dispatch.
- **Persistence localStorage** via le middleware `persist` de Zustand.
- **Partialize** pour exclure l'état éphémère (données de streaming, états de chargement temporaires).
- **Sélecteurs granulaires** : toujours sélectionner le minimum nécessaire pour éviter les re-renders inutiles.

### Bonnes pratiques

```tsx
// BON : sélecteur granulaire
const messages = useChatStore((state) => state.messages);
const envoyer = useChatStore((state) => state.envoyerMessage);

// MAUVAIS : sélection de tout le store
const store = useChatStore();
```

### Règles de state

- **Pas de state global dans les composants** : tout state partagé passe par Zustand.
- **State local autorisé** uniquement pour l'état UI éphémère (hover, focus, input en cours de saisie).
- **Pas de useEffect pour synchroniser du state** : si deux states doivent être synchronisés, les fusionner dans le store ou utiliser un sélecteur dérivé.

---

## Styling (TailwindCSS)

### Approche

- **Utility-first** : pas de CSS custom sauf exceptions documentées.
- **Pas de styles inline** : utiliser les classes Tailwind systématiquement.
- **Dark mode par défaut** : THÉRÈSE est une app desktop sombre, pas de theme toggle.
- **Desktop-first** : pas de breakpoints mobile, l'app tourne exclusivement sur desktop via Tauri.

### Palette Synoptia

| Token | Hex | Usage |
|-------|-----|-------|
| `background` | `#0B1226` | Fond principal (navy profond) |
| `surface` | `#131B35` | Cartes, panneaux, surfaces élevées |
| `text` | `#E6EDF7` | Texte primaire |
| `muted` | `#A9B8D8` | Texte secondaire, labels |
| `primary` | `#2451FF` | Actions principales, boutons primaires |
| `accent_cyan` | `#22D3EE` | Interactions, hover, focus |
| `accent_magenta` | `#E11D8D` | Highlights, notifications, alertes |

### Helper `cn()`

Utiliser `cn()` (basé sur `clsx` + `tailwind-merge`) pour fusionner les classes conditionnelles :

```tsx
import { cn } from '@/lib/utils';

<div className={cn(
  'p-4 rounded-lg bg-[#131B35]',
  actif && 'ring-2 ring-[#2451FF]',
  desactive && 'opacity-50 pointer-events-none'
)} />
```

### Règles Tailwind

- Toujours utiliser les couleurs de la palette (pas de couleurs arbitraires hors palette).
- Arrondi par défaut : `rounded-lg` (8px).
- Espacements cohérents : multiples de 4 (`p-2`, `p-4`, `gap-3`, `gap-6`).
- Transitions CSS via Tailwind (`transition-colors`, `duration-200`) pour les micro-interactions simples.
- Framer Motion pour les animations plus complexes (entrées, sorties, layouts).

---

## Animations (Framer Motion)

### Principes

- **Transitions spring par défaut** : `type: "spring"`, `stiffness: 300`, `damping: 30`.
- **Variants pré-définis** dans `lib/animations.ts` : toujours réutiliser les variants existants avant d'en créer de nouveaux.
- **Respect de prefers-reduced-motion** : utiliser le hook `useReducedMotion` de Framer Motion et désactiver les animations si l'utilisateur le demande.
- **Stagger pour les listes** : 50ms entre chaque élément.
- **AnimatePresence** obligatoire pour les entrées/sorties conditionnelles.
- **Durée maximale** : aucune animation ne doit dépasser 300ms. L'interface doit rester réactive.

### Exemple type

```tsx
import { motion, AnimatePresence } from 'framer-motion';
import { fadeInUp, staggerContainer } from '@/lib/animations';

<AnimatePresence mode="wait">
  {visible && (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      animate="visible"
      exit="hidden"
    >
      {contenu}
    </motion.div>
  )}
</AnimatePresence>
```

### Catalogue de variants (`lib/animations.ts`)

Le fichier contient 30+ variants pré-définis. Consulter ce fichier avant de créer un nouveau variant. Si un pattern d'animation revient plus de 2 fois, l'ajouter au catalogue.

---

## API Client

### Architecture

- **14 modules** dans `services/api/`, un par domaine fonctionnel (core, chat, memory, email, calendar, tasks, etc.).
- **`apiFetch()` centralisé** : toutes les requêtes HTTP passent par cette fonction qui gère les erreurs, les headers, le token d'auth et le base URL.
- **SSE streaming** pour le chat : les réponses de l'IA arrivent en Server-Sent Events, gérées par un module dédié.
- **Token d'auth** initialisé au démarrage de l'application.
- **Types TypeScript** pour toutes les requêtes et réponses : jamais de `any`.

### Règles

- **Jamais de `fetch()` direct** dans les composants ou les stores. Toujours passer par les modules `services/api/`.
- Chaque module API expose des fonctions typées (ex: `getConversations(): Promise<Conversation[]>`).
- Les erreurs API sont interceptées par `apiFetch()` et remontées de manière uniforme.
- Les appels API depuis les composants passent par les actions des stores Zustand (le composant ne connaît pas l'API directement).

---

## Fenêtres Tauri (Panels)

### Types de panels

| Panel | Raccourci | Description |
|-------|-----------|-------------|
| `email` | Cmd+E | Client email intégré |
| `calendar` | (via menu) | Calendrier |
| `tasks` | Cmd+T | Gestionnaire de tâches (kanban) |
| `invoices` | Cmd+I | Facturation |
| `crm` | Cmd+P | CRM intégré |

### Règles

- **Ouverture via `windowManager.openPanelWindow()`** : ne jamais créer de fenêtre manuellement.
- **Pattern singleton** : une seule instance de chaque type de panel à la fois. Si le panel existe déjà, le focus passe dessus.
- **Détection du contexte** : un composant dans un panel détecte son contexte via les URL params (`?panel=xxx`).
- **Nettoyage automatique** : les ressources sont libérées via l'événement `tauri://destroyed`.
- **Communication inter-fenêtres** : via les événements Tauri (`emit`/`listen`), pas de state partagé direct.

---

## Raccourcis clavier

### Liste complète

| Raccourci | Action |
|-----------|--------|
| `Cmd+K` | Palette de commandes |
| `Cmd+M` | Panel mémoire |
| `Cmd+B` | Sidebar conversations |
| `Cmd+N` | Nouvelle conversation |
| `Cmd+D` | Board de décision |
| `Cmd+E` | Email |
| `Cmd+T` | Tâches |
| `Cmd+I` | Factures |
| `Cmd+P` | CRM |
| `Cmd+,` | Paramètres |
| `Cmd+/` | Aide raccourcis |
| `Échap` | Fermer modale / panel actif |

### Règles

- Tous les raccourcis sont gérés dans `hooks/useKeyboardShortcuts.ts`.
- Les raccourcis sont désactivés quand un champ de saisie a le focus (sauf Échap).
- Chaque raccourci est documenté dans le hook et affiché dans l'aide (`Cmd+/`).
- Ne jamais surcharger un raccourci système macOS standard.

---

## Accessibilité

### Exigences

- **WCAG 2.1 AA minimum** : c'est le standard de conformité visé.
- **Contraste 4.5:1** pour tout le texte (vérifié avec la palette Synoptia).
- **Navigation clavier complète** : chaque élément interactif est atteignable au clavier.
- **`aria-labels`** sur tous les éléments interactifs qui n'ont pas de texte visible.
- **Respect de `prefers-reduced-motion`** : les animations sont désactivées ou réduites.
- **Taille de police configurable** : trois niveaux (small, medium, large) via `accessibilityStore`.
- **Mode haut contraste optionnel** : activable dans les paramètres d'accessibilité.

### Règles de développement

- Chaque bouton sans texte doit avoir un `aria-label` descriptif.
- Les modales doivent piéger le focus (focus trap).
- Les listes dynamiques doivent annoncer les changements via `aria-live`.
- Les formulaires doivent avoir des labels associés (`htmlFor` / `id`).

---

## Tests (Vitest)

### Organisation

- Fichiers de tests : `*.test.ts` ou `*.test.tsx`, colocalisés avec les fichiers testés ou dans un dossier `__tests__/`.
- Framework : Vitest + `@testing-library/react`.
- Mocks obligatoires pour les appels API et les APIs Tauri.

### Ce qu'il faut tester

- **Composants** : rendu conditionnel, interactions utilisateur, affichage des props.
- **Stores Zustand** : mutations d'état, persistence, actions asynchrones.
- **Hooks personnalisés** : comportement, effets de bord, nettoyage.
- **Utilitaires** : fonctions pures dans `lib/`.

### Ce qu'il ne faut pas tester

- Les détails d'implémentation internes (state interne, refs).
- Les styles Tailwind (pas de snapshot de classes CSS).
- Les animations Framer Motion (trop fragiles).

### Exemple type

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import MonComposant from './MonComposant';

describe('MonComposant', () => {
  it('affiche le titre passé en prop', () => {
    render(<MonComposant titre="Test" onAction={vi.fn()} />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });

  it('appelle onAction au clic', () => {
    const onAction = vi.fn();
    render(<MonComposant titre="Test" onAction={onAction} />);
    fireEvent.click(screen.getByRole('button'));
    expect(onAction).toHaveBeenCalledOnce();
  });
});
```

---

## Anti-patterns à éviter

| Anti-pattern | Alternative correcte |
|-------------|---------------------|
| `useEffect` pour synchroniser du state | Sélecteur dérivé ou fusionner dans le store |
| State local quand Zustand convient | Déplacer dans le store approprié |
| `fetch()` direct dans un composant | Utiliser les modules `services/api/` |
| Styles inline (`style={{}}`) | Classes Tailwind |
| Composant > 300 lignes | Découper en sous-composants |
| Prop drilling sur 3+ niveaux | Zustand |
| `any` dans les types | Typer explicitement |
| Couleurs hors palette | Utiliser la palette Synoptia |
| `rm` pour supprimer un fichier | `mv fichier ~/.Trash/` |
| Tirets longs (-) | Tirets courts (-) ou parenthèses |
| Classes React | Composants fonctionnels |

---

## Commandes de développement

```bash
# Développement
npm run dev            # Dev server Vite (port 1420)
npm run tauri:dev      # Dev Tauri complet (Rust + WebView)

# Build
npm run build          # Build production frontend
npm run tauri:build    # Build .app + .dmg

# Qualité
npm run test           # Tests Vitest
npm run lint           # ESLint
```

---

## Checklist avant chaque PR

- [ ] Pas de `any` dans le code TypeScript
- [ ] Composants < 300 lignes
- [ ] Props typées avec interfaces
- [ ] Sélecteurs Zustand granulaires (pas de sélection du store entier)
- [ ] `aria-labels` sur les éléments interactifs sans texte
- [ ] Animations respectent `prefers-reduced-motion`
- [ ] Pas de `fetch()` direct (passage par `services/api/`)
- [ ] Couleurs de la palette uniquement
- [ ] Tests ajoutés ou mis à jour
- [ ] `npm run lint` passe sans erreur
- [ ] `npm run test` passe sans erreur
