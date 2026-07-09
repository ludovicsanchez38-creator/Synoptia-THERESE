/**
 * BUG-130 : restauration du fichier de skill (et du provider) au rechargement
 * d'une conversation. Sans ça, un ancien message de génération réaffiche le code
 * brut sans bouton de téléchargement.
 */
import { describe, expect, it } from 'vitest';
import { formatMessageFromResponse } from './useConversationSync';
import type { MessageResponse } from '../services/api';

function makeResponse(over: Partial<MessageResponse> = {}): MessageResponse {
  return {
    id: 'm1',
    conversation_id: 'c1',
    role: 'assistant',
    content: '```python\nwb.save(output_path)\n```',
    tokens_in: null,
    tokens_out: null,
    model: null,
    created_at: '2026-07-09T10:00:00Z',
    ...over,
  };
}

describe('formatMessageFromResponse - restauration skillFile (BUG-130)', () => {
  it('restaure skillFile depuis extra_data JSON', () => {
    const msg = makeResponse({
      extra_data: JSON.stringify({
        skill_file: {
          skill_id: 'xlsx-pro',
          file_id: 'abc-123',
          file_name: 'Offres.xlsx',
          file_size: 4917,
          download_url: '/api/skills/download/abc-123',
          format: 'xlsx',
        },
      }),
    });
    const out = formatMessageFromResponse(msg);
    expect(out.skillFile).toBeTruthy();
    expect(out.skillFile?.file_id).toBe('abc-123');
    expect(out.skillFile?.file_name).toBe('Offres.xlsx');
    expect(out.skillFile?.format).toBe('xlsx');
  });

  it('sans extra_data : pas de skillFile', () => {
    const out = formatMessageFromResponse(makeResponse());
    expect(out.skillFile).toBeUndefined();
  });

  it('extra_data corrompu (non-JSON) : pas de crash, pas de skillFile', () => {
    const out = formatMessageFromResponse(makeResponse({ extra_data: 'pas du json {{{' }));
    expect(out.skillFile).toBeUndefined();
    expect(out.content).toContain('wb.save');
  });

  it('extra_data JSON sans skill_file : pas de skillFile', () => {
    const out = formatMessageFromResponse(makeResponse({ extra_data: '{"autre":1}' }));
    expect(out.skillFile).toBeUndefined();
  });

  it('restaure le provider (badge local/cloud au restore)', () => {
    const out = formatMessageFromResponse(makeResponse({ provider: 'anthropic' }));
    expect(out.provider).toBe('anthropic');
  });

  it('conserve les champs de base', () => {
    const out = formatMessageFromResponse(makeResponse({ id: 'x9', content: 'coucou' }));
    expect(out.id).toBe('x9');
    expect(out.role).toBe('assistant');
    expect(out.content).toBe('coucou');
    expect(out.timestamp).toBeInstanceOf(Date);
  });
});
