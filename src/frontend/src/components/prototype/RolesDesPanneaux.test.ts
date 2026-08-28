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


/**
 * Le canevas de contexte — le panneau que les cinq verbes ouvrent.
 *
 * Trouvé par la relecture du chantier E : `ContextCanvas` porte
 * `role="dialog"` avec `piegeClavier: false`. Un dialogue ARIA promet un focus
 * contenu, une page neutralisée et un Échap qui rend la main. Au-dessus du
 * seuil `xl`, où le panneau vit côte à côte avec la conversation, rien de tout
 * cela n'est vrai — et un lecteur d'écran annonce « dialogue ».
 *
 * La revue 0.49 avait corrigé ses six frères (liste ci-dessus). Celui-ci y a
 * échappé parce qu'il est une fonction interne de la coque, pas un fichier
 * `*Canvas.tsx` : la liste ne pouvait pas le voir. C'est la surface que tout le
 * monde ouvre.
 */
describe('Le canevas de contexte est une région, pas un dialogue', () => {
  const coque = readFileSync(
    path.join(__dirname, 'ConversationCanvasPrototype.tsx'),
    'utf8',
  );

  it('n’annonce pas un dialogue qu’il ne tient pas', () => {
    const ligneDuCanevas = coque
      .split('\n')
      .findIndex((l) => l.includes('aria-labelledby="prototype-context-canvas-title"'));
    expect(ligneDuCanevas).toBeGreaterThan(-1);

    // Le rôle est posé juste avant l'étiquette.
    const alentours = coque.split('\n').slice(ligneDuCanevas - 3, ligneDuCanevas + 1).join('\n');
    expect(alentours).not.toContain('role="dialog"');
    expect(alentours).toContain('role="region"');
  });
});
