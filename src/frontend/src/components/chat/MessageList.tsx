import { useEffect, useRef, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChatStore } from '../../stores/chatStore';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { GuidedPrompts } from '../guided';
import { EntitySuggestion } from './EntitySuggestion';
import { useDemoMask } from '../../hooks';

interface MessageListProps {
  onPromptSelect?: (prompt: string) => void;
}

export function MessageList({ onPromptSelect }: MessageListProps) {
  // Subscribe to actual state to trigger re-renders when messages change
  const conversations = useChatStore((state) => state.conversations);
  const currentConversationId = useChatStore((state) => state.currentConversationId);
  const isStreaming = useChatStore((state) => state.isStreaming);
  const clearMessageEntities = useChatStore((state) => state.clearMessageEntities);
  const { enabled: demoEnabled, maskText } = useDemoMask();

  // Compute current conversation from subscribed state
  const conversation = conversations.find((c) => c.id === currentConversationId) || null;
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const userScrolledUp = useRef(false);

  const handleEntityDismiss = useCallback((messageId: string) => {
    clearMessageEntities(messageId);
  }, [clearMessageEntities]);

  const handleEntitySaved = useCallback(() => {
    // Could trigger a notification or refresh here
    console.log('Entity saved to memory');
  }, []);

  // Détecter si l'utilisateur a scrollé vers le haut (pour ne pas forcer le scroll)
  const handleScroll = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container) return;
    const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
    userScrolledUp.current = distanceFromBottom > 100;
  }, []);

  // Auto-scroll : instant pendant le streaming (pas de secousses), smooth sinon
  useEffect(() => {
    if (userScrolledUp.current) return;
    const container = scrollContainerRef.current;
    if (!container) return;

    if (isStreaming) {
      // Pendant le streaming : scroll instantané vers le bas (pas de smooth qui se battent)
      container.scrollTop = container.scrollHeight;
    } else {
      // Nouveau message ou fin de streaming : smooth scroll
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversation?.messages, isStreaming]);

  // Quand un nouveau message utilisateur est envoyé, reset le flag
  useEffect(() => {
    userScrolledUp.current = false;
  }, [conversation?.messages?.length]);

  // Mode démo : masquer le contenu des messages avant rendu
  const displayMessages = useMemo(() => {
    if (!conversation) return [];
    if (!demoEnabled) return conversation.messages;
    return conversation.messages.map((msg) => ({
      ...msg,
      content: maskText(msg.content),
    }));
  }, [demoEnabled, conversation, maskText]);

  // Empty state with guided prompts UI
  if (!conversation || conversation.messages.length === 0) {
    return (
      <div className="h-full overflow-y-auto flex items-center justify-center py-8">
        <GuidedPrompts onPromptSelect={onPromptSelect || (() => {})} />
      </div>
    );
  }

  return (
    <div ref={scrollContainerRef} onScroll={handleScroll} className="h-full overflow-y-auto px-4 py-6">
      <div className="max-w-3xl mx-auto space-y-4">
        <AnimatePresence initial={false}>
          {displayMessages.map((message, index) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{
                duration: 0.2,
                delay: index * 0.03,
              }}
            >
              <MessageBubble message={message} />

              {/* Show entity suggestions after assistant messages */}
              {message.role === 'assistant' && message.detectedEntities && (
                (message.detectedEntities.contacts.length > 0 ||
                  message.detectedEntities.projects.length > 0) && (
                  <EntitySuggestion
                    contacts={message.detectedEntities.contacts}
                    projects={message.detectedEntities.projects}
                    messageId={message.id}
                    onDismiss={() => handleEntityDismiss(message.id)}
                    onSaved={handleEntitySaved}
                  />
                )
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {isStreaming && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <TypingIndicator />
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
