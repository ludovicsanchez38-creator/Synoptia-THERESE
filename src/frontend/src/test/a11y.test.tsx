/**
 * US-013 : scan axe-core automatisé sur les composants clés.
 *
 * jsdom ne calcule pas les styles en cascade, donc les règles de CONTRASTE
 * sont vérifiées séparément (calcul direct sur les tokens du design system).
 * axe couvre ici : ARIA (roles, labels), structure des dialogues, boutons.
 */
import { render } from '@testing-library/react';
import { axe } from 'vitest-axe';
import { describe, expect, it } from 'vitest';
import { DialogShell } from '../components/ui/DialogShell';
import { SetupChecklist } from '../components/home/SetupChecklist';

// ---------------------------------------------------------------------------
// Contraste WCAG : calcul direct (jsdom n'applique pas les feuilles de style)
// ---------------------------------------------------------------------------

function luminance(hex: string): number {
  const v = hex.replace('#', '');
  const [r, g, b] = [0, 2, 4].map((i) => {
    const c = parseInt(v.slice(i, i + 2), 16) / 255;
    return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(fg: string, bg: string): number {
  const [l1, l2] = [luminance(fg), luminance(bg)].sort((a, b) => b - a);
  return (l1 + 0.05) / (l2 + 0.05);
}

// Revue adversariale US-013 : lire les VRAIES valeurs de globals.css (un test
// sur des constantes copiées ne détecte aucune régression de la feuille de
// style réelle). Échoue si un token attendu disparaît.
// fs direct : l'import Vite ?raw est intercepté par le pipeline CSS de vitest,
// et import.meta.url n'est pas file:// sous vitest -> chemin depuis le cwd
// (vitest tourne toujours depuis src/frontend).
import { readdirSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const CSS = readFileSync(resolve(process.cwd(), 'src/styles/globals.css'), 'utf-8');

function extractBlock(startMarker: string): string {
  const start = CSS.indexOf(startMarker);
  if (start === -1) throw new Error(`Bloc introuvable dans globals.css : ${startMarker}`);
  const open = CSS.indexOf('{', start);
  let depth = 1;
  let i = open + 1;
  while (depth > 0 && i < CSS.length) {
    if (CSS[i] === '{') depth++;
    if (CSS[i] === '}') depth--;
    i++;
  }
  return CSS.slice(open + 1, i - 1);
}

function tokens(block: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const m of block.matchAll(/--color-([a-z0-9-]+)\s*:\s*(#[0-9A-Fa-f]{6})\s*;/g)) {
    out[m[1]] = m[2];
  }
  return out;
}

const LIGHT = tokens(extractBlock('@theme'));
const LIGHT_ROOT = tokens(extractBlock(':root'));
const LIGHT_ALL = { ...LIGHT, ...LIGHT_ROOT };
const DARK = { ...LIGHT_ALL, ...tokens(extractBlock('[data-theme="dark"]')) };
const HIGH_CONTRAST = { ...DARK, ...tokens(extractBlock('[data-high-contrast="true"]')) };

const SEMANTIC_NAMES = ['success', 'warning', 'error', 'info'] as const;
for (const name of SEMANTIC_NAMES) {
  if (!LIGHT[name] || !DARK[name]) {
    throw new Error(`Token sémantique --color-${name} absent d'un des thèmes`);
  }
}

const LIGHT_BG = LIGHT['bg'];
const LIGHT_SURFACE = LIGHT['surface'];
const DARK_BG = DARK['bg'];
const DARK_SURFACE = DARK['surface'];

const LIGHT_SEMANTIC = Object.fromEntries(SEMANTIC_NAMES.map((n) => [n, LIGHT[n]]));
const DARK_SEMANTIC = Object.fromEntries(SEMANTIC_NAMES.map((n) => [n, DARK[n]]));
const HIGH_CONTRAST_SEMANTIC = Object.fromEntries(SEMANTIC_NAMES.map((n) => [n, HIGH_CONTRAST[n]]));

describe('US-013 : contraste AA des tokens sémantiques', () => {
  it.each(Object.entries(LIGHT_SEMANTIC))(
    'thème clair : %s lisible sur fond et surface (>= 4.5:1)',
    (_name, color) => {
      expect(contrast(color, LIGHT_BG)).toBeGreaterThanOrEqual(4.5);
      expect(contrast(color, LIGHT_SURFACE)).toBeGreaterThanOrEqual(4.5);
    }
  );

  it.each(Object.entries(DARK_SEMANTIC))(
    'thème sombre : %s lisible sur fond et surface (>= 4.5:1)',
    (_name, color) => {
      expect(contrast(color, DARK_BG)).toBeGreaterThanOrEqual(4.5);
      expect(contrast(color, DARK_SURFACE)).toBeGreaterThanOrEqual(4.5);
    }
  );

  it.each(Object.entries(HIGH_CONTRAST_SEMANTIC))(
    'contraste élevé : %s lisible sur fond et surface (>= 4.5:1)',
    (_name, color) => {
      expect(contrast(color, HIGH_CONTRAST['bg'])).toBeGreaterThanOrEqual(4.5);
      expect(contrast(color, HIGH_CONTRAST['surface'])).toBeGreaterThanOrEqual(4.5);
    }
  );

  it('texte principal lisible dans les deux thèmes', () => {
    expect(contrast(LIGHT['text'], LIGHT_BG)).toBeGreaterThanOrEqual(7);
    expect(contrast(DARK['text'], DARK_BG)).toBeGreaterThanOrEqual(7);
  });

  it('texte secondaire AA en clair, sombre et contraste élevé', () => {
    expect(contrast(LIGHT_ALL['text-muted'], LIGHT_BG)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(DARK['text-muted'], DARK_BG)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(HIGH_CONTRAST['text-muted'], HIGH_CONTRAST['bg'])).toBeGreaterThanOrEqual(4.5);
  });

  it.each(SEMANTIC_NAMES)('les boutons %s gardent un contraste texte/fond >= 4.5:1 dans chaque thème', (name) => {
    for (const theme of [LIGHT_ALL, DARK, HIGH_CONTRAST]) {
      expect(theme[`${name}-fill`]).toBeTruthy();
      expect(theme[`${name}-ink`]).toBeTruthy();
      expect(contrast(theme[`${name}-ink`], theme[`${name}-fill`])).toBeGreaterThanOrEqual(4.5);
    }
  });

  it.each(SEMANTIC_NAMES)('le texte %s reste AA sur sa teinte claire', (name) => {
    expect(LIGHT_ALL[`${name}-tint`]).toBeTruthy();
    expect(contrast(LIGHT_ALL[name], LIGHT_ALL[`${name}-tint`])).toBeGreaterThanOrEqual(4.5);
  });
});

// ---------------------------------------------------------------------------
// Scan axe sur les composants
// ---------------------------------------------------------------------------

describe('US-013 : axe sans violation', () => {
  it('DialogShell : dialogue conforme (role, aria-modal, label)', async () => {
    const { container } = render(
      <DialogShell open onClose={() => {}} ariaLabel="Dialogue de test">
        <div>
          <h2>Titre</h2>
          <button>Valider</button>
          <button>Annuler</button>
        </div>
      </DialogShell>
    );
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });

  it('SetupChecklist : boutons nommés, structure saine', async () => {
    const { container } = render(
      <SetupChecklist
        status={{
          has_calendar: false,
          has_email: false,
          billing_complete: false, has_invoices: false,
          has_llm_key: false, indisponibles: [],
        }}
      />
    );
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });
});

/* ============================================================
   Lot 1 du plan de cohérence graphique (30/08/2026).

   Le bloc ci-dessus protège les jetons sémantiques. Il ne regardait pas les
   accents : le cyan de marque #22D3EE servait de couleur de TEXTE dans 242
   endroits, à 1,67:1 sur le thème clair. Un test qui donne une assurance
   partielle donne une assurance fausse.

   Distinction posée : --color-accent-cyan reste la couleur de REMPLISSAGE de
   la marque (boutons, bordures, dégradés) ; --color-accent-cyan-ink est sa
   déclinaison lisible, la seule autorisée pour du texte.
   ============================================================ */

const FICHIERS_SOURCE: string[] = [];
(function collecter(dossier: string) {
  for (const e of readdirSync(dossier, { withFileTypes: true })) {
    const chemin = resolve(dossier, e.name);
    if (e.isDirectory()) collecter(chemin);
    else if (/\.tsx?$/.test(e.name)) FICHIERS_SOURCE.push(chemin);
  }
})(resolve(process.cwd(), 'src'));

describe('lot 1 : les accents lisibles', () => {
  const ENCRES = ['accent-cyan-ink', 'accent-magenta-ink'] as const;

  it.each(ENCRES)('%s passe AA en thème clair', (nom) => {
    const c = LIGHT_ALL[nom];
    expect(c, `jeton --color-${nom} absent`).toBeTruthy();
    expect(contrast(c, LIGHT_BG)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(c, LIGHT_SURFACE)).toBeGreaterThanOrEqual(4.5);
  });

  it.each(ENCRES)('%s passe AA en thème sombre', (nom) => {
    const c = DARK[nom];
    expect(c, `jeton --color-${nom} absent du thème sombre`).toBeTruthy();
    expect(contrast(c, DARK_BG)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(c, DARK_SURFACE)).toBeGreaterThanOrEqual(4.5);
  });

  it("l'anneau de focus atteint le seuil UI de 3:1 dans les deux thèmes", () => {
    // Un anneau invisible est une navigation au clavier impossible.
    expect(contrast(LIGHT_ALL['ring'], LIGHT_BG)).toBeGreaterThanOrEqual(3);
    expect(contrast(LIGHT_ALL['ring'], LIGHT_SURFACE)).toBeGreaterThanOrEqual(3);
    expect(contrast(DARK['ring'], DARK_BG)).toBeGreaterThanOrEqual(3);
    expect(contrast(DARK['ring'], DARK_SURFACE)).toBeGreaterThanOrEqual(3);
  });

  it("aucune source n'utilise la couleur de remplissage comme couleur de texte", () => {
    const fautifs: string[] = [];
    for (const f of FICHIERS_SOURCE) {
      const contenu = readFileSync(f, 'utf-8');
      for (const m of contenu.matchAll(/text-accent-(cyan|magenta|violet)(?!-ink)/g)) {
        fautifs.push(`${f.slice(f.lastIndexOf('/src/') + 5)} : ${m[0]}`);
      }
    }
    expect(fautifs, `${fautifs.length} usages, ex. ${fautifs.slice(0, 3).join(' | ')}`).toEqual([]);
  });

  it('la sélection de texte garde l’encre du thème', () => {
    // L'ancienne paire mettait la couleur du FOND en texte sur le cyan plein :
    // 1,67:1, une sélection qu'on ne voyait pas.
    const bloc = CSS.slice(CSS.indexOf('::selection'), CSS.indexOf('::selection') + 500);
    expect(bloc).toContain('color: var(--color-text)');
    expect(bloc).not.toContain('color: var(--color-bg)');
  });

  it("aucune couleur de texte du thème sombre n'est forcée en dur", () => {
    // #E6EDF7 est l'encre du thème SOMBRE. Forcée en couleur de texte sur une
    // surface blanche, elle donne 1,18:1. Introduite en mars 2026, elle avait
    // survécu à la refonte de mai.
    // Le motif vise la COULEUR DE TEXTE : un remplissage SVG ou la table de
    // référence du thème sombre (lib/accessibility.ts) sont légitimes.
    const fautifs: string[] = [];
    for (const f of FICHIERS_SOURCE) {
      if (/\.test\.tsx?$/.test(f)) continue;
      if (/color:\s*["']#E6EDF7["']/i.test(readFileSync(f, 'utf-8'))) {
        fautifs.push(f.slice(f.lastIndexOf('/src/') + 5));
      }
    }
    expect(fautifs, `encre sombre forcée dans : ${fautifs.join(', ')}`).toEqual([]);
  });
});
