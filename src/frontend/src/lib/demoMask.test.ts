import { beforeEach, describe, expect, it } from 'vitest';

import { buildReplacementMap, maskContact, maskText } from './demoMask';

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

describe('B-1075 (cycle 12) : une fiche sans prénom ni nom est masquée aussi', () => {
  const societe = { id: 'c-b2b', first_name: null, last_name: null, company: 'Rocher Menuiserie SARL', email: 'contact@rocher-menuiserie.fr', phone: '06 12 34 56 78' };

  it('maskContact remplace la société, l’adresse et le téléphone sans inventer de nom', () => {
    const masque = maskContact(societe);
    expect(masque.company).not.toBe(societe.company);
    expect(masque.email).not.toBe(societe.email);
    expect(masque.phone).not.toBe(societe.phone);
    expect(masque.first_name ?? null).toBeNull();
    expect(masque.last_name ?? null).toBeNull();
  });

  it('buildReplacementMap couvre la société et l’adresse d’une fiche sans nom', () => {
    const table = buildReplacementMap([societe], []);
    expect(table.has('Rocher Menuiserie SARL')).toBe(true);
    expect(table.has('contact@rocher-menuiserie.fr')).toBe(true);
  });

  it('une adresse seule suffit aussi', () => {
    const table = buildReplacementMap([{ first_name: null, last_name: null, company: null, email: 'solo@exemple.fr' }], []);
    expect(table.has('solo@exemple.fr')).toBe(true);
  });
});
