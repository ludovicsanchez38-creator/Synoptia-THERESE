import { describe, it, expect, beforeEach } from 'vitest';
import { resolveEscape } from './resolveEscape';
import { usePanelStore } from '../stores/panelStore';
import { useAtelierStore } from '../stores/atelierStore';
import { useActionsStore } from '../stores/actionsStore';
import { useNavigationStore } from '../stores/navigationStore';

function resetStores() {
  usePanelStore.setState({
    showSettings: false,
    showBoardPanel: false,
    showContactModal: false,
    showProjectModal: false,
    showCommandPalette: false,
    showShortcuts: false,
    showSaveCommand: false,
    showConversationSidebar: false,
  });
  useAtelierStore.setState({ isOpen: false });
  useActionsStore.setState({ isPanelOpen: false });
  useNavigationStore.setState({ activeView: 'chat', history: [] });
}

describe('resolveEscape (pile Échap/retour unifiée L7)', () => {
  beforeEach(resetStores);

  it('ferme un overlay panelStore ouvert (et ne revient pas en arrière)', () => {
    useNavigationStore.setState({ activeView: 'crm', history: ['chat'] });
    usePanelStore.setState({ showSettings: true });
    resolveEscape();
    expect(usePanelStore.getState().showSettings).toBe(false);
    // une vue est active mais un overlay était ouvert -> pas de retour
    expect(useNavigationStore.getState().activeView).toBe('crm');
  });

  it('respecte le z-order : ferme le modal le plus en avant avant les autres', () => {
    usePanelStore.setState({ showSettings: true, showContactModal: true });
    resolveEscape();
    expect(usePanelStore.getState().showContactModal).toBe(false);
    expect(usePanelStore.getState().showSettings).toBe(true); // pas encore fermé
  });

  it('ferme le panneau Atelier sur Échap (manque comblé)', () => {
    useAtelierStore.setState({ isOpen: true });
    resolveEscape();
    expect(useAtelierStore.getState().isOpen).toBe(false);
  });

  it('ferme le panneau Actions sur Échap (manque comblé)', () => {
    useActionsStore.setState({ isPanelOpen: true });
    resolveEscape();
    expect(useActionsStore.getState().isPanelOpen).toBe(false);
  });

  it("revient à la vue précédente quand aucun overlay n'est ouvert (coeur de L7)", () => {
    useNavigationStore.setState({ activeView: 'memory', history: ['chat'] });
    resolveEscape();
    expect(useNavigationStore.getState().activeView).toBe('chat');
  });

  it("ne revient pas en arrière si un overlay est ouvert sur une vue", () => {
    useNavigationStore.setState({ activeView: 'crm', history: ['chat'] });
    useActionsStore.setState({ isPanelOpen: true });
    resolveEscape();
    expect(useActionsStore.getState().isPanelOpen).toBe(false);
    expect(useNavigationStore.getState().activeView).toBe('crm'); // pas de retour
  });

  it('sur le chat avec la sidebar ouverte : ferme la sidebar (dernier recours)', () => {
    useNavigationStore.setState({ activeView: 'chat', history: [] });
    usePanelStore.setState({ showConversationSidebar: true });
    resolveEscape();
    expect(usePanelStore.getState().showConversationSidebar).toBe(false);
  });

  it('retour de vue prioritaire sur la fermeture de la sidebar', () => {
    useNavigationStore.setState({ activeView: 'crm', history: ['chat'] });
    usePanelStore.setState({ showConversationSidebar: true });
    resolveEscape();
    // on quitte d'abord la vue ; la sidebar reste (on la fermera au prochain Échap)
    expect(useNavigationStore.getState().activeView).toBe('chat');
    expect(usePanelStore.getState().showConversationSidebar).toBe(true);
  });

  it('ne fait rien sur le chat sans overlay ni historique', () => {
    resolveEscape();
    expect(useNavigationStore.getState().activeView).toBe('chat');
  });
});
