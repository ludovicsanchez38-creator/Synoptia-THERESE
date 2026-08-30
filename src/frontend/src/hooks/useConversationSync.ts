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
import { useChatStore, type Message } from '../stores/chatStore';
import {
  listConversations,
  getConversationMessages,
  type ConversationResponse,
  type MessageResponse,
} from '../services/api';

/**
 * BUG-130 : reconstruit un message local depuis la réponse backend en
 * restaurant le fichier de skill généré (extra_data JSON `{skill_file: {...}}`)
 * et le provider (badge local/cloud). Sans cette restauration, au rechargement
 * d'une conversation un ancien message de génération de fichier réafficherait
 * le code brut du générateur, sans bouton de téléchargement. Le fichier lui-même
 * survit sur disque (outputs/ + download par id), seul le lien était perdu.
 */
export function formatMessageFromResponse(msg: MessageResponse): Message {
  // BUG-136 : nouveau format {skill_files: [...]} (liste), lecture du legacy
  // {skill_file: {...}} conservée pour les messages persistés avant le fix.
  let skillFiles: NonNullable<Message['skillFiles']> = [];
  // Revue Soso : le frontend doit savoir qu'un message portait des pièces
  // jointes. Sans cela, une conversation rechargée ignore que le backend va
  // rejouer ces documents, et le consentement demandé ne mentionne rien.
  let hasAttachments = false;
  if (msg.extra_data) {
    try {
      const parsed = JSON.parse(msg.extra_data);
      if (parsed && typeof parsed === 'object') {
        if (Array.isArray(parsed.skill_files)) {
          skillFiles = parsed.skill_files as NonNullable<Message['skillFiles']>;
        } else if (parsed.skill_file) {
          skillFiles = [parsed.skill_file as NonNullable<Message['skillFile']>];
        }
        hasAttachments = Array.isArray(parsed.attachments) && parsed.attachments.length > 0;
      }
    } catch {
      // extra_data non-JSON ou corrompu : on ignore, le message reste affichable.
    }
  }
  return {
    id: msg.id,
    role: msg.role as 'user' | 'assistant' | 'system',
    content: msg.content,
    hasAttachments,
    timestamp: new Date(msg.created_at),
    ...(msg.provider ? { provider: msg.provider } : {}),
    ...(skillFiles.length > 0
      ? { skillFile: skillFiles[0], skillFiles }
      : {}),
  };
}

/**
 * Hook to sync conversations from backend on app startup.
 * Loads conversation list and optionally restores last active conversation.
 */
/**
 * Traduit une conversation du backend vers le format local.
 *
 * Extrait du hook (0.43) pour être testable : le mapping perdait `project_id`,
 * si bien que l'en-tête du chat annonçait « Toute la mémoire » alors que le
 * backend cloisonnait réellement sur un projet. Un affichage qui ment sur la
 * cloison est pire que pas de cloison du tout.
 */
/** Lot F : le GET /conversations est paginé (50). Une seule page laissait
 *  les plus anciennes injoignables. On enchaîne les pages jusqu'à épuisement
 *  ou un plafond de sécurité — au-delà, on avoue la troncature. */
export const PAGE_CONVERSATIONS = 50;
export const PLAFOND_CONVERSATIONS = 500;

export async function chargerConversationsPaginees(
  lister: (limit: number, offset: number) => Promise<ConversationResponse[]>,
  pageSize = PAGE_CONVERSATIONS,
  plafond = PLAFOND_CONVERSATIONS,
): Promise<{ conversations: ConversationResponse[]; truncated: boolean }> {
  const conversations: ConversationResponse[] = [];
  let offset = 0;
  while (offset < plafond) {
    const page = await lister(pageSize, offset);
    conversations.push(...page);
    if (page.length < pageSize) {
      return { conversations, truncated: false };
    }
    offset += pageSize;
  }
  return { conversations, truncated: true };
}

export function formatConversationFromResponse(conv: ConversationResponse) {
  return {
    id: conv.id,
    title: conv.title || 'Nouvelle conversation',
    messages: [] as Message[], // Messages loaded on demand
    createdAt: new Date(conv.created_at),
    updatedAt: new Date(conv.updated_at),
    messageCount: conv.message_count,
    synced: true,
    projectId: conv.project_id ?? null,
    memoryScope: conv.memory_scope ?? 'global',
  };
}

export function useConversationSync() {
  const { setConversations, setConversationMessages, currentConversationId, conversations } = useChatStore();
  const initialSyncDone = useRef(false);
  const lastLoadedConversationId = useRef<string | null>(null);

  // Load conversations from backend and merge with local
  const syncConversations = useCallback(async () => {
    try {
      const { conversations: backendConversations, truncated } =
        await chargerConversationsPaginees(listConversations);

      // Convert backend format to local format
      const syncedConversations = backendConversations.map(formatConversationFromResponse);

      // Get current local conversations (from Zustand state)
      const localConversations = useChatStore.getState().conversations;

      // Préserver les messages locaux non encore synchronisés (BUG-068)
      // Ex: messages de génération d'image stockés uniquement en local
      const mergedSynced = syncedConversations.map((synced) => {
        const local = localConversations.find((l) => l.id === synced.id);
        if (local && local.messages.length > 0) {
          // Toujours préserver les messages locaux existants plutôt qu'un tableau vide du backend
          return { ...synced, messages: local.messages, messageCount: Math.max(local.messages.length, synced.messageCount || 0) };
        }
        return synced;
      });

      // Find local-only conversations (not synced to backend)
      const localOnlyConversations = localConversations.filter(
        (local) => !local.synced && !mergedSynced.some((synced) => synced.id === local.id)
      );

      // Merge: backend conversations first (sorted by date), then local-only
      const mergedConversations = [...mergedSynced, ...localOnlyConversations];

      setConversations(mergedConversations);
      useChatStore.getState().setConversationsTruncated(truncated);

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

      // Convert backend format to local format (restaure fichier de skill + provider)
      const formattedMessages = messages.map(formatMessageFromResponse);

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

    // Charger les messages depuis le backend seulement si la conversation est vide localement (BUG-068)
    const conv = conversations.find((c) => c.id === currentConversationId);
    if (conv && conv.synced && (!conv.messages || conv.messages.length === 0)) {
      loadConversationMessages(currentConversationId);
    }
    lastLoadedConversationId.current = currentConversationId;
  }, [currentConversationId, conversations, loadConversationMessages]);

  return {
    syncConversations,
    loadConversationMessages,
  };
}
