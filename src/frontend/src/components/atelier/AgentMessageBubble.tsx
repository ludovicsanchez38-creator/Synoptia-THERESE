/**
 * THÉRÈSE v2 - Agent Message Bubble
 *
 * Bulle de message pour les agents avec avatar et badge sémantique.
 */

import React from 'react';
import { Headphones, Wrench, User, Info } from 'lucide-react';
import type { AgentMessage } from '../../stores/atelierStore';

const AGENT_STYLES: Record<string, { color: string; bg: string; icon: React.ReactNode; label: string }> = {
  katia: {
    color: 'text-accent',
    bg: 'bg-accent-tint',
    icon: <Headphones size={14} />,
    label: 'Katia',
  },
  zezette: {
    color: 'text-warning',
    bg: 'bg-[var(--color-warning-tint)]',
    icon: <Wrench size={14} />,
    label: 'Zézette',
  },
  user: {
    color: 'text-accent',
    bg: 'bg-accent-tint',
    icon: <User size={14} />,
    label: 'Toi',
  },
  system: {
    color: 'text-text-muted',
    bg: 'bg-surface-2',
    icon: <Info size={14} />,
    label: 'Système',
  },
};

interface Props {
  message: AgentMessage;
}

export function AgentMessageBubble({ message }: Props) {
  const style = AGENT_STYLES[message.agentId] || AGENT_STYLES.system;
  const isUser = message.agentId === 'user';
  const isSystem = message.agentId === 'system';

  // Messages système compacts (tool_use, test_result)
  if (isSystem && (message.type === 'tool_use' || message.type === 'test_result')) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 text-xs text-text-muted opacity-70">
        <span className={style.color}>{style.icon}</span>
        <span>{message.content}</span>
      </div>
    );
  }

  // Carte de handoff
  if (message.type === 'handoff') {
    return (
      <div className="mx-3 my-2 rounded-md border-l-2 border-accent bg-surface-2 p-3 text-sm">
        <div className="mb-1 flex items-center gap-2 text-xs font-medium text-text-muted">
          <Headphones size={12} className="text-agent-purple" />
          <span>Katia transmet à Zézette</span>
          <Wrench size={12} className="text-agent-amber" />
        </div>
        <div className="text-text">{message.content}</div>
      </div>
    );
  }

  return (
    <div className={`flex gap-2.5 px-3 py-2 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full ${style.bg} ${style.color}`}>
        {style.icon}
      </div>

      {/* Contenu */}
      <div className={`max-w-[85%] ${isUser ? 'text-right' : ''}`}>
        {/* Badge agent */}
        {!isUser && (
          <div className={`mb-0.5 text-xs font-medium ${style.color}`}>
            {style.label}
          </div>
        )}

        {/* Message */}
        {/* BUG-127 : couleur de texte via le token de thème (text-text) et non
            une couleur claire figée. Sur fond de bulle à faible opacité en thème
            clair, un texte clair figé donnait « blanc sur blanc » (réponse de
            l'agent codeur invisible). Le token s'adapte clair/sombre. */}
        <div className={`rounded-md px-3 py-2 text-sm leading-relaxed text-text ${isUser ? 'bg-accent-tint' : `${style.bg} border-l-2 border-border`}`}>
          <span style={{ whiteSpace: 'pre-wrap' }}>{message.content}</span>
          {message.isStreaming && (
            <span className="ml-1 inline-block h-3 w-1.5 animate-pulse rounded-sm bg-current opacity-60" />
          )}
        </div>
      </div>
    </div>
  );
}
