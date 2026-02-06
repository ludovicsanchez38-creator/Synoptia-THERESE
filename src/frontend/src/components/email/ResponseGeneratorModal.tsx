/**
 * ResponseGeneratorModal.tsx
 *
 * Modal pour générer et éditer des réponses emails via IA.
 * US-EMAIL-09: Génération de réponse IA
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles, RefreshCw, Check, Loader2 } from 'lucide-react';
import * as api from '../../services/api';

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

  const generateResponse = async () => {
    setIsGenerating(true);
    try {
      const response = await api.generateEmailResponse(messageId, accountId, tone, length);
      setDraft(response.draft);
      setHasGenerated(true);
    } catch (error) {
      console.error('Failed to generate response:', error);
      setDraft('❌ Erreur lors de la génération. Veuillez réessayer.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRegenerate = () => {
    generateResponse();
  };

  const handleUse = () => {
    onUseResponse(draft);
    onClose();
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

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-3xl"
          >
            <div className="bg-surface border border-text-muted/20 rounded-xl shadow-2xl p-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20">
                    <Sparkles className="w-5 h-5 text-accent-cyan" />
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
                        className={`w-full text-left px-3 py-2 rounded-lg border transition-all ${
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
                        className={`w-full text-left px-3 py-2 rounded-lg border transition-all ${
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

              {/* Draft */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-text mb-2">
                  Brouillon
                </label>
                <textarea
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  disabled={isGenerating}
                  placeholder="Génération en cours..."
                  className="w-full h-64 px-4 py-3 bg-background border border-text-muted/20 rounded-lg text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan resize-none font-mono text-sm"
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
                    className="flex items-center gap-2 px-4 py-2 bg-text-muted/10 hover:bg-text-muted/20 text-text rounded-lg transition-colors disabled:opacity-50"
                  >
                    {isGenerating ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <RefreshCw className="w-4 h-4" />
                    )}
                    Régénérer
                  </button>
                )}

                <button
                  onClick={handleUse}
                  disabled={!hasGenerated || isGenerating}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-accent-cyan to-accent-magenta text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  <Check className="w-4 h-4" />
                  Utiliser
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
