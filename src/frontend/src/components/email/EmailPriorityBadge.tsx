/**
 * EmailPriorityBadge.tsx
 *
 * Badge de priorité coloré pour les emails (Rouge/Orange/Vert).
 * US-EMAIL-08: Priorisation visuelle
 */


interface EmailPriorityBadgeProps {
  priority: 'high' | 'medium' | 'low' | null;
  score?: number;
  className?: string;
  showText?: boolean;
}

const PRIORITY_CONFIG = {
  high: {
    emoji: '🔴',
    text: 'Urgent',
    color: 'text-error',
    bg: 'bg-error/10',
    border: 'border-error/30',
  },
  medium: {
    emoji: '🟠',
    text: 'Important',
    color: 'text-agent-amber',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
  },
  low: {
    emoji: '🟢',
    text: 'Normal',
    color: 'text-agent-green',
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
  },
};

export function EmailPriorityBadge({
  priority,
  score,
  className = '',
  showText = false,
}: EmailPriorityBadgeProps) {
  if (!priority) {
    return null;
  }

  const config = PRIORITY_CONFIG[priority];

  return (
    <div
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border ${config.bg} ${config.border} ${className}`}
      title={score ? `Score: ${score}/100` : undefined}
    >
      <span className="text-sm">{config.emoji}</span>
      {showText && (
        <span className={`text-xs font-medium ${config.color}`}>
          {config.text}
        </span>
      )}
    </div>
  );
}
