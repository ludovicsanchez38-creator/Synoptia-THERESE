/**
 * ResponseGeneratorModal.tsx
 *
 * Modal pour générer et éditer des réponses emails via IA.
 * US-EMAIL-09: Génération de réponse IA
 */

import React, { useState, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles, RefreshCw, Check } from 'lucide-react';
import * as api from '../../services/api';
import { Z_LAYER } from '../../styles/z-layers';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { Spinner } from '../ui/Spinner';

interface ResponseGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  messageId: string;
  accountId: string;
  onUseResponse: (response: string) => void;
}

type Tone = 'formal' | 'friendly' | 'neutral';
type Length = 'short' | 'medium' | 'detailed';

const TONE_OPTIONS = [
  { value: 'formal' as Tone, label: 'Formel', description: 'Professionnel et courtois' },
  { value: 'friendly' as Tone, label: 'Amical', description: 'Décontracté et chaleureux' },
  { value: 'neutral' as Tone, label: 'Neutre', description: 'Équilibré' },
];

const LENGTH_OPTIONS = [
  { value: 'short' as Length, label: 'Court', description: '2-3 phrases' },
  { value: 'medium' as Length, label: 'Moyen', description: '1 paragraphe' },
  { value: 'detailed' as Length, label: 'Détaillé', description: '2-3 paragraphes' },
];

export function ResponseGeneratorModal({
  isOpen,
  onClose,
  messageId,
  accountId,
  onUseResponse,
}: ResponseGeneratorModalProps) {
  const [tone, setTone] = useState<Tone>('formal');
  const [length, setLength] = useState<Length>('medium');
  const [draft, setDraft] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [hasGenerated, setHasGenerated] = useState(false);
  // BUG-171. L'erreur était écrite DANS le champ brouillon : le texte de la
  // panne se retrouvait à la place de la réponse, et l'utilisateur devait
  // fermer puis rouvrir la fenêtre pour réessayer. Elle a désormais sa place.
  const [erreur, setErreur] = useState<string | null>(null);

  // US-013 : piège de focus + Échap. onClose vient du parent sous forme de fléchée
  // recréée à chaque rendu : on le stabilise (ref) pour ne pas réarmer le piège
  // (et faire sauter le focus) à chaque re-render d'EmailDetail.
  const dialogRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);
  React.useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);
  const handleEscape = useCallback(() => onCloseRef.current(), []);
  useDialogFocusTrap(dialogRef, { active: isOpen, onEscape: handleEscape });

  const generateResponse = async () => {
    setIsGenerating(true);
    setErreur(null);
    try {
      const response = await api.generateEmailResponse(messageId, accountId, tone, length);
      setDraft(response.draft);
      setHasGenerated(true);
    } catch (error) {
      // Le backend renvoie une cause déjà traduite et nettoyée : clé refusée,
      // modèle sans outils, délai dépassé, fournisseur injoignable. On
      // l'affiche telle quelle plutôt que de la remplacer par un message
      // unique qui n'apprend rien.
      const cause = (error as { message?: string } | null)?.message?.trim();
      setErreur(
        cause && cause.length > 10
          ? cause
          : "La rédaction assistée n'a pas abouti. Réessaie, ou vérifie ton modèle dans Réglages, rubrique IA.",
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRegenerate = () => {
    generateResponse();
  };

  const handleUse = (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      onUseResponse(draft);
    } catch (err) {
      console.error('ResponseGeneratorModal: erreur dans onUseResponse', err);
      // Fallback : fermer le modal même si onUseResponse a échoué
      onClose();
    }
    // NE PAS appeler onClose() ici : onUseResponse gère la fermeture
    // et appelle startComposing qui démonte EmailDetail (et donc ce portal)
  };

  React.useEffect(() => {
    if (isOpen && !hasGenerated) {
      // Auto-generate on open
      generateResponse();
    }
  }, [isOpen]);

  React.useEffect(() => {
    if (!isOpen) {
      // Reset state on close
      setDraft('');
      setHasGenerated(false);
      setTone('formal');
      setLength('medium');
    }
  }, [isOpen]);

  // Portal vers document.body pour éviter les problèmes de stacking context
  // (transform Framer Motion sur les ancêtres + overflow-hidden qui cassent position:fixed)
  return createPortal(
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className={`fixed inset-0 bg-black/60 backdrop-blur-sm ${Z_LAYER.MODAL_NESTED}`}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-label="Génération de réponse email"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className={`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 ${Z_LAYER.MODAL_NESTED} w-full max-w-3xl`}
          >
            <div className="bg-surface border border-text-muted/20 rounded-md shadow-2xl p-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-sm bg-accent-tint border-[1.5px] border-[var(--btn-ink)]">
                    <Sparkles className="w-5 h-5 text-accent-cyan-ink" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-text">
                      Génération de réponse
                    </h2>
                    <p className="text-sm text-text-muted">
                      Brouillon intelligent par THÉRÈSE
                    </p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="text-text-muted hover:text-text transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Options */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                {/* Tone */}
                <div>
                  <label className="block text-sm font-medium text-text mb-2">
                    Ton
                  </label>
                  <div className="space-y-2">
                    {TONE_OPTIONS.map((option) => (
                      <button
                        key={option.value}
                        onClick={() => setTone(option.value)}
                        className={`w-full text-left px-3 py-2 rounded-md border transition-all ${
                          tone === option.value
                            ? 'border-accent-cyan bg-accent-cyan/10'
                            : 'border-text-muted/20 hover:border-text-muted/40'
                        }`}
                      >
                        <div className="font-medium text-sm text-text">
                          {option.label}
                        </div>
                        <div className="text-xs text-text-muted">
                          {option.description}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Length */}
                <div>
                  <label className="block text-sm font-medium text-text mb-2">
                    Longueur
                  </label>
                  <div className="space-y-2">
                    {LENGTH_OPTIONS.map((option) => (
                      <button
                        key={option.value}
                        onClick={() => setLength(option.value)}
                        className={`w-full text-left px-3 py-2 rounded-md border transition-all ${
                          length === option.value
                            ? 'border-accent-magenta bg-accent-magenta/10'
                            : 'border-text-muted/20 hover:border-text-muted/40'
                        }`}
                      >
                        <div className="font-medium text-sm text-text">
                          {option.label}
                        </div>
                        <div className="text-xs text-text-muted">
                          {option.description}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* BUG-171 : la cause de l'échec, à sa place — et un bouton
                  pour réessayer sans fermer la fenêtre. */}
              {erreur && (
                <div
                  className="mb-4 flex items-start gap-2 rounded-md border border-error/40 bg-[var(--color-error-tint)] px-3 py-3"
                  role="alert"
                >
                  <span className="flex-1 text-sm text-error">{erreur}</span>
                  <button
                    type="button"
                    onClick={() => void generateResponse()}
                    disabled={isGenerating}
                    className="shrink-0 text-sm font-semibold text-text underline underline-offset-2 disabled:opacity-50"
                  >
                    Réessayer
                  </button>
                </div>
              )}

              {/* Draft */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-text mb-2">
                  Brouillon
                </label>
                <textarea aria-label="Brouillon de réponse"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  disabled={isGenerating}
                  placeholder="Génération en cours..."
                  className="w-full h-64 px-4 py-3 bg-background border border-text-muted/20 rounded-md text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan resize-none font-mono text-sm"
                />
              </div>

              {/* Actions */}
              <div className="flex items-center justify-end gap-3">
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-text-muted hover:text-text transition-colors"
                >
                  Annuler
                </button>

                {hasGenerated && (
                  <button
                    onClick={handleRegenerate}
                    disabled={isGenerating}
                    className="flex items-center gap-2 px-4 py-2 bg-text-muted/10 hover:bg-text-muted/20 text-text rounded-md transition-colors disabled:opacity-50"
                  >
                    {isGenerating ? (
                      <Spinner taille="bouton" />
                    ) : (
                      <RefreshCw className="w-4 h-4" />
                    )}
                    Régénérer
                  </button>
                )}

                <button
                  onClick={handleUse}
                  disabled={!hasGenerated || isGenerating}
                  className="flex items-center gap-2 px-4 py-2 bg-accent-fill text-accent-ink rounded-md hover:bg-accent-cyan/90 transition-colors disabled:opacity-50"
                >
                  <Check className="w-4 h-4" />
                  Utiliser
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>,
    document.body
  );
}
