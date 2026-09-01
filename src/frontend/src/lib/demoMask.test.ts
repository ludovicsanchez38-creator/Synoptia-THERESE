import { beforeEach, describe, expect, it } from 'vitest';

import { maskText } from './demoMask';

describe('maskText', () => {
  beforeEach(() => {
    // Le module garde en cache la regex compilée : chaque cas repart d'un
    // jeu de clés distinct pour ne pas hériter du précédent.
  });

  it('masque un nom qui commence ou finit par une lettre accentuée', () => {
    // Mesuré le 01/09/2026 : \b de JavaScript est ASCII. Devant « É », il n'y
    // a pas de frontière de mot, donc « Émilie Dupré » traversait le masque
    // intact pendant qu'un « Jean Martin » du même carnet était remplacé.
    // En démonstration client, c'est le vrai nom qui reste à l'écran.
    const remplacements = new Map([
      ['Émilie Dupré', 'Claire Fontaine'],
      ['Jean Martin', 'Paul Durand'],
    ]);

    expect(maskText('Jean Martin a signé', remplacements)).toBe('Paul Durand a signé');
    expect(maskText('Émilie Dupré a signé', remplacements)).toBe('Claire Fontaine a signé');
    expect(maskText('Relance de Émilie Dupré', remplacements)).toBe('Relance de Claire Fontaine');
  });

  it('ne masque pas un nom noyé dans un mot plus long', () => {
    const remplacements = new Map([['Martin', 'Durand']]);

    expect(maskText('Martinique', remplacements)).toBe('Martinique');
    expect(maskText('SuperMartin', remplacements)).toBe('SuperMartin');
    expect(maskText('Martin arrive', remplacements)).toBe('Durand arrive');
  });

  it('masque sans tenir compte de la casse', () => {
    const remplacements = new Map([['Léa Rossi', 'Anne Blanc']]);

    expect(maskText('LÉA ROSSI valide', remplacements)).toBe('Anne Blanc valide');
  });
});
