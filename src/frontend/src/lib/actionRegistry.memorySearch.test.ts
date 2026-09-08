/** P-052 (Nadia, c4) : ⌘⇧F « Rechercher dans les Contacts » ouvrait la vue et posait le focus sur le titre ; le raccourci promet une recherche. */
import { beforeEach, describe, expect, it } from 'vitest';

import { runAction } from './actionRegistry';
import { useNavigationStore } from '../stores/navigationStore';

describe('memory.search (P-052)', () => {
  beforeEach(() => {
    useNavigationStore.setState({ activeView: null, history: [], memorySearchFocusRequested: false });
  });

  it('ouvre les Contacts ET demande le focus du champ de recherche', () => {
    expect(runAction('memory.search')).toBe(true);
    const etat = useNavigationStore.getState();
    expect(etat.activeView).toBe('memory');
    expect(etat.memorySearchFocusRequested).toBe(true);
  });

  it('déjà sur les Contacts : la demande de focus part quand même', () => {
    useNavigationStore.setState({ activeView: 'memory' });
    runAction('memory.search');
    expect(useNavigationStore.getState().memorySearchFocusRequested).toBe(true);
  });

  it('consommer la demande la remet à faux', () => {
    runAction('memory.search');
    useNavigationStore.getState().consumeMemorySearchFocus();
    expect(useNavigationStore.getState().memorySearchFocusRequested).toBe(false);
  });
});
