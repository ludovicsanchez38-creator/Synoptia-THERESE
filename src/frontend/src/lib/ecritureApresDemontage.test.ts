/**
 * Le flush différé ne doit pas exploser quand le stockage a disparu.
 *
 * Trouvé par la CI de la release 0.54.0, pas par mes gates locaux : les 1075
 * tests PASSAIENT, et vitest sortait quand même en 1 sur
 *
 *   ReferenceError: localStorage is not defined
 *    ❯ Timeout.flush src/lib/debouncedStorage.ts:54
 *
 * Un `setTimeout` armé pendant un test se déclenche APRÈS la destruction de
 * l'environnement jsdom. C'est une course : elle dépend de la vitesse de la
 * machine, ce qui explique qu'elle ne se reproduise pas en local. Le build
 * des binaires a été sauté à cause d'elle.
 *
 * Deux leçons, la seconde plus coûteuse que la première :
 * - une écriture différée doit survivre à la disparition de sa cible ;
 * - « mes six gates locaux sont verts » ne veut pas dire « la CI est verte ».
 *   Le workflow Windows était rouge sur CHACUN de mes commits de la journée
 *   et je ne l'ai jamais regardé.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { __resetPersistenceForTests, createDebouncedStorage } from './debouncedStorage';

describe('Une écriture différée survit à la disparition du stockage', () => {
  const vrai = globalThis.localStorage;

  beforeEach(() => {
    __resetPersistenceForTests();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    Object.defineProperty(globalThis, 'localStorage', {
      value: vrai,
      configurable: true,
      writable: true,
    });
  });

  it("ne lève pas quand localStorage a disparu avant l'échéance", () => {
    const stockage = createDebouncedStorage(400);
    stockage.setItem('conversations', '[]');

    // L'environnement est démonté pendant que l'écriture attend.
    Object.defineProperty(globalThis, 'localStorage', {
      value: undefined,
      configurable: true,
      writable: true,
    });

    expect(() => vi.advanceTimersByTime(500)).not.toThrow();
  });

  it("n'avale pas une écriture quand le stockage est bien là", () => {
    // Le `localStorage` de l'environnement de test est un bouchon : `setItem`
    // existe mais ne conserve rien, et `getItem` rend `undefined`. Relire
    // après écriture ne prouverait donc rien - on vérifie l'APPEL, seul geste
    // réellement observable ici.
    const ecrire = vi.spyOn(globalThis.localStorage, 'setItem');
    const stockage = createDebouncedStorage(400);
    stockage.setItem('conversations', '[{"id":1}]');

    expect(ecrire).not.toHaveBeenCalled();
    vi.advanceTimersByTime(500);
    expect(ecrire).toHaveBeenCalledWith('conversations', '[{"id":1}]');
    ecrire.mockRestore();
  });

  it('une lecture ne lève pas non plus sans stockage', () => {
    const stockage = createDebouncedStorage(400);
    Object.defineProperty(globalThis, 'localStorage', {
      value: undefined,
      configurable: true,
      writable: true,
    });

    expect(() => stockage.getItem('conversations')).not.toThrow();
    expect(stockage.getItem('conversations')).toBeNull();
  });
});
