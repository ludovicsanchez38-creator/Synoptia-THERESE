/**
 * Sur une installation neuve, l'établi de l'accueil ne propose pas Facturer.
 *
 * La règle vit dans `actionsDeLEtabli`, testée à part. Ce test-ci vérifie
 * qu'elle est BRANCHÉE : une fonction parfaite que la coque n'appelle pas ne
 * change rien à ce que voit le persona 08.
 *
 * C'est la leçon la plus chère de la campagne : « un champ JSON que l'UI
 * n'affiche pas, c'est POST qui jetait l'adresse - même geste. »
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

import { ACTIONS_ETABLI } from '../../lib/etabli';
import { actionsDeLEtabli } from '../../lib/etabliDePremierLancement';

const COQUE = readFileSync(
  join(__dirname, 'ConversationCanvasPrototype.tsx'),
  'utf-8',
)
  .replace(/\{\/\*[\s\S]*?\*\/\}/g, '')
  .replace(/\/\*[\s\S]*?\*\//g, '')
  .replace(/^\s*\/\/.*$/gm, '');

describe("La règle est branchée dans l'accueil", () => {
  it("l'établi rend la liste FILTRÉE, pas la table brute", () => {
    expect(COQUE).toContain('actionsVisibles.map');
    expect(COQUE).not.toMatch(/\{ACTIONS_ETABLI\.map\(\(action\) => \(/);
  });

  it('la liste filtrée dérive du statut d’installation', () => {
    expect(COQUE).toContain('actionsDeLEtabli({');
    expect(COQUE).toContain('setupStatus.has_invoices');
    expect(COQUE).toContain('setupStatus.billing_complete');
  });

  it('la palette de commandes garde tous les verbes', () => {
    // Masquer un verbe de l'établi ne doit RETIRER aucune capacité : la
    // palette reste la porte de secours, et elle liste la table brute.
    expect(COQUE).toContain('ACTIONS_ETABLI.map((action, optionIndex)');
  });

  it('rien n’est masqué tant que le statut n’est pas lu', () => {
    expect(COQUE).toContain('setupStatus === null');
  });

  it('la règle elle-même masque bien Facturer sur une installation vide', () => {
    const visibles = actionsDeLEtabli({
      auMoinsUneFacture: false,
      infosSocieteCompletes: false,
    });
    expect(visibles.length).toBe(ACTIONS_ETABLI.length - 1);
    expect(visibles.map((a) => a.id)).not.toContain('invoice');
  });
});
