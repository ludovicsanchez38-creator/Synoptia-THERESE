/**
 * THÉRÈSE v2 - Atelier Panel
 *
 * Panneau coulissant pour les agents IA embarqués (swarm local).
 *
 * Vues :
 *   - chat : swarm agents embarqués Katia + Zézette
 *   - agents : agents métier préconfigurés (catalogue + session)
 *   - mission : mission timeline
 *   - review : code review
 */

import React, { useRef, useEffect, useCallback, useState } from "react";
import { X, Headphones, Wrench, MessageSquare, Zap, Eye, Bot } from "lucide-react";
import { useAtelierStore } from "../../stores/atelierStore";
import { streamAgentRequest, getAgentConfig } from "../../services/api/agents";
import type { AgentConfigResponse } from "../../services/api/agents";
import { AgentMessageBubble } from "./AgentMessageBubble";
import { AgentInput } from "./AgentInput";
import { AgentCatalog } from "./AgentCatalog";
import { AgentSession } from "./AgentSession";
import { MissionStepper } from "./MissionStepper";
import { CodeReviewPanel } from "./CodeReviewPanel";
import { Z_LAYER } from "../../styles/z-layers";

export function AtelierPanel() {
  const {
    isOpen,
    closePanel,
    activeView,
    setActiveView,
    messages,
    isStreaming,
    currentMission,
    sourcePath,
    setSourcePath,
    processChunk,
    addUserMessage,
  } = useAtelierStore();

  const [agentConfig, setAgentConfig] = useState<AgentConfigResponse | null>(null);
  const [activeAgentProfile, setActiveAgentProfile] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // BUG-110 : Charger la config agents (source_path, modèles) au montage
  useEffect(() => {
    if (isOpen) {
      getAgentConfig()
        .then((config) => {
          setAgentConfig(config);
          if (config.source_path && !sourcePath) {
            setSourcePath(config.source_path);
          }
        })
        .catch(() => {
          // Silencieux - le backend peut ne pas répondre
        });
    }
  }, [isOpen, sourcePath, setSourcePath]);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = useCallback(
    async (message: string) => {
      addUserMessage(message);

      abortRef.current = new AbortController();

      try {
        for await (const chunk of streamAgentRequest(
          message,
          sourcePath || undefined,
          abortRef.current.signal
        )) {
          processChunk(chunk);
        }
      } catch (e: any) {
        if (e.name !== "AbortError") {
          processChunk({
            type: "error",
            content: e.message || "Erreur de connexion",
          });
        }
      }
    },
    [sourcePath, processChunk, addUserMessage]
  );

  const handleCancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  if (!isOpen) return null;

  // Raccourci pour afficher les modèles dans le header
  const katiaModel = agentConfig?.katia_model || "";
  const zezetteModel = agentConfig?.zezette_model || "";
  const showModelBadge = katiaModel || zezetteModel;

  return (
    <div
      className={`fixed right-0 top-0 ${Z_LAYER.MODAL} flex h-full flex-col border-l border-white/5 bg-[#0B1226] shadow-2xl`}
      style={{ width: "480px" }}
    >
      {/* Header */}
      <div className="flex flex-col border-b border-white/5">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-500/20">
              <Zap size={14} className="text-purple-400" />
            </div>
            <span className="text-sm font-semibold text-[#E6EDF7]">Atelier</span>
          </div>

          {/* Navigation */}
          <div className="flex items-center gap-1">
            <NavButton
              active={activeView === "chat"}
              onClick={() => setActiveView("chat")}
              icon={<MessageSquare size={14} />}
              label="Chat"
            />
            <NavButton
              active={activeView === "agents"}
              onClick={() => setActiveView("agents")}
              icon={<Bot size={14} />}
              label="Agents"
            />
            {currentMission && (
              <>
                <NavButton
                  active={activeView === "mission"}
                  onClick={() => setActiveView("mission")}
                  icon={<Zap size={14} />}
                  label="Mission"
                  pulse={
                    currentMission.phase !== "done" &&
                    currentMission.phase !== "review"
                  }
                />
                <NavButton
                  active={activeView === "review"}
                  onClick={() => setActiveView("review")}
                  icon={<Eye size={14} />}
                  label="Review"
                />
              </>
            )}
          </div>

          <button
            onClick={closePanel}
            className="flex h-7 w-7 items-center justify-center rounded-lg text-[#6B7280] transition hover:bg-white/5 hover:text-[#E6EDF7]"
          >
            <X size={16} />
          </button>
        </div>

        {/* BUG-111 : Badges modèles Katia & Zézette (masqués en vue Agents) */}
        {showModelBadge && activeView !== "agents" && (
          <div className="flex items-center gap-2 px-4 pb-2 text-[10px] text-[#6B7280]">
            {katiaModel && (
              <span className="rounded bg-purple-500/10 px-1.5 py-0.5 text-purple-400">
                Katia: {katiaModel}
              </span>
            )}
            {zezetteModel && (
              <span className="rounded bg-amber-500/10 px-1.5 py-0.5 text-amber-400">
                Zézette: {zezetteModel}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Mission stepper (visible en mode mission et review) */}
      {currentMission &&
        (activeView === "mission" || activeView === "review") && (
          <MissionStepper currentPhase={currentMission.phase} />
        )}

      {/* Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {activeView === "chat" && (
          <>
            {/* Messages */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto py-2">
              {messages.length === 0 ? (
                <EmptyState />
              ) : (
                messages.map((msg) => (
                  <AgentMessageBubble key={msg.id} message={msg} />
                ))
              )}
            </div>

            {/* Input */}
            <AgentInput
              onSend={handleSend}
              onCancel={handleCancel}
              isStreaming={isStreaming}
              placeholder="Posez une question ou demandez une amélioration..."
            />
          </>
        )}

        {activeView === "mission" && (
          <div ref={scrollRef} className="flex-1 overflow-y-auto py-2">
            {messages.length === 0 ? (
              <div className="flex h-full items-center justify-center text-sm text-[#6B7280]">
                Aucune mission en cours
              </div>
            ) : (
              messages.map((msg) => (
                <AgentMessageBubble key={msg.id} message={msg} />
              ))
            )}
          </div>
        )}

        {activeView === "review" && <CodeReviewPanel />}

        {activeView === "agents" && (
          activeAgentProfile ? (
            <AgentSession
              profileId={activeAgentProfile}
              onBack={() => setActiveAgentProfile(null)}
            />
          ) : (
            <AgentCatalog
              onSelectAgent={(profileId) => setActiveAgentProfile(profileId)}
            />
          )
        )}
      </div>
    </div>
  );
}

// ============================================================
// Sub-components
// ============================================================

function NavButton({
  active,
  onClick,
  icon,
  label,
  pulse,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  pulse?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={`relative flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition ${
        active
          ? "bg-purple-500/20 text-purple-400"
          : "text-[#6B7280] hover:bg-white/5 hover:text-[#B6C7DA]"
      }`}
    >
      {icon}
      {label}
      {pulse && (
        <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
      )}
    </button>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 px-8 text-center">
      <div className="flex gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-500/10">
          <Headphones size={24} className="text-purple-400" />
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-500/10">
          <Wrench size={24} className="text-amber-400" />
        </div>
      </div>
      <div>
        <h3 className="mb-1 text-sm font-semibold text-[#E6EDF7]">
          Bienvenue dans l&apos;Atelier
        </h3>
        <p className="text-xs leading-relaxed text-[#6B7280]">
          Katia te guide et comprend tes besoins. Zézette implémente les
          changements. Posez une question ou demandez une amélioration.
        </p>
      </div>
    </div>
  );
}
