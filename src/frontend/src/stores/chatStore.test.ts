import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from './chatStore';

describe('chatStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useChatStore.setState({
      conversations: [],
      currentConversationId: null,
      isStreaming: false,
    });
  });

  describe('createConversation', () => {
    it('should create a new conversation and set it as current', () => {
      const id = useChatStore.getState().createConversation();
      const state = useChatStore.getState();

      expect(id).toBeDefined();
      expect(state.currentConversationId).toBe(id);
      expect(state.conversations).toHaveLength(1);
      expect(state.conversations[0].title).toBe('Nouvelle conversation');
      expect(state.conversations[0].messages).toEqual([]);
    });

    it('should prepend new conversations to the list', () => {
      const id1 = useChatStore.getState().createConversation();
      const id2 = useChatStore.getState().createConversation();
      const state = useChatStore.getState();

      expect(state.conversations).toHaveLength(2);
      expect(state.conversations[0].id).toBe(id2);
      expect(state.conversations[1].id).toBe(id1);
    });
  });

  describe('addMessage', () => {
    it('should create conversation if none exists when adding message', () => {
      const messageId = useChatStore.getState().addMessage({
        role: 'user',
        content: 'Hello world',
      });
      const state = useChatStore.getState();

      expect(messageId).toBeDefined();
      expect(state.conversations).toHaveLength(1);
      expect(state.currentConversationId).toBeDefined();
      expect(state.conversations[0].messages).toHaveLength(1);
      expect(state.conversations[0].messages[0].content).toBe('Hello world');
    });

    it('should set conversation title from first user message', () => {
      useChatStore.getState().addMessage({
        role: 'user',
        content: 'This is my question about something',
      });
      const state = useChatStore.getState();

      expect(state.conversations[0].title).toBe('This is my question about something');
    });

    it('should truncate long messages for title', () => {
      const longMessage = 'A'.repeat(100);
      useChatStore.getState().addMessage({
        role: 'user',
        content: longMessage,
      });
      const state = useChatStore.getState();

      expect(state.conversations[0].title).toBe('A'.repeat(50) + '...');
    });

    it('should add message to existing conversation', () => {
      useChatStore.getState().createConversation();
      useChatStore.getState().addMessage({ role: 'user', content: 'First' });
      useChatStore.getState().addMessage({ role: 'assistant', content: 'Second' });
      const state = useChatStore.getState();

      expect(state.conversations[0].messages).toHaveLength(2);
      expect(state.conversations[0].messages[0].content).toBe('First');
      expect(state.conversations[0].messages[1].content).toBe('Second');
    });
  });

  describe('updateMessage', () => {
    it('should update message content', () => {
      useChatStore.getState().createConversation();
      const messageId = useChatStore.getState().addMessage({
        role: 'assistant',
        content: 'Initial',
        isStreaming: true,
      });
      useChatStore.getState().updateMessage(messageId, 'Updated content');
      const state = useChatStore.getState();

      expect(state.conversations[0].messages[0].content).toBe('Updated content');
      expect(state.conversations[0].messages[0].isStreaming).toBe(false);
    });
  });

  describe('deleteConversation', () => {
    it('should remove conversation from list', () => {
      const id1 = useChatStore.getState().createConversation();
      const id2 = useChatStore.getState().createConversation();
      useChatStore.getState().deleteConversation(id1);
      const state = useChatStore.getState();

      expect(state.conversations).toHaveLength(1);
      expect(state.conversations[0].id).toBe(id2);
    });

    it('should switch to another conversation if current is deleted', () => {
      const id1 = useChatStore.getState().createConversation();
      const id2 = useChatStore.getState().createConversation();
      useChatStore.getState().loadConversation(id2);
      useChatStore.getState().deleteConversation(id2);
      const state = useChatStore.getState();

      expect(state.currentConversationId).toBe(id1);
    });

    it('should set currentConversationId to null if last conversation is deleted', () => {
      const id = useChatStore.getState().createConversation();
      useChatStore.getState().deleteConversation(id);
      const state = useChatStore.getState();

      expect(state.currentConversationId).toBeNull();
      expect(state.conversations).toHaveLength(0);
    });
  });

  describe('loadConversation', () => {
    it('should set currentConversationId', () => {
      const id1 = useChatStore.getState().createConversation();
      useChatStore.getState().createConversation(); // create second conversation
      useChatStore.getState().loadConversation(id1);
      const state = useChatStore.getState();

      expect(state.currentConversationId).toBe(id1);
    });
  });

  describe('currentConversation', () => {
    it('should return current conversation', () => {
      const id = useChatStore.getState().createConversation();
      const conv = useChatStore.getState().currentConversation();

      expect(conv).toBeDefined();
      expect(conv?.id).toBe(id);
    });

    it('should return null if no current conversation', () => {
      const conv = useChatStore.getState().currentConversation();
      expect(conv).toBeNull();
    });
  });

  describe('clearCurrentConversation', () => {
    it('should clear messages from current conversation', () => {
      useChatStore.getState().createConversation();
      useChatStore.getState().addMessage({ role: 'user', content: 'Test' });
      useChatStore.getState().clearCurrentConversation();
      const state = useChatStore.getState();

      expect(state.conversations[0].messages).toEqual([]);
    });
  });

  describe('setStreaming', () => {
    it('should update streaming state', () => {
      useChatStore.getState().setStreaming(true);
      expect(useChatStore.getState().isStreaming).toBe(true);

      useChatStore.getState().setStreaming(false);
      expect(useChatStore.getState().isStreaming).toBe(false);
    });
  });

  // BUG-107 (régression historique chat, Capov 12/06/2026) : une conversation
  // créée par un agent (préparation de RDV) est locale et NON synchronisée.
  // Cliquer dessus dans la sidebar interroge le backend avec un ID inconnu, qui
  // renvoie [] (HTTP 200) ; setConversationMessages écrasait alors ses messages
  // et la marquait synced:true → la conversation "disparaissait de l'historique".
  describe('setConversationMessages - BUG-107 régression historique', () => {
    it("ne vide PAS une conversation locale non synchronisée si le backend renvoie []", () => {
      // Conversation créée par un agent : locale, non synced, 1 message
      useChatStore.getState().addMessage({
        role: 'assistant',
        content: 'Voici ta préparation de RDV.',
      });
      const convId = useChatStore.getState().currentConversationId!;
      expect(useChatStore.getState().conversations[0].messages).toHaveLength(1);
      expect(useChatStore.getState().conversations[0].synced).toBeFalsy();

      // Le clic sidebar interroge le backend → [] pour un ID local inconnu
      useChatStore.getState().setConversationMessages(convId, []);

      const conv = useChatStore.getState().conversations.find((c) => c.id === convId)!;
      // Le message de l'agent est préservé (sinon il disparaît de l'historique)
      expect(conv.messages).toHaveLength(1);
      expect(conv.messages[0].content).toBe('Voici ta préparation de RDV.');
      // Et la conversation n'est pas marquée synchronisée à tort
      expect(conv.synced).toBeFalsy();
    });

    it('remplace bien les messages quand le backend renvoie du contenu', () => {
      useChatStore.getState().addMessage({ role: 'user', content: 'question' });
      const convId = useChatStore.getState().currentConversationId!;

      useChatStore.getState().setConversationMessages(convId, [
        { id: 'm1', role: 'user', content: 'question', timestamp: new Date() },
        { id: 'm2', role: 'assistant', content: 'réponse', timestamp: new Date() },
      ]);

      const conv = useChatStore.getState().conversations.find((c) => c.id === convId)!;
      expect(conv.messages).toHaveLength(2);
      expect(conv.synced).toBe(true);
    });
  });
});
