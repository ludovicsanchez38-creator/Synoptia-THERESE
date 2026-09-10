/**
 * DA « Application affinée », lot 1 (10/09/2026) : le bouton.
 *
 * `base.css` de la DA validée : `.btn` fait 2,25 rem (36 px), sans ombre ni
 * soulèvement ; le primaire est le remplissage cyan, le secondaire une
 * surface bordée, le discret est écrit en accent, le danger repose sur la
 * teinte d'erreur. Les 254 usages gardent leur API (`variant`, `size`).
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Button } from './Button';

function classes(variant?: 'primary' | 'secondary' | 'ghost' | 'danger', size?: 'sm' | 'md' | 'lg' | 'icon') {
  const { unmount } = render(<Button variant={variant} size={size}>Geste</Button>);
  const nom = screen.getByRole('button', { name: 'Geste' }).className;
  unmount();
  return nom;
}

describe('Button, DA lot 1', () => {
  it('la taille courante fait 36 px, l’icône aussi, le grand geste garde 44 px', () => {
    expect(classes(undefined, 'md')).toMatch(/\bh-9\b/);
    expect(classes(undefined, 'md')).not.toMatch(/\bh-11\b/);
    expect(classes(undefined, 'icon')).toMatch(/\bh-9\b.*\bw-9\b|\bw-9\b.*\bh-9\b/);
    expect(classes(undefined, 'lg')).toMatch(/\bh-11\b/);
    expect(classes(undefined, 'sm')).toMatch(/\bh-8\b/);
  });

  it('plus d’ombre ni de soulèvement : btn-da a disparu de tous les variants', () => {
    for (const v of ['primary', 'secondary', 'danger', 'ghost'] as const) {
      expect(classes(v), v).not.toMatch(/\bbtn-da\b/);
      expect(classes(v), v).not.toMatch(/translate/);
    }
  });

  it('chaque variant consomme la palette de la DA', () => {
    expect(classes('primary')).toMatch(/\bbg-accent-fill\b/);
    expect(classes('secondary')).toMatch(/\bborder-border\b/);
    expect(classes('ghost')).toMatch(/\btext-accent\b/);
    expect(classes('ghost')).toMatch(/hover:bg-accent-tint/);
    expect(classes('danger')).toMatch(/bg-\[var\(--color-error-tint\)\]/);
    expect(classes('danger')).toMatch(/\btext-error\b/);
  });
});
