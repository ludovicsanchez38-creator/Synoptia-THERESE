import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useConversationSync } from './useConversationSync';
import { migrerCacheChat, activerSauvegardeChat } from '../lib/chatPersistence';
import { listConversations } from '../services/api';
import { useStatusStore } from '../stores/statusStore';
import { useChatStore } from '../stores/chatStore';

vi.mock('../lib/chatPersistence', async original => ({
  ...await original<object>(), migrerCacheChat: vi.fn(), activerSauvegardeChat: vi.fn(),
}));
vi.mock('../services/api', () => ({ listConversations: vi.fn(), getConversationMessages: vi.fn() }));

it('propose une reprise effective après un refus de migration, sans vider le cache', async () => {
  vi.mocked(migrerCacheChat).mockRejectedValueOnce(new Error('indisponible')).mockResolvedValue(undefined);
  vi.mocked(listConversations).mockResolvedValue([]);
  useChatStore.setState({ conversations: [], currentConversationId: null });
  useStatusStore.setState({ notifications: [] });
  renderHook(() => useConversationSync());
  await waitFor(() => expect(useStatusStore.getState().notifications).toHaveLength(1));
  const action = useStatusStore.getState().notifications[0].action;
  expect(action?.label).toBe('Réessayer');
  act(() => action?.onClick());
  await waitFor(() => expect(listConversations).toHaveBeenCalledTimes(1));
  expect(migrerCacheChat).toHaveBeenCalledTimes(2);
  expect(activerSauvegardeChat).toHaveBeenCalledTimes(1);
});

describe('notification de sauvegarde du chat', () => {
  beforeEach(() => {
    vi.mocked(migrerCacheChat).mockReset().mockResolvedValue(undefined);
    vi.mocked(listConversations).mockReset().mockResolvedValue([]);
    useChatStore.setState({ conversations: [], currentConversationId: null });
    useStatusStore.setState({ notifications: [] });
  });

  it('affiche le message du moteur porté par l’événement', () => {
    const { unmount } = renderHook(() => useConversationSync());
    const message = 'Le profil a changé. Reviens au profil concerné avant de réessayer.';

    act(() => window.dispatchEvent(new CustomEvent('therese:chat-save-error', {
      detail: { message },
    })));

    expect(useStatusStore.getState().notifications[0]).toMatchObject({
      title: 'Échange en attente de sauvegarde', message,
      action: { label: 'Réessayer' },
    });
    unmount();
  });

  it('garde le message générique quand l’événement n’a pas de détail', () => {
    const { unmount } = renderHook(() => useConversationSync());

    act(() => window.dispatchEvent(new CustomEvent('therese:chat-save-error')));

    expect(useStatusStore.getState().notifications[0]).toMatchObject({
      title: 'Échange en attente de sauvegarde',
      message: 'Garde cette fenêtre ouverte et réessaie la synchronisation.',
      action: { label: 'Réessayer' },
    });
    unmount();
  });
});
