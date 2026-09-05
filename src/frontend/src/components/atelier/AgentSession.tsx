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
import { getAgentProfiles, streamAgentSpawn } from "../../services/api/agents";
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

/**
 * Couleurs par profil.
 *
 * B-296 : `accent` et `bordure` sont ECRITS EN TOUTES LETTRES, jamais composes
 * a l'execution. Tailwind 4 ne genere que les classes qu'il lit litteralement
 * dans les sources : `${colors.accent}/80`, assemble au rendu, n'apparaissait
 * nulle part et cinq profils sur six affichaient la mention « <nom> reflechit »
 * dans la couleur de texte par defaut au lieu de leur accent.
 *
 * L'attenuation a 80 % n'a PAS ete retablie en classe litterale : composee sur
 * le fond clair (#F3F6FC) elle donne 4,42:1 pour le cyan comme pour le vert,
 * sous les 4,5:1 qu'exige RULES-DESIGN section 1.2 pour du texte de 12 px ; et
 * pour le profil inconnu, une opacite sur le jeton de texte secondaire tombe
 * sous une regle deja testee par opaciteSurLeTexte.test.ts. La mention porte
 * donc l'accent plein, comme le nom du profil juste au-dessus : de 6,9:1 a
 * 11,1:1 selon le profil et le theme.
 */
const COLOR_MAP: Record<string, { accent: string; bordure: string; bg: string }> = {
  cyan: {
    accent: "text-agent-cyan",
    bordure: "border-l-agent-cyan",
    bg: "bg-agent-cyan/10",
  },
  magenta: {
    accent: "text-agent-magenta",
    bordure: "border-l-agent-magenta",
    bg: "bg-agent-magenta/10",
  },
  blue: {
    accent: "text-agent-blue",
    bordure: "border-l-agent-blue",
    bg: "bg-agent-blue/10",
  },
  green: {
    accent: "text-agent-green",
    bordure: "border-l-agent-green",
    bg: "bg-agent-green/10",
  },
  purple: {
    accent: "text-agent-purple",
    bordure: "border-l-agent-purple",
    bg: "bg-agent-purple/10",
  },
  amber: {
    accent: "text-agent-amber",
    bordure: "border-l-agent-amber",
    bg: "bg-agent-amber/10",
  },
};

const DEFAULT_COLOR = {
  accent: "text-text-muted",
  bordure: "border-l-border",
  bg: "bg-surface-2",
};

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
    description: "Analyse de données, code et documents",
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
          className={`inline-block h-1 w-1 rounded-full ${color === "text-agent-cyan" ? "bg-[var(--color-agent-cyan)]/60" : color === "text-agent-magenta" ? "bg-[var(--color-agent-magenta)]/60" : color === "text-agent-blue" ? "bg-[var(--color-agent-blue)]/60" : color === "text-agent-green" ? "bg-[var(--color-agent-green)]/60" : color === "text-agent-purple" ? "bg-[var(--color-agent-purple)]/60" : color === "text-agent-amber" ? "bg-[var(--color-agent-amber)]/60" : "bg-white/40"}`}
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
    <div className="mx-3 my-1.5 rounded-md border border-border bg-surface-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm text-text-muted transition hover:bg-surface-elevated"
      >
        <Wrench size={12} className="flex-shrink-0 text-agent-amber/70" />
        <span className="flex-1 truncate font-medium">{toolName}</span>
        {toolResult && (
          expanded ? (
            <ChevronDown size={12} className="flex-shrink-0 text-text-muted" />
          ) : (
            <ChevronRight size={12} className="flex-shrink-0 text-text-muted" />
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
            <pre className="border-t border-border px-3 py-2 text-xs leading-relaxed text-text-muted overflow-x-auto max-h-40 overflow-y-auto">
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
  model?: string;
  onBack: () => void;
}

let _sessionMsgCounter = 0;
function genMsgId(): string {
  return `amsg-${Date.now()}-${++_sessionMsgCounter}`;
}

export function AgentSession({ profileId, model, onBack }: Props) {
  // B-393 : les outils annoncés dans la carte de consentement viennent du
  // serveur (déjà filtrés), la table locale ne sert que de repli d'affichage.
  const [serverProfile, setServerProfile] = useState<AgentProfile | null>(null);
  const [profilCharge, setProfilCharge] = useState(false);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const profils = await getAgentProfiles();
        if (cancelled) return;
        const trouve = profils.find((p) => p.id === profileId);
        if (trouve) setServerProfile(trouve);
      } catch {
        /* repli sur la table locale */
      } finally {
        if (!cancelled) setProfilCharge(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [profileId]);
  const profile = serverProfile ?? PROFILE_MAP[profileId];
  // B-522 : un profil inconnu du client ET du serveur rendait un écran muet.
  const profilIntrouvable = profilCharge && !profile;
  const colors = COLOR_MAP[profile?.color || ""] || DEFAULT_COLOR;

  const [messages, setMessages] = useState<AgentSessionMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [activeModel, setActiveModel] = useState<string>(model || profile?.default_model || "");
  const [needsInitialPrompt, setNeedsInitialPrompt] = useState(true);
  const [pendingInstruction, setPendingInstruction] = useState<string | null>(null);

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
          activeModel || undefined,
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
    [activeModel, profileId],
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
    setPendingInstruction(trimmed);
  }, [inputValue, isStreaming]);

  const confirmSend = useCallback(() => {
    if (!pendingInstruction) return;
    const instruction = pendingInstruction;
    setPendingInstruction(null);
    setInputValue("");
    setNeedsInitialPrompt(false);
    void handleStream(instruction);
  }, [handleStream, pendingInstruction]);

  const handleCancel = useCallback(() => {
    abortRef.current?.abort();
    // Failsafe : forcer le reset de l'UI même si le stream ne se termine pas proprement
    setIsStreaming(false);
    setMessages((prev) =>
      prev.map((m) =>
        m.isStreaming ? { ...m, isStreaming: false } : m,
      ),
    );
  }, []);

  useEffect(() => () => abortRef.current?.abort(), []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-border px-3 py-2.5">
        <button
          onClick={onBack}
          className="flex h-7 w-7 items-center justify-center rounded-md text-text-muted transition hover:bg-surface-2 hover:text-text"
          title="Retour au catalogue"
        >
          <ArrowLeft size={16} />
        </button>

        {/* Icone agent */}
        <div
          className={`flex h-7 w-7 items-center justify-center rounded-md ${colors.bg} text-sm`}
        >
          {profile?.icon || <Bot size={14} />}
        </div>

        {/* Nom agent */}
        <span className={`text-sm font-semibold ${colors.accent}`}>
          {profile?.name || profileId}
        </span>

        {/* Badge modele */}
        {activeModel && (
          <span className="ml-auto rounded-sm bg-surface-2 px-1.5 py-0.5 text-xs text-text-muted">
            {activeModel}
          </span>
        )}
      </div>

      {profilIntrouvable && (
        <p role="alert" className="mx-3 mt-2 rounded-md border border-error/40 bg-[var(--color-error-tint)] p-3 text-sm text-error">
          Profil d’agent « {profileId} » introuvable, ni sur le serveur ni dans la liste locale. Reviens à la liste et choisis un autre agent.
        </p>
      )}

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
                    role="alert"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="mx-3 my-1.5 rounded-md border border-error/20 bg-error/5 px-3 py-2 text-xs text-error"
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
                        ? "bg-agent-cyan/10 text-agent-cyan"
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
                    {/* B-294 : surfaces prises dans les jetons du theme (le
                        rgba litteral rendait la bulle d'agent invisible en
                        theme clair). B-290 : le lisere porte une couleur
                        DECLAREE - « 2px solid » sans borderLeftColor retombait
                        sur currentColor, donc sur l'encre du texte - et tient
                        en 1 px (RULES-DESIGN section 12). */}
                    <div
                      className={`rounded-md px-3 py-2 text-sm leading-relaxed text-text ${
                        isUser
                          ? "bg-agent-cyan/10"
                          : `bg-surface-2 border-l ${colors.bordure}`
                      }`}
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
              <span className={`text-xs ${colors.accent}`}>
                {profile?.name || "Agent"} reflechit
              </span>
              <ThinkingDots color={colors.accent} />
            </div>
          )}
      </div>

      {/* Input */}
      {pendingInstruction && (
        <div className="border-t border-border bg-bg px-3 pt-3" data-testid="agent-profile-confirmation">
          <div className="rounded-md border border-agent-amber/40 bg-agent-amber/10 p-3 text-xs text-text">
            <div className="font-semibold">Confirmer l&apos;appel de cet agent expérimental</div>
            <p className="mt-1 leading-relaxed text-text-muted">
              Modèle : {activeModel || "non identifié"}. Outils déclarés : {profile?.tools.join(", ") || "aucun"}.
              Les extraits utiles et ta demande peuvent être transmis au fournisseur du modèle.
              Cet échange n&apos;est pas conservé après fermeture.
            </p>
            <div className="mt-3 flex justify-end gap-2">
              <button type="button" onClick={() => setPendingInstruction(null)} className="rounded-md border border-border px-3 py-1.5 font-medium text-text-muted">Retour</button>
              <button type="button" onClick={confirmSend} className="rounded-md bg-success px-3 py-1.5 font-semibold text-ink-on-fill">Confirmer l&apos;appel</button>
            </div>
          </div>
        </div>
      )}
      <div className="flex items-end gap-2 border-t border-border bg-bg px-3 py-2.5">
        <textarea aria-label="Message à l’agent"
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
          className="flex-1 resize-none rounded-md border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted outline-none transition focus:border-agent-cyan/50 disabled:opacity-50"
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
            className="flex h-9 w-9 items-center justify-center rounded-md bg-error/20 text-error transition hover:bg-error/30"
            title="Annuler"
          >
            <Square size={16} />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!inputValue.trim()}
            className="flex h-9 w-9 items-center justify-center rounded-md bg-agent-cyan/20 text-agent-cyan transition hover:bg-agent-cyan/30 disabled:opacity-30 disabled:hover:bg-agent-cyan/20"
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
        className={`flex h-14 w-14 items-center justify-center rounded-md ${colors.bg} text-2xl`}
      >
        {profile.icon}
      </motion.div>
      <div>
        <h3 className={`mb-1 text-sm font-semibold ${colors.accent}`}>
          {profile.name}
        </h3>
        <p className="text-xs leading-relaxed text-text-muted">
          {profile.description}
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-1.5">
        {profile.tools.map((tool) => (
          <span
            key={tool}
            className="rounded-sm bg-surface-2 px-2 py-0.5 text-xs text-text-muted"
          >
            {tool}
          </span>
        ))}
      </div>
    </div>
  );
}
