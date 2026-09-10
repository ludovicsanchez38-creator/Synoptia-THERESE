/**
 * Cycle 6, lecteur #203 (actionRegistry.ts) : la palette annonçait ⌘H pour
 * « Accueil » alors qu'aucune branche du gestionnaire de raccourcis ne traite
 * la touche h (et Cmd+H est pris par macOS). Ce test lit les deux sens : tout
 * raccourci lettre annoncé par le registre doit avoir sa branche dans
 * useKeyboardShortcuts.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

import { APP_ACTIONS } from './actionRegistry';

const source = readFileSync(resolve(__dirname, '../hooks/useKeyboardShortcuts.ts'), 'utf8');

describe('#203 : un raccourci annoncé est un raccourci traité', () => {
  const annonces = APP_ACTIONS.filter((a) => a.shortcut && /^⇧?[A-Z]$/.test(a.shortcut));

  it.each(annonces.map((a) => [a.id, a.shortcut as string]))('%s annonce %s : le gestionnaire a la branche', (_id, raccourci) => {
    const lettre = raccourci.replace('⇧', '').toLowerCase();
    const shift = raccourci.startsWith('⇧');
    const motif = shift
      ? new RegExp(`key === '${lettre}' && event\\.shiftKey`)
      : new RegExp(`key === '${lettre}'(?: && !event\\.shiftKey)?\\)`);
    expect(source).toMatch(motif);
  });
});
