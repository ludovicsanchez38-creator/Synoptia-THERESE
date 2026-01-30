import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Shield,
  AlertTriangle,
  Cloud,
  Terminal,
  FolderOpen,
  Mic,
  Globe,
  CheckCircle2,
  ExternalLink,
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface SecurityStepProps {
  onNext: () => void;
  onBack: () => void;
}

interface RiskItem {
  icon: React.ElementType;
  title: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
}

const RISKS: RiskItem[] = [
  {
    icon: Cloud,
    title: 'LLMs Cloud',
    description: 'Tes messages sont envoyes aux serveurs des providers (Anthropic, OpenAI, Gemini...). Ne partage jamais de donnees sensibles (mots de passe, secrets, donnees clients).',
    severity: 'high',
  },
  {
    icon: Terminal,
    title: 'Serveurs MCP',
    description: 'Les tools MCP peuvent executer des commandes, lire et ecrire des fichiers sur ta machine. Active uniquement les serveurs de confiance.',
    severity: 'high',
  },
  {
    icon: FolderOpen,
    title: 'Acces fichiers',
    description: 'THERESE peut lire tes fichiers locaux pour le contexte. Les fichiers indexes sont stockes localement dans Qdrant.',
    severity: 'medium',
  },
  {
    icon: Globe,
    title: 'Recherche Web',
    description: 'Les recherches sont envoyees a DuckDuckGo ou Google (selon le provider). Tes requetes peuvent etre tracees.',
    severity: 'low',
  },
  {
    icon: Mic,
    title: 'Transcription vocale',
    description: 'L\'audio est envoye a Groq pour transcription. Ne dicte pas d\'informations confidentielles.',
    severity: 'medium',
  },
];

const severityColors = {
  high: 'text-red-400 bg-red-500/10 border-red-500/30',
  medium: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  low: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
};

const severityLabels = {
  high: 'Risque eleve',
  medium: 'Risque modere',
  low: 'Risque faible',
};

export function SecurityStep({ onNext, onBack }: SecurityStepProps) {
  const [acknowledged, setAcknowledged] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      className="space-y-6"
    >
      {/* Header avec warning */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-amber-500/20 border border-amber-500/30">
          <Shield className="w-8 h-8 text-amber-400" />
        </div>
        <h2 className="text-2xl font-bold text-text">Securite et confidentialite</h2>
        <p className="text-text-muted max-w-md mx-auto">
          THERESE est un outil puissant qui se connecte a plusieurs services.
          Comprends les risques avant de continuer.
        </p>
      </div>

      {/* Alert banner */}
      <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
        <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="text-amber-200 font-medium">Important</p>
          <p className="text-amber-200/80 mt-1">
            Les agents IA peuvent executer des commandes et agir via les tools que tu actives.
            Commence avec le minimum de permissions necessaires.
          </p>
        </div>
      </div>

      {/* Risks list */}
      <div className="space-y-2 max-h-[280px] overflow-y-auto pr-2">
        {RISKS.map((risk, index) => {
          const Icon = risk.icon;
          const isExpanded = expanded === index;

          return (
            <motion.button
              key={index}
              onClick={() => setExpanded(isExpanded ? null : index)}
              className={cn(
                'w-full text-left p-3 rounded-xl border transition-all',
                'hover:bg-white/5',
                isExpanded ? 'bg-white/5' : 'bg-transparent',
                'border-border'
              )}
              initial={false}
              animate={{ height: isExpanded ? 'auto' : 'auto' }}
            >
              <div className="flex items-center gap-3">
                <div className={cn(
                  'w-10 h-10 rounded-lg flex items-center justify-center',
                  severityColors[risk.severity]
                )}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-text">{risk.title}</span>
                    <span className={cn(
                      'text-xs px-2 py-0.5 rounded-full',
                      severityColors[risk.severity]
                    )}>
                      {severityLabels[risk.severity]}
                    </span>
                  </div>
                  {isExpanded && (
                    <motion.p
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="text-sm text-text-muted mt-2"
                    >
                      {risk.description}
                    </motion.p>
                  )}
                </div>
              </div>
            </motion.button>
          );
        })}
      </div>

      {/* Best practices link */}
      <a
        href="https://synoptia.fr/therese/securite"
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center justify-center gap-2 text-sm text-accent-cyan hover:text-accent-cyan/80 transition-colors"
      >
        <span>En savoir plus sur la securite</span>
        <ExternalLink className="w-4 h-4" />
      </a>

      {/* Acknowledgment checkbox */}
      <label className="flex items-start gap-3 p-4 rounded-xl bg-surface border border-border cursor-pointer hover:bg-surface-elevated transition-colors">
        <input
          type="checkbox"
          checked={acknowledged}
          onChange={(e) => setAcknowledged(e.target.checked)}
          className="mt-1 w-5 h-5 rounded border-border bg-transparent text-accent-cyan focus:ring-2 focus:ring-accent-cyan focus:ring-offset-0"
        />
        <div className="text-sm">
          <p className="text-text font-medium">
            Je comprends que THERESE est un outil puissant avec des risques inherents
          </p>
          <p className="text-text-muted mt-1">
            Je m'engage a ne pas partager de donnees sensibles et a configurer les permissions avec prudence.
          </p>
        </div>
      </label>

      {/* Navigation */}
      <div className="flex gap-3 pt-2">
        <button
          onClick={onBack}
          className={cn(
            'flex-1 px-4 py-3 rounded-xl font-medium',
            'bg-surface border border-border',
            'text-text hover:bg-surface-elevated',
            'transition-colors'
          )}
        >
          Retour
        </button>
        <button
          onClick={onNext}
          disabled={!acknowledged}
          className={cn(
            'flex-1 flex items-center justify-center gap-2',
            'px-4 py-3 rounded-xl font-medium',
            'transition-all',
            acknowledged
              ? 'bg-accent-cyan text-bg hover:bg-accent-cyan/90'
              : 'bg-surface text-text-muted cursor-not-allowed opacity-50'
          )}
        >
          <CheckCircle2 className="w-5 h-5" />
          <span>J'ai compris, continuer</span>
        </button>
      </div>
    </motion.div>
  );
}
