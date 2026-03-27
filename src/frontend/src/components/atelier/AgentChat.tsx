/**
 * THÉRÈSE v2 - Agent Chat (US-002)
 *
 * Chat interactif avec un agent OpenClaw.
 * Messages a gauche (Katia), a droite (utilisateur), input en bas.
 * Indicateur "Katia reflechit...", scroll auto, actions distinctes, bouton Copier.
 */

import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Square,
  RefreshCw,
  XCircle,
  Headphones,
  User,
  Copy,
  Check,
  Zap,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useOpenClawStore } from "../../stores/openclawStore";
import { useAccessibilityStore } from "../../stores/accessibilityStore";
import { announceToScreenReader } from "../../lib/accessibility";

/** Detecte si un message est une "action" Katia (email, fichier, etc.) */
function isActionMessage(content: string): boolean {
  const actionPrefixes = [
    "\u2709\ufe0f", // enveloppe
    "\u2705",       // check vert
    "\ud83d\udcc4", // page
    "\ud83d\udce8", // incoming envelope
    "\ud83d\udce7", // e-mail
    "\u270f\ufe0f", // crayon
    "\ud83d\udd0d", // loupe
    "\ud83d\udcc1", // dossier
    "\u26a1",       // eclair
    "[ACTION]",
    "[DONE]",
  ];
  return actionPrefixes.some((p) => content.trimStart().startsWith(p));
}

/** Composant "Katia reflechit..." anime */
function ThinkingIndicator() {
  const reduceMotion = useAccessibilityStore((s) => s.reduceMotion);

  return (
    <div className="flex items-center gap-2.5 px-3 py-2">
      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-purple-500/10">
        <Headphones size={14} className={reduceMotion ? "text-purple-400" : "text-purple-400 animate-pulse"} />
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-purple-400/80">Katia reflechit</span>
        {!reduceMotion && (
          <span className="flex gap-0.5">
            {[0, 1, 2].map((i) => (
              <motion.span
                key={i}
                className="inline-block h-1 w-1 rounded-full bg-purple-400/60"
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{
                  repeat: Infinity,
                  duration: 1.2,
                  delay: i * 0.2,
                }}
              />
            ))}
          </span>
        )}
      </div>
    </div>
  );
}

/** Bouton copier le contenu */
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback silencieux
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="rounded p-0.5 text-[#6B7280] transition hover:bg-white/5 hover:text-[#B6C7DA]"
      title="Copier le message"
      aria-label="Copier le message"
    >
      {copied ? <Check size={12} className="text-green-400" /> : <Copy size={12} />}
    </button>
  );
}

export function AgentChat() {
  const {
    activeSessionId,
    activeSessionMessages,
    sessions,
    isSending,
    sendMessage,
    refreshActiveSession,
    cancelSession,
  } = useOpenClawStore();

  const reduceMotion = useAccessibilityStore((s) => s.reduceMotion);

  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const prevMessageCountRef = useRef(0);

  // Session active
  const activeSession = sessions.find((s) => s.id === activeSessionId);

  // Auto-scroll quand les messages changent
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: reduceMotion ? "auto" : "smooth",
      });
    }
  }, [activeSessionMessages, reduceMotion]);

  // Annoncer les nouveaux messages pour les lecteurs d ecran
  useEffect(() => {
    const count = activeSessionMessages.length;
    if (count > prevMessageCountRef.current && count > 0) {
      const lastMsg = activeSessionMessages[count - 1];
      if (lastMsg.role !== "user" && lastMsg.role !== "human") {
        announceToScreenReader("Nouveau message de Katia");
      }
    }
    prevMessageCountRef.current = count;
  }, [activeSessionMessages]);

  // Polling des messages si la session est running
  useEffect(() => {
    if (activeSession?.status === "running") {
      pollRef.current = setInterval(() => {
        refreshActiveSession();
      }, 3000);
    }

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [activeSession?.status, activeSession?.id, refreshActiveSession]);

  const handleSend = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || !activeSessionId || isSending) return;
    setInput("");
    await sendMessage(activeSessionId, trimmed);
    inputRef.current?.focus();
  }, [input, activeSessionId, isSending, sendMessage]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Indicateur "reflechit" : session running et aucun nouveau message recemment
  const showThinking =
    activeSession?.status === "running" &&
    (activeSessionMessages.length === 0 ||
      (activeSessionMessages.length > 0 &&
        activeSessionMessages[activeSessionMessages.length - 1].role !== "assistant"));

  if (!activeSessionId || !activeSession) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 px-8 text-center">
        <Headphones size={32} className="text-purple-400/30" />
        <p className="text-xs text-[#6B7280]">
          Selectionnez une session ou lancez une nouvelle tache.
        </p>
      </div>
    );
  }

  const messageVariants = reduceMotion
    ? {}
    : {
        initial: { opacity: 0, y: 8 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.2 },
      };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Session header */}
      <div className="flex items-center justify-between border-b border-white/5 px-3 py-2">
        <div className="flex-1 min-w-0">
          <p className="truncate text-xs font-medium text-[#E6EDF7]">
            {activeSession.instruction.length > 80
              ? activeSession.instruction.slice(0, 80) + "..."
              : activeSession.instruction}
          </p>
          <p className="text-[10px] text-[#6B7280]">
            Agent : {activeSession.agent_name} - {activeSession.status}
            {activeSession.actions_count > 0 && (
              <> - {activeSession.actions_count} action{activeSession.actions_count > 1 ? "s" : ""}</>
            )}
          </p>
        </div>
        <div className="flex items-center gap-1 ml-2">
          <button
            onClick={refreshActiveSession}
            className="rounded p-1 text-[#6B7280] transition hover:bg-white/5 hover:text-[#B6C7DA]"
            title="Rafraichir"
            aria-label="Rafraichir la session"
          >
            <RefreshCw size={12} />
          </button>
          {activeSession.status === "running" && (
            <button
              onClick={() => cancelSession(activeSessionId)}
              className="rounded p-1 text-red-400/70 transition hover:bg-red-500/10 hover:text-red-400"
              title="Annuler la session"
              aria-label="Annuler la session"
            >
              <XCircle size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto py-2"
        aria-live="polite"
        aria-label="Messages de la session"
      >
        {activeSessionMessages.length === 0 && !showThinking ? (
          <div className="flex flex-col items-center justify-center gap-2 py-12 text-center">
            {activeSession.status === "running" ? (
              <>
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-500/10">
                  <Headphones size={20} className="animate-pulse text-purple-400" />
                </div>
                <p className="text-xs text-[#6B7280]">Katia travaille sur la tache...</p>
              </>
            ) : (
              <p className="text-xs text-[#6B7280]">Aucun message dans cette session.</p>
            )}
          </div>
        ) : (
          <>
            <AnimatePresence initial={false}>
              {activeSessionMessages.map((msg, idx) => {
                const isUser = msg.role === "user" || msg.role === "human";
                const isAction = !isUser && isActionMessage(msg.content);
                const isLongMessage = msg.content.length > 200;

                return (
                  <motion.div
                    key={idx}
                    {...messageVariants}
                    className={`flex gap-2.5 px-3 py-2 ${isUser ? "flex-row-reverse" : ""}`}
                  >
                    {/* Avatar */}
                    <div
                      className={`mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full ${
                        isUser
                          ? "bg-cyan-500/10 text-cyan-400"
                          : isAction
                          ? "bg-amber-500/10 text-amber-400"
                          : "bg-purple-500/10 text-purple-400"
                      }`}
                    >
                      {isUser ? (
                        <User size={14} />
                      ) : isAction ? (
                        <Zap size={14} />
                      ) : (
                        <Headphones size={14} />
                      )}
                    </div>

                    {/* Message */}
                    <div className={`max-w-[85%] ${isUser ? "text-right" : ""}`}>
                      {!isUser && (
                        <div className="mb-0.5 flex items-center gap-1.5">
                          <span className={`text-xs font-medium ${isAction ? "text-amber-400" : "text-purple-400"}`}>
                            {isAction ? "Action" : "Katia"}
                          </span>
                          {isLongMessage && <CopyButton text={msg.content} />}
                        </div>
                      )}
                      <div
                        className={`rounded-lg px-3 py-2 text-sm leading-relaxed ${
                          isAction
                            ? "border border-amber-500/20 bg-amber-500/5"
                            : ""
                        }`}
                        style={
                          isAction
                            ? {
                                borderLeft: "2px solid #F59E0B",
                                color: "#E6EDF7",
                              }
                            : {
                                backgroundColor: isUser
                                  ? "rgba(34, 211, 238, 0.1)"
                                  : "rgba(168, 85, 247, 0.1)",
                                borderLeft: isUser ? "none" : "2px solid #A855F7",
                                color: "#E6EDF7",
                              }
                        }
                      >
                        <span style={{ whiteSpace: "pre-wrap" }}>{msg.content}</span>
                      </div>
                      {msg.timestamp && (
                        <div className="mt-0.5 flex items-center gap-1.5">
                          <span className="text-[10px] text-[#6B7280]">
                            {new Date(msg.timestamp).toLocaleTimeString("fr-FR", {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                          {isUser && isLongMessage && <CopyButton text={msg.content} />}
                        </div>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>

            {/* Indicateur "Katia reflechit..." */}
            {showThinking && <ThinkingIndicator />}
          </>
        )}
      </div>

      {/* Input (only if session is running) */}
      {activeSession.status === "running" && (
        <div className="flex items-end gap-2 border-t border-white/5 bg-[#0B1226] px-3 py-2.5">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Envoyer un message a Katia..."
            disabled={isSending}
            rows={1}
            className="flex-1 resize-none rounded-lg border border-white/10 bg-[#131B35] px-3 py-2 text-sm text-[#E6EDF7] placeholder-[#6B7280] outline-none transition focus:border-purple-500/50 disabled:opacity-50"
            style={{ minHeight: "38px", maxHeight: "120px" }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = "auto";
              target.style.height = `${Math.min(target.scrollHeight, 120)}px`;
            }}
          />
          {isSending ? (
            <button
              className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-500/20 text-gray-400"
              disabled
            >
              <Square size={16} className="animate-pulse" />
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="flex h-9 w-9 items-center justify-center rounded-lg bg-purple-500/20 text-purple-400 transition hover:bg-purple-500/30 disabled:opacity-30"
              title="Envoyer"
              aria-label="Envoyer le message"
            >
              <Send size={16} />
            </button>
          )}
        </div>
      )}

      {/* Session terminee */}
      {activeSession.status !== "running" && (
        <div className="border-t border-white/5 px-3 py-2 text-center">
          <span className="text-xs text-[#6B7280]">
            Session {activeSession.status === "done" ? "terminee" : activeSession.status === "error" ? "en erreur" : "annulee"}
            {activeSession.result_summary && (
              <span title={activeSession.result_summary}>
                {" "}- {activeSession.result_summary.length > 80
                  ? activeSession.result_summary.slice(0, 80) + "..."
                  : activeSession.result_summary}
              </span>
            )}
          </span>
        </div>
      )}
    </div>
  );
}
