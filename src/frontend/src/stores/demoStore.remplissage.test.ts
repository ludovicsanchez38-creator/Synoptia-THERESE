import { beforeEach, describe, expect, it } from 'vitest';

import { useContactsStore } from './contactsStore';
import { useDemoStore } from './demoStore';

describe('demoStore : la map se remplit toute seule', () => {
  beforeEach(() => {
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
    useContactsStore.setState({ contacts: [] });
  });

  // Reproduit dans l'application lancée le 01/09/2026. Cmd+Shift+D activait
  // bien le mode, et rien n'était masqué : `replacementMap` n'est pas persistée
  // et n'était remplie que par CRMPanel et MemoryPanel. Tant qu'on n'avait pas
  // ouvert l'un des deux, le mode démo était un interrupteur sans effet — y
  // compris sur les six surfaces qui, elles, consomment bien le masque.
  it('remplit la map en activant le mode, sans passer par le CRM', () => {
    useContactsStore.setState({
      contacts: [
        { id: 'c1', first_name: 'Nathalie', last_name: 'BALLOT', company: 'Lou Bio' },
      ] as never,
    });

    useDemoStore.getState().toggle();

    expect(useDemoStore.getState().enabled).toBe(true);
    expect(useDemoStore.getState().replacementMap.size).toBeGreaterThan(0);
  });

  it('vide la map en éteignant le mode', () => {
    useContactsStore.setState({
      contacts: [{ id: 'c1', first_name: 'Nathalie', last_name: 'BALLOT' }] as never,
    });

    useDemoStore.getState().toggle();
    expect(useDemoStore.getState().replacementMap.size).toBeGreaterThan(0);

    useDemoStore.getState().toggle();
    expect(useDemoStore.getState().enabled).toBe(false);
    expect(useDemoStore.getState().replacementMap.size).toBe(0);
  });
});
