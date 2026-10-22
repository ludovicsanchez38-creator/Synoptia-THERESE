import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createJSONStorage } from 'zustand/middleware';
import { useConversationSync } from './useConversationSync';
import { createChatStorage } from '../lib/chatPersistence';
import { discardAllPendingWrites, __resetPersistenceForTests } from '../lib/debouncedStorage';
import { getConversationMessages, listConversations } from '../services/api';
import { request } from '../services/api/core';
import { useChatStore } from '../stores/chatStore';
import { useStatusStore } from '../stores/statusStore';

vi.mock('../services/api', () => ({ listConversations: vi.fn(), getConversationMessages: vi.fn() }));
vi.mock('../services/api/core', () => ({ request: vi.fn() }));

const date = '2026-07-13T09:00:00Z';

beforeEach(() => {
  vi.useFakeTimers();
  discardAllPendingWrites();
  localStorage.clear();
  useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
  __resetPersistenceForTests();
  useChatStore.persist.setOptions({ storage: createJSONStorage(() => createChatStorage()) });
  useStatusStore.setState({ notifications: [] });
  vi.mocked(request).mockReset().mockRejectedValue(new Error('Écriture refusée en lecture seule'));
  vi.mocked(listConversations).mockReset().mockResolvedValue([{
    id: 'conversation-history', title: 'Historique', summary: null, message_count: 1,
    created_at: date, updated_at: date, project_id: null, memory_scope: 'global',
  }]);
  vi.mocked(getConversationMessages).mockReset().mockResolvedValue([{
    id: 'message-1', conversation_id: 'conversation-history', role: 'assistant', content: 'Réponse enregistrée',
    tokens_in: null, tokens_out: null, model: null, created_at: date,
  }]);
});

afterEach(() => {
  discardAllPendingWrites();
  __resetPersistenceForTests();
  vi.useRealTimers();
});

async function laisserPasserLaSauvegarde() {
  await act(async () => { await vi.advanceTimersByTimeAsync(1000); });
}

describe('R7 : consulter les données ne réimporte pas le chat', () => {
  it('ouvrir une surface en lecture seule charge l’historique sans aucun POST différé', async () => {
    renderHook(() => useConversationSync());
    await laisserPasserLaSauvegarde();
    expect(useChatStore.getState().conversations[0]?.title).toBe('Historique');
    expect(listConversations).toHaveBeenCalledOnce();
    expect(request).not.toHaveBeenCalled();
  });

  it('lire puis sélectionner un échange ne crée pas de fausse notification de sauvegarde devant le composeur', async () => {
    renderHook(() => useConversationSync());
    await laisserPasserLaSauvegarde();
    act(() => useChatStore.getState().loadConversation('conversation-history'));
    await laisserPasserLaSauvegarde();
    expect(getConversationMessages).toHaveBeenCalledWith('conversation-history');
    expect(useChatStore.getState().conversations[0].messages[0]?.content).toBe('Réponse enregistrée');
    expect(request).not.toHaveBeenCalled();
    expect(useStatusStore.getState().notifications).toEqual([]);
  });

  it('une lecture concurrente conserve la sauvegarde d’un vrai message local', async () => {
    const { result } = renderHook(() => useConversationSync());
    await laisserPasserLaSauvegarde();
    vi.mocked(request).mockResolvedValue({ success: true });
    act(() => {
      useChatStore.getState().loadConversation('conversation-history');
      useChatStore.getState().addMessage({ role: 'assistant', content: 'Résultat local à conserver' });
    });
    await act(async () => { await result.current.syncConversations(); });
    await laisserPasserLaSauvegarde();
    expect(request).toHaveBeenCalledOnce();
    expect(request).toHaveBeenCalledWith('/api/chat/cache-migration', expect.objectContaining({ method: 'POST' }));
    expect(JSON.parse(vi.mocked(request).mock.calls[0][1]!.body as string).conversations[0].messages)
      .toEqual(expect.arrayContaining([expect.objectContaining({ content: 'Résultat local à conserver' })]));
  });

  it('un vrai refus de sauvegarde reste signalé et son action permet de réessayer', async () => {
    renderHook(() => useConversationSync());
    await laisserPasserLaSauvegarde();
    act(() => useChatStore.getState().addMessage({ role: 'assistant', content: 'Résultat local' }));
    await laisserPasserLaSauvegarde();
    expect(request).toHaveBeenCalledOnce();
    expect(useStatusStore.getState().notifications).toHaveLength(1);
    vi.mocked(request).mockResolvedValue({ success: true });
    act(() => useStatusStore.getState().notifications[0].action?.onClick());
    await laisserPasserLaSauvegarde();
    expect(request).toHaveBeenCalledTimes(2);
  });
});
