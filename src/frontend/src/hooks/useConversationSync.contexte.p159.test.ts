/**
 * P-159 : au rechargement, le contexte transmis revient avec le message.
 */
import { describe, expect, it } from 'vitest';
import { formatMessageFromResponse } from './useConversationSync';
import type { MessageResponse } from '../services/api';

function reponse(extra_data: string | null): MessageResponse {
  return {
    id: 'm1',
    conversation_id: 'c1',
    role: 'assistant',
    content: 'Réponse.',
    tokens_in: null,
    tokens_out: null,
    model: null,
    created_at: '2026-09-29T10:00:00Z',
    extra_data,
  };
}

describe('formatMessageFromResponse — contexte transmis (P-159)', () => {
  it('restaure les deux comptes depuis extra_data', () => {
    const message = formatMessageFromResponse(reponse(JSON.stringify({
      contexte: { messages_relus: 50, messages_transmis: 30 },
      skill_files: [{ skill_id: 'docx', file_id: 'f1', file_name: 'a.docx', file_size: 10, format: 'docx' }],
    })));
    expect(message.contexte).toEqual({ messages_relus: 50, messages_transmis: 30 });
    expect(message.skillFile?.file_id).toBe('f1');
  });

  it('restaure la quantité de texte retirée du message en cours', () => {
    const message = formatMessageFromResponse(reponse(JSON.stringify({
      contexte: { messages_relus: 0, messages_transmis: 0, caracteres_retires: 752 },
    })));
    expect(message.contexte).toEqual({
      messages_relus: 0,
      messages_transmis: 0,
      caracteres_retires: 752,
    });
  });

  it('ignore un contexte incomplet sans perdre le message', () => {
    const message = formatMessageFromResponse(reponse('{"contexte": {"messages_relus": 4}}'));
    expect(message.contexte).toBeUndefined();
    expect(message.content).toBe('Réponse.');
  });
});
