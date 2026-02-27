import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, Plus, Globe, X, Shield } from 'lucide-react';
import { AdvisorCard } from './AdvisorCard';
import { SynthesisCard } from './SynthesisCard';
import { Button } from '../ui/Button';
import { cn } from '../../lib/utils';
import type { AdvisorRole, BoardSynthesis } from '../../services/api';

const ADVISOR_ORDER: AdvisorRole[] = ['analyst', 'strategist', 'devil', 'pragmatic', 'visionary'];

// Advisor configuration (emoji deprecated, using icons in AdvisorCard)
const ADVISOR_CONFIG: Record<AdvisorRole, { name: string; color: string }> = {
  analyst: { name: "L'Analyste", color: '#22D3EE' },
  strategist: { name: 'Le Stratège', color: '#A855F7' },
  devil: { name: "L'Avocat du Diable", color: '#EF4444' },
  pragmatic: { name: 'Le Pragmatique', color: '#F59E0B' },
  visionary: { name: 'Le Visionnaire', color: '#E11D8D' },
};

interface AdvisorState {
  role: AdvisorRole;
  content: string;
  provider?: string;
  isLoading: boolean;
  isComplete: boolean;
}

interface DeliberationViewProps {
  question: string;
  isSearchingWeb?: boolean;
  isSovereign?: boolean;
  advisorStates: Map<AdvisorRole, AdvisorState>;
  synthesis: BoardSynthesis | null;
  isSynthesizing: boolean;
  isComplete: boolean;
  onNewDeliberation?: () => void;
  onClose?: () => void;
}

export function DeliberationView({
  question,
  isSearchingWeb = false,
  isSovereign = false,
  advisorStates,
  synthesis,
  isSynthesizing,
  isComplete,
  onNewDeliberation,
  onClose,
}: DeliberationViewProps) {
  const advisors = Array.from(advisorStates.values());
  const completedCount = advisors.filter((a) => a.isComplete).length;
  const activeAdvisor = advisors.find((a) => a.isLoading);
  const totalAdvisors = Math.max(advisors.length, 5);

  return (
    <div className="space-y-6">
      {/* Question */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          'p-4 rounded-xl',
          'bg-gradient-to-r from-accent-cyan/10 to-accent-magenta/10',
          'border border-accent-cyan/30'
        )}
      >
        <h3 className="text-sm font-medium text-text-muted mb-1">
          Question soumise au Board
        </h3>
        <p className="text-text font-medium">{question}</p>
      </motion.div>

      {/* Web Search Indicator */}
      <AnimatePresence>
        {isSearchingWeb && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className={cn(
              'flex items-center justify-center gap-3 py-6',
              'rounded-xl bg-surface-elevated border border-border'
            )}
          >
            <Globe className="w-5 h-5 text-accent-cyan animate-pulse" />
            <span className="text-text-muted">
              Recherche d'informations actualisées sur le web...
            </span>
            <Loader2 className="w-4 h-4 animate-spin text-accent-cyan" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sovereign mode banner */}
      {isSovereign && !isComplete && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-magenta/10 border border-accent-magenta/20"
        >
          <Shield className="w-4 h-4 text-accent-magenta" />
          <span className="text-sm text-accent-magenta">
            Mode souverain - Conseillers interrogés un par un via Ollama
          </span>
        </motion.div>
      )}

      {/* Progress indicator */}
      {!isComplete && advisors.length > 0 && (
        <div className="flex items-center gap-3">
          <div className="flex-1 h-1.5 bg-surface-elevated rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-accent-cyan to-accent-magenta rounded-full"
              initial={{ width: '0%' }}
              animate={{ width: `${(completedCount / totalAdvisors) * 100}%` }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            />
          </div>
          <span className="text-xs text-text-muted whitespace-nowrap">
            {activeAdvisor
              ? `${completedCount + 1}/${totalAdvisors} - ${ADVISOR_CONFIG[activeAdvisor.role]?.name || ''} en réflexion...`
              : isSynthesizing
                ? 'Synthèse en cours...'
                : `${completedCount}/${totalAdvisors}`
            }
          </span>
        </div>
      )}

      {/* Advisors Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        <AnimatePresence mode="popLayout">
          {(isSovereign ? ADVISOR_ORDER : Array.from(advisorStates.keys())).map((role) => {
            const advisor = advisorStates.get(role);
            const config = ADVISOR_CONFIG[role];
            if (!config) return null;

            // En mode souverain, afficher les conseillers en attente grisés
            if (!advisor && isSovereign) {
              return (
                <AdvisorCard
                  key={role}
                  role={role}
                  name={config.name}
                  color={config.color}
                  content=""
                  isLoading={false}
                  isComplete={false}
                  isWaiting={true}
                />
              );
            }
            if (!advisor) return null;

            return (
              <AdvisorCard
                key={advisor.role}
                role={advisor.role}
                name={config.name}
                color={config.color}
                content={advisor.isComplete && !advisor.isLoading ? advisor.content.slice(0, 300) + (advisor.content.length > 300 ? '...' : '') : advisor.content}
                provider={advisor.provider}
                isLoading={advisor.isLoading}
                isComplete={advisor.isComplete}
              />
            );
          })}
        </AnimatePresence>
      </div>

      {/* Synthesizing indicator */}
      {isSynthesizing && !synthesis && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center justify-center gap-3 py-8"
        >
          <Loader2 className="w-5 h-5 animate-spin text-accent-cyan" />
          <span className="text-text-muted">Synthèse en cours...</span>
        </motion.div>
      )}

      {/* Synthesis */}
      <AnimatePresence>
        {synthesis && (
          <SynthesisCard synthesis={synthesis} />
        )}
      </AnimatePresence>

      {/* Complete indicator + CTA */}
      {isComplete && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center gap-4 pt-4"
        >
          <p className="text-sm text-text-muted">
            Délibération terminée - Décision sauvegardée
          </p>
          <div className="flex items-center gap-3">
            {onNewDeliberation && (
              <Button
                variant="primary"
                size="lg"
                onClick={onNewDeliberation}
                className="gap-2"
              >
                <Plus className="w-5 h-5" />
                Nouvelle question
              </Button>
            )}
            {onClose && (
              <Button
                variant="secondary"
                size="lg"
                onClick={onClose}
                className="gap-2"
              >
                <X className="w-5 h-5" />
                Fermer
              </Button>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
}
