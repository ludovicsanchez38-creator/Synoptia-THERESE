/**
 * B-112 : deux raccourcis fournis à un hook qui ne les appelle jamais.
 *
 * `ShortcutHandlers` déclarait `onNewContact` et `onNewProject`, la coque les
 * remplissait consciencieusement (ConversationCanvasPrototype), et le corps du
 * hook ne les invoquait nulle part : aucune touche ne pouvait les atteindre.
 * Un créneau déclaré est une promesse faite à celui qui branche le hook ; ici
 * elle était vide, et rien ne le disait.
 *
 * Le pendant existe déjà pour l'autre sens : ShortcutsModal.verite.test.tsx
 * vérifie qu'un raccourci ANNONCÉ a bien un gestionnaire. Celui-ci ferme la
 * réciproque : un créneau OFFERT doit être appelé. C'est d'ailleurs le même
 * arbitrage qu'en août, quand « ⌘⇧P Nouveau projet » a été retiré de la fiche
 * d'aide plutôt qu'implémenté.
 */
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const ici = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(resolve(ici, 'useKeyboardShortcuts.ts'), 'utf-8');

/** Les créneaux déclarés par l'interface `ShortcutHandlers`. */
function creneauxDeclares(): string[] {
  const debut = source.indexOf('interface ShortcutHandlers');
  expect(debut, 'interface ShortcutHandlers introuvable').toBeGreaterThan(-1);
  const fin = source.indexOf('}', debut);
  const corps = source.slice(debut, fin);
  return [...corps.matchAll(/^\s*(on[A-Za-z]+)\??:/gm)].map((m) => m[1]);
}

describe('B-112 - tout créneau de raccourci déclaré est réellement appelé', () => {
  const creneaux = creneauxDeclares();

  it("lit bien l'interface du hook", () => {
    expect(creneaux.length).toBeGreaterThan(15);
    expect(creneaux).toContain('onCommandPalette');
  });

  it.each(creneaux)('« %s » est invoqué par le hook', (creneau) => {
    expect(
      source.includes(`handlers.${creneau}?.`) ||
        source.includes(`handlers.${creneau}(`),
      `« ${creneau} » est déclaré par ShortcutHandlers mais le corps du hook ` +
        `ne l'appelle jamais : la coque le fournit pour rien, aucune touche ` +
        `ne peut le déclencher`,
    ).toBe(true);
  });
});
