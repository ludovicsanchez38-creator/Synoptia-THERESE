import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
vi.mock('../../services/api/email', () => ({
  createDraft: vi.fn(), generateEmailResponse: vi.fn(), getEmailMessage: vi.fn(),
  getEmailAuthStatus: vi.fn(), listEmailMessages: vi.fn(),
}));
import { getEmailAuthStatus, listEmailMessages } from '../../services/api/email';
import { useEmailStore } from '../../stores/emailStore';
import { usePrototypeEmailData } from './usePrototypeEmailData';

const comptes = { connected: true, accounts: [{
  id: 'compte-fictif', email: 'test@example.test', provider: 'imap' as const,
  scopes: [], created_at: '2026-01-01', last_sync: null,
}] };

describe('B-1958 : les erreurs indiquent l’étape de lecture en échec', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    useEmailStore.setState({ accounts: [], currentAccountId: null, messages: [] });
    vi.mocked(getEmailAuthStatus).mockResolvedValue(comptes);
    vi.mocked(listEmailMessages).mockResolvedValue({ messages: [] });
  });

  it('explique l’échec de vérification des comptes avant de lister les messages, puis permet de réessayer', async () => {
    vi.mocked(getEmailAuthStatus).mockRejectedValueOnce(new Error('Erreur simulée des comptes'));
    const { result } = renderHook(() => usePrototypeEmailData());
    await waitFor(() => expect(result.current.inboxResource.status).toBe('error'));
    expect(result.current.inboxResource.error).toBe('Impossible de vérifier la connexion de tes comptes e-mail pour le moment. Réessaie.');
    expect(listEmailMessages).not.toHaveBeenCalled();
    await act(async () => result.current.refreshInbox());
    expect(result.current.inboxResource.status).toBe('ready');
    expect(result.current.inboxResource.error).toBeNull();
  });

  it('conserve une erreur de chargement des messages si les comptes ont bien été vérifiés', async () => {
    vi.mocked(listEmailMessages).mockRejectedValueOnce(new Error('Erreur simulée de liste'));
    const { result } = renderHook(() => usePrototypeEmailData());
    await waitFor(() => expect(result.current.inboxResource.status).toBe('error'));
    expect(result.current.inboxResource.error).toBe('Impossible de charger les messages pour le moment.');
    expect(listEmailMessages).toHaveBeenCalledTimes(1);
  });
});
