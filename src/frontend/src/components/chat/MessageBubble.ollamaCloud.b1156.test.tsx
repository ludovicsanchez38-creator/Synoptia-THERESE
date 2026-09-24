/**
 * B-1156 (cycle 13) : la pastille du chat disait « Local » pour un modèle
 * Ollama Cloud, dont les requêtes partent chez ollama.com : elle ne testait
 * que le fournisseur (prov === 'ollama'), pas le modèle.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MessageBubble } from './MessageBubble';
import type { Message } from '../../stores/chatStore';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, downloadSkillFile: vi.fn(), fetchImageObjectUrl: vi.fn() };
});

function messageDe(model: string): Message {
  return {
    id: 'm1',
    role: 'assistant',
    content: 'Bonjour',
    timestamp: new Date(),
    usage: { input_tokens: 10, output_tokens: 5, cost_eur: 0, model, provider: 'ollama' },
  } as Message;
}

describe('B-1156 pastille locale', () => {
  it('dit « Local » pour un modèle Ollama installé (témoin)', () => {
    render(<MessageBubble message={messageDe('qwen3:8b')} />);
    expect(screen.getByText('Local')).toBeInTheDocument();
  });

  it('dit « Cloud » pour un modèle Ollama Cloud', () => {
    render(<MessageBubble message={messageDe('kimi-k2.6:cloud')} />);
    expect(screen.queryByText('Local')).toBeNull();
    expect(screen.getByText('Cloud')).toBeInTheDocument();
  });
});
