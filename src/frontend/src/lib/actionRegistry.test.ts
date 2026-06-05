import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getActions, runAction, APP_ACTIONS } from './actionRegistry';
import { useNavigationStore } from '../stores/navigationStore';
import { usePanelStore } from '../stores/panelStore';
import { useActionsStore } from '../stores/actionsStore';

beforeEach(() => {
  useNavigationStore.setState({ activeView: 'chat', history: [] });
  usePanelStore.setState({
    showSettings: false,
    showBoardPanel: false,
    showContactModal: false,
    showProjectModal: false,
    showShortcuts: false,
    showConversationSidebar: false,
  });
  useActionsStore.setState({ isPanelOpen: false });
});

describe('actionRegistry (L8 - registre d\'actions invocable)', () => {
  it('expose une liste non vide d\'actions, toutes avec id/label/group/run', () => {
    const actions = getActions();
    expect(actions.length).toBeGreaterThan(5);
    for (const a of actions) {
      expect(typeof a.id).toBe('string');
      expect(typeof a.label).toBe('string');
      expect(typeof a.group).toBe('string');
      expect(typeof a.run).toBe('function');
    }
  });

  it('les id sont uniques', () => {
    const ids = APP_ACTIONS.map((a) => a.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("runAction('memory.open') bascule sur la vue Mémoire", () => {
    expect(runAction('memory.open')).toBe(true);
    expect(useNavigationStore.getState().activeView).toBe('memory');
  });

  it("runAction('crm.open') bascule sur la vue CRM", () => {
    runAction('crm.open');
    expect(useNavigationStore.getState().activeView).toBe('crm');
  });

  it("runAction('files.open') bascule sur la vue Indexation (arbitrage A/B)", () => {
    runAction('files.open');
    expect(useNavigationStore.getState().activeView).toBe('files');
  });

  it("runAction('contact.new') ouvre la modale de contact", () => {
    runAction('contact.new');
    expect(usePanelStore.getState().showContactModal).toBe(true);
  });

  it("runAction('settings.open') ouvre les réglages", () => {
    runAction('settings.open');
    expect(usePanelStore.getState().showSettings).toBe(true);
  });

  it("runAction('actions.open') ouvre le panneau Actions", () => {
    runAction('actions.open');
    expect(useActionsStore.getState().isPanelOpen).toBe(true);
  });

  it("runAction sur un id inconnu retourne false sans planter", () => {
    expect(runAction('does.not.exist')).toBe(false);
  });

  it("les actions contextuelles passent par un événement window (découplage ChatLayout)", () => {
    const handler = vi.fn();
    window.addEventListener('therese:open-guided', handler);
    expect(runAction('guided.open')).toBe(true);
    expect(handler).toHaveBeenCalledTimes(1);
    window.removeEventListener('therese:open-guided', handler);
  });
});
