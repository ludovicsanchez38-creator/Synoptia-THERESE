# Epic 5 : UX/UI Premium

> L'effet "wahou" qui différencie THÉRÈSE des interfaces génériques

## Vision

Créer une expérience visuelle et interactive qui :
- Impressionne dès l'ouverture (effet premium)
- Respecte l'identité Synoptïa (dark mode, glow, glassmorphism)
- Maximise l'efficacité (keyboard-first, raccourcis)
- Guide sans infantiliser (onboarding intelligent)

**"Pro mais pas corporate, efficace pas fluff, chaleureux pas froid"**

## Stories incluses

| ID | Titre | Points | Priorité |
|----|-------|--------|----------|
| E5-01 | Implémenter le thème dark Synoptïa | 5 | P0 |
| E5-02 | Créer les composants UI de base | 5 | P0 |
| E5-03 | Ajouter les raccourcis clavier globaux | 3 | P1 |
| E5-04 | Créer l'écran d'onboarding | 5 | P1 |
| E5-05 | Ajouter les micro-animations | 3 | P2 |
| E5-06 | Implémenter le system tray + raccourci global | 3 | P1 |
| E5-07 | Créer l'écran Settings | 5 | P1 |
| E5-08 | Optimiser la responsive | 2 | P2 |

**Total : 31 points**

## Critères de succès de l'Epic

- [ ] Le thème dark est cohérent sur toute l'app
- [ ] ⌘K ouvre la command palette
- [ ] L'onboarding guide en < 2 minutes
- [ ] Les transitions sont fluides (60 fps)
- [ ] L'icône system tray fonctionne
- [ ] Les settings sont accessibles et complets

## Design System Synoptïa

### Palette de couleurs

```css
:root {
  /* Backgrounds */
  --color-bg: #0B1226;
  --color-surface: #131B35;
  --color-surface-elevated: #1A2442;

  /* Text */
  --color-text: #E6EDF7;
  --color-text-muted: #B6C7DA;
  --color-text-subtle: #6B7A94;

  /* Accents */
  --color-accent-cyan: #22D3EE;
  --color-accent-magenta: #E11D8D;
  --color-accent-cyan-glow: rgba(34, 211, 238, 0.3);
  --color-accent-magenta-glow: rgba(225, 29, 141, 0.3);

  /* Semantic */
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-error: #EF4444;

  /* Borders & Shadows */
  --color-border: rgba(182, 199, 218, 0.1);
  --shadow-glow-cyan: 0 0 20px var(--color-accent-cyan-glow);
  --shadow-glow-magenta: 0 0 20px var(--color-accent-magenta-glow);
}
```

### Typographie

```css
:root {
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
}
```

### Espacements

```css
:root {
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */

  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;
}
```

## Composants UI

### Boutons

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Primary       │  │  Secondary      │  │  Ghost          │
│  bg: cyan      │  │  bg: surface    │  │  bg: transparent│
│  glow on hover │  │  border: cyan   │  │  text: muted    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Inputs

```
┌──────────────────────────────────────────┐
│ 🔍 Rechercher...                         │  ← placeholder muted
└──────────────────────────────────────────┘
   border: transparent → cyan on focus
   bg: surface-elevated
```

### Cards

```
┌──────────────────────────────────────────┐
│  ┌────────────────────────────────────┐  │  ← glassmorphism
│  │         Card Content               │  │     background: rgba + blur
│  │                                    │  │     border: subtle gradient
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

## Raccourcis clavier

| Raccourci | Action |
|-----------|--------|
| ⌘K | Command palette |
| ⌘N | Nouvelle conversation |
| ⌘, | Settings |
| ⌘⇧M | Toggle panneau mémoire |
| ⌘⇧F | Toggle file browser |
| ⌘↵ | Envoyer message |
| Esc | Fermer modal/panel |
| ⌘1-5 | Naviguer onglets |

## Écran d'onboarding

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                    🤖                                   │
│                                                         │
│            Bienvenue dans THÉRÈSE                       │
│                                                         │
│     "Ta mémoire, tes données, ton business."           │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 1️⃣  Entre ta clé API Claude                       │ │
│  │     [sk-ant-...                               ]    │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 2️⃣  Choisis un dossier de travail                 │ │
│  │     [📁 Sélectionner un dossier]                   │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 3️⃣  Parle-moi de toi (optionnel)                  │ │
│  │     [Je suis consultant IA...                 ]    │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│               [Commencer avec THÉRÈSE →]                │
│                                                         │
│  ○ ○ ●  Page 1/3                                       │
└─────────────────────────────────────────────────────────┘
```

## Micro-animations

### Transitions

| Élément | Animation | Durée |
|---------|-----------|-------|
| Modal open | Scale 0.95→1 + fade | 150ms |
| Panel slide | Translate X | 200ms |
| Button hover | Glow pulse | 200ms |
| Message appear | Fade in + slide up | 150ms |
| Streaming dots | Pulse 3 dots | 1s loop |

### Easing

```css
--ease-out: cubic-bezier(0.33, 1, 0.68, 1);
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
--ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
```

## System Tray

```
┌─────────────────┐
│ 🤖 THÉRÈSE      │
├─────────────────┤
│ Nouvelle conv.  │
│ ─────────────── │
│ Historique      │
│ Mémoire         │
│ ─────────────── │
│ Préférences...  │
│ ─────────────── │
│ Quitter         │
└─────────────────┘
```

### Raccourci global
- **macOS** : ⌘⇧Space
- **Windows** : Ctrl+Shift+Space
- Ouvre THÉRÈSE au premier plan

## Risques identifiés

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Inconsistance visuelle | UX cheap | Design system strict + review |
| Animations trop lourdes | Perf | GPU accelerate + reduce motion |
| Raccourcis conflits OS | Frustration | Personnalisation + fallbacks |
| Onboarding trop long | Abandon | Skip option + 3 étapes max |

## Dépendances

- E1-01 (Tauri + React) obligatoire
- E2-01 (Chat UI) pour tester thème

## Définition of Done

- Tous les composants UI documentés
- Design system Tailwind configuré
- Raccourcis fonctionnels et documentés
- Onboarding testé < 2 min
- 0 jank sur animations
- Dark mode cohérent partout

---

*Epic owner : Agent UX Designer + Dev Frontend*
*Sprint cible : Sprint 2 (base) + Sprint 4 (polish)*
