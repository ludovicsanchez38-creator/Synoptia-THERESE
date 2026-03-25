/**
 * THÉRÈSE V3 - RFCChat
 *
 * Mini-chat éphémère pour les étapes Réfléchir et Faire du workflow RFC.
 * Utilise un system prompt spécialisé "concepteur de commandes".
 *
 * BUG-097 : ajout AbortController (stop/cancel), timeout 60s,
 *           limite de contenu 8000 caractères pour éviter les boucles infinies.
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Square, Loader2 } from 'lucide-react';
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

/** Limite de contenu par réponse pour couper les boucles LLM (BUG-097) */
const MAX_RESPONSE_LENGTH = 8_000;
/** Timeout global par requête en ms (BUG-097) */
const STREAM_TIMEOUT_MS = 60_000;

export function RFCChat({ systemPrompt, placeholder, initialMessage, onConversationUpdate }: RFCChatProps) {
  const [messages, setMessages] = useState<RFCMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const idCounter = useRef(0);
  const abortRef = useRef<AbortController | null>(null);

  const nextId = () => `rfc-${++idCounter.current}`;

  // Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  // Cleanup : aborter le stream si le composant est démonté (changement d'étape)
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  // Envoyer le message initial si fourni
  useEffect(() => {
    if (initialMessage) {
      sendMessage(initialMessage);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /** Interrompre le streaming en cours (BUG-097) */
  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
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

    // AbortController pour le stop button + timeout (BUG-097)
    const controller = new AbortController();
    abortRef.current = controller;
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, STREAM_TIMEOUT_MS);

    try {
      // Préfixer le message avec le contexte système pour le RFC
      // Ajouter une instruction explicite de ne pas utiliser d'outils (BUG-097)
      const prefixedMessage = `[Instructions système : ${systemPrompt}\n\nIMPORTANT : Tu es dans un mini-chat RFC (Réfléchir-Faire-Capturer). Ne fais PAS d'appels d'outils (web_search, browser, mémoire, etc.). Réponds uniquement avec du texte. Sois concis (max 500 mots par réponse).]\n\nMessage de l'utilisateur : ${content}`;
      const stream = streamMessage({
        message: prefixedMessage,
        stream: true,
        disable_tools: true,  // BUG-097 : pas d'outils dans le mini-chat RFC
      }, controller.signal);

      let accumulated = '';
      let wasTruncated = false;
      for await (const chunk of stream) {
        // Vérifier si annulé (BUG-097)
        if (controller.signal.aborted) break;

        if (chunk.type === 'text') {
          accumulated += chunk.content;

          // Garde-fou : couper si la réponse dépasse la limite (BUG-097)
          if (accumulated.length > MAX_RESPONSE_LENGTH) {
            accumulated = accumulated.slice(0, MAX_RESPONSE_LENGTH);
            wasTruncated = true;
            controller.abort(); // Arrêter le stream
            break;
          }

          setMessages((prev) =>
            prev.map((m) => (m.id === assistantMsg.id ? { ...m, content: accumulated } : m))
          );
        }
        // Ignorer les chunks de type tool_result/status pour le RFC (BUG-097)
      }

      if (wasTruncated) {
        accumulated += '\n\n_(Réponse tronquée - trop longue)_';
      }

      const finalContent = accumulated || (controller.signal.aborted ? '_(Interrompu)_' : '');
      const finalMessages = [...updatedMessages, { ...assistantMsg, content: finalContent }];
      setMessages(finalMessages);
      onConversationUpdate(finalMessages);
    } catch (err) {
      // AbortError = annulation volontaire, pas une erreur
      const isAbort = err instanceof DOMException && err.name === 'AbortError';
      if (isAbort) {
        // Garder le contenu accumulé tel quel
        const currentMessages = [...updatedMessages];
        setMessages((prev) => {
          const lastMsg = prev.find((m) => m.id === assistantMsg.id);
          const content = lastMsg?.content || '_(Interrompu)_';
          const final = [...currentMessages, { ...assistantMsg, content }];
          // Mettre à jour via le callback dans le prochain tick
          setTimeout(() => onConversationUpdate(final), 0);
          return final;
        });
      } else {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? { ...m, content: 'Erreur de communication. Réessaie.' }
              : m
          )
        );
      }
    } finally {
      clearTimeout(timeoutId);
      abortRef.current = null;
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
          {/* BUG-097 : Stop button pendant le streaming */}
          {isStreaming ? (
            <Button
              variant="primary"
              size="icon"
              className="h-9 w-9 flex-shrink-0 bg-error hover:bg-error/80"
              onClick={stopStreaming}
              title="Arrêter la réponse"
            >
              <Square className="w-4 h-4" />
            </Button>
          ) : (
            <Button
              variant="primary"
              size="icon"
              className="h-9 w-9 flex-shrink-0"
              onClick={() => sendMessage()}
              disabled={!input.trim()}
            >
              <Send className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
