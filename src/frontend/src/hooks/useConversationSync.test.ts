/**
 * BUG-130 : restauration du fichier de skill (et du provider) au rechargement
 * d'une conversation. Sans ça, un ancien message de génération réaffiche le code
 * brut sans bouton de téléchargement.
 */
import { describe, expect, it } from 'vitest';
import { formatMessageFromResponse, formatConversationFromResponse } from './useConversationSync';
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

  it('restaure les sources d’une recherche approfondie depuis extra_data', () => {
    const out = formatMessageFromResponse(makeResponse({
      extra_data: JSON.stringify({
        sources: [{ title: 'Article', url: 'https://exemple.test/a', snippet: 'Extrait' }],
      }),
    }));
    expect(out.webSources).toEqual([
      { title: 'Article', url: 'https://exemple.test/a', snippet: 'Extrait' },
    ]);
  });
});

describe('formatConversationFromResponse (0.43)', () => {
  it('restaure le rattachement à un projet', () => {
    // Sans ce mapping, l'en-tête du chat afficherait « Toute la mémoire » alors
    // que le backend cloisonne réellement sur un projet : l'utilisateur croirait
    // consulter toute sa mémoire pendant qu'une partie lui est masquée. Un
    // affichage qui ment sur la cloison est pire que pas de cloison.
    const out = formatConversationFromResponse({
      id: 'c1',
      title: 'Client A',
      summary: null,
      message_count: 3,
      created_at: '2026-07-31T10:00:00Z',
      updated_at: '2026-07-31T10:00:00Z',
      project_id: 'projet-a',
      memory_scope: 'project',
    });
    expect(out.projectId).toBe('projet-a');
  });

  it('une conversation libre n’a pas de rattachement', () => {
    const out = formatConversationFromResponse({
      id: 'c2',
      title: null,
      summary: null,
      message_count: 0,
      created_at: '2026-07-31T10:00:00Z',
      updated_at: '2026-07-31T10:00:00Z',
      project_id: null,
      memory_scope: 'global',
    });
    expect(out.projectId).toBeNull();
    expect(out.title).toBe('Nouvelle conversation');
  });
});
