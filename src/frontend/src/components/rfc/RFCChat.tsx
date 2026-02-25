/**
 * THÉRÈSE V3 - RFCChat
 *
 * Mini-chat éphémère pour les étapes Réfléchir et Faire du workflow RFC.
 * Utilise un system prompt spécialisé "concepteur de commandes".
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { streamMessage } from '../../services/api';
import { cn } from '../../lib/utils';

interface RFCMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface RFCChatProps {
  systemPrompt: string;
  placeholder: string;
  initialMessage?: string;
  onConversationUpdate: (messages: RFCMessage[]) => void;
}

export function RFCChat({ systemPrompt, placeholder, initialMessage, onConversationUpdate }: RFCChatProps) {
  const [messages, setMessages] = useState<RFCMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const idCounter = useRef(0);

  const nextId = () => `rfc-${++idCounter.current}`;

  // Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  // Envoyer le message initial si fourni
  useEffect(() => {
    if (initialMessage) {
      sendMessage(initialMessage);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sendMessage = useCallback(async (text?: string) => {
    const content = text || input.trim();
    if (!content || isStreaming) return;

    const userMsg: RFCMessage = { id: nextId(), role: 'user', content };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInput('');
    setIsStreaming(true);

    const assistantMsg: RFCMessage = { id: nextId(), role: 'assistant', content: '' };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      // Préfixer le message avec le contexte système pour le RFC
      const prefixedMessage = `[Instructions système : ${systemPrompt}]\n\nMessage de l'utilisateur : ${content}`;
      const stream = streamMessage({
        message: prefixedMessage,
        stream: true,
      });

      let accumulated = '';
      for await (const chunk of stream) {
        if (chunk.type === 'text') {
          accumulated += chunk.content;
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantMsg.id ? { ...m, content: accumulated } : m))
          );
        }
      }

      const finalMessages = [...updatedMessages, { ...assistantMsg, content: accumulated }];
      setMessages(finalMessages);
      onConversationUpdate(finalMessages);
    } catch (_err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsg.id
            ? { ...m, content: 'Erreur de communication. Réessaie.' }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
    }
  }, [input, isStreaming, messages, systemPrompt, onConversationUpdate]);

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-3 p-3">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                'px-3 py-2 rounded-xl text-sm max-w-[85%]',
                msg.role === 'user'
                  ? 'ml-auto bg-accent-cyan/10 text-text'
                  : 'mr-auto bg-surface-elevated text-text',
              )}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </motion.div>
          ))}
        </AnimatePresence>

        {isStreaming && messages[messages.length - 1]?.content === '' && (
          <div className="flex items-center gap-2 text-text-muted text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            THÉRÈSE réfléchit...
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-3 border-t border-border">
        <div className="flex items-end gap-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder={placeholder}
            disabled={isStreaming}
            rows={2}
            className="flex-1 resize-none bg-surface-elevated/60 text-text text-sm leading-5 rounded-lg px-3 py-2 border border-border focus:border-accent-cyan/50 focus:outline-none placeholder:text-text-muted"
          />
          <Button
            variant="primary"
            size="icon"
            className="h-9 w-9 flex-shrink-0"
            onClick={() => sendMessage()}
            disabled={isStreaming || !input.trim()}
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
