/**
 * THÉRÈSE v2 - Tests services/api/documents.ts (revue finale, 07/07/2026)
 *
 * Verrouille deux corrections de la revue de branche `feat/atelier-documentaire` :
 * - finding bloquant 2 : `downloadExportedDocument` doit fetcher une URL
 *   ABSOLUE (`API_BASE` + `download_url`) - `apiFetch` ne préfixe jamais,
 *   pas de proxy Vite, donc une URL relative casse dès que le front n'est
 *   pas sur l'origine backend (toujours le cas en dev/packagé).
 * - finding minor 7 : `draftSection`, sur réponse HTTP non-ok, doit parser
 *   le corps JSON et en extraire `detail`/`message` (comme `request()`
 *   dans core.ts) plutôt que de mettre le JSON brut dans `error.message`.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockApiFetch = vi.fn();

vi.mock('./core', async () => {
  const actual = await vi.importActual<typeof import('./core')>('./core');
  return {
    ...actual,
    API_BASE: 'http://127.0.0.1:17293',
    apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  };
});

import { downloadExportedDocument, draftSection } from './documents';

describe('downloadExportedDocument', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetche une URL ABSOLUE (API_BASE + download_url), pas le chemin relatif seul', async () => {
    const blob = new Blob(['# Guide export'], { type: 'text/markdown' });
    mockApiFetch.mockResolvedValueOnce({ ok: true, blob: () => Promise.resolve(blob) });

    const createObjectURLSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:doc');
    const revokeObjectURLSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);

    await downloadExportedDocument({
      success: true,
      format: 'md',
      file_name: 'guide-export.md',
      download_url: '/api/skills/download/abc123',
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      'http://127.0.0.1:17293/api/skills/download/abc123'
    );

    clickSpy.mockRestore();
    revokeObjectURLSpy.mockRestore();
    createObjectURLSpy.mockRestore();
  });
});

describe('draftSection - erreur HTTP non-ok', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('extrait detail/message du corps JSON plutôt que de mettre le JSON brut dans error.message', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: false,
      status: 429,
      statusText: 'Too Many Requests',
      json: () => Promise.resolve({ detail: 'Quota LLM dépassé, réessaie plus tard.' }),
    });

    const generator = draftSection('section-1');

    await expect(generator.next()).rejects.toMatchObject({
      name: 'ApiError',
      status: 429,
      message: 'Quota LLM dépassé, réessaie plus tard.',
    });
  });

  it("retombe sur un message par défaut si le corps n'est pas du JSON exploitable", async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.reject(new Error('pas du JSON')),
    });

    const generator = draftSection('section-1');

    await expect(generator.next()).rejects.toMatchObject({
      name: 'ApiError',
      status: 500,
      message: 'Erreur 500',
    });
  });
});
