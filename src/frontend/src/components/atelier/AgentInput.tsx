/**
 * THÉRÈSE v2 - Agent Input
 *
 * Input compact pour envoyer des messages aux agents.
 */

import React, { useState, useRef } from 'react';
import { Send, Square } from 'lucide-react';
import { Button } from '../ui/Button';
import { Textarea } from '../ui/Textarea';

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
      <Textarea aria-label="Message à l’agent"
        ref={inputRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || 'Décris ce que tu veux...'}
        disabled={isStreaming}
        rows={1}
        className="max-h-[120px] flex-1 resize-none"
        onInput={(e) => {
          const target = e.target as HTMLTextAreaElement;
          target.style.height = 'auto';
          target.style.height = `${Math.min(target.scrollHeight, 120)}px`;
        }}
      />

      {isStreaming ? (
        <Button
          type="button"
          variant="danger"
          size="icon"
          onClick={onCancel}
          title="Annuler"
          aria-label="Annuler"
        >
          <Square size={16} />
        </Button>
      ) : (
        <Button
          type="button"
          variant="primary"
          size="icon"
          onClick={handleSubmit}
          disabled={!value.trim()}
          title="Envoyer"
          aria-label="Envoyer"
        >
          <Send size={16} />
        </Button>
      )}
    </div>
  );
}
