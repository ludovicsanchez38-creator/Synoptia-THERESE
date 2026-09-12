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
import { Alerte } from '../ui/Alerte';
import { Button } from '../ui/Button';
import { Carte } from '../ui/Carte';
import { FormField } from '../ui/FormField';
import { Segments } from '../ui/Segments';
import { Textarea } from '../ui/Textarea';

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
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className={`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 ${Z_LAYER.MODAL_NESTED} w-full max-w-3xl`}
          >
            <Carte className="p-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="rounded-full bg-accent-tint p-2">
                    <Sparkles className="h-5 w-5 text-accent" />
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
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onClose}
                  aria-label="Fermer la génération de réponse"
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>

              {/* Options */}
              <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
                {/* Tone */}
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-text">Ton</p>
                  <Segments
                    label="Ton de la réponse"
                    options={TONE_OPTIONS.map((option) => ({ id: option.value, label: option.label }))}
                    valeur={tone}
                    onChange={(value) => setTone(value as Tone)}
                    className="flex-wrap"
                  />
                  <p className="text-sm text-text-muted">{TONE_OPTIONS.find((option) => option.value === tone)?.description}</p>
                </div>

                {/* Length */}
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-text">Longueur</p>
                  <Segments
                    label="Longueur de la réponse"
                    options={LENGTH_OPTIONS.map((option) => ({ id: option.value, label: option.label }))}
                    valeur={length}
                    onChange={(value) => setLength(value as Length)}
                    className="flex-wrap"
                  />
                  <p className="text-sm text-text-muted">{LENGTH_OPTIONS.find((option) => option.value === length)?.description}</p>
                </div>
              </div>

              {/* BUG-171 : la cause de l'échec, à sa place — et un bouton
                  pour réessayer sans fermer la fenêtre. */}
              {erreur && (
                <Alerte
                  className="mb-4"
                  action={<Button
                    variant="secondary"
                    size="sm"
                    onClick={() => void generateResponse()}
                    disabled={isGenerating}
                  >
                    Réessayer
                  </Button>}
                >{erreur}</Alerte>
              )}

              {/* Draft */}
              <FormField label="Brouillon" htmlFor="email-response-draft" className="mb-6">
                <Textarea id="email-response-draft" aria-label="Brouillon de réponse"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  disabled={isGenerating}
                  placeholder="Génération en cours..."
                  className="h-64 resize-none font-mono"
                />
              </FormField>

              {/* Actions */}
              <div className="flex flex-wrap items-center justify-end gap-3 max-[840px]:justify-start">
                <Button
                  variant="ghost"
                  onClick={onClose}
                >
                  Annuler
                </Button>

                {hasGenerated && (
                  <Button
                    variant="secondary"
                    onClick={handleRegenerate}
                    disabled={isGenerating}
                  >
                    {isGenerating ? (
                      <Spinner taille="bouton" />
                    ) : (
                      <RefreshCw className="w-4 h-4" />
                    )}
                    Régénérer
                  </Button>
                )}

                <Button
                  variant="primary"
                  onClick={handleUse}
                  disabled={!hasGenerated || isGenerating}
                >
                  <Check className="w-4 h-4" />
                  Utiliser
                </Button>
              </div>
            </Carte>
          </motion.div>
        </>
      )}
    </AnimatePresence>,
    document.body
  );
}
