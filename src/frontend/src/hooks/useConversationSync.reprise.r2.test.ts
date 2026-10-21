import { act, renderHook, waitFor } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
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
