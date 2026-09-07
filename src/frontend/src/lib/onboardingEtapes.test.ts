import { describe, expect, it } from 'vitest';

import { etatDeLEtape } from './onboardingEtapes';

describe('etatDeLEtape (B-612)', () => {
  it('distingue une étape faite d’une étape passée', () => {
    expect(etatDeLEtape(1, 4, [2])).toBe('faite');
    expect(etatDeLEtape(2, 4, [2])).toBe('passee');
    expect(etatDeLEtape(4, 4, [2])).toBe('courante');
    expect(etatDeLEtape(5, 4, [2])).toBe('a-venir');
  });
});

import { doitEffacerLeChoixDeServiceIa } from './onboardingEtapes';

describe('doitEffacerLeChoixDeServiceIa (B-607)', () => {
  it('efface quand un fournisseur avait été enregistré et que l’on passe plus tard', () => {
    expect(doitEffacerLeChoixDeServiceIa('ollama', null)).toBe(true);
  });
  it('ne touche à rien sans enregistrement préalable, ni quand un fournisseur est choisi', () => {
    expect(doitEffacerLeChoixDeServiceIa(null, null)).toBe(false);
    expect(doitEffacerLeChoixDeServiceIa('ollama', 'anthropic')).toBe(false);
    expect(doitEffacerLeChoixDeServiceIa(null, 'ollama')).toBe(false);
  });
});
