/**
 * B-1396 (persona Zoé, cycle 13) : à 200 % (720×450), l'Atelier gardait ses
 * trois colonnes côte à côte, trame et Pistes à 288 px chacune : l'éditeur
 * tombait à 131 px et le bouton « Replier le volet Pistes » dépassait du
 * cadre (5 px visibles). Dans une fenêtre étroite, le volet Pistes s'ouvre
 * replié (48 px) ; la trame passe à 224 px sous 1 280 px. L'éditeur garde
 * ~390 px à 720 px, mesurés dans Chrome.
 */
import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { PistesPanel } from './PistesPanel';

function fenetre(etroite: boolean) {
  vi.mocked(window.matchMedia).mockImplementation((requete: string) => ({
    matches: etroite && requete.includes('max-width: 1023px'),
    media: requete,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }) as unknown as MediaQueryList);
}

afterEach(() => fenetre(false));

describe('B-1396 : l’Atelier laisse la place d’écrire dans une fenêtre étroite', () => {
  it('fenêtre étroite : le volet Pistes s’ouvre replié', () => {
    fenetre(true);
    render(<PistesPanel pistes={[]} onExplore={vi.fn()} onIgnore={vi.fn()} />);

    expect(screen.getByTestId('pistes-panel-collapsed')).toBeInTheDocument();
    expect(screen.queryByTestId('pistes-panel')).toBeNull();
  });

  it('fenêtre large : le volet reste ouvert, comme avant', () => {
    fenetre(false);
    render(<PistesPanel pistes={[]} onExplore={vi.fn()} onIgnore={vi.fn()} />);

    expect(screen.getByTestId('pistes-panel')).toBeInTheDocument();
  });
});
