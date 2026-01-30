import { motion } from 'framer-motion';
import { CheckCircle, AlertTriangle, ArrowRight, Target } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { BoardSynthesis } from '../../services/api';

interface SynthesisCardProps {
  synthesis: BoardSynthesis;
}

const confidenceConfig = {
  high: {
    color: 'text-green-400',
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
    label: 'Confiance élevée',
  },
  medium: {
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/30',
    label: 'Confiance moyenne',
  },
  low: {
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    label: 'Confiance faible',
  },
};

export function SynthesisCard({ synthesis }: SynthesisCardProps) {
  const config = confidenceConfig[synthesis.confidence] || confidenceConfig.medium;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'rounded-2xl border p-6',
        'bg-gradient-to-br from-surface-elevated to-surface',
        'border-accent-cyan/30'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-text flex items-center gap-2">
          <Target className="w-5 h-5 text-accent-cyan" />
          Synthèse du Board
        </h3>
        <span className={cn(
          'px-3 py-1 rounded-full text-xs font-medium',
          config.bg,
          config.border,
          config.color,
          'border'
        )}>
          {config.label}
        </span>
      </div>

      {/* Recommendation */}
      <div className={cn(
        'mb-6 p-4 rounded-xl',
        'bg-accent-cyan/5 border border-accent-cyan/20'
      )}>
        <h4 className="text-sm font-medium text-accent-cyan mb-2">
          Recommandation
        </h4>
        <p className="text-text leading-relaxed">
          {synthesis.recommendation}
        </p>
      </div>

      {/* Consensus & Divergences */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Consensus */}
        {synthesis.consensus_points.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-green-400 flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              Points de consensus
            </h4>
            <ul className="space-y-1.5">
              {synthesis.consensus_points.map((point, i) => (
                <li key={i} className="text-sm text-text-muted flex items-start gap-2">
                  <span className="text-green-400 mt-1">•</span>
                  {point}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Divergences */}
        {synthesis.divergence_points.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-yellow-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Points de divergence
            </h4>
            <ul className="space-y-1.5">
              {synthesis.divergence_points.map((point, i) => (
                <li key={i} className="text-sm text-text-muted flex items-start gap-2">
                  <span className="text-yellow-400 mt-1">•</span>
                  {point}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Next Steps */}
      {synthesis.next_steps.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-accent-magenta flex items-center gap-2 mb-2">
            <ArrowRight className="w-4 h-4" />
            Prochaines étapes
          </h4>
          <ol className="space-y-1.5">
            {synthesis.next_steps.map((step, i) => (
              <li key={i} className="text-sm text-text-muted flex items-start gap-2">
                <span className="text-accent-magenta font-medium">{i + 1}.</span>
                {step}
              </li>
            ))}
          </ol>
        </div>
      )}
    </motion.div>
  );
}
