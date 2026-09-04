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

import { createDraft, getEmailSignature, modifyEmailMessage, updateEmailSignature } from './email';

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

  it('createDraft crée un brouillon sans appeler la route d’envoi', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ id: 'draft-1', labelIds: ['DRAFT'] }),
    });

    const result = await createDraft('acc-1', {
      to: ['client@example.test'], subject: 'Proposition', body: 'Bonjour', html: false,
    });

    expect(result.id).toBe('draft-1');
    expect(mockApiFetch).toHaveBeenCalledWith(
      'http://127.0.0.1:17293/api/email/messages/draft?account_id=acc-1',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          to: ['client@example.test'], subject: 'Proposition', body: 'Bonjour', html: false,
        }),
      }),
    );
  });

  /**
   * B-060 (reliquat frontend). Le backend sait remplacer un brouillon depuis
   * le lot RE25 : la route accepte `draft_id`. Tant que le client n'a aucune
   * porte pour le transmettre, chaque correction re-enregistree laisse un
   * exemplaire de plus chez le fournisseur, sous le meme bandeau vert.
   */
  it('createDraft remplace le brouillon designe quand un identifiant est fourni', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ id: 'draft-1', labelIds: ['DRAFT'] }),
    });

    await createDraft(
      'acc-1',
      { to: ['client@example.test'], subject: 'Proposition', body: 'Bonjour corrige', html: false },
      'draft-1',
    );

    expect(mockApiFetch).toHaveBeenCalledWith(
      'http://127.0.0.1:17293/api/email/messages/draft?account_id=acc-1&draft_id=draft-1',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('modifyEmailMessage traduit les noms TypeScript vers le schema FastAPI', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ id: 'msg-1', labelIds: ['STARRED'] }),
    });

    await modifyEmailMessage('acc-1', 'msg-1', {
      addLabelIds: ['STARRED'],
      removeLabelIds: ['UNREAD'],
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      'http://127.0.0.1:17293/api/email/messages/msg-1?account_id=acc-1',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({
          add_label_ids: ['STARRED'],
          remove_label_ids: ['UNREAD'],
        }),
      }),
    );
  });
});
