import { motion } from 'framer-motion';
import { CheckCircle, AlertTriangle, ArrowRight, Target } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { BoardSynthesis } from '../../services/api';

interface SynthesisCardProps {
  synthesis: BoardSynthesis;
}

const confidenceConfig = {
  high: {
    color: 'text-agent-green',
    bg: 'bg-agent-green/10',
    border: 'border-agent-green/30',
    label: 'Confiance élevée',
  },
  medium: {
    color: 'text-warning',
    bg: 'bg-agent-amber/10',
    border: 'border-agent-amber/30',
    label: 'Confiance moyenne',
  },
  low: {
    color: 'text-error',
    bg: 'bg-error/10',
    border: 'border-error/30',
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
        'rounded-md border p-6',
        'bg-surface-elevated',
        'border-accent-cyan/30'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-text flex items-center gap-2">
          <Target className="w-5 h-5 text-accent-cyan-ink" />
          Synthèse du Board
        </h3>
        <span className={cn(
          'px-3 py-1 rounded-sm text-xs font-medium',
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
        'mb-6 p-4 rounded-md',
        'bg-accent-cyan/5 border border-accent-cyan/20'
      )}>
        <h4 className="text-sm font-medium text-accent-cyan-ink mb-2">
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
            <h4 className="text-sm font-medium text-agent-green flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              Points de consensus
            </h4>
            <ul className="space-y-1.5">
              {synthesis.consensus_points.map((point, i) => (
                <li key={i} className="text-sm text-text-muted flex items-start gap-2">
                  <span className="text-agent-green mt-1">•</span>
                  {point}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Divergences */}
        {synthesis.divergence_points.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-warning flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Points de divergence
            </h4>
            <ul className="space-y-1.5">
              {synthesis.divergence_points.map((point, i) => (
                <li key={i} className="text-sm text-text-muted flex items-start gap-2">
                  <span className="text-warning mt-1">•</span>
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
          <h4 className="text-sm font-medium text-accent-magenta-ink flex items-center gap-2 mb-2">
            <ArrowRight className="w-4 h-4" />
            Prochaines étapes
          </h4>
          <ol className="space-y-1.5">
            {synthesis.next_steps.map((step, i) => (
              <li key={i} className="text-sm text-text-muted flex items-start gap-2">
                <span className="text-accent-magenta-ink font-medium">{i + 1}.</span>
                {step}
              </li>
            ))}
          </ol>
        </div>
      )}
    </motion.div>
  );
}
