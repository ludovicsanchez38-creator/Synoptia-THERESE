/**
 * Entrées 6 et 7 du plan du 28/08 : une touche morte et quatre-vingt-dix
 * puces d'infrastructure.
 *
 * Deux défauts du même genre : une capacité déjà payée qu'on n'atteint pas, et
 * une densité qui coûte sans rien apporter. La règle qui les sépare : on
 * retire ce qui n'aide personne, on branche ce qui aide déjà.
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

const RACINE = path.join(__dirname, '..');

function lire(relatif: string): string {
  return readFileSync(path.join(RACINE, relatif), 'utf8');
}

describe('Entrée 6 : ⌘O cesse d’être une touche morte', () => {
  it('la coque fournit enfin le geste que le raccourci appelle', () => {
    const coque = lire('components/prototype/ConversationCanvasPrototype.tsx');
    // Le gestionnaire a sa branche depuis toujours ; personne ne la remplissait.
    expect(coque).toMatch(/onOpenFile:\s*\(\)\s*=>/);
  });

  it('la fiche des raccourcis n’annonce plus un groupe vide', () => {
    const fiche = lire('components/chat/ShortcutsModal.tsx');
    // Si le groupe Fichiers est déclaré, il porte au moins un raccourci.
    const groupe = fiche.match(/Fichiers[\s\S]{0,400}/);
    if (groupe) expect(groupe[0]).toMatch(/⌘\s*\+?\s*O|Ctrl\s*\+\s*O/i);
  });
});

describe('Entrée 7 : le tiroir n’affiche plus ses puces d’infrastructure', () => {
  it('les puces ne sont plus rendues', () => {
    const tiroir = lire('components/prototype/CapabilityCenter.tsx');
    expect(tiroir).not.toMatch(/<FeaturePills/);
  });

  it('mais le champ reste, parce que la recherche s’en sert', () => {
    const tiroir = lire('components/prototype/CapabilityCenter.tsx');
    // Taper « imap » doit continuer de trouver la carte Messagerie.
    expect(tiroir).toContain('...item.features');
    expect(tiroir).toContain("features: ['IMAP/Gmail'");
  });
});
