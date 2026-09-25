/**
 * B-1390 (persona Nathalie, cycle 13) : petites fautes de langue relevées en
 * chemin. Annonce « la carte de Élodie Martin … a été déposé » (élision et
 * accord), aide au vouvoiement dans une application qui tutoie.
 */
import { describe, expect, it } from 'vitest';
import { annoncesGlisserDeposer, laCarteDe } from './accessibiliteGlisserDeposer';

describe('B-1390 : annonces de glisser-déposer', () => {
  it('élide devant une voyelle : « la carte d’Élodie Martin »', () => {
    expect(laCarteDe('Élodie Martin')).toBe('la carte d’Élodie Martin');
    expect(laCarteDe('Hélène Ménard')).toBe('la carte d’Hélène Ménard');
    expect(laCarteDe('Karim Benali')).toBe('la carte de Karim Benali');
  });

  it('le dépôt s’annonce sans accord de genre fautif', () => {
    const annonces = annoncesGlisserDeposer((id) => (id === 'c1' ? 'la carte d’Élodie Martin' : 'la colonne Découverte'));
    const fin = annonces.onDragEnd!({ active: { id: 'c1' }, over: { id: 'discovery' } } as never);
    expect(fin).toBe('Dépôt effectué : la carte d’Élodie Martin, sur la colonne Découverte.');
    expect(fin).not.toMatch(/a été déposé /);
  });
});
