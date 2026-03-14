/**
 * THÉRÈSE v2 - Atelier Panel
 *
 * Panneau coulissant pour les agents IA embarqués.
 * Contient : chat agents, mission timeline, code review.
 */

import React, { useRef, useEffect, useCallback } from 'react';
import { X, Headphones, Wrench, MessageSquare, Zap, Eye } from 'lucide-react';
import { useAtelierStore } from '../../stores/atelierStore';
import { streamAgentRequest } from '../../services/api/agents';
import { AgentMessageBubble } from './AgentMessageBubble';
import { AgentInput } from './AgentInput';
import { MissionStepper } from './MissionStepper';
import { CodeReviewPanel } from './CodeReviewPanel';

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
    processChunk,
    addUserMessage,
  } = useAtelierStore();

  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = useCallback(async (message: string) => {
    addUserMessage(message);

    abortRef.current = new AbortController();

    try {
      for await (const chunk of streamAgentRequest(
        message,
        sourcePath || undefined,
        abortRef.current.signal,
      )) {
        processChunk(chunk);
      }
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        processChunk({
          type: 'error',
          content: e.message || 'Erreur de connexion',
        });
      }
    }
  }, [sourcePath, processChunk, addUserMessage]);

  const handleCancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  if (!isOpen) return null;

  if (!sourcePath) {
    return (
      <div
        className="fixed right-0 top-0 z-50 flex h-full flex-col border-l border-white/5 bg-[#0B1226] shadow-2xl"
        style={{ width: '480px' }}
      >
        <div className="flex items-center justify-between border-b border-white/5 px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-500/20">
              <Zap size={14} className="text-purple-400" />
            </div>
            <span className="text-sm font-semibold text-[#E6EDF7]">Atelier</span>
          </div>
          <button onClick={closePanel} className="rounded-lg p-1.5 text-[#B6C7DA] hover:bg-white/5">
            <X size={16} />
          </button>
        </div>
        <div className="flex flex-1 flex-col items-center justify-center gap-4 px-8 text-center">
          <Wrench size={40} className="text-[#B6C7DA]/30" />
          <p className="text-sm text-[#B6C7DA]">
            Configure le chemin du code source dans <strong>Paramètres &gt; Agents</strong> pour utiliser l'Atelier.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="fixed right-0 top-0 z-50 flex h-full flex-col border-l border-white/5 bg-[#0B1226] shadow-2xl"
      style={{ width: '480px' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/5 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-500/20">
            <Zap size={14} className="text-purple-400" />
          </div>
          <span className="text-sm font-semibold text-[#E6EDF7]">Atelier</span>
        </div>

        {/* Navigation */}
        <div className="flex items-center gap-1">
          <NavButton
            active={activeView === 'chat'}
            onClick={() => setActiveView('chat')}
            icon={<MessageSquare size={14} />}
            label="Chat"
          />
          {currentMission && (
            <>
              <NavButton
                active={activeView === 'mission'}
                onClick={() => setActiveView('mission')}
                icon={<Zap size={14} />}
                label="Mission"
                pulse={currentMission.phase !== 'done' && currentMission.phase !== 'review'}
              />
              <NavButton
                active={activeView === 'review'}
                onClick={() => setActiveView('review')}
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

      {/* Mission stepper (visible en mode mission et review) */}
      {currentMission && (activeView === 'mission' || activeView === 'review') && (
        <MissionStepper currentPhase={currentMission.phase} />
      )}

      {/* Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {activeView === 'chat' && (
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

        {activeView === 'mission' && (
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

        {activeView === 'review' && (
          <CodeReviewPanel />
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
          ? 'bg-purple-500/20 text-purple-400'
          : 'text-[#6B7280] hover:bg-white/5 hover:text-[#B6C7DA]'
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
          Bienvenue dans l'Atelier
        </h3>
        <p className="text-xs leading-relaxed text-[#6B7280]">
          Thérèse vous guide et comprend vos besoins.
          Zézette implémente les changements.
          Posez une question ou demandez une amélioration.
        </p>
      </div>
    </div>
  );
}
