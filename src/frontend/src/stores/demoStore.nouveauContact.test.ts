/**
 * B-523 : un contact créé APRÈS l'armement du mode démonstration n'était
 * jamais masqué dans le texte libre. `armerLaTableSiVide` ne reconstruisait
 * la table que si elle était vide ; l'abonnement au carnet se déclenchait à
 * chaque changement sans jamais pouvoir y ajouter les nouveaux venus.
 */
import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { installLocalStorageStub } from '../test/localStorage-stub';
import { useDemoMask } from '../hooks/useDemoMask';
import { useContactsStore } from './contactsStore';
import { useDemoStore } from './demoStore';

const MARIE = { id: 'c1', first_name: 'Marie', last_name: 'Exemple', company: 'Fictif Conseil' };
const PAUL = { id: 'c2', first_name: 'Paul', last_name: 'Nouveau', company: 'Atelier Neuf' };

describe('B-523 : un contact créé après l’armement est masqué lui aussi', () => {
  beforeEach(() => {
    installLocalStorageStub();
    localStorage.clear();
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
    useContactsStore.setState({ contacts: [MARIE] as never });
  });

  it('ajoute le nouveau venu à la table sans perdre les anciens', () => {
    act(() => useDemoStore.getState().setEnabled(true));
    const { result } = renderHook(() => useDemoMask());
    expect(result.current.maskText('Point avec Marie Exemple')).not.toContain('Marie Exemple');

    act(() => {
      useContactsStore.setState({ contacts: [MARIE, PAUL] as never });
    });

    expect(result.current.maskText('Relance de Paul Nouveau chez Atelier Neuf')).not.toContain('Paul Nouveau');
    expect(result.current.maskText('Relance de Paul Nouveau chez Atelier Neuf')).not.toContain('Atelier Neuf');
    expect(result.current.maskText('Point avec Marie Exemple')).not.toContain('Marie Exemple');
  });
});
