import { motion } from 'framer-motion';
import {
  Loader2,
  BarChart3,
  Target,
  Flame,
  Wrench,
  Rocket,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import type { AdvisorRole } from '../../services/api';

// Icons for each advisor role
const ADVISOR_ICONS: Record<AdvisorRole, LucideIcon> = {
  analyst: BarChart3,
  strategist: Target,
  devil: Flame,
  pragmatic: Wrench,
  visionary: Rocket,
};

interface AdvisorCardProps {
  role: AdvisorRole;
  name: string;
  emoji?: string; // Deprecated, using icons now
  color: string;
  content: string;
  provider?: string;
  isLoading?: boolean;
  isComplete?: boolean;
}

// Provider display names and colors
const PROVIDER_INFO: Record<string, { label: string; color: string }> = {
  anthropic: { label: 'CLAUDE', color: '#D97757' },
  openai: { label: 'GPT', color: '#10A37F' },
  gemini: { label: 'GEMINI', color: '#4285F4' },
  mistral: { label: 'MISTRAL', color: '#FF7000' },
  grok: { label: 'GROK', color: '#1DA1F2' },
  ollama: { label: 'LOCAL', color: '#8B5CF6' },
};

export function AdvisorCard({
  role,
  name,
  emoji: _emoji, // Deprecated
  color,
  content,
  provider,
  isLoading,
  isComplete,
}: AdvisorCardProps) {
  void _emoji; // Unused, keeping for backwards compatibility

  const Icon = ADVISOR_ICONS[role];
  const providerInfo = provider ? PROVIDER_INFO[provider] : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'relative rounded-xl border p-4',
        'bg-surface-elevated/80 backdrop-blur-sm',
        isComplete ? 'border-border' : 'border-border/50'
      )}
      style={{
        borderColor: isComplete ? color : undefined,
        boxShadow: isComplete ? `0 0 20px ${color}20` : undefined,
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: `${color}20` }}
        >
          <Icon className="w-5 h-5" style={{ color }} />
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-text" style={{ color }}>
            {name}
          </h4>
        </div>
        {providerInfo && (
          <span
            className="text-[10px] px-1.5 py-0.5 rounded font-medium uppercase tracking-wide"
            style={{
              backgroundColor: `${providerInfo.color}20`,
              color: providerInfo.color,
            }}
          >
            {providerInfo.label}
          </span>
        )}
        {isLoading && (
          <Loader2 className="w-4 h-4 animate-spin text-text-muted" />
        )}
      </div>

      {/* Content */}
      <div className="text-sm text-text-muted leading-relaxed whitespace-pre-wrap">
        {content || (
          <span className="italic opacity-50">En attente de réponse...</span>
        )}
        {isLoading && content && (
          <span className="inline-block w-2 h-4 ml-1 bg-text-muted/50 animate-pulse" />
        )}
      </div>
    </motion.div>
  );
}
