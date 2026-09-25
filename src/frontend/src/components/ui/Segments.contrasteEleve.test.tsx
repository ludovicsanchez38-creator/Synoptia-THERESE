/**
 * B-1404 (persona Zoé, cycle 13) : en contraste élevé, le filtre choisi et
 * les autres ne se distinguaient plus (texte #FFFFFF contre #E0E0E0, 1,32:1 ;
 * fond #0A0A0A contre noir, 1,06:1 ; même graisse), très en dessous des 3:1
 * de WCAG 1.4.11 pour l'état d'un composant. L'état choisi s'inverse : fond
 * blanc, encre noire, en gras (21:1 entre les deux états).
 *
 * La règle vit dans globals.css, hors couche (une utilitaire en couche ne
 * doit pas pouvoir la battre) : le test l'applique à un vrai rendu.
 */
import { render, screen } from '@testing-library/react';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';

import { Segments } from './Segments';

function reglesHorsCouche(): string {
  const css = readFileSync(join(__dirname, '../../styles/globals.css'), 'utf-8');
  return css
    .replace(/@layer\s+[\w-]+\s*\{[\s\S]*?\n\}/g, '')
    .replace(/@(theme|custom-variant|import|plugin|source)[^;{]*(\{[\s\S]*?\n\}|;)/g, '')
    .match(/\[data-high-contrast="true"\][^{]*\{[^}]*\}/g)!
    .join('\n');
}

let feuille: HTMLStyleElement | null = null;
afterEach(() => {
  feuille?.remove();
  feuille = null;
});

function rendreEnContrasteEleve() {
  feuille = document.createElement('style');
  feuille.textContent = reglesHorsCouche();
  document.head.appendChild(feuille);
  render(
    <div data-high-contrast="true">
      <Segments label="Type" valeur="devis" onChange={() => {}} options={[{ id: 'devis', label: 'Devis' }, { id: 'facture', label: 'Facture' }]} />
    </div>,
  );
}

describe('B-1404 : l’état choisi se voit en contraste élevé', () => {
  it('le segment choisi est inversé : fond blanc, encre noire, gras', () => {
    rendreEnContrasteEleve();
    const choisi = getComputedStyle(screen.getByRole('button', { name: 'Devis' }));

    expect(choisi.backgroundColor).toBe('rgb(255, 255, 255)');
    expect(choisi.color).toBe('rgb(0, 0, 0)');
    expect(choisi.fontWeight).toBe('700');
  });

  it('les autres segments ne prennent pas l’inversion', () => {
    rendreEnContrasteEleve();
    const autre = getComputedStyle(screen.getByRole('button', { name: 'Facture' }));

    expect(autre.backgroundColor).not.toBe('rgb(255, 255, 255)');
    expect(autre.fontWeight).not.toBe('700');
  });
});
