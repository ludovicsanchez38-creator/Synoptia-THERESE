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
import { cancelTask, streamAgentRequest, getAgentConfig } from "../../services/api/agents";
import type { AgentConfigResponse } from "../../services/api/agents";
import { AgentMessageBubble } from "./AgentMessageBubble";
import { AgentInput } from "./AgentInput";
import { AgentCatalog } from "./AgentCatalog";
import { AgentSession } from "./AgentSession";
import { MissionStepper } from "./MissionStepper";
import { CodeReviewPanel } from "./CodeReviewPanel";
import { Z_LAYER } from "../../styles/z-layers";
import { Button } from "../ui/Button";
import { EtatVide } from "../ui/EtatVide";

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
    composerFocusRequested,
    consumeComposerFocus,
  } = useAtelierStore();
  const racineRef = useRef<HTMLDivElement>(null);

  // B-641 (Nadia, c4) : ⌘+⇧+K annonçait « Katia - nouvelle tâche » mais
  // ouvrait seulement l'Atelier, focus resté sur BODY. Le store porte la
  // demande ; le panneau la sert une fois monté et l'efface.
  useEffect(() => {
    if (!isOpen || !composerFocusRequested) return;
    const id = window.setTimeout(() => {
      racineRef.current
        ?.querySelector<HTMLTextAreaElement>('textarea[aria-label="Message à l’agent"]')
        ?.focus();
      consumeComposerFocus();
    }, 0);
    return () => window.clearTimeout(id);
  }, [isOpen, composerFocusRequested, consumeComposerFocus]);

  const [agentConfig, setAgentConfig] = useState<AgentConfigResponse | null>(null);
  const [activeAgentProfile, setActiveAgentProfile] = useState<string | null>(null);
  const [activeAgentModel, setActiveAgentModel] = useState<string | undefined>(undefined);
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);
  // `isStreaming` du store ne passe a vrai qu'au PREMIER CHUNK recu. Entre le
  // lancement et ce chunk, la saisie restait ouverte et le bouton d'annulation
  // absent : deux missions enchainees, la seconde ecrasait le jeton de la
  // premiere, puis le `finally` de la premiere effacait celui de la seconde,
  // devenue inarretable. Cet etat ferme la fenetre.
  const [missionEnCours, setMissionEnCours] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const taskIdRef = useRef<string | null>(null);

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

  const runMission = useCallback(
    async (message: string) => {
      // Une mission a la fois : le jeton en cours fait foi.
      if (abortRef.current) return;

      addUserMessage(message);

      const controleur = new AbortController();
      abortRef.current = controleur;
      setMissionEnCours(true);

      try {
        for await (const chunk of streamAgentRequest(
          message,
          sourcePath || undefined,
          controleur.signal
        )) {
          if (chunk.task_id) taskIdRef.current = chunk.task_id;
          processChunk(chunk);
        }
      } catch (e: any) {
        if (e.name !== "AbortError") {
          processChunk({
            type: "error",
            content: e.message || "Erreur de connexion",
          });
        }
      } finally {
        // Ne nettoyer que SON propre jeton : sinon la fin d'une mission efface
        // celui d'une autre, qui n'est plus annulable.
        if (abortRef.current === controleur) {
          abortRef.current = null;
          taskIdRef.current = null;
          setMissionEnCours(false);
        }
      }
    },
    [sourcePath, processChunk, addUserMessage]
  );

  const handleCancel = useCallback(async () => {
    if (taskIdRef.current) {
      try {
        await cancelTask(taskIdRef.current);
      } catch {
        // La fermeture du flux déclenche aussi l'annulation côté backend.
      }
    }
    abortRef.current?.abort();
    // Liberer le jeton ICI plutot que d'attendre le `finally` du flux : si le
    // flux n'honore pas le signal, l'Atelier resterait bloque a jamais. Le
    // `finally` de la mission avortee verra que le jeton n'est plus le sien et
    // ne touchera pas a celui d'une mission relancee entre-temps.
    abortRef.current = null;
    taskIdRef.current = null;
    setPendingMessage(null);
    setMissionEnCours(false);
  }, []);

  const handleClose = useCallback(() => {
    void handleCancel();
    closePanel();
  }, [closePanel, handleCancel]);

  useEffect(() => {
    if (!isOpen && abortRef.current) void handleCancel();
  }, [handleCancel, isOpen]);

  useEffect(() => () => {
    if (taskIdRef.current) void cancelTask(taskIdRef.current).catch(() => undefined);
    abortRef.current?.abort();
  }, []);

  if (!isOpen) return null;

  // Raccourci pour afficher les modèles dans le header
  const katiaModel = agentConfig?.katia_model || "";
  const zezetteModel = agentConfig?.zezette_model || "";
  const showModelBadge = katiaModel || zezetteModel;
  // B-648 (Nadia, c4) : sans clé cloud, « Katia: claude-sonnet-4-6 » s'affichait
  // comme si de rien n'était. Un modèle absent de la liste utilisable est dit tel.
  const modelesUtilisables = new Set((agentConfig?.available_models ?? []).map((m) => m.id));
  const indisponible = (modele: string) =>
    Boolean(modele) && modelesUtilisables.size > 0 && !modelesUtilisables.has(modele);
  const TITRE_INDISPONIBLE =
    "Ce modèle n’est pas utilisable ici : aucune clé cloud configurée, ou modèle local non installé. Change-le dans Réglages > IA.";

  return (
    <div
      ref={racineRef}
      className={`fixed right-0 top-0 ${Z_LAYER.MODAL} flex h-full w-[480px] max-w-full flex-col border-l border-border bg-bg shadow-sm`}
    >
      {/* Header */}
      <div className="flex flex-col border-b border-border">
        <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-agent-purple/20">
              <Zap size={14} className="text-agent-purple" />
            </div>
            <span className="text-sm font-semibold text-text">Atelier</span>
          </div>

          {/* Navigation */}
          <div className="flex flex-wrap items-center gap-1 max-[840px]:basis-full max-[840px]:order-3">
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

          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={handleClose}
            className="h-8 w-8"
            aria-label="Fermer l’Atelier"
          >
            <X size={16} />
          </Button>
        </div>

        {/* BUG-111 : Badges modèles Katia & Zézette (masqués en vue Agents) */}
        {showModelBadge && activeView !== "agents" && (
          <div className="flex items-center gap-2 px-4 pb-2 text-xs text-text-muted">
            {katiaModel && (
              <span
                data-etiquette=""
                className={`inline-flex rounded-full px-2 py-0.5 text-sm font-semibold ${indisponible(katiaModel) ? "bg-[var(--color-warning-tint)] text-warning" : "bg-[var(--color-info-tint)] text-info"}`}
                title={indisponible(katiaModel) ? TITRE_INDISPONIBLE : undefined}
              >
                Katia: {katiaModel}{indisponible(katiaModel) && " · non disponible"}
              </span>
            )}
            {zezetteModel && (
              <span
                data-etiquette=""
                className={`inline-flex rounded-full px-2 py-0.5 text-sm font-semibold ${indisponible(zezetteModel) ? "bg-[var(--color-warning-tint)] text-warning" : "bg-surface-2 text-text-muted"}`}
                title={indisponible(zezetteModel) ? TITRE_INDISPONIBLE : undefined}
              >
                Zézette: {zezetteModel}{indisponible(zezetteModel) && " · non disponible"}
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
            {pendingMessage && (
              <div className="mx-3 mb-2 rounded-md border border-warning/30 bg-[var(--color-warning-tint)] p-3 text-sm text-text" data-testid="classic-atelier-confirmation">
                <div className="font-semibold">Confirmer la mission de code</div>
                <p className="mt-1 leading-relaxed text-text-muted">
                  Katia et Zézette pourront lire le dépôt, transmettre les extraits utiles au modèle configuré,
                  écrire dans un worktree isolé et lancer les commandes de vérification autorisées.
                  L&apos;application sur main demandera une autre confirmation.
                </p>
                <div className="mt-3 flex flex-wrap justify-end gap-2">
                  <Button type="button" variant="secondary" onClick={() => setPendingMessage(null)}>Retour</Button>
                  <Button type="button" variant="primary" onClick={() => { const message = pendingMessage; setPendingMessage(null); void runMission(message); }}>Confirmer et lancer</Button>
                </div>
              </div>
            )}
            <AgentInput
              onSend={(message) => setPendingMessage(message)}
              onCancel={() => void handleCancel()}
              isStreaming={isStreaming || missionEnCours}
              placeholder="Posez une question ou demandez une amélioration..."
            />
          </>
        )}

        {activeView === "mission" && (
          <div ref={scrollRef} className="flex-1 overflow-y-auto py-2">
            {messages.length === 0 ? (
              <EtatVide titre="Aucune mission en cours" className="flex h-full flex-col items-center justify-center" />
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
              model={activeAgentModel}
              onBack={() => { setActiveAgentProfile(null); setActiveAgentModel(undefined); }}
            />
          ) : (
            <AgentCatalog
              onSelectAgent={(profileId, model) => { setActiveAgentProfile(profileId); setActiveAgentModel(model); }}
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
    <Button
      type="button"
      variant="ghost"
      size="sm"
      onClick={onClick}
      aria-pressed={active}
      className={`relative gap-1 ${
        active
          ? "bg-accent-tint text-accent"
          : "text-text-muted"
      }`}
    >
      {icon}
      {label}
      {pulse && (
        <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-warning animate-pulse" />
      )}
    </Button>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 px-8 text-center">
      <div className="flex gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-md bg-agent-purple/10">
          <Headphones size={24} className="text-agent-purple" />
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-md bg-agent-amber/10">
          <Wrench size={24} className="text-agent-amber" />
        </div>
      </div>
      <EtatVide titre="Bienvenue dans l’Atelier" className="p-0">
        <span className="text-sm leading-relaxed text-text-muted">
          Katia te guide et comprend tes besoins. Zézette implémente les
          changements. Posez une question ou demandez une amélioration.
        </span>
      </EtatVide>
    </div>
  );
}
