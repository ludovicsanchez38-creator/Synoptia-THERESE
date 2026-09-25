/**
 * B-1441 (recette P-146, lot 2, O6) : à la saisie au clavier, dnd-kit place
 * la carte au-dessus d'elle-même ; l'annonce disait « la carte de Thomas
 * Aubert est au-dessus de la carte de Thomas Aubert. », et un dépôt sur place
 * « Dépôt effectué : X, sur X ». Sur elle-même, la carte est à sa place.
 */
import { describe, expect, it } from 'vitest';

import { annoncesGlisserDeposer } from './accessibiliteGlisserDeposer';

const annonces = annoncesGlisserDeposer((id) => (id === 'c-1' ? 'la carte de Thomas Aubert' : 'la colonne Découverte'));
const carte = { id: 'c-1' } as never;

describe('B-1441 : une carte au-dessus d’elle-même est à sa place', () => {
  it('pendant le glisser', () => {
    expect(annonces.onDragOver?.({ active: carte, over: carte } as never)).toBe(
      'la carte de Thomas Aubert est à sa place de départ.',
    );
  });

  it('au dépôt', () => {
    expect(annonces.onDragEnd?.({ active: carte, over: carte } as never)).toBe(
      'la carte de Thomas Aubert reste à sa place.',
    );
  });

  it('au-dessus d’une autre zone, rien ne change', () => {
    expect(annonces.onDragOver?.({ active: carte, over: { id: 'discovery' } } as never)).toBe(
      'la carte de Thomas Aubert est au-dessus de la colonne Découverte.',
    );
  });
});
