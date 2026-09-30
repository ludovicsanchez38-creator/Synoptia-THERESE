/**
 * P-157 : la grille défile en largeur. Quand des étapes restent hors cadre,
 * un fondu marque le bord et une mention (« 3 étapes à droite ») le dit,
 * y compris au lecteur d’écran. Un clic ou Entrée amène ces étapes.
 * jsdom ne mesure pas : le débordement est simulé sur la grille rendue.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
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

  it('à 1440 px, la géométrie réelle laisse des étapes hors cadre, et l’indice disparaît dès que la grille les contient', () => {
    const zone = rendre();
    // Le minimum réel est dans la grille : 15 rem et la gouttière gap-3.
    // Des colonnes de 160 px ne peuvent pas se produire ici.
    expect(zone.className).toContain('auto-cols-[minmax(15rem,1fr)]');
    expect(zone.className).toContain('gap-3');
    const largeur = 15 * 16;
    const pas = largeur + 0.75 * 16;
    simuler(zone, { clientWidth: 1440, scrollLeft: 0, largeur, pas });
    fireEvent.scroll(zone);

    expect(screen.getByRole('button', { name: '3 étapes à droite' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /à gauche/ })).not.toBeInTheDocument();

    const largeurSuffisante = 7 * pas + largeur;
    expect(largeurSuffisante).toBeGreaterThan(1440);
    simuler(zone, { clientWidth: largeurSuffisante, scrollLeft: 0, largeur, pas });
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

  it('le bouton à droite avance quand la première colonne dépasse le cadre', () => {
    const zone = rendre();
    simuler(zone, { clientWidth: 200, scrollLeft: 0, largeur: 240, pas: 252 });
    fireEvent.scroll(zone);
    const scrollTo = vi.fn();
    zone.scrollTo = scrollTo as unknown as typeof zone.scrollTo;

    fireEvent.click(screen.getByRole('button', { name: '8 étapes à droite' }));

    expect(scrollTo).toHaveBeenCalledWith({ left: 40, behavior: 'smooth' });
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

  it.each([
    { cote: 'droite', depart: 1008, arrivee: 1204 },
    { cote: 'gauche', depart: 252, arrivee: 0 },
  ])('au bord $cote, la grille reprend le focus du bouton qui disparaît', ({ cote, depart, arrivee }) => {
    const zone = rendre();
    simuler(zone, { clientWidth: 800, scrollLeft: depart });
    fireEvent.scroll(zone);
    zone.scrollTo = vi.fn();
    const bouton = screen.getByRole('button', { name: `1 étape à ${cote}` });
    act(() => { bouton.focus(); });
    expect(bouton).toHaveFocus();

    fireEvent.keyDown(bouton, { key: 'Enter' });
    expect(zone.scrollTo).toHaveBeenCalledOnce();
    // Le navigateur borne le défilement à la largeur réellement disponible.
    // jsdom ne défile pas : on reproduit la mesure de sa fin de parcours.
    simuler(zone, { clientWidth: 800, scrollLeft: arrivee });
    fireEvent.scroll(zone);

    expect(bouton).not.toBeInTheDocument();
    expect(zone).toHaveFocus();
  });

  it('garde le focus sur l’indice tant que le défilement ne l’a pas retiré', () => {
    const zone = rendre();
    simuler(zone, { clientWidth: 800, scrollLeft: 0 });
    fireEvent.scroll(zone);
    const bouton = screen.getByRole('button', { name: '5 étapes à droite' });
    act(() => { bouton.focus(); });

    simuler(zone, { clientWidth: 800, scrollLeft: 756 });
    fireEvent.scroll(zone);

    expect(bouton).toHaveFocus();
    expect(bouton).toHaveAccessibleName('2 étapes à droite');
  });

  it('rend le focus à la grille quand un redimensionnement retire l’indice focalisé', () => {
    const zone = rendre();
    simuler(zone, { clientWidth: 800, scrollLeft: 0 });
    fireEvent.scroll(zone);
    const bouton = screen.getByRole('button', { name: '5 étapes à droite' });
    act(() => { bouton.focus(); });

    simuler(zone, { clientWidth: 2100, scrollLeft: 0 });
    fireEvent(window, new Event('resize'));

    expect(bouton).not.toBeInTheDocument();
    expect(zone).toHaveFocus();
  });

  it('préserve le focus déplacé sur l’autre indice avant d’atteindre le bord', () => {
    const zone = rendre();
    simuler(zone, { clientWidth: 800, scrollLeft: 1008 });
    fireEvent.scroll(zone);
    const autreBouton = screen.getByRole('button', { name: '4 étapes à gauche' });
    act(() => { autreBouton.focus(); });

    simuler(zone, { clientWidth: 800, scrollLeft: 1204 });
    fireEvent.scroll(zone);

    expect(screen.queryByRole('button', { name: /à droite/ })).not.toBeInTheDocument();
    expect(autreBouton).toHaveFocus();
    expect(zone).not.toHaveFocus();
  });
});
