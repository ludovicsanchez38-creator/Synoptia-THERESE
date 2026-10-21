import { create } from 'zustand';
import { useNavigationStore } from './navigationStore';

export const useAgentMemoryStore = create<{
  selectedId: string | null;
  sourceMessageId: string | null;
  sourceConversationId: string | null;
}>(() => ({ selectedId: null, sourceMessageId: null, sourceConversationId: null }));

export function openMemoryCard(id: string): void {
  useAgentMemoryStore.setState({ selectedId: id });
  useNavigationStore.getState().setView('agent_memory');
}
