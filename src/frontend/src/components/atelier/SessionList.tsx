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

const STATUS_COLORS: Record<string, { dot: string; text: string; label: string }> = {
  running: { dot: "bg-green-400", text: "text-green-400", label: "En cours" },
  done: { dot: "bg-gray-400", text: "text-gray-400", label: "Terminée" },
  error: { dot: "bg-red-400", text: "text-red-400", label: "Erreur" },
  cancelled: { dot: "bg-amber-400", text: "text-amber-400", label: "Annulée" },
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
    <div className="mt-1.5 ml-4 h-1 w-full overflow-hidden rounded-full bg-white/5">
      <motion.div
        className="h-full rounded-full bg-gradient-to-r from-purple-500 to-green-400"
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
        initial: { opacity: 0, x: -20, scale: 0.95 },
        animate: { opacity: 1, x: 0, scale: 1 },
        exit: { opacity: 0, x: -20, scale: 0.95 },
      };

  return (
    <div className="flex h-full flex-col border-r border-white/5" style={{ width: "250px" }}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/5 px-3 py-2">
        <span className="text-xs font-semibold text-[#B6C7DA]">Sessions</span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => fetchSessions()}
            className="rounded p-1 text-[#6B7280] transition hover:bg-white/5 hover:text-[#B6C7DA]"
            title="Rafraichir"
            aria-label="Rafraichir les sessions"
          >
            <RefreshCw size={12} />
          </button>
          <button
            onClick={openNewTask}
            disabled={!openclawConnected}
            className="rounded p-1 text-purple-400 transition hover:bg-purple-500/10 disabled:opacity-30"
            title="Nouvelle tache"
            aria-label="Lancer une nouvelle tache"
          >
            <Plus size={14} />
          </button>
        </div>
      </div>

      {/* Connexion status */}
      <div className="flex items-center gap-1.5 border-b border-white/5 px-3 py-1.5">
        <span
          className={`h-1.5 w-1.5 rounded-full ${
            openclawConnected ? "bg-green-400" : "bg-red-400"
          }`}
        />
        <span className="text-[10px] text-[#6B7280]">
          {openclawConnected ? "OpenClaw connecte" : "OpenClaw deconnecte"}
        </span>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {visibleSessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 px-4 py-8 text-center">
            <span className="text-xs text-[#6B7280]">Aucune session</span>
            <button
              onClick={openNewTask}
              disabled={!openclawConnected}
              className="rounded-lg bg-purple-500/10 px-3 py-1.5 text-xs font-medium text-purple-400 transition hover:bg-purple-500/20 disabled:opacity-30"
            >
              Lancer une tache
            </button>
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {visibleSessions.map((session) => {
              const statusStyle = STATUS_COLORS[session.status] || STATUS_COLORS.done;
              const isActive = session.id === activeSessionId;

              return (
                <motion.button
                  key={session.id}
                  {...itemVariants}
                  transition={{ duration: reduceMotion ? 0 : 0.25 }}
                  layout={!reduceMotion}
                  onClick={() => selectSession(session.id)}
                  className={`w-full border-b border-white/5 px-3 py-2.5 text-left transition ${
                    isActive
                      ? "bg-purple-500/10 border-l-2 border-l-purple-400"
                      : "hover:bg-white/5"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`h-2 w-2 flex-shrink-0 rounded-full ${statusStyle.dot} ${
                        session.status === "running" ? "animate-pulse" : ""
                      }`}
                    />
                    <span className="flex-1 truncate text-xs font-medium text-[#E6EDF7]">
                      {session.instruction.length > 60
                        ? session.instruction.slice(0, 60) + "..."
                        : session.instruction}
                    </span>

                    {/* Bouton Annuler pour les sessions running */}
                    {session.status === "running" && (
                      <button
                        onClick={(e) => handleCancel(e, session.id)}
                        className="flex-shrink-0 rounded p-0.5 text-red-400/60 transition hover:bg-red-500/10 hover:text-red-400"
                        title="Annuler cette session"
                        aria-label="Annuler cette session"
                      >
                        <X size={12} />
                      </button>
                    )}

                    {/* Bouton Relancer pour les sessions en erreur */}
                    {session.status === "error" && (
                      <button
                        onClick={(e) => handleRetry(e, session.instruction)}
                        className="flex-shrink-0 rounded p-0.5 text-amber-400/60 transition hover:bg-amber-500/10 hover:text-amber-400"
                        title="Relancer cette tache"
                        aria-label="Relancer cette tache"
                      >
                        <RotateCcw size={12} />
                      </button>
                    )}
                  </div>

                  <div className="mt-1 flex items-center gap-2 pl-4">
                    <span className={`text-[10px] ${statusStyle.text}`}>
                      {statusStyle.label}
                    </span>
                    <span className="text-[10px] text-[#6B7280]">
                      {formatDuration(session.created_at, session.finished_at)}
                    </span>
                    {session.actions_count > 0 && (
                      <span className="text-[10px] text-[#6B7280]">
                        {session.actions_count} action{session.actions_count > 1 ? "s" : ""}
                      </span>
                    )}
                  </div>

                  {/* Barre de progression pour les sessions running */}
                  {session.status === "running" && !reduceMotion && <RunningProgressBar />}

                  {/* Result summary pour les sessions terminées */}
                  {session.status === "done" && session.result_summary && (
                    <div className="mt-1 pl-4" title={session.result_summary}>
                      <span className="text-[10px] leading-tight text-[#6B7280] line-clamp-2">
                        {session.result_summary}
                      </span>
                    </div>
                  )}
                </motion.button>
              );
            })}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
