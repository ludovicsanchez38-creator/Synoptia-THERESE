/**
 * EmailPriorityBadge.tsx
 *
 * Badge de priorité coloré pour les emails (Rouge/Orange/Vert), pastille dessinée.
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
    dot: 'bg-error',
    text: 'Urgent',
    color: 'text-error',
    bg: 'bg-error/10',
    border: 'border-error/30',
  },
  medium: {
    dot: 'bg-agent-amber',
    text: 'Important',
    color: 'text-agent-amber',
    bg: 'bg-agent-amber/10',
    border: 'border-agent-amber/30',
  },
  low: {
    dot: 'bg-agent-green',
    text: 'Normal',
    color: 'text-agent-green',
    bg: 'bg-agent-green/10',
    border: 'border-agent-green/30',
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
      {/* B-293 : pastille dessinée, plus d'emoji (charte : icônes SVG ou formes) */}
      <span aria-hidden="true" className={`inline-block h-2 w-2 rounded-full ${config.dot}`} />
      {showText ? (
        <span className={`text-xs font-medium ${config.color}`}>
          {config.text}
        </span>
      ) : (
        // #143 : sans texte visible, la priorité garde un nom pour les
        // technologies d'assistance (la couleur seule ne la porte pas).
        <span className="sr-only">{config.text}</span>
      )}
    </div>
  );
}
