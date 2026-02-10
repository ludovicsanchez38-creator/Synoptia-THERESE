/**
 * THÉRÈSE v2 - EmailSetupWizard - Étape 2
 *
 * Guide interactif avec agent conversationnel.
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { HelpCircle, ExternalLink, ChevronLeft } from 'lucide-react';
import { Button } from '../../ui/Button';
import * as api from '../../../services/api';
import ReactMarkdown from 'react-markdown';

interface GuideStepProps {
  provider: 'gmail' | 'smtp';
  onHasProjectChange: (hasProject: boolean) => void;
  onBack: () => void;
}

export function GuideStep({ provider, onHasProjectChange, onBack }: GuideStepProps) {
  const [selected, setSelected] = useState<boolean | null>(null);
  const [guideMessage, setGuideMessage] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const handleSelect = async (hasProject: boolean) => {
    setSelected(hasProject);
    setLoading(true);

    try {
      const response = await api.generateEmailSetupGuide(provider, hasProject);
      setGuideMessage(response.message);
    } catch (error) {
      console.error('Failed to generate guide:', error);
      setGuideMessage('Erreur lors de la génération du guide. Réessaye.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      className="space-y-6"
    >
      <div className="text-center space-y-2">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center mx-auto mb-2">
          <HelpCircle className="w-6 h-6 text-accent-cyan" />
        </div>
        <h3 className="text-lg font-semibold text-text">
          🤖 Je vais t'aider à configurer Gmail
        </h3>
        <p className="text-sm text-text-muted">
          As-tu déjà un projet Google Cloud avec des identifiants OAuth ?
        </p>
      </div>

      {/* Choix Oui/Non */}
      {selected === null && (
        <div className="space-y-3">
          <motion.button
            onClick={() => handleSelect(true)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full p-4 bg-background/40 border-2 border-border/30 rounded-xl hover:border-accent-cyan/60 transition-all text-left"
          >
            <p className="text-base font-medium text-text">✓ Oui, j'ai déjà des identifiants</p>
            <p className="text-sm text-text-muted mt-1">
              Je vais passer directement à la saisie
            </p>
          </motion.button>

          <motion.button
            onClick={() => handleSelect(false)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full p-4 bg-background/40 border-2 border-border/30 rounded-xl hover:border-accent-cyan/60 transition-all text-left"
          >
            <p className="text-base font-medium text-text">✗ Non, guide-moi</p>
            <p className="text-sm text-text-muted mt-1">
              Je vais te montrer comment créer un projet
            </p>
          </motion.button>
        </div>
      )}

      {/* Guide message */}
      {selected !== null && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          <div className="p-4 bg-accent-cyan/10 border border-accent-cyan/20 rounded-lg">
            {loading ? (
              <p className="text-sm text-text-muted">Génération du guide...</p>
            ) : (
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown
                  components={{
                    a: ({ ...props }) => (
                      <a
                        {...props}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-accent-cyan hover:underline inline-flex items-center gap-1"
                      >
                        {props.children}
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ),
                  }}
                >
                  {guideMessage}
                </ReactMarkdown>
              </div>
            )}
          </div>

          <div className="flex gap-3">
            <Button variant="ghost" size="md" onClick={onBack} className="flex-1">
              <ChevronLeft className="w-4 h-4 mr-2" />
              Retour
            </Button>
            <Button
              variant="primary"
              size="md"
              onClick={() => onHasProjectChange(selected)}
              disabled={loading}
              className="flex-1"
            >
              Continuer
            </Button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
