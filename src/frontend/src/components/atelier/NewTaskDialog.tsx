/**
 * THÉRÈSE v2 - New Task Dialog (US-001)
 *
 * Dialog modal pour lancer une tâche OpenClaw.
 * "Que veux-tu que Katia fasse ?"
 */

import React, { useState, useRef, useEffect } from "react";
import { X, Zap, Loader2 } from "lucide-react";
import { useOpenClawStore } from "../../stores/openclawStore";
import { Z_LAYER } from "../../styles/z-layers";
import { useDialogFocusTrap } from "../../hooks/useDialogFocusTrap";

export function NewTaskDialog() {
  const { isNewTaskOpen, closeNewTask, dispatchTask, isDispatching, openclawConnected, runningCount, maxAgents } =
    useOpenClawStore();
  const [instruction, setInstruction] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isMaxReached = runningCount >= maxAgents;

  // US-013 : piège de focus + Échap (closeNewTask est une action Zustand, stable).
  // Appelé avant l'early return pour respecter la règle des hooks.
  const dialogRef = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(dialogRef, { active: isNewTaskOpen, onEscape: closeNewTask });

  useEffect(() => {
    if (isNewTaskOpen && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isNewTaskOpen]);

  if (!isNewTaskOpen) return null;

  const handleSubmit = async () => {
    const trimmed = instruction.trim();
    if (!trimmed || isDispatching) return;
    await dispatchTask(trimmed);
    setInstruction("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
    // Échap : géré par useDialogFocusTrap (un seul handler actif).
  };

  return (
    <div className={`fixed inset-0 ${Z_LAYER.MODAL_NESTED} flex items-center justify-center bg-black/50 backdrop-blur-sm`}>
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Nouvelle tâche pour Katia"
        className="mx-4 w-full max-w-lg rounded-xl border border-border bg-bg shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-5 py-3">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-500/20">
              <Zap size={14} className="text-purple-400" />
            </div>
            <span className="text-sm font-semibold text-text">
              Nouvelle tâche pour Katia
            </span>
          </div>
          <button
            onClick={closeNewTask}
            className="rounded-lg p-1.5 text-text-muted transition hover:bg-surface-2 hover:text-text"
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4">
          {!openclawConnected && (
            <div className="mb-3 rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
              OpenClaw n&apos;est pas connecté. Vérifiez que le gateway tourne.
            </div>
          )}

          <label className="mb-2 block text-xs font-medium text-text-muted">
            Que veux-tu que Katia fasse ?
          </label>
          <textarea
            ref={textareaRef}
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ex: Envoie un email de relance à Jean Dupont pour la facture F-2024-042..."
            rows={4}
            className="w-full resize-none rounded-lg border border-border bg-surface px-3 py-2.5 text-sm text-text placeholder-[#6B7280] outline-none transition focus:border-purple-500/50"
            disabled={isDispatching}
          />
          <p className="mt-1.5 text-xs text-text-muted">
            Katia peut envoyer des emails, créer des factures, gérer le CRM et plus encore.
            <span className="ml-1 text-text-muted">Cmd+Entrée</span> pour lancer.
          </p>

          {isMaxReached && (
            <div className="mt-2 rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
              Tu as déjà {maxAgents} agents en cours. Attends qu&apos;un se termine ou annule-en un.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 border-t border-border px-5 py-3">
          <button
            onClick={closeNewTask}
            className="rounded-lg px-3 py-1.5 text-xs font-medium text-text-muted transition hover:bg-surface-2"
            disabled={isDispatching}
          >
            Annuler
          </button>
          <button
            onClick={handleSubmit}
            disabled={!instruction.trim() || isDispatching || !openclawConnected || isMaxReached}
            className="flex items-center gap-1.5 rounded-lg bg-purple-500/20 px-4 py-1.5 text-xs font-medium text-purple-300 transition hover:bg-purple-500/30 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isDispatching ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                Lancement...
              </>
            ) : (
              <>
                <Zap size={14} />
                Lancer
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
