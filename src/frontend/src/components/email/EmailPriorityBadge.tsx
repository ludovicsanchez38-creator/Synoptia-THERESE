/**
 * EmailPriorityBadge.tsx
 *
 * Badge de priorité coloré pour les emails (Rouge/Orange/Vert).
 * US-EMAIL-08: Priorisation visuelle
 */

import React from 'react';

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
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
  },
  medium: {
    emoji: '🟠',
    text: 'Important',
    color: 'text-orange-400',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
  },
  low: {
    emoji: '🟢',
    text: 'Normal',
    color: 'text-green-400',
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
