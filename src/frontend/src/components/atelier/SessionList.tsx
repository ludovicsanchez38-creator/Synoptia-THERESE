/**
 * THÉRÈSE v2 - Session List (US-001)
 *
 * Liste des sessions OpenClaw avec pastille de statut.
 * Vert = running, Gris = done, Rouge = error, Jaune = cancelled.
 */

import React, { useEffect } from "react";
import { RefreshCw, Plus } from "lucide-react";
import { useOpenClawStore } from "../../stores/openclawStore";

const STATUS_COLORS: Record<string, { dot: string; text: string; label: string }> = {
  running: { dot: "bg-green-400", text: "text-green-400", label: "En cours" },
  done: { dot: "bg-gray-400", text: "text-gray-400", label: "Terminée" },
  error: { dot: "bg-red-400", text: "text-red-400", label: "Erreur" },
  cancelled: { dot: "bg-amber-400", text: "text-amber-400", label: "Annulée" },
};

function formatDuration(startStr: string, endStr?: string): string {
  const start = new Date(startStr).getTime();
  const end = endStr ? new Date(endStr).getTime() : Date.now();
  const diffMs = end - start;

  if (diffMs < 60_000) return `${Math.round(diffMs / 1000)}s`;
  if (diffMs < 3_600_000) return `${Math.round(diffMs / 60_000)}min`;
  return `${Math.round(diffMs / 3_600_000)}h`;
}

export function SessionList() {
  const {
    sessions,
    activeSessionId,
    fetchSessions,
    selectSession,
    openNewTask,
    openclawConnected,
  } = useOpenClawStore();

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  return (
    <div className="flex h-full flex-col border-r border-white/5" style={{ width: "250px" }}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/5 px-3 py-2">
        <span className="text-xs font-semibold text-[#B6C7DA]">Sessions</span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => fetchSessions()}
            className="rounded p-1 text-[#6B7280] transition hover:bg-white/5 hover:text-[#B6C7DA]"
            title="Rafraîchir"
          >
            <RefreshCw size={12} />
          </button>
          <button
            onClick={openNewTask}
            disabled={!openclawConnected}
            className="rounded p-1 text-purple-400 transition hover:bg-purple-500/10 disabled:opacity-30"
            title="Nouvelle tâche"
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
          {openclawConnected ? "OpenClaw connecté" : "OpenClaw déconnecté"}
        </span>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 px-4 py-8 text-center">
            <span className="text-xs text-[#6B7280]">Aucune session</span>
            <button
              onClick={openNewTask}
              disabled={!openclawConnected}
              className="rounded-lg bg-purple-500/10 px-3 py-1.5 text-xs font-medium text-purple-400 transition hover:bg-purple-500/20 disabled:opacity-30"
            >
              Lancer une tâche
            </button>
          </div>
        ) : (
          sessions.map((session) => {
            const statusStyle = STATUS_COLORS[session.status] || STATUS_COLORS.done;
            const isActive = session.id === activeSessionId;

            return (
              <button
                key={session.id}
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
                  <span className="truncate text-xs font-medium text-[#E6EDF7]">
                    {session.instruction.length > 60
                      ? session.instruction.slice(0, 60) + "..."
                      : session.instruction}
                  </span>
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
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
