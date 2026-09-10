/**
 * Étiquette : pilule sémantique ou de domaine.
 *
 * Les fonds sont les teintes OPAQUES du projet (déjà AA sur la surface),
 * jamais un color-mix translucide. L'encre est le jeton sémantique.
 *
 * Le contraste élevé retire la teinte par une règle globale
 * `[data-high-contrast="true"] [data-etiquette]` (posée dans globals.css
 * par un autre lot). Ici on pose seulement `data-etiquette` : sans cet
 * attribut, la règle n'aurait rien à attraper.
 */
import { render, screen } from '@testing-library/react';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

import { Etiquette } from './Etiquette';

describe('Etiquette', () => {
  it('est un span pilule, avec data-etiquette pour le contraste élevé', () => {
    render(<Etiquette>En retard</Etiquette>);

    const pastille = screen.getByText('En retard');
    expect(pastille.tagName).toBe('SPAN');
    expect(pastille).toHaveAttribute('data-etiquette');
    expect(pastille.className).toMatch(/inline-flex/);
    expect(pastille.className).toMatch(/items-center/);
    expect(pastille.className).toMatch(/gap-1/);
    expect(pastille.className).toMatch(/rounded-full/);
    expect(pastille.className).toMatch(/px-2/);
    expect(pastille.className).toMatch(/py-0\.5/);
    expect(pastille.className).toMatch(/text-sm/);
    expect(pastille.className).toMatch(/font-semibold/);
    expect(pastille.className).toMatch(/whitespace-nowrap/);
  });

  it.each([
    ['erreur', 'bg-[var(--color-error-tint)]', 'text-error'],
    ['attention', 'bg-[var(--color-warning-tint)]', 'text-warning'],
    ['succes', 'bg-[var(--color-success-tint)]', 'text-success'],
    ['info', 'bg-[var(--color-info-tint)]', 'text-info'],
  ] as const)('ton %s : teinte opaque et encre sémantique', (ton, fond, encre) => {
    render(<Etiquette ton={ton}>{ton}</Etiquette>);
    const pastille = screen.getByText(ton);
    expect(pastille.className).toContain(fond);
    expect(pastille.className).toContain(encre);
  });

  it('ton neutre : surface-2 et texte muted', () => {
    render(<Etiquette ton="neutre">Brouillon</Etiquette>);
    const pastille = screen.getByText('Brouillon');
    expect(pastille.className).toMatch(/bg-surface-2/);
    expect(pastille.className).toMatch(/text-text-muted/);
  });

  it.each([
    ['agenda', 'bg-domaine-agenda-tint', 'text-domaine-agenda'],
    ['taches', 'bg-domaine-taches-tint', 'text-domaine-taches'],
    ['factures', 'bg-domaine-factures-tint', 'text-domaine-factures'],
    ['prospects', 'bg-domaine-prospects-tint', 'text-domaine-prospects'],
  ] as const)('domaine %s : teinte et encre de domaine', (domaine, fond, encre) => {
    render(<Etiquette domaine={domaine}>{domaine}</Etiquette>);
    const pastille = screen.getByText(domaine);
    expect(pastille.className).toContain(fond);
    expect(pastille.className).toContain(encre);
  });
});

/**
 * §8.5 du design : en contraste élevé, une étiquette abandonne sa teinte
 * pour une bordure d'encre. La règle vit dans globals.css, HORS couche
 * (dans `@layer base`, `bg-*-tint` gagnerait et la teinte resterait).
 */
describe('Etiquette : contraste élevé', () => {
  it('la règle [data-high-contrast] [data-etiquette] est posée hors couche', () => {
    const css = readFileSync(join(__dirname, '../../styles/globals.css'), 'utf-8');
    const horsCouche = css.replace(/@layer\s+\w+\s*\{[\s\S]*?\n\}/g, '');
    expect(horsCouche).toMatch(/\[data-high-contrast="true"\]\s*\[data-etiquette\]\s*\{[^}]*background:\s*transparent[^}]*border:\s*1px solid currentColor/s);
  });
});
