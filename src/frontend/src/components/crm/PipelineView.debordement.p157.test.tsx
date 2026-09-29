/**
 * P-157 : la grille défile en largeur. Quand des étapes restent hors cadre,
 * un fondu marque le bord et une mention (« 3 étapes à droite ») le dit,
 * y compris au lecteur d’écran. Un clic ou Entrée amène ces étapes.
 * jsdom ne mesure pas : le débordement est simulé sur la grille rendue.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { PipelineView } from './PipelineView';

afterEach(() => {
  _clearEscapeHandlers();
});

function grille(): HTMLElement {
  return screen.getByRole('region', { name: 'Étapes du pipeline' });
}

function simuler(
  zone: HTMLElement,
  { clientWidth, scrollLeft, largeur = 240, pas = 252 }: {
    clientWidth: number;
    scrollLeft: number;
    largeur?: number;
    pas?: number;
  },
) {
  const colonnes = Array.from(zone.querySelectorAll<HTMLElement>('[data-colonne]'));
  expect(colonnes).toHaveLength(8);
  colonnes.forEach((colonne, index) => {
    Object.defineProperty(colonne, 'offsetLeft', { configurable: true, value: index * pas });
    Object.defineProperty(colonne, 'offsetWidth', { configurable: true, value: largeur });
  });
  Object.defineProperty(zone, 'clientWidth', { configurable: true, value: clientWidth });
  zone.scrollLeft = scrollLeft;
}

function rendre() {
  render(<PipelineView contacts={[]} onContactClick={vi.fn()} onStageChange={vi.fn()} />);
  return grille();
}

describe('P-157 : indice de débordement du pipeline', () => {
  it('à 800 px, annonce les étapes à droite et fond ce bord', () => {
    const zone = rendre();
    simuler(zone, { clientWidth: 800, scrollLeft: 0 });
    fireEvent.scroll(zone);

    const mention = screen.getByRole('button', { name: '5 étapes à droite' });
    expect(mention).toHaveTextContent('5 étapes à droite');
    expect(mention.className).toMatch(/bg-surface/);
    expect(mention.className).not.toMatch(/gradient/);
    expect(screen.queryByRole('button', { name: /à gauche/ })).not.toBeInTheDocument();

    const fondu = document.querySelector<HTMLElement>('[data-fondu="droite"]');
    expect(fondu).not.toBeNull();
    expect(fondu).toHaveAttribute('aria-hidden', 'true');
    expect(fondu?.className).toMatch(/bg-gradient-to-l/);
    expect(fondu?.className).toMatch(/from-text\/15/);
    expect(fondu?.className).toMatch(/pointer-events-none/);
    expect(document.querySelector('[data-fondu="gauche"]')).toBeNull();
  });

  it('après défilement, annonce aussi les étapes restées à gauche', () => {
    const zone = rendre();
    simuler(zone, { clientWidth: 800, scrollLeft: 756 });
    fireEvent.scroll(zone);

    expect(screen.getByRole('button', { name: '3 étapes à gauche' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '2 étapes à droite' })).toBeInTheDocument();
    expect(document.querySelector('[data-fondu="gauche"]')).not.toBeNull();
    expect(document.querySelector('[data-fondu="droite"]')).not.toBeNull();
  });

  it('se met à jour quand le cadre change, et disparaît quand tout tient', () => {
    const zone = rendre();
    simuler(zone, { clientWidth: 800, scrollLeft: 0 });
    fireEvent.scroll(zone);
    expect(screen.getByRole('button', { name: '5 étapes à droite' })).toBeInTheDocument();

    simuler(zone, { clientWidth: 2100, scrollLeft: 0 });
    fireEvent(window, new Event('resize'));

    expect(screen.queryByRole('button', { name: /étape/ })).not.toBeInTheDocument();
    expect(document.querySelector('[data-fondu]')).toBeNull();
  });

  it('à 1440 px, aucun indice quand les huit étapes tiennent dans le cadre', () => {
    const zone = rendre();
    // Plus étroites que le minimum réel : le cas où 1 440 px suffit.
    simuler(zone, { clientWidth: 1440, scrollLeft: 0, largeur: 160, pas: 170 });
    fireEvent.scroll(zone);
    fireEvent(window, new Event('resize'));

    expect(screen.queryByRole('button', { name: /étape/ })).not.toBeInTheDocument();
    expect(document.querySelector('[data-fondu]')).toBeNull();
  });

  it('à 1440 px, l’indice reste si les colonnes de 15 rem dépassent encore', () => {
    const zone = rendre();
    simuler(zone, { clientWidth: 1440, scrollLeft: 0 });
    fireEvent.scroll(zone);

    expect(screen.getByRole('button', { name: '3 étapes à droite' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /à gauche/ })).not.toBeInTheDocument();
  });

  it('un clic sur la mention fait défiler vers les étapes cachées', () => {
    const zone = rendre();
    simuler(zone, { clientWidth: 800, scrollLeft: 0 });
    fireEvent.scroll(zone);
    const scrollTo = vi.fn();
    zone.scrollTo = scrollTo as unknown as typeof zone.scrollTo;

    fireEvent.click(screen.getByRole('button', { name: '5 étapes à droite' }));

    expect(scrollTo).toHaveBeenCalledWith({ left: 756, behavior: 'smooth' });
  });

  it('Entrée sur la mention de gauche fait défiler vers ces étapes', () => {
    const zone = rendre();
    simuler(zone, { clientWidth: 800, scrollLeft: 756 });
    fireEvent.scroll(zone);
    const scrollTo = vi.fn();
    zone.scrollTo = scrollTo as unknown as typeof zone.scrollTo;

    fireEvent.keyDown(screen.getByRole('button', { name: '3 étapes à gauche' }), { key: 'Enter' });

    expect(scrollTo).toHaveBeenCalledWith({ left: 504, behavior: 'smooth' });
  });
});
