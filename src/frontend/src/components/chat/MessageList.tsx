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
import { computeFollowOutput } from './followOutput';
import type { Message } from '../../stores/chatStore';

interface MessageListProps {
  onPromptSelect?: (prompt: string, skillId?: string) => void;
  onSaveAsCommand?: (userPrompt: string, assistantContent: string) => void;
  onGuidedPanelChange?: (active: boolean) => void;
}

// Revue adversariale US-010 : Header/Footer au niveau MODULE. Définis inline,
// leur identité changeait à chaque rendu et react-virtuoso (comparaison par
// référence) démontait/remontait le sous-arbre à chaque flush de phrase :
// l'animation d'entrée du TypingIndicator rejouait en boucle pendant tout le
// stream. Le Footer lit les stores directement pour rester autonome.
function ListHeader() {
  return <div className="pt-4" aria-hidden="true" />;
}

function ListFooter() {
  const isStreaming = useChatStore((state) => state.isStreaming);
  const reduceMotion = useAccessibilityStore((s) => s.reduceMotion);
  return (
    <div className="max-w-3xl mx-auto px-4 pb-4">
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
  );
}

export function MessageList({ onPromptSelect, onSaveAsCommand, onGuidedPanelChange }: MessageListProps) {
  // Subscribe to actual state to trigger re-renders when messages change
  const conversations = useChatStore((state) => state.conversations);
  const currentConversationId = useChatStore((state) => state.currentConversationId);
  const isStreaming = useChatStore((state) => state.isStreaming);
  const clearMessageEntities = useChatStore((state) => state.clearMessageEntities);
  const { enabled: demoEnabled, maskText } = useDemoMask();
  const announceMessages = useAccessibilityStore((s) => s.announceMessages);
  const prevMsgCountRef = useRef(0);

  // Compute current conversation from subscribed state
  const conversation = conversations.find((c) => c.id === currentConversationId) || null;

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
        announceToScreenReader('Nouveau message de Thérèse');
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

  // US-010 : le scroll ne « colle » au bas que si l'utilisateur y est déjà.
  // react-virtuoso gère la position ; followOutput décide du comportement.
  const followOutput = useCallback(
    (isAtBottom: boolean) => computeFollowOutput(isAtBottom, isStreaming),
    [isStreaming]
  );

  // Suggestion Dr_logic 20/07 : ENVOYER un message ramène toujours en bas
  // (même si on avait remonté l'historique) ; pendant la réponse, le scroll
  // manuel reste respecté (followOutput ci-dessus ne change pas).
  const virtuosoRef = useRef<VirtuosoHandle>(null);
  useEffect(() => {
    const onScrollBottom = () => {
      virtuosoRef.current?.scrollToIndex({ index: 'LAST', behavior: 'smooth' });
    };
    window.addEventListener('therese:scroll-chat-bottom', onScrollBottom);
    return () => window.removeEventListener('therese:scroll-chat-bottom', onScrollBottom);
  }, []);

  const itemContent = useCallback(
    (index: number, message: Message) => (
      <div className="max-w-3xl mx-auto px-4 py-2" data-testid="chat-message-item">
        <MessageBubble
          message={message}
          onSaveAsCommand={
            message.role === 'assistant' && !message.isStreaming && onSaveAsCommand
              ? () => {
                  let userPrompt = '';
                  for (let i = index - 1; i >= 0; i--) {
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
    ),
    [displayMessages, onSaveAsCommand, handleEntityDismiss, handleEntitySaved]
  );

  // Empty state with guided prompts UI
  if (!conversation || conversation.messages.length === 0) {
    return (
      <div className="h-full overflow-y-auto flex items-center justify-center py-8">
        <HomeCommands onPromptSelect={onPromptSelect || (() => {})} onGuidedPanelChange={onGuidedPanelChange} />
      </div>
    );
  }

  return (
    // Revue adversariale US-010 : PAS d'aria-live sur un conteneur virtualisé
    // (remonter une vieille conversation monte d'anciens messages dans le DOM
    // -> le lecteur d'écran les annoncerait comme nouveaux). Les nouveaux
    // messages sont annoncés via announceToScreenReader (canal dédié).
    <div
      className="h-full"
      aria-label="Messages de la conversation"
      data-testid="chat-message-list"
    >
      {/* US-010 : virtualisation - seuls les messages visibles sont montés,
          les longues conversations restent fluides.
          key={conversation.id} : changer de conversation REMONTE la liste,
          donc initialTopMostItemIndex repositionne en bas (sinon on héritait
          d'un offset en pixels arbitraire de la conversation précédente). */}
      <Virtuoso
        ref={virtuosoRef}
        key={conversation.id}
        style={{ height: '100%' }}
        data={displayMessages}
        computeItemKey={(index, message) => message.id || String(index)}
        itemContent={itemContent}
        followOutput={followOutput}
        atBottomThreshold={120}
        initialTopMostItemIndex={Math.max(0, displayMessages.length - 1)}
        increaseViewportBy={{ top: 400, bottom: 400 }}
        components={{ Header: ListHeader, Footer: ListFooter }}
      />
    </div>
  );
}
