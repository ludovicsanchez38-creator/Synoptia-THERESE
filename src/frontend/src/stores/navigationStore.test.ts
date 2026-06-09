import { describe, it, expect, beforeEach } from 'vitest';
import { useNavigationStore } from './navigationStore';

describe('navigationStore', () => {
  beforeEach(() => {
    useNavigationStore.setState({ activeView: 'chat', history: [] });
  });

  it('par défaut : vue chat, historique vide', () => {
    const s = useNavigationStore.getState();
    expect(s.activeView).toBe('chat');
    expect(s.history).toEqual([]);
  });

  it('setView empile la vue courante et active la nouvelle', () => {
    useNavigationStore.getState().setView('crm');
    let s = useNavigationStore.getState();
    expect(s.activeView).toBe('crm');
    expect(s.history).toEqual(['chat']);

    useNavigationStore.getState().setView('email');
    s = useNavigationStore.getState();
    expect(s.activeView).toBe('email');
    expect(s.history).toEqual(['chat', 'crm']);
  });

  it('setView sur la vue déjà active est un no-op (pas de doublon dans l\'historique)', () => {
    useNavigationStore.getState().setView('crm');
    useNavigationStore.getState().setView('crm');
    const s = useNavigationStore.getState();
    expect(s.activeView).toBe('crm');
    expect(s.history).toEqual(['chat']);
  });

  it('goBack dépile vers la vue précédente', () => {
    useNavigationStore.getState().setView('crm');
    useNavigationStore.getState().setView('email');
    useNavigationStore.getState().goBack();
    const s = useNavigationStore.getState();
    expect(s.activeView).toBe('crm');
    expect(s.history).toEqual(['chat']);
  });

  it('goBack avec historique vide revient à chat', () => {
    useNavigationStore.getState().setView('crm');
    useNavigationStore.getState().goBack(); // -> chat (history avait ['chat'])
    useNavigationStore.getState().goBack(); // déjà chat, history vide -> reste chat
    const s = useNavigationStore.getState();
    expect(s.activeView).toBe('chat');
    expect(s.history).toEqual([]);
  });

  it('resetToChat ramène à chat et vide l\'historique', () => {
    useNavigationStore.getState().setView('crm');
    useNavigationStore.getState().setView('invoices');
    useNavigationStore.getState().resetToChat();
    const s = useNavigationStore.getState();
    expect(s.activeView).toBe('chat');
    expect(s.history).toEqual([]);
  });

  it("BUG-104 : la vue 'projects' existe et l'action ⌘K projects.open y navigue", async () => {
    const { runAction } = await import('../lib/actionRegistry');
    const ok = runAction('projects.open');
    expect(ok).toBe(true);
    expect(useNavigationStore.getState().activeView).toBe('projects');
  });
});
