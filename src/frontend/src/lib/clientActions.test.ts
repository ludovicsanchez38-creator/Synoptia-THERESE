/**
 * Actions déterministes - tranche 1a : exécution côté client de l'événement
 * `client_action` émis par le backend pour un message-action pur
 * ({action: ouvrir email} -> navigation locale, zéro LLM).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { handleClientActionChunk, runNavigationAction } from './clientActions';
import { runAction } from './actionRegistry';

vi.mock('./actionRegistry', async () => {
  const actual = await vi.importActual<typeof import('./actionRegistry')>('./actionRegistry');
  return { ...actual, runAction: vi.fn(() => true) };
});

const mockedRun = vi.mocked(runAction);

describe('handleClientActionChunk', () => {
  beforeEach(() => mockedRun.mockClear());

  it('exécute une navigation via le registre d\'actions', () => {
    const handled = handleClientActionChunk({
      type: 'client_action',
      content: '',
      client_action: { action: 'navigate', action_id: 'email.open', target: 'email' },
    } as never);
    expect(handled).toBe(true);
    expect(mockedRun).toHaveBeenCalledWith('email.open');
  });

  it('BUG-139 : la coque 0.40 peut revendiquer la navigation (vue embarquée)', () => {
    const claim = (e: Event) => {
      e.preventDefault();
    };
    window.addEventListener('therese:client-action', claim);
    try {
      const handled = handleClientActionChunk({
        type: 'client_action',
        content: '',
        client_action: { action: 'navigate', action_id: 'crm.open', target: 'crm' },
      } as never);
      expect(handled).toBe(true);
      // Revendicé par la coque : le registre classique n'est PAS appelé.
      expect(mockedRun).not.toHaveBeenCalled();
    } finally {
      window.removeEventListener('therese:client-action', claim);
    }
  });

  it('BUG-139 : le détail de l’événement porte l’action_id', () => {
    let received: string | undefined;
    const spy = (e: Event) => {
      received = (e as CustomEvent<{ actionId?: string }>).detail?.actionId;
      e.preventDefault();
    };
    window.addEventListener('therese:client-action', spy);
    try {
      handleClientActionChunk({
        type: 'client_action',
        content: '',
        client_action: { action: 'navigate', action_id: 'tasks.open', target: 'tasks' },
      } as never);
      expect(received).toBe('tasks.open');
    } finally {
      window.removeEventListener('therese:client-action', spy);
    }
  });

  // BUG-139 (suite, 20/07) : les commandes / de navigation s'exécutent
  // DIRECTEMENT à la sélection (dictée), sans insérer de message-action.
  it('runNavigationAction navigue via le registre quand personne ne revendique', () => {
    expect(runNavigationAction('email.open')).toBe(true);
    expect(mockedRun).toHaveBeenCalledWith('email.open');
  });

  it('runNavigationAction laisse la coque revendiquer sans appeler le registre', () => {
    const claim = (e: Event) => {
      e.preventDefault();
    };
    window.addEventListener('therese:client-action', claim);
    try {
      expect(runNavigationAction('crm.open')).toBe(true);
      expect(mockedRun).not.toHaveBeenCalled();
    } finally {
      window.removeEventListener('therese:client-action', claim);
    }
  });

  it('F6 revue : refuse la navigation directe pendant un streaming (état vivant)', async () => {
    const { useChatStore } = await import('../stores/chatStore');
    const { useStatusStore } = await import('../stores/statusStore');
    const notifsAvant = useStatusStore.getState().notifications.length;
    useChatStore.setState({ isStreaming: true });
    try {
      expect(runNavigationAction('crm.open')).toBe(false);
      expect(mockedRun).not.toHaveBeenCalled();
      expect(useStatusStore.getState().notifications.length).toBe(notifsAvant + 1);
    } finally {
      useChatStore.setState({ isStreaming: false });
    }
  });

  it('ignore un chunk sans client_action exploitable', () => {
    expect(handleClientActionChunk({ type: 'client_action', content: '' } as never)).toBe(false);
    expect(
      handleClientActionChunk({
        type: 'client_action',
        content: '',
        client_action: { action: 'autre_chose', action_id: 'email.open' },
      } as never)
    ).toBe(false);
    expect(mockedRun).not.toHaveBeenCalled();
  });
});
