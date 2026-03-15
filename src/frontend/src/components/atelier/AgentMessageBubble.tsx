/**
 * THÉRÈSE v2 - Agent Message Bubble
 *
 * Bulle de message pour les agents avec avatar et badge coloré.
 * Thérèse = violet (#A855F7), Zézette = orange (#F59E0B).
 */

import React from 'react';
import { Headphones, Wrench, User, Info } from 'lucide-react';
import type { AgentMessage } from '../../stores/atelierStore';

const AGENT_STYLES: Record<string, { color: string; bg: string; icon: React.ReactNode; label: string }> = {
  katia: {
    color: '#A855F7',
    bg: 'rgba(168, 85, 247, 0.1)',
    icon: <Headphones size={14} />,
    label: 'Katia',
  },
  zezette: {
    color: '#F59E0B',
    bg: 'rgba(245, 158, 11, 0.1)',
    icon: <Wrench size={14} />,
    label: 'Zézette',
  },
  user: {
    color: '#22D3EE',
    bg: 'rgba(34, 211, 238, 0.1)',
    icon: <User size={14} />,
    label: 'Vous',
  },
  system: {
    color: '#6B7280',
    bg: 'rgba(107, 114, 128, 0.08)',
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
      <div className="flex items-center gap-2 px-3 py-1.5 text-xs text-[#B6C7DA] opacity-70">
        <span style={{ color: style.color }}>{style.icon}</span>
        <span>{message.content}</span>
      </div>
    );
  }

  // Carte de handoff
  if (message.type === 'handoff') {
    return (
      <div
        className="mx-3 my-2 rounded-lg p-3 text-sm"
        style={{
          background: 'linear-gradient(135deg, rgba(168,85,247,0.15), rgba(245,158,11,0.15))',
          borderLeft: '3px solid',
          borderImage: 'linear-gradient(to bottom, #A855F7, #F59E0B) 1',
        }}
      >
        <div className="mb-1 flex items-center gap-2 text-xs font-medium text-[#B6C7DA]">
          <Headphones size={12} className="text-purple-400" />
          <span>Katia transmet à Zézette</span>
          <Wrench size={12} className="text-amber-400" />
        </div>
        <div className="text-[#E6EDF7]">{message.content}</div>
      </div>
    );
  }

  return (
    <div className={`flex gap-2.5 px-3 py-2 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className="mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full"
        style={{ backgroundColor: style.bg, color: style.color }}
      >
        {style.icon}
      </div>

      {/* Contenu */}
      <div className={`max-w-[85%] ${isUser ? 'text-right' : ''}`}>
        {/* Badge agent */}
        {!isUser && (
          <div
            className="mb-0.5 text-xs font-medium"
            style={{ color: style.color }}
          >
            {style.label}
          </div>
        )}

        {/* Message */}
        <div
          className="rounded-lg px-3 py-2 text-sm leading-relaxed"
          style={{
            backgroundColor: isUser ? 'rgba(34, 211, 238, 0.1)' : style.bg,
            borderLeft: isUser ? 'none' : `2px solid ${style.color}`,
            color: '#E6EDF7',
          }}
        >
          <span style={{ whiteSpace: 'pre-wrap' }}>{message.content}</span>
          {message.isStreaming && (
            <span className="ml-1 inline-block h-3 w-1.5 animate-pulse rounded-sm bg-current opacity-60" />
          )}
        </div>
      </div>
    </div>
  );
}
