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
import { grantCloudConsent } from '../../lib/consent';
import type { LLMProvider } from '../../services/api';

interface SecurityStepProps {
  provider: LLMProvider | null;
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
    description: 'Tes messages sont envoyés aux serveurs des providers (Anthropic, OpenAI, Gemini...). Ne partage jamais de données sensibles (mots de passe, secrets, données clients).',
    severity: 'high',
  },
  {
    icon: Terminal,
    title: 'Serveurs MCP',
    description: 'Les tools MCP peuvent exécuter des commandes, lire et écrire des fichiers sur ta machine. Active uniquement les serveurs de confiance.',
    severity: 'high',
  },
  {
    icon: FolderOpen,
    title: 'Accès fichiers',
    description: 'THÉRÈSE peut lire tes fichiers locaux pour le contexte. Les fichiers indexés sont stockés localement dans Qdrant.',
    severity: 'medium',
  },
  {
    icon: Globe,
    title: 'Recherche Web',
    description: 'Les recherches sont envoyées à DuckDuckGo ou Google (selon le provider). Tes requêtes peuvent être tracées.',
    severity: 'low',
  },
  {
    icon: Mic,
    title: 'Transcription vocale',
    description: 'L\'audio est envoyé à Groq pour transcription. Ne dicte pas d\'informations confidentielles.',
    severity: 'medium',
  },
];

const severityColors = {
  high: 'text-error bg-[var(--color-error-tint)] border-error/40',
  medium: 'text-warning bg-[var(--color-warning-tint)] border-warning/40',
  low: 'text-info bg-[var(--color-info-tint)] border-info/40',
};

const severityLabels = {
  high: 'Risque élevé',
  medium: 'Risque modéré',
  low: 'Risque faible',
};

const providerLabels: Partial<Record<LLMProvider, string>> = {
  anthropic: 'Anthropic', openai: 'OpenAI', gemini: 'Google Gemini', mistral: 'Mistral',
  grok: 'xAI', openrouter: 'OpenRouter', perplexity: 'Perplexity', deepseek: 'DeepSeek',
  infomaniak: 'Infomaniak', ollama: 'Ollama local',
};

export function SecurityStep({ provider, onNext, onBack }: SecurityStepProps) {
  const [acknowledged, setAcknowledged] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);
  const cloudEnabled = provider !== null && provider !== 'ollama';
  const providerLabel = provider ? providerLabels[provider] || provider : null;

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      className="space-y-6"
    >
      {/* Header avec warning */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[var(--color-warning-tint)] border border-warning/40">
          <Shield className="w-8 h-8 text-warning" />
        </div>
        <h2 className="text-2xl font-bold text-text">Sécurité et confidentialité</h2>
        <p className="text-text-muted max-w-md mx-auto">
          THÉRÈSE est un outil puissant qui se connecte à plusieurs services.
          Comprends les risques avant de continuer.
        </p>
      </div>

      {/* Alert banner */}
      <div className="flex items-start gap-3 p-4 rounded-xl bg-[var(--color-warning-tint)] border border-warning/40">
        <AlertTriangle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="text-warning font-medium">Important</p>
          <p className="text-warning mt-1">
            Les agents IA peuvent exécuter des commandes et agir via les tools que tu actives.
            Commence avec le minimum de permissions nécessaires.
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
                'hover:bg-surface-2',
                isExpanded ? 'bg-surface-2' : 'bg-transparent',
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
                      'text-xs px-2 py-0.5 rounded-[6px]',
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
        <span>En savoir plus sur la sécurité</span>
        <ExternalLink className="w-4 h-4" />
      </a>

      {/* Consentement RGPD uniquement lorsqu'un fournisseur cloud est activé. */}
      {cloudEnabled ? <label className="flex items-start gap-3 p-4 rounded-xl bg-surface border border-border cursor-pointer hover:bg-surface-elevated transition-colors">
        <input
          type="checkbox"
          id="security-consent"
          checked={acknowledged}
          onChange={(e) => setAcknowledged(e.target.checked)}
          className="mt-1 w-5 h-5 rounded border-border bg-transparent text-accent-cyan focus:ring-2 focus:ring-accent-cyan focus:ring-offset-0"
        />
        <div className="text-sm">
          <p className="text-text font-medium">
            Je consens au transfert de mes données vers {providerLabel}
          </p>
          <p className="text-text-muted mt-1">
            J'accepte que mes messages, pièces jointes sélectionnées et contexte utile soient envoyés à {providerLabel}
            pour traitement. Je comprends les risques et m'engage à ne pas partager de données sensibles
            (mots de passe, données clients, informations confidentielles).
          </p>
        </div>
      </label> : (
        <div className="flex items-start gap-3 rounded-xl border border-accent-cyan/30 bg-accent-cyan/10 p-4" data-testid="local-security-notice">
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-accent-cyan" />
          <div className="text-sm"><p className="font-medium text-text">Parcours local sans consentement cloud</p><p className="mt-1 text-text-muted">{provider === 'ollama' ? 'Ollama traite les messages sur cette machine.' : 'Aucun fournisseur cloud n’est activé pour le moment.'} Un accord distinct sera demandé au premier usage cloud réel, avec le fournisseur et les données transmis.</p></div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex gap-3 pt-2">
        <button
          onClick={onBack}
          data-testid="onboarding-prev-btn"
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
          onClick={() => {
            if (cloudEnabled && provider) {
              grantCloudConsent('llm', provider, ['messages', 'pièces jointes sélectionnées', 'contexte utile']);
            }
            onNext();
          }}
          disabled={cloudEnabled && !acknowledged}
          data-testid="onboarding-next-btn"
          className={cn(
            'flex-1 flex items-center justify-center gap-2',
            'px-4 py-3 rounded-xl font-medium',
            'transition-all',
            (!cloudEnabled || acknowledged)
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
