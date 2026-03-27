import { useEffect, useRef, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Virtuoso, type VirtuosoHandle } from 'react-virtuoso';
import { useChatStore } from '../../stores/chatStore';
import { useAccessibilityStore } from '../../stores/accessibilityStore';
import { announceToScreenReader } from '../../lib/accessibility';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { HomeCommands } from '../home';
import { EntitySuggestion } from './EntitySuggestion';
import { useDemoMask } from '../../hooks';

interface MessageListProps {
  onPromptSelect?: (prompt: string, skillId?: string) => void;
  onSaveAsCommand?: (userPrompt: string, assistantContent: string) => void;
  onGuidedPanelChange?: (active: boolean) => void;
}

export function MessageList({ onPromptSelect, onSaveAsCommand, onGuidedPanelChange }: MessageListProps) {
  // Subscribe to actual state to trigger re-renders when messages change
  const conversations = useChatStore((state) => state.conversations);
  const currentConversationId = useChatStore((state) => state.currentConversationId);
  const isStreaming = useChatStore((state) => state.isStreaming);
  const clearMessageEntities = useChatStore((state) => state.clearMessageEntities);
  const { enabled: demoEnabled, maskText } = useDemoMask();
  const reduceMotion = useAccessibilityStore((s) => s.reduceMotion);
  const announceMessages = useAccessibilityStore((s) => s.announceMessages);
  const prevMsgCountRef = useRef(0);

  // Compute current conversation from subscribed state
  const conversation = conversations.find((c) => c.id === currentConversationId) || null;
  const virtuosoRef = useRef<VirtuosoHandle>(null);

  const handleEntityDismiss = useCallback((messageId: string) => {
    clearMessageEntities(messageId);
  }, [clearMessageEntities]);

  const handleEntitySaved = useCallback(() => {
    console.log('Entity saved to memory');
  }, []);

  // US-012 : Annoncer les nouveaux messages assistant au lecteur d'écran
  useEffect(() => {
    if (!conversation || !announceMessages) return;
    const msgCount = conversation.messages.length;
    if (msgCount > prevMsgCountRef.current && msgCount > 0) {
      const lastMsg = conversation.messages[msgCount - 1];
      if (lastMsg.role === 'assistant' && !lastMsg.isStreaming) {
        announceToScreenReader('Nouveau message de Therese');
      }
    }
    prevMsgCountRef.current = msgCount;
  }, [conversation?.messages, announceMessages]);

  // Mode démo : masquer le contenu des messages avant rendu
  const displayMessages = useMemo(() => {
    if (!conversation) return [];
    if (!demoEnabled) return conversation.messages;
    return conversation.messages.map((msg) => ({
      ...msg,
      content: maskText(msg.content),
    }));
  }, [demoEnabled, conversation, maskText]);

  // followOutput : scroller automatiquement quand un nouveau message arrive
  const followOutput = useCallback((isAtBottom: boolean) => {
    if (isAtBottom) {
      return 'smooth' as const;
    }
    return false as const;
  }, []);

  // Rendu d'un item dans la liste virtualisée
  const itemContent = useCallback((index: number) => {
    const message = displayMessages[index];
    if (!message) return null;

    return (
      <div
        className="py-2"
        style={{
          contentVisibility: message.isStreaming ? 'visible' : 'auto',
          containIntrinsicSize: 'auto 80px',
        }}
      >
        <MessageBubble
          message={message}
          onSaveAsCommand={
            message.role === 'assistant' && !message.isStreaming && onSaveAsCommand
              ? () => {
                  const msgIndex = displayMessages.indexOf(message);
                  let userPrompt = '';
                  for (let i = msgIndex - 1; i >= 0; i--) {
                    if (displayMessages[i].role === 'user') {
                      userPrompt = displayMessages[i].content;
                      break;
                    }
                  }
                  onSaveAsCommand(userPrompt, message.content);
                }
              : undefined
          }
        />

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
      </div>
    );
  }, [displayMessages, onSaveAsCommand, handleEntityDismiss, handleEntitySaved]);

  // Empty state with guided prompts UI
  if (!conversation || conversation.messages.length === 0) {
    return (
      <div className="h-full overflow-y-auto flex items-center justify-center py-8">
        <HomeCommands onPromptSelect={onPromptSelect || (() => {})} onGuidedPanelChange={onGuidedPanelChange} />
      </div>
    );
  }

  return (
    <div className="h-full" aria-live="polite" aria-label="Messages de la conversation">
      <Virtuoso
        ref={virtuosoRef}
        data={displayMessages}
        totalCount={displayMessages.length}
        overscan={200}
        followOutput={followOutput}
        initialTopMostItemIndex={displayMessages.length - 1}
        alignToBottom
        itemContent={itemContent}
        className="h-full"
        style={{ height: '100%' }}
        components={{
          // Wrapper pour le contenu scrollable avec le bon max-width
          List: ({ style, children, ...props }) => (
            <div {...props} style={style}>
              <div className="max-w-3xl mx-auto px-4 py-6">
                {children}
              </div>
            </div>
          ),
          // Footer : typing indicator + ancre scroll
          Footer: () => (
            <div className="max-w-3xl mx-auto px-4">
              <AnimatePresence>
                {isStreaming && (
                  <motion.div
                    initial={reduceMotion ? false : { opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                  >
                    <TypingIndicator />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ),
        }}
      />
    </div>
  );
}
