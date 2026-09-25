/**
 * B-1427 (tri de la couverture écran P-145, décision du 25/09) : le pouce des
 * barres de défilement prenait `--color-border`, à 1,2:1 sur la surface en
 * clair et 1,4:1 en sombre : presque invisible. Un jeton `--color-defilement`
 * tient 3:1 (composant d'interface) sur chaque fond de chaque thème.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const CSS = readFileSync(join(__dirname, 'globals.css'), 'utf-8');

function hex(valeur: string): [number, number, number] {
  const h = valeur.replace('#', '');
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)) as [number, number, number];
}

function luminance([r, g, b]: [number, number, number]): number {
  const f = (x: number) => {
    const v = x / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}

function contraste(a: string, b: string): number {
  const [haut, bas] = [luminance(hex(a)), luminance(hex(b))].sort((x, y) => y - x);
  return (haut + 0.05) / (bas + 0.05);
}

/** Chaque bloc qui déclare le jeton, avec ses fonds. */
function blocsDuJeton(): Array<{ defilement: string; fonds: string[] }> {
  const blocs: Array<{ defilement: string; fonds: string[] }> = [];
  for (const m of CSS.matchAll(/--color-defilement:\s*(#[0-9A-Fa-f]{6})/g)) {
    const debut = CSS.lastIndexOf('{', m.index);
    const fin = CSS.indexOf('\n}', m.index);
    const bloc = CSS.slice(debut, fin);
    const fonds = [...bloc.matchAll(/--color-(?:bg|surface|surface-2):\s*(#[0-9A-Fa-f]{6})/g)].map((f) => f[1]);
    blocs.push({ defilement: m[1], fonds });
  }
  return blocs;
}

describe('B-1427 : les barres de défilement se voient', () => {
  it('le pouce utilise le jeton de défilement', () => {
    expect(CSS).toMatch(/::-webkit-scrollbar-thumb\s*\{[^}]*var\(--color-defilement\)/);
  });

  it('le jeton tient 3:1 sur chaque fond, dans chaque thème', () => {
    const blocs = blocsDuJeton();
    expect(blocs.length).toBeGreaterThanOrEqual(3); // clair, sombre, contraste élevé
    for (const { defilement, fonds } of blocs) {
      expect(fonds.length).toBeGreaterThan(0);
      for (const fond of fonds) {
        expect(contraste(defilement, fond), `${defilement} sur ${fond}`).toBeGreaterThanOrEqual(3);
      }
    }
  });
});
