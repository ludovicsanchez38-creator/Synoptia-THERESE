/**
 * B-768 (cycle 9) : chaque risque replié portait un aria-controls vers un
 * identifiant absent du DOM (le détail n'était rendu que déplié), et le détail
 * déplié était un <p> à l'intérieur d'un <button>, ce que HTML interdit.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { SecurityStep } from './SecurityStep';

describe('SecurityStep - B-768, les risques sont des disclosures valides', () => {
  it('aucun aria-controls ne pointe vers un élément absent, replié comme déplié', () => {
    const { container } = render(<SecurityStep provider="openai" onNext={vi.fn()} onBack={vi.fn()} />);
    const verifier = () => {
      for (const el of container.querySelectorAll('[aria-controls]')) {
        const cible = el.getAttribute('aria-controls')!;
        expect(document.getElementById(cible), `aria-controls="${cible}" sans cible`).not.toBeNull();
      }
    };
    verifier();
    const premier = screen.getAllByRole('button', { expanded: false })[0];
    fireEvent.click(premier);
    expect(premier).toHaveAttribute('aria-expanded', 'true');
    verifier();
  });

  it('un bouton de risque ne contient jamais de paragraphe', () => {
    const { container } = render(<SecurityStep provider="openai" onNext={vi.fn()} onBack={vi.fn()} />);
    fireEvent.click(screen.getAllByRole('button', { expanded: false })[0]);
    expect(container.querySelector('button p')).toBeNull();
  });
});
