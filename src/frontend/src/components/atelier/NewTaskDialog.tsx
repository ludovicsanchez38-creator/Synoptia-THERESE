/**
 * THÉRÈSE v2 - New Task Dialog (US-001)
 *
 * Dialog modal pour lancer une tâche OpenClaw.
 * "Que veux-tu que Katia fasse ?"
 */

import React, { useState, useRef, useEffect } from "react";
import { X, Zap, Loader2 } from "lucide-react";
import { useOpenClawStore } from "../../stores/openclawStore";

export function NewTaskDialog() {
  const { isNewTaskOpen, closeNewTask, dispatchTask, isDispatching, openclawConnected } =
    useOpenClawStore();
  const [instruction, setInstruction] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

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
    if (e.key === "Escape") {
      closeNewTask();
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div
        className="mx-4 w-full max-w-lg rounded-xl border border-white/10 bg-[#0F172A] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/5 px-5 py-3">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-500/20">
              <Zap size={14} className="text-purple-400" />
            </div>
            <span className="text-sm font-semibold text-[#E6EDF7]">
              Nouvelle tâche pour Katia
            </span>
          </div>
          <button
            onClick={closeNewTask}
            className="rounded-lg p-1.5 text-[#6B7280] transition hover:bg-white/5 hover:text-[#E6EDF7]"
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

          <label className="mb-2 block text-xs font-medium text-[#B6C7DA]">
            Que veux-tu que Katia fasse ?
          </label>
          <textarea
            ref={textareaRef}
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ex: Envoie un email de relance à Jean Dupont pour la facture F-2024-042..."
            rows={4}
            className="w-full resize-none rounded-lg border border-white/10 bg-[#131B35] px-3 py-2.5 text-sm text-[#E6EDF7] placeholder-[#6B7280] outline-none transition focus:border-purple-500/50"
            disabled={isDispatching}
          />
          <p className="mt-1.5 text-xs text-[#6B7280]">
            Katia peut envoyer des emails, créer des factures, gérer le CRM et plus encore.
            <span className="ml-1 text-[#B6C7DA]">Cmd+Entrée</span> pour lancer.
          </p>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 border-t border-white/5 px-5 py-3">
          <button
            onClick={closeNewTask}
            className="rounded-lg px-3 py-1.5 text-xs font-medium text-[#B6C7DA] transition hover:bg-white/5"
            disabled={isDispatching}
          >
            Annuler
          </button>
          <button
            onClick={handleSubmit}
            disabled={!instruction.trim() || isDispatching || !openclawConnected}
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
