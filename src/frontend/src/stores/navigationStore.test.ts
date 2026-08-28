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

  /**
   * Ce test disait « revient à chat ». Il datait d'avant la coque
   * conversationnelle, quand le chat ÉTAIT l'écran de base. Depuis, l'écran
   * de base est l'accueil de la coque, et ramener au chat produisait un
   * second geste parasite : après avoir fermé une vue, l'utilisateur se
   * retrouvait dans une conversation qu'il n'avait pas demandée.
   * `null` = aucune vue embarquée = l'accueil. (27/08/2026)
   */
  it('goBack avec historique vide revient à l’accueil, pas au chat', () => {
    useNavigationStore.getState().setView('crm');
    useNavigationStore.getState().goBack(); // -> chat (history avait ['chat'])
    useNavigationStore.getState().goBack(); // history vide -> accueil
    const s = useNavigationStore.getState();
    expect(s.activeView).toBeNull();
    expect(s.history).toEqual([]);
  });

  it('venir de l’accueil n’empile aucune vue fantôme', () => {
    useNavigationStore.setState({ activeView: null, history: [] });

    useNavigationStore.getState().setView('crm');

    const s = useNavigationStore.getState();
    expect(s.activeView).toBe('crm');
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

  it("l'action ⌘K home.open ramène à l'accueil de la coque, pas à une vue", async () => {
    // 28/08, signalé par Ludo : aucun chemin nommé ne ramenait à l'accueil
    // réel. Celui-ci menait au SECOND écran d'accueil, celui que le plan
    // retire — le seul bouton nommé « Accueil » conduisait au mauvais.
    const { runAction } = await import('../lib/actionRegistry');
    useNavigationStore.getState().setView('crm');
    const ok = runAction('home.open');
    expect(ok).toBe(true);
    expect(useNavigationStore.getState().activeView).toBeNull();
  });

  it("la vue 'documents' existe et l'action ⌘K documents.open y navigue (D2)", async () => {
    const { runAction } = await import('../lib/actionRegistry');
    const ok = runAction('documents.open');
    expect(ok).toBe(true);
    expect(useNavigationStore.getState().activeView).toBe('documents');
  });
});
