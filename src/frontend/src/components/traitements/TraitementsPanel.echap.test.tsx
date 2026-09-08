/**
 * B-651 (ronde B, D1) : le panneau « Travaux en cours » est un role=dialog
 * qu'Échap ne fermait pas : aucun gestionnaire, ni dans le composant, ni dans
 * la cascade de la coque. Il s'inscrit dans la pile d'Échap (première moitié
 * de la cascade : les overlays portés par les stores).
 */
import { render } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const pile = vi.hoisted(() => ({ handlers: [] as Array<() => void>, retraits: 0 }));
vi.mock('../../lib/escapeStack', () => ({
  pushEscapeHandler: (h: () => void) => {
    pile.handlers.push(h);
    return () => { pile.retraits += 1; };
  },
  runTopEscapeHandler: () => { const h = pile.handlers.at(-1); if (!h) return false; h(); return true; },
  _clearEscapeHandlers: () => { pile.handlers.length = 0; },
}));
vi.mock('../../services/api', () => ({ listerTraitements: vi.fn(), annulerTraitement: vi.fn() }));

import { useProcessingTasksStore } from '../../stores/processingTasksStore';
import { TraitementsPanel } from './TraitementsPanel';

describe('B-651 : Échap ferme le panneau des travaux', () => {
  beforeEach(() => {
    pile.handlers.length = 0;
    pile.retraits = 0;
    useProcessingTasksStore.setState({ traitements: [], erreur: null, arretsDemandes: new Set(), panneauOuvert: true });
  });

  it('monté, il s’inscrit dans la pile d’Échap et le gestionnaire le ferme', () => {
    render(<TraitementsPanel />);
    expect(pile.handlers).toHaveLength(1);
    pile.handlers[0]();
    expect(useProcessingTasksStore.getState().panneauOuvert).toBe(false);
  });

  it('démonté, il se retire de la pile', () => {
    const { unmount } = render(<TraitementsPanel />);
    unmount();
    expect(pile.retraits).toBe(1);
  });
});
