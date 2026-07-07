/**
 * THÉRÈSE v2 - Tests services/api/chat.ts (revue finale, 07/07/2026)
 *
 * Verrouille le fix jumeau du finding bloquant 2 de la revue de branche
 * `feat/atelier-documentaire` : `exportConversation` doit fetcher une URL
 * ABSOLUE (`API_BASE` + `download_url`), pas le chemin relatif renvoyé par
 * le backend. Même bug que `documents.ts::downloadExportedDocument`
 * (`apiFetch` ne préfixe jamais, pas de proxy Vite).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockApiFetch = vi.fn();
const mockRequest = vi.fn();

vi.mock('./core', async () => {
  const actual = await vi.importActual<typeof import('./core')>('./core');
  return {
    ...actual,
    API_BASE: 'http://127.0.0.1:17293',
    apiFetch: (...args: unknown[]) => mockApiFetch(...args),
    request: (...args: unknown[]) => mockRequest(...args),
  };
});

import { exportConversation } from './chat';

describe('exportConversation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetche une URL ABSOLUE (API_BASE + download_url), pas le chemin relatif seul', async () => {
    mockRequest.mockResolvedValueOnce({
      success: true,
      format: 'md',
      file_name: 'conversation.md',
      download_url: '/api/skills/download/xyz789',
    });
    const blob = new Blob(['# Export conversation'], { type: 'text/markdown' });
    mockApiFetch.mockResolvedValueOnce({ ok: true, blob: () => Promise.resolve(blob) });

    const createObjectURLSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:conv');
    const revokeObjectURLSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);

    await exportConversation('conv-1', 'md');

    expect(mockApiFetch).toHaveBeenCalledWith(
      'http://127.0.0.1:17293/api/skills/download/xyz789'
    );

    clickSpy.mockRestore();
    revokeObjectURLSpy.mockRestore();
    createObjectURLSpy.mockRestore();
  });
});
