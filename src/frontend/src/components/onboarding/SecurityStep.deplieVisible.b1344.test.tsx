/**
 * B-1344 (persona Claire, cycle 13) : l'explication d'un risque se dépliait
 * hors de vue.
 *
 * Les risques vivaient dans une liste à hauteur bornée (`max-h-[280px]
 * overflow-y-auto`), elle-même dans un assistant qui défile : le dernier
 * élément déplié (celui qui dit que la dictée part en ligne par défaut) était
 * coupé, il fallait défiler une liste dans une liste. La liste n'a plus de
 * défilement propre, et l'élément déplié est amené sous les yeux.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { SecurityStep } from './SecurityStep';

const origine = Element.prototype.scrollIntoView;

describe('étape Sécurité : un risque déplié reste visible (B-1344)', () => {
  beforeEach(() => {
    Element.prototype.scrollIntoView = vi.fn();
  });
  afterEach(() => {
    Element.prototype.scrollIntoView = origine;
  });

  it('la liste des risques ne défile pas dans l’assistant qui défile', () => {
    render(<SecurityStep provider="ollama" onNext={vi.fn()} onBack={vi.fn()} />);
    const boutons = screen.getAllByRole('button', { expanded: false });
    const liste = boutons[0].parentElement as HTMLElement;
    expect(liste.className).not.toMatch(/overflow-y-auto|max-h-/);
  });

  it('déplier le dernier risque l’amène sous les yeux', () => {
    render(<SecurityStep provider="ollama" onNext={vi.fn()} onBack={vi.fn()} />);
    const boutons = screen.getAllByRole('button', { expanded: false });
    const dernier = boutons[boutons.length - 1];
    fireEvent.click(dernier);
    expect(dernier).toHaveAttribute('aria-expanded', 'true');
    expect(vi.mocked(Element.prototype.scrollIntoView).mock.contexts).toContain(dernier);
  });
});
