/**
 * Chantier A-texte : la pastille de l'onglet Avancé annonçait « Données 100%
 * locales ».
 *
 * Le stockage métier l'est ; le reste ne l'est pas (comptes raccordés,
 * recherche web, vérification de mise à jour). Un absolu de plus, dans une
 * application dont trois personas sont partis à cause de ses absolus.
 *
 * Même réserve que pour la pastille du chat : test de source, faute de pouvoir
 * monter l'onglet sans ses appels réseau.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const source = readFileSync(join(__dirname, 'AdvancedTab.tsx'), 'utf-8')
  .replace(/\/\*[\s\S]*?\*\//g, '')
  .replace(/^\s*\/\/.*$/gm, '');

describe('La pastille de l’onglet Avancé ne dit plus « 100% locales »', () => {
  it('n’annonce plus un absolu', () => {
    expect(source).not.toMatch(/Données 100% locales/);
  });

  it('dit où sont les données, sans promettre ce qui sort', () => {
    expect(source).toMatch(/Stockées sur cette machine/);
  });
});
