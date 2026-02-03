# Règles Design et UX - THÉRÈSE V2

> **Direction artistique** : "Dark Glassmorphism" - Interface premium, calme, bruit visuel minimal.
> Inspirée de Linear, Superhuman, Arc et Notion.

---

## 1. Palette de couleurs

```yaml
palette:
  background: "#0B1226"      # Navy profond - fond principal
  surface: "#131B35"          # Surface des cartes et panneaux
  surface_hover: "#1A2340"    # Surface au survol
  border: "#1E2A4A"           # Bordures subtiles
  text: "#E6EDF7"             # Texte principal
  muted: "#A9B8D8"            # Texte secondaire
  primary: "#2451FF"          # Actions principales
  accent_cyan: "#22D3EE"      # Interactions, liens
  accent_magenta: "#E11D8D"   # Highlights, badges
  success: "#22C55E"          # Confirmations
  warning: "#F59E0B"          # Alertes
  error: "#EF4444"            # Erreurs
```

### 1.1 Règles d'utilisation des couleurs

| Couleur | Token | Usage |
|---------|-------|-------|
| `#0B1226` | background | Fond de l'application uniquement |
| `#131B35` | surface | Cartes, panneaux, modales, sidebar |
| `#1A2340` | surface_hover | Survol des surfaces |
| `#1E2A4A` | border | Bordures subtiles (1px max) |
| `#E6EDF7` | text | Texte principal (jamais #FFFFFF) |
| `#A9B8D8` | muted | Labels, texte d'aide, placeholders |
| `#2451FF` | primary | Boutons d'action principale, liens actifs |
| `#22D3EE` | accent_cyan | Éléments interactifs secondaires, statuts actifs |
| `#E11D8D` | accent_magenta | Badges, compteurs, éléments d'accent |
| `#22C55E` | success | Confirmations, validations |
| `#F59E0B` | warning | Alertes, avertissements |
| `#EF4444` | error | Erreurs, suppressions |

### 1.2 Contraste

- Contraste minimum texte courant : **4.5:1** (WCAG 2.1 AA)
- Contraste minimum grands textes (>= 18px ou 14px bold) : **3:1**
- Les couleurs vives sur fond sombre doivent toujours être atténuées (`/10`, `/20`) pour éviter l'agression visuelle

---

## 2. Typographie

### 2.1 Police système

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
```

Natif macOS pour des performances optimales et un rendu cohérent.

### 2.2 Échelle typographique

| Token | Taille | px | Usage |
|-------|--------|----|-------|
| `xs` | 0.75rem | 12px | Labels, badges, métadonnées |
| `sm` | 0.875rem | 14px | Texte secondaire, sidebar |
| `base` | 1rem | 16px | Texte principal, messages |
| `lg` | 1.125rem | 18px | Sous-titres |
| `xl` | 1.25rem | 20px | Titres de section |
| `2xl` | 1.5rem | 24px | Titres de page |

### 2.3 Règles typographiques

- **Monospace** : réservé aux blocs de code dans le chat
- **Font-weight** : 400 (normal), 500 (medium pour labels), 600 (semibold pour titres)
- **Line-height** : 1.5 pour le texte courant, 1.25 pour les titres
- **Letter-spacing** : 0 par défaut, -0.01em pour les titres 2xl
- Taille de police ajustable par l'utilisateur : small / medium / large

---

## 3. Composants UI

### 3.1 Boutons

| Variante | Background | Texte | Hover |
|----------|-----------|-------|-------|
| **Primaire** | `primary` (#2451FF) | white | scale 1.02 |
| **Secondaire** | `surface` + border | text | bg surface_hover |
| **Ghost** | transparent | text | bg surface/50 |
| **Danger** | error/10 | error | bg error/20 |

**Spécifications communes :**
- Hauteur minimale : **36px**
- Padding horizontal : **16px**
- Border-radius : **8px**
- Transition : **150ms ease**
- whileHover : `scale: 1.02`
- whileTap : `scale: 0.98`
- Focus : `ring-2 ring-accent_cyan`

### 3.2 Cartes

```
Background :    surface (#131B35)
Border :        1px solid border (#1E2A4A)
Border-radius : 12px
Padding :       16px
Hover :         border accent_cyan/30, shadow subtle
Glassmorphism : backdrop-blur-xl bg-surface/80 (optionnel)
```

### 3.3 Modales

- **Overlay** : `bg-black/60 backdrop-blur-sm`
- **Container** : `bg-surface rounded-2xl shadow-2xl`
- **Animation** : fadeIn + scaleIn (spring)
- **Fermeture** : Échap, clic overlay, bouton X
- **Largeur max** : 640px (md), 800px (lg)
- **Pas de modales imbriquées** : 1 niveau maximum

### 3.4 Inputs

- Background : `bg-background`
- Border : `1px solid border`, focus `border-accent_cyan`
- Border-radius : **8px**
- Padding : `10px 14px`
- Placeholder : `text-muted`
- Focus : `ring-2 ring-accent_cyan/20`
- Transition focus : **150ms**

### 3.5 Sidebar

- Largeur : **280px** (rétractable)
- Background : `surface` avec bordure droite
- Animation slide : **200ms ease**
- Toggle via rails gauche/droite (`SideToggle`)
- Groupement des conversations par date

### 3.6 Messages (chat)

| Type | Style | Alignement |
|------|-------|------------|
| **User** | `bg-primary/10 border-primary/20` | Droite |
| **Assistant** | `bg-surface border` | Gauche |

- Markdown rendu avec `prose dark` et syntax highlighting
- Métadonnées : tokens, coût, modèle (texte muted en bas)
- Animation d'apparition : `fadeInUp` avec stagger **50ms**

---

## 4. Animations (Framer Motion)

### 4.1 Principes fondamentaux

- **Spring par défaut** (pas de linear/ease sauf exception justifiée)
- Durée perçue < **300ms** pour les micro-interactions
- Stagger de **50ms** pour les listes
- `AnimatePresence` obligatoire pour les entrées/sorties
- Respect strict de `prefers-reduced-motion` (tout désactivé si actif)

### 4.2 Transitions pré-définies

```typescript
// Transition spring standard (micro-interactions)
const springTransition = {
  type: "spring",
  stiffness: 300,
  damping: 30,
};

// Transition ease rapide (tooltips, menus)
const easeTransition = {
  duration: 0.2,
  ease: "easeOut",
};

// Transition smooth (panneaux, modales)
const smoothTransition = {
  duration: 0.3,
  ease: [0.4, 0, 0.2, 1],
};
```

### 4.3 Variants standards

| Nom | Description | Propriétés |
|-----|-------------|-----------|
| `fadeIn` | Fondu simple | opacity: 0 -> 1 |
| `fadeInUp` | Fondu + glissement haut | opacity: 0 -> 1, y: 10 -> 0 |
| `scaleIn` | Zoom léger | scale: 0.95 -> 1, opacity: 0 -> 1 |
| `slideInFromRight` | Glissement latéral | x: 300 -> 0 |
| `popIn` | Apparition rebond | scale: 0.8 -> 1 (spring bounce) |

### 4.4 Animations interactives

| Élément | Interaction | Animation |
|---------|-------------|-----------|
| Boutons | whileHover | `scale: 1.02` |
| Boutons | whileTap | `scale: 0.98` |
| Cartes | whileHover | `y: -2`, shadow augmenté |
| Toggle | layout | Layout animation pour le switch |
| Loading | - | Pulse ou shimmer animation |

---

## 5. Layout principal

```
┌─────────────────────────────────────────────────────────┐
│  ChatHeader (titre, profil, branding)                   │
├──────────┬─────────────────────────────┬────────────────┤
│          │                             │                │
│ Sidebar  │      Zone de chat           │  MemoryPanel   │
│ (convs)  │   (messages + input)        │  (contacts /   │
│  280px   │        flex-1               │   projets)     │
│          │                             │    320px       │
│          │                             │                │
├──────────┴─────────────────────────────┴────────────────┤
│  ChatInput (textarea, voice, file drop)                 │
└─────────────────────────────────────────────────────────┘
```

### 5.1 Règles de layout

- Rails gauche/droite pour toggle sidebar/memory
- Modales empilées : CommandPalette, Settings, Board, etc.
- Overlay drag-drop plein écran pour les fichiers
- Zone de chat : `flex-1`, centrée, largeur max de contenu **800px**
- Scroll : smooth, auto-scroll vers le bas sur nouveau message

---

## 6. Onboarding (6 étapes)

| Étape | Contenu | Éléments |
|-------|---------|----------|
| 1. **Bienvenue** | Logo, tagline | Bouton "Commencer" |
| 2. **Profil** | Nom, entreprise, rôle | Formulaire |
| 3. **LLM** | Choix du provider + clé API | Select + input sécurisé |
| 4. **Sécurité** | Explications chiffrement | Texte informatif |
| 5. **Répertoire** | Choix du dossier de travail | File picker natif |
| 6. **Terminé** | Récapitulatif | Accès au chat |

**Animations :** Chaque étape avec transition `fadeInUp`, barre de progression, navigation avant/arrière.

---

## 7. Prompts guidés (état vide)

Affichés dans un grid responsive quand la conversation est vide.

3 catégories d'actions avec **8 options** chacune :

| Catégorie | Couleur | Exemples d'actions |
|-----------|---------|-------------------|
| **Produire** | accent_cyan (#22D3EE) | Rédiger, Créer une présentation, Générer un email... |
| **Comprendre** | accent_magenta (#E11D8D) | Analyser, Résumer, Expliquer, Comparer... |
| **Organiser** | primary (#2451FF) | Planifier, Prioriser, Structurer, Lister... |

---

## 8. Icônes

- **Bibliothèque** : `lucide-react` (400+ icônes)
- **Taille par défaut** : 18px (`w-[18px] h-[18px]`)
- **Couleur** : `currentColor` (hérite du texte parent)
- **Stroke-width** : 1.5 (défaut lucide)
- Toujours accompagnées d'un `aria-label` si elles ne sont pas suivies de texte

---

## 9. Accessibilité (WCAG 2.1 AA)

### 9.1 Contrastes

- Texte courant : minimum **4.5:1**
- Grands textes : minimum **3:1**
- Éléments interactifs : minimum **3:1**

### 9.2 Navigation

- Focus visible : `ring-2 ring-accent_cyan`
- Navigation clavier complète : Tab, Enter, Escape
- Ordre de tabulation logique et prévisible

### 9.3 Sémantique

- `aria-label` sur tous les boutons sans texte visible
- `aria-live` pour les mises à jour dynamiques (streaming du chat)
- Headings hiérarchiques (`h1` -> `h2` -> `h3`, sans saut)
- Screen reader friendly

### 9.4 Préférences utilisateur

- Respect `prefers-reduced-motion` (animations désactivées)
- Taille de police ajustable : small / medium / large
- Mode haut contraste optionnel

---

## 10. Responsive

- **Desktop-first** (pas de support mobile)
- Largeur minimale : **800px**
- Sidebar rétractable sur les petits écrans (< 1200px)
- MemoryPanel rétractable
- Modales avec `max-width` adaptatif
- Pas de scrollbar horizontale (jamais)

---

## 11. Glassmorphism

### 11.1 Quand l'utiliser

- Modales
- Tooltips
- Overlays
- CommandPalette

### 11.2 Propriétés

```css
backdrop-filter: blur(24px);       /* backdrop-blur-xl */
background: rgba(19, 27, 53, 0.8); /* bg-surface/80 */
border: 1px solid rgba(255, 255, 255, 0.05); /* border-white/5 */
```

### 11.3 Limite stricte

- Ne **jamais** empiler plus de **2 couches** de blur
- Tester les performances sur les machines les moins puissantes

---

## 12. Anti-patterns design (interdit)

| Interdit | Raison | Alternative |
|----------|--------|-------------|
| Couleurs vives brutes sur fond sombre | Agression visuelle | Atténuer avec `/10`, `/20` |
| Animations > 500ms | Perception de lenteur | Rester sous 300ms |
| Modales imbriquées | Confusion UX | 1 niveau max |
| Scrollbar horizontale | Casse le layout | Overflow hidden/auto |
| Texte blanc pur (#FFFFFF) | Trop contrasté, fatigue oculaire | Utiliser #E6EDF7 |
| Bordures > 1px | Lourdeur visuelle | 1px maximum |
| Shadows colorées excessives | Bruit visuel | Shadows neutres subtiles |
| Emojis dans l'interface | Incohérence (sauf conseillers du Board) | Icônes lucide |
| Tirets longs (-) | Convention Synoptia | Tirets courts (-) ou parenthèses |
| Fond dégradé agressif | Distraction | Couleurs plates |
| Police custom lourde | Performance | Police système native |
| Z-index > 9999 | Ingérable | Échelle ordonnée (10, 20, 30...) |
