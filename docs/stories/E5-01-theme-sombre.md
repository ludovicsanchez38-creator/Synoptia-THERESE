# Story E5-01 : Implémenter le thème sombre premium

## Description

En tant que **utilisateur**,
Je veux **une interface sombre élégante et cohérente**,
Afin de **travailler confortablement sans fatigue visuelle**.

## Contexte technique

- **Composants impactés** : Frontend React, TailwindCSS
- **Dépendances** : E1-01
- **Fichiers concernés** :
  - `src/frontend/tailwind.config.js` (màj)
  - `src/frontend/src/styles/globals.css` (nouveau)
  - `src/frontend/src/styles/theme.ts` (nouveau)

## Critères d'acceptation

- [ ] Palette de couleurs Synoptïa appliquée
- [ ] Variables CSS pour tous les tokens
- [ ] Composants de base stylés (boutons, inputs, cards)
- [ ] Glassmorphism sur surfaces élevées
- [ ] Transitions douces sur hover/focus
- [ ] Contrast ratio WCAG AA respecté

## Notes techniques

### Design tokens

```typescript
// styles/theme.ts
export const theme = {
  colors: {
    // Backgrounds
    bg: '#0B1226',
    surface: '#131B35',
    surfaceElevated: '#1A2340',
    surfaceOverlay: 'rgba(19, 27, 53, 0.95)',

    // Text
    text: '#E6EDF7',
    textMuted: '#B6C7DA',
    textDisabled: '#6B7A94',

    // Accents
    accentCyan: '#22D3EE',
    accentCyanHover: '#06B6D4',
    accentCyanMuted: 'rgba(34, 211, 238, 0.15)',
    accentMagenta: '#E11D8D',
    accentMagentaHover: '#DB2777',
    accentMagentaMuted: 'rgba(225, 29, 141, 0.15)',

    // Semantic
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    info: '#3B82F6',

    // Border
    border: '#2A3654',
    borderHover: '#3D4F75',
  },

  // Glassmorphism
  glass: {
    background: 'rgba(19, 27, 53, 0.7)',
    backdropBlur: '12px',
    border: '1px solid rgba(42, 54, 84, 0.5)',
  },

  // Shadows
  shadows: {
    sm: '0 1px 2px rgba(0, 0, 0, 0.3)',
    md: '0 4px 6px rgba(0, 0, 0, 0.4)',
    lg: '0 10px 15px rgba(0, 0, 0, 0.5)',
    glow: '0 0 20px rgba(34, 211, 238, 0.3)',
    glowMagenta: '0 0 20px rgba(225, 29, 141, 0.3)',
  },

  // Radii
  radii: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    full: '9999px',
  },

  // Transitions
  transitions: {
    fast: '150ms ease',
    normal: '200ms ease',
    slow: '300ms ease',
  },
};

export type Theme = typeof theme;
```

### Configuration TailwindCSS

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0B1226',
        surface: '#131B35',
        'surface-elevated': '#1A2340',
        text: '#E6EDF7',
        'text-muted': '#B6C7DA',
        'text-disabled': '#6B7A94',
        'accent-cyan': '#22D3EE',
        'accent-magenta': '#E11D8D',
        border: '#2A3654',
        success: '#10B981',
        warning: '#F59E0B',
        error: '#EF4444',
        info: '#3B82F6',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 20px rgba(34, 211, 238, 0.3)',
        'glow-magenta': '0 0 20px rgba(225, 29, 141, 0.3)',
      },
      backdropBlur: {
        glass: '12px',
      },
      animation: {
        'fade-in': 'fadeIn 200ms ease',
        'slide-up': 'slideUp 200ms ease',
        'slide-down': 'slideDown 200ms ease',
        pulse: 'pulse 2s infinite',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: 0 },
          to: { opacity: 1 },
        },
        slideUp: {
          from: { opacity: 0, transform: 'translateY(10px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
        },
        slideDown: {
          from: { opacity: 0, transform: 'translateY(-10px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};
```

### Styles globaux

```css
/* styles/globals.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

/* CSS Variables */
:root {
  --color-bg: #0B1226;
  --color-surface: #131B35;
  --color-surface-elevated: #1A2340;
  --color-text: #E6EDF7;
  --color-text-muted: #B6C7DA;
  --color-accent-cyan: #22D3EE;
  --color-accent-magenta: #E11D8D;
  --color-border: #2A3654;

  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', Menlo, monospace;

  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;

  --transition-fast: 150ms ease;
  --transition-normal: 200ms ease;
}

/* Base */
html {
  font-family: var(--font-sans);
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  background-color: var(--color-bg);
  color: var(--color-text);
  line-height: 1.5;
}

/* Scrollbar custom */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #3D4F75;
}

/* Focus styles */
*:focus-visible {
  outline: 2px solid var(--color-accent-cyan);
  outline-offset: 2px;
}

/* Selection */
::selection {
  background: rgba(34, 211, 238, 0.3);
  color: var(--color-text);
}

/* Glassmorphism utility */
@layer utilities {
  .glass {
    background: rgba(19, 27, 53, 0.7);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(42, 54, 84, 0.5);
  }

  .glass-elevated {
    background: rgba(26, 35, 64, 0.8);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(42, 54, 84, 0.6);
  }
}
```

### Composants de base

```tsx
// components/ui/Button.tsx
import { cn } from '../../lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

export function Button({
  variant = 'primary',
  size = 'md',
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center font-medium rounded-lg transition-all',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-bg',
        'disabled:opacity-50 disabled:pointer-events-none',

        // Variants
        variant === 'primary' && 'bg-accent-cyan text-bg hover:bg-accent-cyan/90 shadow-glow/50',
        variant === 'secondary' && 'bg-surface-elevated text-text border border-border hover:border-accent-cyan/50',
        variant === 'ghost' && 'text-text-muted hover:text-text hover:bg-surface-elevated',
        variant === 'danger' && 'bg-error/10 text-error hover:bg-error/20',

        // Sizes
        size === 'sm' && 'px-3 py-1.5 text-sm',
        size === 'md' && 'px-4 py-2 text-sm',
        size === 'lg' && 'px-6 py-3 text-base',

        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
```

```tsx
// components/ui/Input.tsx
import { cn } from '../../lib/utils';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export function Input({ error, className, ...props }: InputProps) {
  return (
    <input
      className={cn(
        'w-full px-4 py-2 bg-surface-elevated rounded-lg',
        'text-text placeholder:text-text-muted',
        'border border-border focus:border-accent-cyan',
        'focus:outline-none focus:ring-2 focus:ring-accent-cyan/20',
        'transition-colors duration-150',
        error && 'border-error focus:border-error focus:ring-error/20',
        className
      )}
      {...props}
    />
  );
}
```

```tsx
// components/ui/Card.tsx
import { cn } from '../../lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'elevated';
}

export function Card({ variant = 'default', className, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-xl p-4',
        variant === 'default' && 'bg-surface border border-border',
        variant === 'glass' && 'glass',
        variant === 'elevated' && 'bg-surface-elevated shadow-lg',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
```

### Utilitaire cn

```typescript
// lib/utils.ts
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

## Estimation

- **Complexité** : S
- **Points** : 3

## Palette visuelle

```
┌─────────────────────────────────────────────────────────────┐
│ Background       #0B1226  ████████████████████████████████  │
│ Surface          #131B35  ████████████████████████████████  │
│ Surface Elevated #1A2340  ████████████████████████████████  │
│ Border           #2A3654  ████████████████████████████████  │
├─────────────────────────────────────────────────────────────┤
│ Text             #E6EDF7  ████████████████████████████████  │
│ Text Muted       #B6C7DA  ████████████████████████████████  │
├─────────────────────────────────────────────────────────────┤
│ Accent Cyan      #22D3EE  ████████████████████████████████  │
│ Accent Magenta   #E11D8D  ████████████████████████████████  │
└─────────────────────────────────────────────────────────────┘
```

## Definition of Done

- [ ] Tokens CSS définis
- [ ] TailwindCSS configuré
- [ ] Composants Button, Input, Card
- [ ] Glassmorphism fonctionnel
- [ ] Scrollbar custom
- [ ] Focus states accessibles

---

*Sprint : 1*
*Assigné : Agent Dev Frontend*
