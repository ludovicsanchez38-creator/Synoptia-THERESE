/**
 * DA « Application affinée », lot 1 (10/09/2026) : les primitives et la
 * coque ne connaissent que des jetons.
 *
 * Bornée à `components/ui/**` et au fichier de la coque : les couleurs de
 * marque des fournisseurs (`AdvisorCard`) et le SVG de `ChatHeader` sont
 * légitimes, un rouge dessus serait du bruit, pas une preuve.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const UI = resolve(__dirname);
const COQUE = resolve(__dirname, '../prototype/ConversationCanvasPrototype.tsx');

/** Chemins (relatifs à src/) tolérés, avec la raison. Vide au départ. */
const LISTE_BLANCHE: Record<string, string> = {
  // Bannière de mise à jour : seize `rgba` en styles inline hérités, avec
  // survol piloté en JS. C'est une couche, migrée avec les couches.
  'components/ui/UpdateBanner.tsx': 'couche, lot des couches de la DA',
};

function sources(): string[] {
  const fichiers = readdirSync(UI)
    .filter((f) => /\.tsx?$/.test(f) && !/\.test\.tsx?$/.test(f))
    .map((f) => join(UI, f));
  return [...fichiers, COQUE];
}

const court = (f: string) => f.slice(f.lastIndexOf('/src/') + 5);

describe('aucune couleur en dur dans les primitives ni la coque', () => {
  it('ni #rrggbb ni rgb()', () => {
    const fautifs: string[] = [];
    for (const f of sources()) {
      if (LISTE_BLANCHE[court(f)]) continue;
      const contenu = readFileSync(f, 'utf-8');
      contenu.split('\n').forEach((ligne, i) => {
        if (/#[0-9A-Fa-f]{6}\b|rgba?\(/.test(ligne)) fautifs.push(`${court(f)}:${i + 1}`);
      });
    }
    expect(fautifs).toEqual([]);
  });
});
