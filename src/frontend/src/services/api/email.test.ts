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

import { getEmailSignature, updateEmailSignature } from './email';

describe('Signature email API (quick win testeur)', () => {
  beforeEach(() => vi.clearAllMocks());

  it('getEmailSignature appelle GET /accounts/{id}/signature', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ account_id: 'acc-1', signature_html: '<p>Ludo</p>' }),
    });

    const res = await getEmailSignature('acc-1');

    expect(res.signature_html).toBe('<p>Ludo</p>');
    expect(mockApiFetch).toHaveBeenCalledWith(
      'http://127.0.0.1:17293/api/email/accounts/acc-1/signature'
    );
  });

  it('updateEmailSignature fait un PUT avec le HTML en body', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ account_id: 'acc-1', signature_html: '<p>Ludo</p>' }),
    });

    const res = await updateEmailSignature('acc-1', '<p>Ludo</p>');

    expect(res.signature_html).toBe('<p>Ludo</p>');
    expect(mockApiFetch).toHaveBeenCalledWith(
      'http://127.0.0.1:17293/api/email/accounts/acc-1/signature',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({ signature_html: '<p>Ludo</p>' }),
      })
    );
  });

  it('getEmailSignature lève si la réponse n est pas ok', async () => {
    mockApiFetch.mockResolvedValueOnce({ ok: false });
    await expect(getEmailSignature('acc-1')).rejects.toThrow();
  });
});
