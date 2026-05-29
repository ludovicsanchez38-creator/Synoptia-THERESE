/**
 * THÉRÈSE v2 - Agent Input
 *
 * Input compact pour envoyer des messages aux agents.
 */

import React, { useState, useRef } from 'react';
import { Send, Square } from 'lucide-react';

interface Props {
  onSend: (message: string) => void;
  onCancel?: () => void;
  isStreaming: boolean;
  placeholder?: string;
}

export function AgentInput({ onSend, onCancel, isStreaming, placeholder }: Props) {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || isStreaming) return;
    onSend(trimmed);
    setValue('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex items-end gap-2 border-t border-border bg-bg px-3 py-2.5">
      <textarea
        ref={inputRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || 'Décris ce que tu veux...'}
        disabled={isStreaming}
        rows={1}
        className="flex-1 resize-none rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text placeholder-[#6B7280] outline-none transition focus:border-purple-500/50 disabled:opacity-50"
        style={{ minHeight: '38px', maxHeight: '120px' }}
        onInput={(e) => {
          const target = e.target as HTMLTextAreaElement;
          target.style.height = 'auto';
          target.style.height = `${Math.min(target.scrollHeight, 120)}px`;
        }}
      />

      {isStreaming ? (
        <button
          onClick={onCancel}
          className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-500/20 text-red-400 transition hover:bg-red-500/30"
          title="Annuler"
        >
          <Square size={16} />
        </button>
      ) : (
        <button
          onClick={handleSubmit}
          disabled={!value.trim()}
          className="flex h-9 w-9 items-center justify-center rounded-lg bg-purple-500/20 text-purple-400 transition hover:bg-purple-500/30 disabled:opacity-30 disabled:hover:bg-purple-500/20"
          title="Envoyer"
        >
          <Send size={16} />
        </button>
      )}
    </div>
  );
}
