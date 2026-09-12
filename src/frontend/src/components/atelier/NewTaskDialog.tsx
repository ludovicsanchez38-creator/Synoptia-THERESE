/**
 * THÉRÈSE v2 - New Task Dialog (US-001)
 *
 * Dialog modal pour lancer une tâche OpenClaw.
 * "Que veux-tu que Katia fasse ?"
 */

import React, { useState, useRef, useEffect } from "react";
import { X, Zap } from "lucide-react";
import { useOpenClawStore } from "../../stores/openclawStore";
import { Z_LAYER } from "../../styles/z-layers";
import { useDialogFocusTrap } from "../../hooks/useDialogFocusTrap";
import { Spinner } from "../ui/Spinner";
import { Button } from "../ui/Button";
import { Textarea } from "../ui/Textarea";
import { FormField } from "../ui/FormField";
import { Alerte } from "../ui/Alerte";

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
    <div className={`fixed inset-0 ${Z_LAYER.MODAL_NESTED} flex items-center justify-center bg-text/35`}>
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Nouvelle tâche pour Katia"
        className="mx-4 w-full max-w-lg rounded-md border border-border bg-surface shadow-sm"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-5 py-3">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-agent-purple/20">
              <Zap size={14} className="text-agent-purple" />
            </div>
            <span className="text-sm font-semibold text-text">
              Nouvelle tâche pour Katia
            </span>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={closeNewTask}
            aria-label="Fermer"
          >
            <X size={16} />
          </Button>
        </div>

        {/* Body */}
        <div className="px-5 py-4">
          {!openclawConnected && (
            <Alerte ton="attention" className="mb-3" titre="OpenClaw déconnecté">
              OpenClaw n&apos;est pas connecté. Vérifie que le gateway tourne.
            </Alerte>
          )}

          <FormField label="Que veux-tu que Katia fasse ?" htmlFor="mission-instruction">
          <Textarea aria-label="Instruction de la mission"
            id="mission-instruction"
            ref={textareaRef}
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ex: Envoie un email de relance à Jean Dupont pour la facture F-2024-042..."
            rows={4}
            className="resize-none"
            disabled={isDispatching}
          />
          </FormField>
          <p className="mt-1.5 text-xs text-text-muted">
            Katia peut envoyer des emails, créer des factures, gérer le CRM et plus encore.
            <span className="ml-1 text-text-muted">Cmd+Entrée</span> pour lancer.
          </p>

          {isMaxReached && (
            <Alerte ton="attention" className="mt-2" titre="Limite atteinte">
              Tu as déjà {maxAgents} agents en cours. Attends qu&apos;un se termine ou annule-en un.
            </Alerte>
          )}
        </div>

        {/* Footer */}
        <div className="flex flex-wrap items-center justify-end gap-2 border-t border-border px-5 py-3">
          <Button
            type="button"
            variant="secondary"
            onClick={closeNewTask}
            disabled={isDispatching}
          >
            Annuler
          </Button>
          <Button
            type="button"
            variant="primary"
            onClick={handleSubmit}
            disabled={!instruction.trim() || isDispatching || !openclawConnected || isMaxReached}
          >
            {isDispatching ? (
              <>
                <Spinner taille="ligne" />
                Lancement...
              </>
            ) : (
              <>
                <Zap size={14} />
                Lancer
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
