/**
 * Squelette : barre de chargement décorative.
 *
 * aria-hidden : Spinner reste l'attente ponctuelle qu'on annonce. Ici on
 * peint une forme, on ne dit rien. L'animation `glisse` vit dans le
 * composant (pas dans globals.css) ; les filets globaux
 * prefers-reduced-motion (globals.css l.479) et
 * html[data-reduce-motion="true"] (l.491) l'arrêtent déjà.
 */
import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Squelette } from './Squelette';

describe('Squelette', () => {
  it('est une barre ronde muette, animée par glisse', () => {
    const { container } = render(<Squelette />);

    const muet = container.querySelector('[aria-hidden="true"]');
    expect(muet).not.toBeNull();
    expect(container.querySelector('[role]')).toBeNull();

    const barre = container.querySelector('.h-3') as HTMLElement;
    expect(barre).not.toBeNull();
    expect(barre.className).toMatch(/h-3/);
    expect(barre.className).toMatch(/rounded-full/);
    expect(barre.className).toMatch(/animate-\[glisse_1\.2s_linear_infinite\]/);

    const style = [...container.querySelectorAll('style')].map((n) => n.textContent).join('');
    expect(style).toMatch(/@keyframes\s+glisse/);
  });

  it('répète le nombre de lignes demandé et accepte une largeur', () => {
    const { container } = render(<Squelette lignes={3} largeur="w-1/2" />);
    const barres = container.querySelectorAll('.h-3');
    expect(barres).toHaveLength(3);
    for (const barre of barres) {
      expect(barre.className).toMatch(/w-1\/2/);
    }
  });
});
