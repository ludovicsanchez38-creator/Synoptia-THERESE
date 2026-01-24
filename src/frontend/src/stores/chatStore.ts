import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { generateId } from '../lib/utils';

import type { DetectedEntities } from '../services/api';

export interface MessageUsage {
  input_tokens: number;
  output_tokens: number;
  cost_eur: number;
  model: string;
}

export interface MessageUncertainty {
  is_uncertain: boolean;
  confidence_level: 'high' | 'medium' | 'low';
  confidence_score: number;
  uncertainty_phrases: string[];
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  detectedEntities?: DetectedEntities;
  usage?: MessageUsage;
  uncertainty?: MessageUncertainty;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
  messageCount?: number;
  synced?: boolean;
  ephemeral?: boolean; // Conversations éphémères ne sont pas persistées
}

interface ChatStore {
  // State
  conversations: Conversation[];
  currentConversationId: string | null;
  isStreaming: boolean;

  // Computed
  currentConversation: () => Conversation | null;
  isCurrentConversationEmpty: () => boolean;

  // Actions
  createConversation: (ephemeral?: boolean) => string;
  loadConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'> & { id?: string }) => string;
  updateMessage: (id: string, content: string) => void;
  setMessageEntities: (id: string, entities: DetectedEntities) => void;
  clearMessageEntities: (id: string) => void;
  setMessageMetadata: (id: string, usage?: MessageUsage, uncertainty?: MessageUncertainty) => void;
  setStreaming: (isStreaming: boolean) => void;
  clearCurrentConversation: () => void;

  // Sync actions
  setConversations: (conversations: Conversation[]) => void;
  setConversationMessages: (conversationId: string, messages: Message[]) => void;
  updateConversationId: (oldId: string, newId: string) => void;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      conversations: [],
      currentConversationId: null,
      isStreaming: false,

      currentConversation: () => {
        const { conversations, currentConversationId } = get();
        return conversations.find((c) => c.id === currentConversationId) || null;
      },

      isCurrentConversationEmpty: () => {
        const { conversations, currentConversationId } = get();
        if (!currentConversationId) return true;
        const current = conversations.find((c) => c.id === currentConversationId);
        return !current || current.messages.length === 0;
      },

      createConversation: (ephemeral = false) => {
        const id = generateId();
        const newConversation: Conversation = {
          id,
          title: ephemeral ? 'Conversation éphémère' : 'Nouvelle conversation',
          messages: [],
          createdAt: new Date(),
          updatedAt: new Date(),
          synced: false, // Not yet synced to backend
          ephemeral,
        };
        set((state) => ({
          conversations: [newConversation, ...state.conversations],
          currentConversationId: id,
        }));
        return id;
      },

      loadConversation: (id) => {
        set({ currentConversationId: id });
      },

      deleteConversation: (id) => {
        set((state) => {
          const filtered = state.conversations.filter((c) => c.id !== id);
          const newCurrentId =
            state.currentConversationId === id
              ? filtered[0]?.id || null
              : state.currentConversationId;
          return {
            conversations: filtered,
            currentConversationId: newCurrentId,
          };
        });
      },

      addMessage: (message) => {
        const messageId = message.id || generateId();
        const newMessage: Message = {
          ...message,
          id: messageId,
          timestamp: new Date(),
        };

        set((state) => {
          const { currentConversationId, conversations } = state;

          // Create conversation if none exists
          if (!currentConversationId) {
            const id = generateId();
            const title =
              message.role === 'user'
                ? message.content.slice(0, 50) + (message.content.length > 50 ? '...' : '')
                : 'Nouvelle conversation';
            return {
              conversations: [
                {
                  id,
                  title,
                  messages: [newMessage],
                  createdAt: new Date(),
                  updatedAt: new Date(),
                },
                ...conversations,
              ],
              currentConversationId: id,
            };
          }

          // Add to existing conversation
          return {
            conversations: conversations.map((c) =>
              c.id === currentConversationId
                ? {
                    ...c,
                    messages: [...c.messages, newMessage],
                    updatedAt: new Date(),
                    // Update title from first user message
                    title:
                      c.messages.length === 0 && message.role === 'user'
                        ? message.content.slice(0, 50) +
                          (message.content.length > 50 ? '...' : '')
                        : c.title,
                  }
                : c
            ),
          };
        });

        return messageId;
      },

      updateMessage: (id, content) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === state.currentConversationId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === id ? { ...m, content, isStreaming: false } : m
                  ),
                  updatedAt: new Date(),
                }
              : c
          ),
        }));
      },

      setMessageEntities: (id, entities) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === state.currentConversationId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === id ? { ...m, detectedEntities: entities } : m
                  ),
                }
              : c
          ),
        }));
      },

      clearMessageEntities: (id) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === state.currentConversationId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === id ? { ...m, detectedEntities: undefined } : m
                  ),
                }
              : c
          ),
        }));
      },

      setMessageMetadata: (id, usage, uncertainty) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === state.currentConversationId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === id
                      ? {
                          ...m,
                          ...(usage && { usage }),
                          ...(uncertainty && { uncertainty }),
                        }
                      : m
                  ),
                }
              : c
          ),
        }));
      },

      setStreaming: (isStreaming) => set({ isStreaming }),

      clearCurrentConversation: () => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === state.currentConversationId
              ? { ...c, messages: [], updatedAt: new Date() }
              : c
          ),
        }));
      },

      // Sync actions
      setConversations: (conversations) => {
        set({ conversations });
      },

      setConversationMessages: (conversationId, messages) => {
        set((state) => {
          const existingConv = state.conversations.find((c) => c.id === conversationId);

          if (existingConv) {
            // Update existing conversation
            return {
              conversations: state.conversations.map((c) =>
                c.id === conversationId
                  ? { ...c, messages, messageCount: messages.length, synced: true }
                  : c
              ),
            };
          } else {
            // Create conversation if it doesn't exist (loaded from backend)
            const firstUserMessage = messages.find((m) => m.role === 'user');
            const title = firstUserMessage
              ? firstUserMessage.content.slice(0, 50) + (firstUserMessage.content.length > 50 ? '...' : '')
              : 'Conversation';

            const newConversation: Conversation = {
              id: conversationId,
              title,
              messages,
              createdAt: messages[0]?.timestamp || new Date(),
              updatedAt: messages[messages.length - 1]?.timestamp || new Date(),
              messageCount: messages.length,
              synced: true,
            };

            return {
              conversations: [newConversation, ...state.conversations],
            };
          }
        });
      },

      updateConversationId: (oldId, newId) => {
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === oldId ? { ...c, id: newId, synced: true } : c
          ),
          currentConversationId:
            state.currentConversationId === oldId ? newId : state.currentConversationId,
        }));
      },
    }),
    {
      name: 'therese-chat',
      partialize: (state) => ({
        // Exclure les conversations éphémères de la persistance
        conversations: state.conversations.filter((c) => !c.ephemeral),
        currentConversationId: state.currentConversationId,
      }),
    }
  )
);
