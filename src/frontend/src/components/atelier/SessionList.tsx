/**
 * THÉRÈSE v2 - Session List (US-002)
 *
 * Liste des sessions OpenClaw avec pastille de statut,
 * barre de progression, actions_count, result_summary,
 * boutons Annuler/Relancer, filtre 24h, animation framer-motion.
 */

import React, { useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RefreshCw, Plus, X, RotateCcw } from "lucide-react";
import { useOpenClawStore } from "../../stores/openclawStore";
import { useAccessibilityStore } from "../../stores/accessibilityStore";
import { Button } from "../ui/Button";
import { Alerte } from "../ui/Alerte";
import { EtatVide } from "../ui/EtatVide";

const STATUS_COLORS: Record<string, { dot: string; text: string; label: string }> = {
  running: { dot: "bg-success", text: "text-success", label: "En cours" },
  done: { dot: "bg-text-muted", text: "text-text-muted", label: "Terminée" },
  error: { dot: "bg-error", text: "text-error", label: "Erreur" },
  cancelled: { dot: "bg-warning", text: "text-warning", label: "Annulée" },
};

const TWENTY_FOUR_HOURS_MS = 24 * 60 * 60 * 1000;

function formatDuration(startStr: string, endStr?: string): string {
  const start = new Date(startStr).getTime();
  const end = endStr ? new Date(endStr).getTime() : Date.now();
  const diffMs = end - start;

  if (diffMs < 60_000) return `${Math.round(diffMs / 1000)}s`;
  if (diffMs < 3_600_000) return `${Math.round(diffMs / 60_000)}min`;
  return `${Math.round(diffMs / 3_600_000)}h`;
}

/** Barre de progression animée pour sessions running */
function RunningProgressBar() {
  return (
    <div className="mt-1.5 ml-4 h-1 w-full overflow-hidden rounded-full bg-surface-2">
      <motion.div
        className="h-full rounded-full bg-accent-fill"
        initial={{ x: "-100%" }}
        animate={{ x: "100%" }}
        transition={{
          repeat: Infinity,
          duration: 1.5,
          ease: "easeInOut",
        }}
        style={{ width: "40%" }}
      />
    </div>
  );
}

export function SessionList() {
  const {
    sessions,
    activeSessionId,
    fetchSessions,
    selectSession,
    openNewTask,
    cancelSession,
    dispatchTask,
    openclawConnected,
    runningCount,
    maxAgents,
    error,
    sessionsLoading,
  } = useOpenClawStore();

  const reduceMotion = useAccessibilityStore((s) => s.reduceMotion);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // Filtrer : les sessions terminées (done/cancelled) de plus de 24h disparaissent
  const visibleSessions = useMemo(() => {
    const now = Date.now();
    return sessions.filter((session) => {
      if (session.status === "running" || session.status === "error") return true;
      const finishedAt = session.finished_at
        ? new Date(session.finished_at).getTime()
        : new Date(session.created_at).getTime();
      return now - finishedAt < TWENTY_FOUR_HOURS_MS;
    });
  }, [sessions]);

  const handleCancel = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    cancelSession(sessionId);
  };

  const handleRetry = (e: React.MouseEvent, instruction: string) => {
    e.stopPropagation();
    dispatchTask(instruction);
  };

  const itemVariants = reduceMotion
    ? { initial: {}, animate: {}, exit: {} }
    : {
        initial: { opacity: 0, x: -20 },
        animate: { opacity: 1, x: 0 },
        exit: { opacity: 0, x: -20 },
      };

  return (
    <div className="flex h-full w-[250px] flex-col border-r border-border">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <span className="text-xs font-semibold text-text-muted">Sessions</span>
        <div className="flex items-center gap-1">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => fetchSessions()}
            className="h-8 w-8"
            title="Rafraichir"
            aria-label="Rafraichir les sessions"
          >
            <RefreshCw size={12} />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={openNewTask}
            disabled={!openclawConnected || runningCount >= maxAgents}
            className="h-8 w-8"
            title={runningCount >= maxAgents ? `${maxAgents} agents max` : "Nouvelle tache"}
            aria-label={runningCount >= maxAgents ? `${maxAgents} agents max` : "Lancer une nouvelle tache"}
          >
            <Plus size={14} />
          </Button>
        </div>
      </div>

      {/* US-003 : Compteur agents actifs */}
      <div className="flex items-center justify-between border-b border-border px-3 py-1.5">
        <span className="text-xs text-text-muted">
          <span className={runningCount >= maxAgents ? "text-warning font-medium" : "text-accent"}>
            {runningCount}/{maxAgents}
          </span>
          {" agents actifs"}
        </span>
      </div>

      {/* Connexion status */}
      <div className="flex items-center gap-1.5 border-b border-border px-3 py-1.5">
        <span
          className={`h-1.5 w-1.5 rounded-full ${
            openclawConnected ? "bg-success" : "bg-error"
          }`}
        />
        <span className="text-xs text-text-muted">
          {openclawConnected ? "OpenClaw connecté" : "OpenClaw déconnecté"}
        </span>
      </div>

      {/* D195 : liste pleine et rafraîchissement en panne, la panne se dit quand même. */}
      {error && visibleSessions.length > 0 && (
        <Alerte className="rounded-sm border-x-0 border-t-0 px-3 py-2 text-sm">{error}</Alerte>
      )}

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {visibleSessions.length === 0 && error ? (
          // B-537 : une panne de lecture n'est pas « Aucune session ».
          <Alerte
            className="m-3"
            titre="Sessions non lues"
            action={<Button type="button" variant="secondary" size="sm" onClick={() => void fetchSessions()}>Réessayer</Button>}
          >
            {error}
          </Alerte>
        ) : visibleSessions.length === 0 && sessionsLoading ? (
          // B-401 : une liste pas encore lue n'est pas « Aucune session ».
          <div role="status" className="flex items-center justify-center px-4 py-8 text-center">
            <span className="text-xs text-text-muted">Lecture des sessions…</span>
          </div>
        ) : visibleSessions.length === 0 ? (
          <EtatVide
            titre="Aucune session"
            action={
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={openNewTask}
                disabled={!openclawConnected || runningCount >= maxAgents}
                title={runningCount >= maxAgents ? `${maxAgents} agents max` : undefined}
              >
                {runningCount >= maxAgents ? `${maxAgents} agents max` : "Lancer une tache"}
              </Button>
            }
          />
        ) : (
          <AnimatePresence initial={false}>
            {visibleSessions.map((session) => {
              const statusStyle = STATUS_COLORS[session.status] || STATUS_COLORS.done;
              const isActive = session.id === activeSessionId;

              return (
                <motion.div
                  key={session.id}
                  {...itemVariants}
                  transition={{ duration: reduceMotion ? 0 : 0.25 }}
                  layout={!reduceMotion}
                  className={`relative w-full border-b border-border transition-colors ${
                    isActive
                      ? "border-l border-l-accent bg-accent-tint"
                      : "hover:bg-surface-2"
                  }`}
                >
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => selectSession(session.id)}
                    aria-label={`Ouvrir la session ${session.instruction}`}
                    className="h-auto w-full flex-col items-stretch rounded-sm px-3 py-2.5 pr-12 text-left font-normal hover:bg-transparent"
                  >
                  <div className="flex items-center gap-2">
                    <span
                      className={`h-2 w-2 flex-shrink-0 rounded-full ${statusStyle.dot} ${
                        session.status === "running" ? "animate-pulse" : ""
                      }`}
                    />
                    <span className="flex-1 truncate text-sm font-medium text-text">
                      {session.instruction.length > 60
                        ? session.instruction.slice(0, 60) + "..."
                        : session.instruction}
                    </span>

                  </div>

                  <div className="mt-1 flex items-center gap-2 pl-4">
                    <span className={`text-xs ${statusStyle.text}`}>
                      {statusStyle.label}
                    </span>
                    <span className="text-xs text-text-muted">
                      {formatDuration(session.created_at, session.finished_at)}
                    </span>
                    {session.actions_count > 0 && (
                      <span className="text-xs text-text-muted">
                        {session.actions_count} action{session.actions_count > 1 ? "s" : ""}
                      </span>
                    )}
                  </div>

                  {/* Barre de progression pour les sessions running */}
                  {session.status === "running" && !reduceMotion && <RunningProgressBar />}

                  {/* Result summary pour les sessions terminées */}
                  {session.status === "done" && session.result_summary && (
                    <div className="mt-1 pl-4" title={session.result_summary}>
                      <span className="text-xs leading-tight text-text-muted line-clamp-2">
                        {session.result_summary}
                      </span>
                    </div>
                  )}
                  </Button>

                  {session.status === "running" && (
                    <Button
                      type="button"
                      variant="danger"
                      size="icon"
                      onClick={(e) => handleCancel(e, session.id)}
                      className="absolute right-2 top-2 h-8 w-8"
                      title="Annuler cette session"
                      aria-label="Annuler cette session"
                    >
                      <X size={14} />
                    </Button>
                  )}

                  {session.status === "error" && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={(e) => handleRetry(e, session.instruction)}
                      className="absolute right-2 top-2 h-8 w-8 text-warning"
                      title="Relancer cette tache"
                      aria-label="Relancer cette tache"
                    >
                      <RotateCcw size={14} />
                    </Button>
                  )}
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
