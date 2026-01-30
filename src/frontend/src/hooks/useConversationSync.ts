/**
 * THÉRÈSE v2 - Conversation Sync Hook
 *
 * Syncs local conversation state with backend SQLite database.
 * Handles:
 * - Initial sync on app startup
 * - Loading messages when conversation changes
 * - Periodic refresh of conversation list
 */

import { useEffect, useCallback, useRef } from 'react';
import { useChatStore } from '../stores/chatStore';
import {
  listConversations,
  getConversationMessages,
  type ConversationResponse,
  type MessageResponse,
} from '../services/api';

/**
 * Hook to sync conversations from backend on app startup.
 * Loads conversation list and optionally restores last active conversation.
 */
export function useConversationSync() {
  const { setConversations, setConversationMessages, currentConversationId, conversations } = useChatStore();
  const initialSyncDone = useRef(false);
  const lastLoadedConversationId = useRef<string | null>(null);

  // Load conversations from backend and merge with local
  const syncConversations = useCallback(async () => {
    try {
      const backendConversations = await listConversations(50, 0);

      // Convert backend format to local format
      const syncedConversations = backendConversations.map((conv: ConversationResponse) => ({
        id: conv.id,
        title: conv.title || 'Nouvelle conversation',
        messages: [], // Messages loaded on demand
        createdAt: new Date(conv.created_at),
        updatedAt: new Date(conv.updated_at),
        messageCount: conv.message_count,
        synced: true,
      }));

      // Get current local conversations (from Zustand state)
      const localConversations = useChatStore.getState().conversations;

      // Find local-only conversations (not synced to backend)
      const localOnlyConversations = localConversations.filter(
        (local) => !local.synced && !syncedConversations.some((synced) => synced.id === local.id)
      );

      // Merge: backend conversations first (sorted by date), then local-only
      const mergedConversations = [...syncedConversations, ...localOnlyConversations];

      setConversations(mergedConversations);

      return syncedConversations;
    } catch (error) {
      console.error('Failed to sync conversations:', error);
      return [];
    }
  }, [setConversations]);

  // Load messages for a specific conversation
  const loadConversationMessages = useCallback(async (conversationId: string) => {
    try {
      const messages = await getConversationMessages(conversationId);

      // Convert backend format to local format
      const formattedMessages = messages.map((msg: MessageResponse) => ({
        id: msg.id,
        role: msg.role as 'user' | 'assistant' | 'system',
        content: msg.content,
        timestamp: new Date(msg.created_at),
      }));

      // Update store with loaded messages
      setConversationMessages(conversationId, formattedMessages);

      return formattedMessages;
    } catch (error) {
      console.error('Failed to load conversation messages:', error);
      return [];
    }
  }, [setConversationMessages]);

  // Initial sync on mount
  useEffect(() => {
    if (initialSyncDone.current) return;
    initialSyncDone.current = true;

    syncConversations().then((syncedConversations) => {
      // If there's a current conversation ID, load its messages
      if (currentConversationId && syncedConversations.length > 0) {
        const conv = syncedConversations.find((c: { id: string }) => c.id === currentConversationId);
        if (conv) {
          loadConversationMessages(currentConversationId);
          lastLoadedConversationId.current = currentConversationId;
        }
      }
    });
  }, [syncConversations, currentConversationId, loadConversationMessages]);

  // Load messages when conversation changes
  useEffect(() => {
    if (!currentConversationId) return;
    if (currentConversationId === lastLoadedConversationId.current) return;

    // Check if conversation exists and needs messages loaded
    const conv = conversations.find((c) => c.id === currentConversationId);
    if (conv && conv.synced && (!conv.messages || conv.messages.length === 0)) {
      loadConversationMessages(currentConversationId);
      lastLoadedConversationId.current = currentConversationId;
    }
  }, [currentConversationId, conversations, loadConversationMessages]);

  return {
    syncConversations,
    loadConversationMessages,
  };
}
