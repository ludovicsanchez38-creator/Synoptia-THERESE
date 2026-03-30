/**
 * THERESE v2 - Agent Session
 *
 * Chat streaming avec un agent spawne.
 * Header : bouton retour + icone agent + nom + badge modele LLM.
 * Messages en streaming SSE depuis POST /api/agents/spawn.
 * Input textarea + bouton envoyer pour les follow-up.
 * Tool calls visibles inline (icone outil + nom + resultat collapsible).
 */

import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  ArrowLeft,
  Send,
  Square,
  Wrench,
  ChevronDown,
  ChevronRight,
  Bot,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { streamAgentSpawn } from "../../services/api/agents";
import type { SpawnAgentStreamChunk, AgentProfile } from "../../services/api/agents";

// ============================================================
// Types
// ============================================================

interface AgentSessionMessage {
  id: string;
  role: "user" | "assistant" | "tool_call" | "tool_result" | "error";
  content: string;
  toolName?: string;
  toolArgs?: Record<string, unknown>;
  toolResult?: string;
  isStreaming?: boolean;
}

/** Couleurs par profil */
const COLOR_MAP: Record<string, { accent: string; bg: string }> = {
  cyan: { accent: "text-cyan-400", bg: "bg-cyan-500/10" },
  magenta: { accent: "text-pink-400", bg: "bg-pink-500/10" },
  blue: { accent: "text-blue-400", bg: "bg-blue-500/10" },
  green: { accent: "text-emerald-400", bg: "bg-emerald-500/10" },
  purple: { accent: "text-purple-400", bg: "bg-purple-500/10" },
  amber: { accent: "text-amber-400", bg: "bg-amber-500/10" },
};

const DEFAULT_COLOR = { accent: "text-[#B6C7DA]", bg: "bg-white/5" };

/** Profils par defaut (identiques a AgentCatalog) */
const PROFILE_MAP: Record<string, AgentProfile> = {
  researcher: {
    id: "researcher",
    name: "Chercheur Web",
    description: "Recherche, synthese et veille sur le web",
    icon: "\uD83D\uDD0D",
    color: "cyan",
    tools: ["web_search", "read_file", "write_file"],
    default_model: "claude-sonnet-4-6",
  },
  writer: {
    id: "writer",
    name: "Redacteur",
    description: "Redaction, reformulation et correction de textes",
    icon: "\u270D\uFE0F",
    color: "magenta",
    tools: ["read_file", "write_file"],
    default_model: "claude-sonnet-4-6",
  },
  analyst: {
    id: "analyst",
    name: "Analyste",
    description: "Analyse de donnees, code et documents",
    icon: "\uD83D\uDCCA",
    color: "blue",
    tools: ["read_file", "search_codebase", "run_command"],
    default_model: "claude-sonnet-4-6",
  },
  planner: {
    id: "planner",
    name: "Planificateur",
    description: "Organisation, planning et suivi de projets",
    icon: "\uD83D\uDCC5",
    color: "green",
    tools: ["read_file", "write_file"],
    default_model: "claude-sonnet-4-6",
  },
  coder: {
    id: "coder",
    name: "Codeur",
    description: "Developpement, debug et refactoring",
    icon: "\uD83D\uDCBB",
    color: "purple",
    tools: ["read_file", "write_file", "search_codebase", "run_command", "git_status"],
    default_model: "claude-sonnet-4-6",
  },
  creative: {
    id: "creative",
    name: "Creatif",
    description: "Brainstorming, ideation et contenus visuels",
    icon: "\uD83C\uDFA8",
    color: "amber",
    tools: ["web_search", "write_file"],
    default_model: "claude-sonnet-4-6",
  },
};

// ============================================================
// Sub-components
// ============================================================

/** Indicateur de reflexion */
function ThinkingDots({ color }: { color: string }) {
  return (
    <span className="flex gap-0.5">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className={`inline-block h-1 w-1 rounded-full ${color === "text-cyan-400" ? "bg-cyan-400/60" : color === "text-pink-400" ? "bg-pink-400/60" : color === "text-blue-400" ? "bg-blue-400/60" : color === "text-emerald-400" ? "bg-emerald-400/60" : color === "text-purple-400" ? "bg-purple-400/60" : color === "text-amber-400" ? "bg-amber-400/60" : "bg-white/40"}`}
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{
            repeat: Infinity,
            duration: 1.2,
            delay: i * 0.2,
          }}
        />
      ))}
    </span>
  );
}

/** Tool call collapsible */
function ToolCallBlock({
  toolName,
  toolResult,
}: {
  toolName: string;
  toolResult?: string;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="mx-3 my-1.5 rounded-lg border border-white/5 bg-[#0e1529]">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-xs text-[#B6C7DA] transition hover:bg-white/5"
      >
        <Wrench size={12} className="flex-shrink-0 text-amber-400/70" />
        <span className="flex-1 truncate font-medium">{toolName}</span>
        {toolResult && (
          expanded ? (
            <ChevronDown size={12} className="flex-shrink-0 text-[#6B7280]" />
          ) : (
            <ChevronRight size={12} className="flex-shrink-0 text-[#6B7280]" />
          )
        )}
      </button>
      <AnimatePresence>
        {expanded && toolResult && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden"
          >
            <pre className="border-t border-white/5 px-3 py-2 text-[10px] leading-relaxed text-[#6B7280] overflow-x-auto max-h-40 overflow-y-auto">
              {toolResult}
            </pre>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ============================================================
// Main component
// ============================================================

interface Props {
  profileId: string;
  onBack: () => void;
}

let _sessionMsgCounter = 0;
function genMsgId(): string {
  return `amsg-${Date.now()}-${++_sessionMsgCounter}`;
}

export function AgentSession({ profileId, onBack }: Props) {
  const profile = PROFILE_MAP[profileId];
  const colors = COLOR_MAP[profile?.color || ""] || DEFAULT_COLOR;

  const [messages, setMessages] = useState<AgentSessionMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [activeModel, setActiveModel] = useState<string>(profile?.default_model || "");
  const [needsInitialPrompt, setNeedsInitialPrompt] = useState(true);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Focus input au montage
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleStream = useCallback(
    async (instruction: string) => {
      setIsStreaming(true);
      abortRef.current = new AbortController();

      // Ajouter le message utilisateur
      setMessages((prev) => [
        ...prev,
        {
          id: genMsgId(),
          role: "user",
          content: instruction,
        },
      ]);

      // ID du message assistant en cours de streaming
      const assistantId = genMsgId();
      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: "assistant",
          content: "",
          isStreaming: true,
        },
      ]);

      try {
        for await (const chunk of streamAgentSpawn(
          profileId,
          instruction,
          abortRef.current.signal,
        )) {
          handleChunk(chunk, assistantId);
        }
      } catch (e: unknown) {
        const err = e as { name?: string; message?: string };
        if (err.name !== "AbortError") {
          setMessages((prev) => [
            ...prev,
            {
              id: genMsgId(),
              role: "error",
              content: err.message || "Erreur de connexion au serveur",
            },
          ]);
        }
      } finally {
        // Terminer le streaming
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, isStreaming: false } : m,
          ),
        );
        setIsStreaming(false);
      }
    },
    [profileId],
  );

  const handleChunk = (chunk: SpawnAgentStreamChunk, assistantId: string) => {
    switch (chunk.type) {
      case "agent_start":
        if (chunk.model) {
          setActiveModel(chunk.model);
        }
        break;

      case "chunk":
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: m.content + chunk.content }
              : m,
          ),
        );
        break;

      case "tool_call":
        setMessages((prev) => [
          ...prev,
          {
            id: genMsgId(),
            role: "tool_call",
            content: "",
            toolName: chunk.tool_name || "outil",
            toolArgs: chunk.tool_args,
          },
        ]);
        break;

      case "tool_result":
        // Mettre a jour le dernier tool_call avec le resultat
        setMessages((prev) => {
          let lastToolIdx = -1;
          for (let i = prev.length - 1; i >= 0; i--) {
            if (prev[i].role === "tool_call" && prev[i].toolName === chunk.tool_name) {
              lastToolIdx = i;
              break;
            }
          }
          if (lastToolIdx >= 0) {
            const updated = [...prev];
            updated[lastToolIdx] = {
              ...updated[lastToolIdx],
              toolResult: chunk.tool_result || chunk.content,
            };
            return updated;
          }
          return prev;
        });
        break;

      case "done":
        // Terminer le streaming du message assistant
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, isStreaming: false } : m,
          ),
        );
        break;

      case "error":
        setMessages((prev) => [
          ...prev,
          {
            id: genMsgId(),
            role: "error",
            content: chunk.content || "Erreur inattendue",
          },
        ]);
        break;
    }
  };

  const handleSend = useCallback(() => {
    const trimmed = inputValue.trim();
    if (!trimmed || isStreaming) return;
    setInputValue("");
    setNeedsInitialPrompt(false);
    handleStream(trimmed);
  }, [inputValue, isStreaming, handleStream]);

  const handleCancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-white/5 px-3 py-2.5">
        <button
          onClick={onBack}
          className="flex h-7 w-7 items-center justify-center rounded-lg text-[#6B7280] transition hover:bg-white/5 hover:text-[#E6EDF7]"
          title="Retour au catalogue"
        >
          <ArrowLeft size={16} />
        </button>

        {/* Icone agent */}
        <div
          className={`flex h-7 w-7 items-center justify-center rounded-lg ${colors.bg} text-sm`}
        >
          {profile?.icon || <Bot size={14} />}
        </div>

        {/* Nom agent */}
        <span className={`text-sm font-semibold ${colors.accent}`}>
          {profile?.name || profileId}
        </span>

        {/* Badge modele */}
        {activeModel && (
          <span className="ml-auto rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-[#6B7280]">
            {activeModel}
          </span>
        )}
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto py-2">
        {messages.length === 0 && !isStreaming ? (
          <InitialPrompt
            profile={profile}
            colors={colors}
            show={needsInitialPrompt}
          />
        ) : (
          <AnimatePresence initial={false}>
            {messages.map((msg) => {
              if (msg.role === "tool_call") {
                return (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.15 }}
                  >
                    <ToolCallBlock
                      toolName={msg.toolName || "outil"}
                      toolResult={msg.toolResult}
                    />
                  </motion.div>
                );
              }

              if (msg.role === "error") {
                return (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="mx-3 my-1.5 rounded-lg border border-red-500/20 bg-red-500/5 px-3 py-2 text-xs text-red-400"
                  >
                    {msg.content}
                  </motion.div>
                );
              }

              const isUser = msg.role === "user";

              return (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                  className={`flex gap-2.5 px-3 py-2 ${isUser ? "flex-row-reverse" : ""}`}
                >
                  {/* Avatar */}
                  <div
                    className={`mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full ${
                      isUser
                        ? "bg-cyan-500/10 text-cyan-400"
                        : `${colors.bg}`
                    } text-sm`}
                  >
                    {isUser ? "👤" : profile?.icon || "🤖"}
                  </div>

                  {/* Contenu */}
                  <div className={`max-w-[85%] ${isUser ? "text-right" : ""}`}>
                    {!isUser && (
                      <div
                        className={`mb-0.5 text-xs font-medium ${colors.accent}`}
                      >
                        {profile?.name || profileId}
                      </div>
                    )}
                    <div
                      className="rounded-lg px-3 py-2 text-sm leading-relaxed"
                      style={{
                        backgroundColor: isUser
                          ? "rgba(34, 211, 238, 0.1)"
                          : "rgba(255, 255, 255, 0.03)",
                        borderLeft: isUser ? "none" : "2px solid",
                        borderLeftColor: isUser ? "transparent" : undefined,
                        color: "#E6EDF7",
                      }}
                    >
                      <span style={{ whiteSpace: "pre-wrap" }}>
                        {msg.content}
                      </span>
                      {msg.isStreaming && (
                        <span className="ml-1 inline-block h-3 w-1.5 animate-pulse rounded-sm bg-current opacity-60" />
                      )}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}

        {/* Indicateur de reflexion */}
        {isStreaming &&
          messages.length > 0 &&
          messages[messages.length - 1]?.role === "user" && (
            <div className="flex items-center gap-2 px-3 py-2">
              <div className={`flex h-7 w-7 items-center justify-center rounded-full ${colors.bg} text-sm`}>
                {profile?.icon || "🤖"}
              </div>
              <span className={`text-xs ${colors.accent}/80`}>
                {profile?.name || "Agent"} reflechit
              </span>
              <ThinkingDots color={colors.accent} />
            </div>
          )}
      </div>

      {/* Input */}
      <div className="flex items-end gap-2 border-t border-white/5 bg-[#0B1226] px-3 py-2.5">
        <textarea
          ref={inputRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            needsInitialPrompt
              ? `Decris ta tache pour ${profile?.name || "l'agent"}...`
              : "Message de suivi..."
          }
          disabled={isStreaming}
          rows={1}
          className="flex-1 resize-none rounded-lg border border-white/10 bg-[#131B35] px-3 py-2 text-sm text-[#E6EDF7] placeholder-[#6B7280] outline-none transition focus:border-cyan-500/50 disabled:opacity-50"
          style={{ minHeight: "38px", maxHeight: "120px" }}
          onInput={(e) => {
            const target = e.target as HTMLTextAreaElement;
            target.style.height = "auto";
            target.style.height = `${Math.min(target.scrollHeight, 120)}px`;
          }}
        />

        {isStreaming ? (
          <button
            onClick={handleCancel}
            className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-500/20 text-red-400 transition hover:bg-red-500/30"
            title="Annuler"
          >
            <Square size={16} />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!inputValue.trim()}
            className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/20 text-cyan-400 transition hover:bg-cyan-500/30 disabled:opacity-30 disabled:hover:bg-cyan-500/20"
            title="Envoyer"
          >
            <Send size={16} />
          </button>
        )}
      </div>
    </div>
  );
}

// ============================================================
// Prompt initial (avant le premier message)
// ============================================================

function InitialPrompt({
  profile,
  colors,
  show,
}: {
  profile: AgentProfile | undefined;
  colors: { accent: string; bg: string };
  show: boolean;
}) {
  if (!show || !profile) return null;

  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 px-8 text-center">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.3 }}
        className={`flex h-14 w-14 items-center justify-center rounded-2xl ${colors.bg} text-2xl`}
      >
        {profile.icon}
      </motion.div>
      <div>
        <h3 className={`mb-1 text-sm font-semibold ${colors.accent}`}>
          {profile.name}
        </h3>
        <p className="text-xs leading-relaxed text-[#6B7280]">
          {profile.description}
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-1.5">
        {profile.tools.map((tool) => (
          <span
            key={tool}
            className="rounded bg-white/5 px-2 py-0.5 text-[10px] text-[#6B7280]"
          >
            {tool}
          </span>
        ))}
      </div>
    </div>
  );
}
