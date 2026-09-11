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

import { CHEMINS_LOT6 } from '../../test/fichiersLot6';

const UI = resolve(__dirname);
const COQUE = resolve(__dirname, '../prototype/ConversationCanvasPrototype.tsx');
// Lot 2 : la carte du brief consomme les primitives, donc les jetons.
const BRIEF = resolve(__dirname, '../prototype/TodayDashboardCard.tsx');
// Lot 3 : le tiroir des conversations, et le catalogue hors TrustCenter.
const TIROIR = resolve(__dirname, '../prototype/PrototypeConversationDrawer.tsx');
const CATALOGUE = resolve(__dirname, '../prototype/CapabilityCenter.tsx');
// Lot 6 : les six composants de l'écran Projets et tâches. La liste vit dans
// `src/test/fichiersLot6.ts` : la garde du plancher de taille
// (`src/test/lot6DA.test.ts`) parcourt exactement les mêmes fichiers.
const LOT6 = CHEMINS_LOT6;
// Lot 7 : l'écran Décision consomme les primitives, donc les jetons.
const DECISION = resolve(__dirname, '../prototype/BoardConversationCard.tsx');
// Lot 9 : les trois fichiers de la rubrique Parametres. C'est un CLIQUET, pas
// une preuve : verifie le 11/09, aucun des trois ne porte de hex, rgb(), hsl()
// ni color-mix() aujourd'hui. L'extension ne rougit donc pas avant le code,
// elle empeche une regression pendant le restyle -- et elle ne voit pas les
// classes Tailwind brutes, que seule la relecture attrape.
const LOT9 = [
  resolve(__dirname, '../settings/SettingsModal.tsx'),
  resolve(__dirname, '../settings/LLMTab.tsx'),
  resolve(__dirname, '../settings/ProfileTab.tsx'),
];

/** Chemins (relatifs à src/) tolérés, avec la raison. Vide au départ. */
const LISTE_BLANCHE: Record<string, string> = {
  // Bannière de mise à jour : seize `rgba` en styles inline hérités, avec
  // survol piloté en JS. C'est une couche, migrée avec les couches.
  'components/ui/UpdateBanner.tsx': 'couche, lot des couches de la DA',
};

function sources(): string[] {
  const fichiers = (readdirSync(UI, { recursive: true }) as string[])
    .filter((f) => /\.tsx?$/.test(f) && !/\.test\.tsx?$/.test(f))
    .map((f) => join(UI, f));
  return [...fichiers, COQUE, BRIEF, TIROIR, CATALOGUE, ...LOT6, DECISION, ...LOT9];
}

function contenuPourGarde(fichier: string): string {
  const contenu = readFileSync(fichier, 'utf-8');
  if (fichier !== CATALOGUE) return contenu;
  const debut = contenu.indexOf('export function CapabilityCenter');
  const fin = contenu.indexOf('\nfunction TrustRow', debut);
  return contenu.slice(debut, fin < 0 ? contenu.length : fin);
}

/** Hex de 3 à 8 chiffres, rgb/rgba, hsl/hsla, color-mix : tout ce qui n'est pas un jeton. */
// Lot 2 : `\b` ratait `shadow-[0_1px_rgba(...)]` (le `_` est un caractère de
// mot) ; on ancre sur « pas une lettre avant », ce qui garde `rgba(` dans
// une valeur arbitraire Tailwind.
const COULEUR_EN_DUR = /#[0-9A-Fa-f]{3,8}\b|(?<![A-Za-z])rgba?\(|(?<![A-Za-z])hsla?\(|\bcolor-mix\(/;
// Lot 6 : le motif ci-dessus ne voit NI `bg-black/60` (TasksPanel, overlay)
// NI `bg-gray-500/10` (TaskKanban, priorité basse) - ce sont des palettes
// Tailwind brutes, pas des notations de couleur. Sur les six fichiers du lot,
// on les refuse aussi : les voiles passent à `bg-text/35`.
const PALETTE_BRUTE = /\bbg-black\/|\bbg-gray-/;
const COMMENTAIRE = /^\s*(\/\/|\*|\/\*)/;

const court = (f: string) => f.slice(f.lastIndexOf('/src/') + 5);

describe('aucune couleur en dur dans les primitives ni la coque', () => {
  it('ni hex, ni rgb(), ni hsl(), ni color-mix()', () => {
    const fautifs: string[] = [];
    for (const f of sources()) {
      if (LISTE_BLANCHE[court(f)]) continue;
      const contenu = contenuPourGarde(f);
      contenu.split('\n').forEach((ligne, i) => {
        if (COMMENTAIRE.test(ligne)) return;
        if (COULEUR_EN_DUR.test(ligne)) fautifs.push(`${court(f)}:${i + 1}`);
      });
    }
    expect(fautifs).toEqual([]);
  });

  it('ni palette Tailwind brute sur l’écran Projets et tâches', () => {
    const fautifs: string[] = [];
    for (const f of LOT6) {
      readFileSync(f, 'utf-8').split('\n').forEach((ligne, i) => {
        if (COMMENTAIRE.test(ligne)) return;
        if (PALETTE_BRUTE.test(ligne)) fautifs.push(`${court(f)}:${i + 1}`);
      });
    }
    expect(fautifs).toEqual([]);
  });
});
