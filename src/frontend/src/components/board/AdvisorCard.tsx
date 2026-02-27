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
  isWaiting?: boolean;
}

// Provider display names and colors
const PROVIDER_INFO: Record<string, { label: string; color: string }> = {
  anthropic: { label: 'CLAUDE', color: '#D97757' },
  openai: { label: 'GPT', color: '#10A37F' },
  gemini: { label: 'GEMINI', color: '#4285F4' },
  mistral: { label: 'MISTRAL', color: '#FF7000' },
  grok: { label: 'GROK', color: '#1DA1F2' },
  ollama: { label: 'OLLAMA', color: '#8B5CF6' },
};

function getProviderInfo(provider?: string): { label: string; color: string } | null {
  if (!provider) return null;
  // Support "ollama:model-name" format
  if (provider.startsWith('ollama:')) {
    const model = provider.slice(7);
    return { label: model.toUpperCase(), color: '#8B5CF6' };
  }
  return PROVIDER_INFO[provider] || null;
}

export function AdvisorCard({
  role,
  name,
  emoji: _emoji, // Deprecated
  color,
  content,
  provider,
  isLoading,
  isComplete,
  isWaiting,
}: AdvisorCardProps) {
  void _emoji; // Unused, keeping for backwards compatibility

  const Icon = ADVISOR_ICONS[role];
  const providerInfo = getProviderInfo(provider);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: isWaiting ? 0.4 : 1, y: 0 }}
      className={cn(
        'relative rounded-xl border p-4 transition-all duration-300',
        'bg-surface-elevated/80 backdrop-blur-sm',
        isWaiting && 'opacity-40',
        isComplete ? 'border-border' : 'border-border/50',
      )}
      style={{
        borderColor: isLoading ? color : isComplete ? color : undefined,
        boxShadow: isLoading
          ? `0 0 24px ${color}30, inset 0 0 12px ${color}08`
          : isComplete
            ? `0 0 20px ${color}20`
            : undefined,
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
        <div
          className={cn(
            'w-14 h-14 rounded-full flex items-center justify-center transition-all',
            isLoading && 'animate-pulse',
          )}
          style={{
            backgroundColor: `${color}15`,
            outline: `2px solid ${isLoading ? color : `${color}40`}`,
            outlineOffset: '2px',
            boxShadow: isLoading ? `0 0 16px ${color}40` : undefined,
          }}
        >
          <Icon className="w-6 h-6" style={{ color }} />
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
