# Benchmark UX/UI - THÉRÈSE v2

> Document généré pour THÉRÈSE v2
> Date : 21 janvier 2026

## Statut

En cours

---

## 1. Vue d'ensemble

### Positionnement UX

THÉRÈSE vise une expérience **premium** et **calme** - l'opposé des interfaces cluttered des outils IA grand public. Inspiration : Linear, Superhuman, Arc.

> "The dominant philosophy is calm design with minimal visual noise, smooth flows, and lots of whitespace."

### Direction artistique

```yaml
palette:
  background: "#0B1226"      # Deep navy - repos visuel
  surface: "#131B35"         # Cards et modales
  text_primary: "#E6EDF7"    # Texte principal
  text_muted: "#B6C7DA"      # Texte secondaire
  accent_cyan: "#22D3EE"     # Actions, liens, CTA
  accent_magenta: "#E11D8D"  # Highlights, notifications

style:
  approach: "Dark Glassmorphism"
  effects: ["blur", "glass layers", "subtle glow"]
  typography: "Variable fonts, contraste bold/light"
  motion: "Purposeful animations, transitions fluides"
```

---

## 2. Analyse des concurrents UI

### 2.1 Claude Desktop / claude.ai

| Aspect | Observation |
|--------|-------------|
| **Layout** | 2 colonnes : sidebar conversations + chat principal |
| **Style** | Minimaliste, fond blanc/noir, accents violets |
| **Forces** | Clean, focus sur le contenu, Projects pour organisation |
| **Faiblesses** | Peu de personnalisation, pas de vue contacts/projets |

**Screenshot mental** : Interface épurée, messages alternés You/Claude, timestamps discrets.

### 2.2 ChatGPT Desktop

| Aspect | Observation |
|--------|-------------|
| **Layout** | Sidebar + chat, Canvas pour édition documents |
| **Style** | Plus chargé que Claude, icônes nombreuses |
| **Forces** | Canvas innovant, GPT Store intégré |
| **Faiblesses** | Navigation complexe, beaucoup de features |

### 2.3 Cowork (Anthropic)

| Aspect | Observation |
|--------|-------------|
| **Layout** | Chat centré, accès fichiers via folder picker |
| **Style** | Hérite de Claude Desktop, minimal |
| **Forces** | Simplicité, pas d'apprentissage |
| **Faiblesses** | Pas de vue projet, pas de dashboard, pas de CRM |

### 2.4 Linear (référence premium)

| Aspect | Observation |
|--------|-------------|
| **Layout** | Sidebar compacte, liste issues, détail |
| **Style** | **Dark mode exemplaire**, glassmorphism subtil |
| **Forces** | Animations butter-smooth, keyboard-first |
| **Faiblesses** | Courbe d'apprentissage pour raccourcis |

**Patterns à répliquer** :
- Command palette (⌘K)
- Transitions fluides entre vues
- Typographie variable (contraste gras/léger)
- Hover states subtils avec glow

### 2.5 Notion

| Aspect | Observation |
|--------|-------------|
| **Layout** | Sidebar arborescente, blocks flexibles |
| **Style** | Light par défaut, dark mode propre |
| **Forces** | Flexibilité blocks, AI intégrée, relations |
| **Faiblesses** | Peut devenir cluttered, performance |

**Patterns à répliquer** :
- Slash commands (/)
- Blocks drag & drop
- @ mentions
- Relations entre éléments

### 2.6 Superhuman (référence email premium)

| Aspect | Observation |
|--------|-------------|
| **Layout** | Split view, inbox + email |
| **Style** | Dark mode luxueux, animations soignées |
| **Forces** | Keyboard shortcuts everywhere, vitesse |
| **Faiblesses** | Prix élevé, niche |

**Patterns à répliquer** :
- Undo everywhere
- Keyboard shortcuts omniprésents
- AI triage discret mais puissant
- Reminders intégrés

### 2.7 Arc Browser

| Aspect | Observation |
|--------|-------------|
| **Layout** | Sidebar verticale, spaces, mini-apps |
| **Style** | Glassmorphism coloré, personnalisable |
| **Forces** | Spaces pour contextes, visuellement unique |
| **Faiblesses** | Trop différent pour certains |

**Patterns à répliquer** :
- Spaces/contextes de travail
- Boost (personnalisation pages)
- Split view natif

---

## 3. Top 10 Patterns UX à adopter

### 3.1 Command Palette (⌘K)

```
┌────────────────────────────────────────┐
│ 🔍 Que veux-tu faire ?                  │
├────────────────────────────────────────┤
│ ▸ Nouveau message                      │
│ ▸ Chercher dans mes contacts           │
│ ▸ Ouvrir projet "Client X"             │
│ ▸ Résumer la dernière conversation     │
└────────────────────────────────────────┘
```

**Pourquoi** : Accès rapide à tout sans quitter le clavier. Standard moderne (Linear, Notion, Raycast).

### 3.2 Slash Commands

Dans le chat :
```
/résume [ce document]
/contact ajouter Jean Dupont
/projet créer "Refonte site"
/export PDF
```

**Pourquoi** : Familier des utilisateurs Notion/Slack. Découvrabilité naturelle.

### 3.3 Dark Glassmorphism

```css
.card {
  background: rgba(19, 27, 53, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}
```

**Pourquoi** : Profondeur visuelle, premium feel, 2026-proof.

### 3.4 Contextual Memory Display

Afficher ce que THÉRÈSE "sait" sur le contexte actuel :

```
┌─ Contexte actif ──────────────────────┐
│ 👤 Client : Jean Dupont               │
│ 📁 Projet : Audit digital             │
│ 📅 Dernière interaction : hier        │
│ 💡 THÉRÈSE se souvient de 12 éléments │
└───────────────────────────────────────┘
```

**Pourquoi** : Montre la valeur de la mémoire, rassure l'utilisateur.

### 3.5 Progressive Disclosure

- **Niveau 1** : Chat simple
- **Niveau 2** : Panneau latéral (contacts, projets)
- **Niveau 3** : Dashboard complet

L'utilisateur avance à son rythme.

### 3.6 Keyboard-First Design

| Action | Shortcut |
|--------|----------|
| Command palette | ⌘K |
| Nouveau chat | ⌘N |
| Recherche | ⌘F |
| Contacts | ⌘1 |
| Projets | ⌘2 |
| Settings | ⌘, |
| Focus mode | ⌘. |

### 3.7 Micro-interactions & Feedback

- **Message envoyé** : Subtle bounce + confirmation
- **Mémoire enregistrée** : Pulse icon cyan
- **Erreur** : Shake + red glow (pas de popup intrusif)
- **Chargement** : Skeleton screens, pas de spinners

### 3.8 Split View

```
┌────────────────────────────────────────────────────────┐
│ ◀ Contacts │           Chat avec Jean              ▶   │
├────────────┼───────────────────────────────────────────┤
│            │                                           │
│ Jean D.    │  Bonjour Jean, voici le résumé de notre  │
│ Marie L.   │  dernier échange...                      │
│ Pierre M.  │                                           │
│            │  [Document généré]                        │
│            │                                           │
└────────────┴───────────────────────────────────────────┘
```

### 3.9 Inline Actions

Pas de menus contextuels profonds - actions au hover :

```
┌─────────────────────────────────────────────────┐
│ Message de Claude à 14:32                        │
│ Voici l'analyse du marché...      [📋] [✏️] [📤] │
└─────────────────────────────────────────────────┘
                                    copier éditer export
```

### 3.10 Empty States inspirants

Au lieu de "Pas de contacts" :

```
┌─────────────────────────────────────────┐
│                                          │
│     👥 Tes contacts apparaîtront ici     │
│                                          │
│  THÉRÈSE se souvient des personnes que   │
│  tu mentionnes. Commence une conversation│
│  pour qu'elle apprenne ton réseau.       │
│                                          │
│  [Importer des contacts] [Commencer]     │
│                                          │
└─────────────────────────────────────────┘
```

---

## 4. Top 5 Anti-patterns à éviter

### 4.1 Popups et modales intrusives

**Non** : Popup "Bienvenue!" + "Accepter cookies" + "Activer notifications"

**Oui** : Onboarding inline, progressive, dismissable

### 4.2 Menus hamburger sur desktop

**Non** : ☰ qui cache la navigation

**Oui** : Sidebar visible, collapsible proprement

### 4.3 Spinners bloquants

**Non** : "Chargement..." avec spinner qui bloque tout

**Oui** : Skeleton screens, streaming de réponses, indicateurs non-bloquants

### 4.4 Trop d'options visibles

**Non** : 20 boutons dans la toolbar

**Oui** : 3-5 actions principales, le reste dans ⌘K ou menu

### 4.5 Notifications intrusives

**Non** : Toast qui apparaît toutes les 30 secondes

**Oui** : Badge discret, notification center, son optionnel

---

## 5. Wireframes suggérés

### 5.1 Layout principal

```
┌────────────────────────────────────────────────────────────────┐
│ ◀ THÉRÈSE                              🔍  ⚙️  👤              │
├────────┬───────────────────────────────────────────────────────┤
│        │                                                       │
│ CHATS  │                                                       │
│        │                                                       │
│ > Auj. │         Zone de conversation principale               │
│   hier │                                                       │
│   sem. │         Messages alternés user/THÉRÈSE                │
│        │                                                       │
├────────┤         Typing indicator animé                        │
│        │                                                       │
│ CONT.  │                                                       │
│        │                                                       │
│ 👤 J.D │                                                       │
│ 👤 M.L │─────────────────────────────────────────────────────── │
│        │ ┌────────────────────────────────────────────────────┐│
│ PROJ.  │ │ 💬 Message...                          [📎] [🎤] [↵]││
│        │ └────────────────────────────────────────────────────┘│
│ 📁 A.D │                                                       │
│ 📁 Ref │                                                       │
│        │                                                       │
└────────┴───────────────────────────────────────────────────────┘
```

### 5.2 Vue Contact

```
┌────────────────────────────────────────────────────────────────┐
│ ◀ Contacts  │  Jean Dupont                         [✏️] [📤]   │
├─────────────┼──────────────────────────────────────────────────┤
│             │  ┌─────────────────────────────────────────────┐ │
│ 🔍 Recherche│  │ 👤 Jean Dupont                               │ │
│             │  │    Directeur - Entreprise XYZ               │ │
│ ┌─────────┐ │  │    📧 jean@xyz.com                          │ │
│ │👤Jean D.│ │  │    📱 06 12 34 56 78                        │ │
│ └─────────┘ │  └─────────────────────────────────────────────┘ │
│ 👤 Marie L. │                                                  │
│ 👤 Pierre M.│  ── Ce que THÉRÈSE sait ──────────────────────── │
│ 👤 Sophie B.│                                                  │
│             │  • Client depuis mars 2025                       │
│             │  • Projet : Audit digital (en cours)             │
│             │  • Préfère les échanges par email                │
│             │  • Budget : ~5 000 €                             │
│             │                                                  │
│             │  ── Dernières conversations ─────────────────── │
│             │                                                  │
│             │  📅 20 jan - Suivi projet audit                  │
│             │  📅 15 jan - Devis accepté                       │
│             │  📅 10 jan - Premier contact                     │
│             │                                                  │
└─────────────┴──────────────────────────────────────────────────┘
```

### 5.3 Vue Projet

```
┌────────────────────────────────────────────────────────────────┐
│ ◀ Projets  │  Audit Digital - Jean Dupont         [✏️] [📤]    │
├────────────┼───────────────────────────────────────────────────┤
│            │                                                   │
│ 📁 Actifs  │  ┌───────────────────────────────────────────┐   │
│            │  │ Statut: 🟢 En cours                        │   │
│ > Audit D. │  │ Client: Jean Dupont                        │   │
│   Refonte  │  │ Créé: 10 janvier 2026                      │   │
│   Site B.  │  │ Valeur: 2 500 € HT                         │   │
│            │  └───────────────────────────────────────────┘   │
│ 📁 Archivés│                                                   │
│            │  ── Documents liés ────────────────────────────   │
│   Projet X │                                                   │
│   Projet Y │  📄 Devis_Audit_Jean.pdf                          │
│            │  📄 Notes_Réunion_15jan.md                        │
│            │  📄 Rapport_Préliminaire.docx                     │
│            │                                                   │
│            │  ── Timeline ──────────────────────────────────   │
│            │                                                   │
│            │  ○ 10 jan - Création projet                       │
│            │  ○ 15 jan - Devis envoyé                          │
│            │  ● 20 jan - Audit en cours                        │
│            │  ○ 25 jan - Livraison prévue                      │
│            │                                                   │
└────────────┴───────────────────────────────────────────────────┘
```

### 5.4 Command Palette (⌘K)

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│           ┌────────────────────────────────────────┐           │
│           │ 🔍 Tape une commande...                 │           │
│           ├────────────────────────────────────────┤           │
│           │                                        │           │
│           │ SUGGESTIONS                            │           │
│           │ ▸ Nouveau chat                    ⌘N   │           │
│           │ ▸ Chercher un contact             ⌘⇧C  │           │
│           │ ▸ Ouvrir un projet                ⌘⇧P  │           │
│           │                                        │           │
│           │ RÉCENT                                 │           │
│           │ ▸ Jean Dupont - Audit                  │           │
│           │ ▸ Marie Laurent - Site web             │           │
│           │                                        │           │
│           │ ACTIONS                                │           │
│           │ ▸ /résume                              │           │
│           │ ▸ /export PDF                          │           │
│           │ ▸ /paramètres                     ⌘,   │           │
│           │                                        │           │
│           └────────────────────────────────────────┘           │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 6. Accessibilité (WCAG 2.1+)

### 6.1 Contraste

| Élément | Ratio minimum | THÉRÈSE |
|---------|--------------|---------|
| Texte principal | 4.5:1 | #E6EDF7 sur #0B1226 = **12.8:1** |
| Texte secondaire | 4.5:1 | #B6C7DA sur #0B1226 = **8.4:1** |
| Accent cyan | 4.5:1 | #22D3EE sur #0B1226 = **9.2:1** |

### 6.2 Navigation clavier

- **Tab** : Navigation entre éléments focusables
- **Enter** : Activation
- **Escape** : Fermeture modales/palettes
- **Flèches** : Navigation dans listes
- **Skip link** : Aller directement au chat

### 6.3 Screen readers

- Labels ARIA sur tous les éléments interactifs
- Annonces live pour nouveaux messages
- Rôles sémantiques (main, navigation, dialog)
- Alternative texte pour tous les états

### 6.4 Réduction de mouvement

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 7. Animations & Micro-interactions

### 7.1 Principes

- **Purposeful** : Chaque animation a une raison
- **Fast** : 150-300ms max pour les transitions
- **Interruptible** : Peut être annulée
- **Natural** : Ease-out pour entrées, ease-in pour sorties

### 7.2 Catalogue d'animations

| Interaction | Animation | Durée |
|-------------|-----------|-------|
| Message envoyé | Slide up + fade | 200ms |
| Message reçu | Slide in + fade | 250ms |
| Ouverture sidebar | Slide + blur reveal | 200ms |
| Command palette | Scale + fade | 150ms |
| Hover card | Subtle lift + glow | 150ms |
| Typing indicator | Pulsing dots | Loop |
| Memory saved | Cyan pulse | 300ms |
| Error | Shake | 300ms |

### 7.3 Framer Motion (React)

```tsx
// Message entrant
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.25, ease: "easeOut" }}
>
  {message}
</motion.div>

// Hover card
<motion.div
  whileHover={{
    y: -2,
    boxShadow: "0 8px 30px rgba(34, 211, 238, 0.15)"
  }}
>
  {card}
</motion.div>
```

---

## 8. Composants Design System

### 8.1 Tokens

```css
:root {
  /* Colors */
  --color-bg: #0B1226;
  --color-surface: #131B35;
  --color-text: #E6EDF7;
  --color-muted: #B6C7DA;
  --color-accent-cyan: #22D3EE;
  --color-accent-magenta: #E11D8D;

  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;

  /* Radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-full: 9999px;

  /* Typography */
  --font-sans: "Inter", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", monospace;

  /* Shadows */
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.2);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.3);
  --shadow-glow-cyan: 0 0 20px rgba(34, 211, 238, 0.3);
}
```

### 8.2 Composants principaux

1. **Button** : Primary (cyan), Secondary (ghost), Danger (magenta)
2. **Input** : Text, Textarea, Search
3. **Card** : Glass effect, hover lift
4. **Avatar** : Initials ou image, online indicator
5. **Badge** : Status, count, notification
6. **Tooltip** : Contextual help
7. **Modal** : Centered, with backdrop blur
8. **Toast** : Success/Error/Info, auto-dismiss

---

## 9. Recommandations techniques

### 9.1 Stack UI

| Outil | Rôle |
|-------|------|
| **React 19** | Framework UI |
| **TailwindCSS 4** | Styling |
| **Framer Motion** | Animations |
| **Radix UI** | Primitives accessibles |
| **Lucide Icons** | Iconographie |
| **Tauri 2** | Desktop wrapper |

### 9.2 Performance

- **Code splitting** : Lazy load des vues secondaires
- **Virtualization** : Listes longues (contacts, messages)
- **Optimistic updates** : UI réactive avant confirmation
- **Skeleton screens** : Feedback immédiat

### 9.3 Responsive (desktop)

| Breakpoint | Layout |
|------------|--------|
| < 800px | Sidebar cachée, toggle |
| 800-1200px | Sidebar compacte |
| > 1200px | Sidebar complète |

---

## 10. Comparatif final

| Critère | Claude | Cowork | THÉRÈSE (cible) |
|---------|--------|--------|-----------------|
| **Dark mode** | Basique | Basique | Premium glassmorphism |
| **Vue contacts** | Non | Non | CRM intégré |
| **Vue projets** | Projects | Non | Timeline + docs |
| **Command palette** | Non | Non | ⌘K complet |
| **Shortcuts** | Limités | Limités | Keyboard-first |
| **Animations** | Minimales | Minimales | Purposeful |
| **Accessibilité** | Bonne | Moyenne | WCAG 2.1 AA |

---

## 11. Sources

### Design Systems
- [Linear Design System](https://linear.app/design)
- [Radix UI Primitives](https://www.radix-ui.com/)
- [Tailwind CSS](https://tailwindcss.com/)

### Articles UX
- [Dark Glassmorphism: The Aesthetic That Will Define UI in 2026](https://medium.com/@developer_89726/dark-glassmorphism-the-aesthetic-that-will-define-ui-in-2026-93aa4153088f)
- [UX/UI, AI and Trends That Actually Work in 2026](https://medium.com/@dev.family/ux-ui-ai-and-trends-that-actually-work-in-2026-dfef7f98f9a5)
- [UX for AI Chatbots: Complete Guide](https://www.parallelhq.com/blog/ux-ai-chatbots)

### Accessibilité
- [Accessibility Guidelines for AI Interfaces (AAG)](https://medium.com/@anky18milestone/aag-v0-1-accessibility-guidelines-for-ai-interfaces-inspired-by-wcag-40ab4e8badc2)
- [Building Inclusive Conversations: Accessibility in Chatbots](https://dubbot.com/dubblog/2025/building-inclusive-conversations-accessibility-in-chatbots.html)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

### Inspiration
- [Best SaaS Websites for Design Inspiration 2026](https://www.bookmarkify.io/blog/best-saas-websites-of-2025-end-of-year-showcase)
- [Top Dashboard Designs 2026](https://www.wrappixel.com/best-dashboard-designs/)
- [Dribbble Dark Mode Dashboards](https://dribbble.com/tags/dark-mode-dashboard)

### Comparatifs AI UI
- [Comparing Conversational AI Tool User Interfaces 2025](https://intuitionlabs.ai/articles/conversational-ai-ui-comparison-2025)
- [Claude Desktop vs ChatGPT Comparison](https://skywork.ai/blog/ai-agent/claude-desktop-vs-chatgpt-perplexity-copilot-lm-studio-2025-comparison/)

---

## 12. Conclusion

L'UX de THÉRÈSE doit se différencier par :

1. **Premium feel** : Dark glassmorphism, animations soignées
2. **Keyboard-first** : Power users welcome
3. **Mémoire visible** : Montrer ce que THÉRÈSE sait
4. **CRM intégré** : Contacts et projets au premier plan
5. **Accessibilité** : WCAG 2.1 AA minimum

**Tagline UX** : "Une interface qui travaille pour toi, pas contre toi."

---

*Document généré le 21 janvier 2026*
*THÉRÈSE v2 - Synoptïa*
