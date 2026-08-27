/**
 * Un panneau latéral n'est pas un dialogue - qu'il le dise.
 *
 * Le hotfix 0.48.1 a tranché : « un panneau qui laisse une partie de l'écran
 * interactive n'est JAMAIS une modale au sens ARIA » (le rail et l'en-tête
 * restent vivants par choix produit). Le comportement a suivi - plus de piège
 * clavier, plus d'aria-modal - mais quatre panneaux continuent d'annoncer
 * role="dialog" au lecteur d'écran.
 *
 * Un rôle « dialog » promet trois choses qu'aucun de ces panneaux ne tient :
 * le focus contenu, le reste de la page neutralisé, une sortie par Échap qui
 * rend la main au point de départ. L'annoncer, c'est envoyer quelqu'un qui ne
 * voit pas l'écran chercher une frontière qui n'existe pas.
 *
 * PrototypeUnifiedViewCanvas montre déjà la forme juste : role="region" avec
 * un nom accessible.
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

const PANNEAUX = [
  'VoiceWorkspaceCanvas',
  'ImagesWorkspaceCanvas',
  'DeliverablesWorkspaceCanvas',
  'FollowUpsWorkspaceCanvas',
  'CalculatorWorkspaceCanvas',
  'PrototypeUnifiedViewCanvas',
];

function source(nom: string): string {
  return readFileSync(path.join(__dirname, `${nom}.tsx`), 'utf8');
}

/** La ligne qui porte le conteneur du panneau (celui qui reçoit le ref du trap). */
function conteneur(code: string): string | undefined {
  return code
    .split('\n')
    .find((l) => l.includes('ref={dialogRef}') || l.includes('ref={conteneurRef}'));
}

describe('Le rôle annoncé par un panneau correspond à son comportement', () => {
  it.each(PANNEAUX)('%s ne se déclare pas dialogue', (nom) => {
    const code = source(nom);
    // Ne vaut que pour les panneaux non modaux ; un panneau qui piégerait
    // vraiment le clavier aurait droit à son rôle de dialogue.
    if (!code.includes('piegeClavier: false')) return;

    const ligne = conteneur(code);
    expect(ligne, `${nom} : conteneur du panneau introuvable`).toBeDefined();
    expect(ligne).not.toContain('role="dialog"');
  });

  it.each(PANNEAUX)('%s porte un rôle de repère et un nom accessible', (nom) => {
    const code = source(nom);
    if (!code.includes('piegeClavier: false')) return;

    const ligne = conteneur(code) ?? '';
    expect(ligne).toContain('role="region"');
    expect(ligne).toMatch(/aria-labelledby=|aria-label=/);
  });
});
