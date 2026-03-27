/**
 * THÉRÈSE v2 - Agent Chat (US-001)
 *
 * Chat interactif avec un agent OpenClaw.
 * Messages a gauche (Katia), a droite (utilisateur), input en bas.
 */

import React, { useState, useRef, useEffect, useCallback } from "react";
import { Send, Square, RefreshCw, XCircle, Headphones, User } from "lucide-react";
import { useOpenClawStore } from "../../stores/openclawStore";

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

  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Session active
  const activeSession = sessions.find((s) => s.id === activeSessionId);

  // Auto-scroll quand les messages changent
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
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

  if (!activeSessionId || !activeSession) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 px-8 text-center">
        <Headphones size={32} className="text-purple-400/30" />
        <p className="text-xs text-[#6B7280]">
          Sélectionnez une session ou lancez une nouvelle tâche.
        </p>
      </div>
    );
  }

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
          </p>
        </div>
        <div className="flex items-center gap-1 ml-2">
          <button
            onClick={refreshActiveSession}
            className="rounded p-1 text-[#6B7280] transition hover:bg-white/5 hover:text-[#B6C7DA]"
            title="Rafraîchir"
          >
            <RefreshCw size={12} />
          </button>
          {activeSession.status === "running" && (
            <button
              onClick={() => cancelSession(activeSessionId)}
              className="rounded p-1 text-red-400/70 transition hover:bg-red-500/10 hover:text-red-400"
              title="Annuler la session"
            >
              <XCircle size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto py-2">
        {activeSessionMessages.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 py-12 text-center">
            {activeSession.status === "running" ? (
              <>
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-500/10">
                  <Headphones size={20} className="animate-pulse text-purple-400" />
                </div>
                <p className="text-xs text-[#6B7280]">Katia travaille sur la tâche...</p>
              </>
            ) : (
              <p className="text-xs text-[#6B7280]">Aucun message dans cette session.</p>
            )}
          </div>
        ) : (
          activeSessionMessages.map((msg, idx) => {
            const isUser = msg.role === "user" || msg.role === "human";
            return (
              <div
                key={idx}
                className={`flex gap-2.5 px-3 py-2 ${isUser ? "flex-row-reverse" : ""}`}
              >
                {/* Avatar */}
                <div
                  className={`mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full ${
                    isUser
                      ? "bg-cyan-500/10 text-cyan-400"
                      : "bg-purple-500/10 text-purple-400"
                  }`}
                >
                  {isUser ? <User size={14} /> : <Headphones size={14} />}
                </div>

                {/* Message */}
                <div className={`max-w-[85%] ${isUser ? "text-right" : ""}`}>
                  {!isUser && (
                    <div className="mb-0.5 text-xs font-medium text-purple-400">Katia</div>
                  )}
                  <div
                    className="rounded-lg px-3 py-2 text-sm leading-relaxed"
                    style={{
                      backgroundColor: isUser
                        ? "rgba(34, 211, 238, 0.1)"
                        : "rgba(168, 85, 247, 0.1)",
                      borderLeft: isUser ? "none" : "2px solid #A855F7",
                      color: "#E6EDF7",
                    }}
                  >
                    <span style={{ whiteSpace: "pre-wrap" }}>{msg.content}</span>
                  </div>
                  {msg.timestamp && (
                    <div className="mt-0.5 text-[10px] text-[#6B7280]">
                      {new Date(msg.timestamp).toLocaleTimeString("fr-FR", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </div>
                  )}
                </div>
              </div>
            );
          })
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
            placeholder="Envoyer un message à Katia..."
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
            >
              <Send size={16} />
            </button>
          )}
        </div>
      )}

      {/* Session terminée */}
      {activeSession.status !== "running" && (
        <div className="border-t border-white/5 px-3 py-2 text-center">
          <span className="text-xs text-[#6B7280]">
            Session {activeSession.status === "done" ? "terminée" : activeSession.status === "error" ? "en erreur" : "annulée"}
            {activeSession.result_summary && ` - ${activeSession.result_summary}`}
          </span>
        </div>
      )}
    </div>
  );
}
