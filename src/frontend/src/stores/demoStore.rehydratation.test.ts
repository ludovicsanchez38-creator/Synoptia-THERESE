/**
 * B-145 : au rechargement, le mode démo s'annonçait actif sans rien masquer.
 *
 * `partialize` ne rend que le drapeau `enabled` ; la table de remplacement,
 * elle, repart vide à la construction du store. Après un rechargement de
 * l'application, le badge affichait donc « mode démo » pendant que
 * « Point avec Marie Exemple chez Fictif Conseil » ressortait tel quel dans le
 * texte libre — `maskText` est l'identité tant que la table est vide. Le
 * correctif du 01/09 n'avait armé que `toggle` et `setEnabled`, jamais la
 * rehydratation.
 *
 * Deux ordres doivent être couverts, et c'est tout l'enjeu : à un vrai
 * rechargement, la rehydratation précède le chargement des contacts, si bien
 * qu'un simple `onRehydrateStorage` construirait une table vide.
 */
import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { installLocalStorageStub } from '../test/localStorage-stub';
import { useDemoMask } from '../hooks/useDemoMask';
import { useContactsStore } from './contactsStore';
import { useDemoStore } from './demoStore';

const PHRASE = 'Point avec Marie Exemple chez Fictif Conseil';

const CARNET = [
  { id: 'c1', first_name: 'Marie', last_name: 'Exemple', company: 'Fictif Conseil' },
] as never;

/** Ce que le stockage porte après une session en mode démo : le drapeau seul. */
function semerLeStockage() {
  localStorage.setItem(
    'therese-demo-mode',
    JSON.stringify({ state: { enabled: true }, version: 0 }),
  );
}

describe('B-145 : le mode démo relu du stockage masque vraiment', () => {
  beforeEach(() => {
    installLocalStorageStub();
    localStorage.clear();
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
    useContactsStore.setState({ contacts: [] });
  });

  it("masque le texte libre quand les contacts arrivent APRÈS la rehydratation", async () => {
    semerLeStockage();

    await useDemoStore.persist.rehydrate();
    expect(useDemoStore.getState().enabled).toBe(true);

    const { result } = renderHook(() => useDemoMask());
    act(() => {
      useContactsStore.setState({ contacts: CARNET });
    });

    expect(result.current.maskText(PHRASE)).not.toContain('Marie Exemple');
    expect(result.current.maskText(PHRASE)).not.toContain('Fictif Conseil');
  });

  it('masque le texte libre quand les contacts étaient déjà là', async () => {
    useContactsStore.setState({ contacts: CARNET });
    semerLeStockage();

    await useDemoStore.persist.rehydrate();

    const { result } = renderHook(() => useDemoMask());
    expect(result.current.maskText(PHRASE)).not.toContain('Marie Exemple');
  });

  it("ne masque rien si le stockage dit que le mode démo est éteint", async () => {
    localStorage.setItem(
      'therese-demo-mode',
      JSON.stringify({ state: { enabled: false }, version: 0 }),
    );

    await useDemoStore.persist.rehydrate();
    const { result } = renderHook(() => useDemoMask());
    act(() => {
      useContactsStore.setState({ contacts: CARNET });
    });

    expect(result.current.maskText(PHRASE)).toBe(PHRASE);
    expect(useDemoStore.getState().replacementMap.size).toBe(0);
  });

  it("n'écrase pas une table plus riche construite par une surface", async () => {
    semerLeStockage();
    await useDemoStore.persist.rehydrate();

    // MemoryPanel et CRMPanel appellent `buildMap` avec contacts ET projets :
    // le rattrapage de rehydratation ne doit pas reprendre la main dessus.
    useDemoStore.getState().buildMap(CARNET, [{ name: 'Refonte du site Bonetti' }]);
    const richesse = useDemoStore.getState().replacementMap.size;
    expect(richesse).toBeGreaterThan(0);

    useContactsStore.setState({ contacts: CARNET });

    expect(useDemoStore.getState().replacementMap.size).toBe(richesse);
    expect(useDemoStore.getState().replacementMap.has('Refonte du site Bonetti')).toBe(true);
  });
});
