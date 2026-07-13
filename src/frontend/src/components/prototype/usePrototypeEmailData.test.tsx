import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/email', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../services/api/email')>();
  return {
    ...actual,
    createDraft: vi.fn(),
    generateEmailResponse: vi.fn(),
    getEmailAuthStatus: vi.fn(),
    getEmailMessage: vi.fn(),
    listEmailMessages: vi.fn(),
  };
});

import {
  createDraft,
  generateEmailResponse,
  getEmailAuthStatus,
  getEmailMessage,
  listEmailMessages,
  type EmailMessage,
} from '../../services/api/email';
import { useEmailStore } from '../../stores/emailStore';
import { usePrototypeEmailData } from './usePrototypeEmailData';

const detailedMessage: EmailMessage = {
  id: 'message-1',
  thread_id: 'thread-1',
  subject: 'Sujet réel',
  from_email: 'camille@example.test',
  from_name: 'Camille',
  to_emails: ['ludo@example.test'],
  cc_emails: [],
  bcc_emails: [],
  date: '2026-07-13T08:30:00+02:00',
  labels: ['INBOX', 'UNREAD'],
  is_read: false,
  is_starred: false,
  is_draft: false,
  has_attachments: false,
  snippet: 'Aperçu réel',
  body_plain: 'Corps réel',
  body_html: null,
};

describe('usePrototypeEmailData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useEmailStore.setState({ accounts: [], currentAccountId: null, messages: [] });
  });

  it('orchestre la lecture, le détail, la génération et la création de brouillon sur le compte actif', async () => {
    vi.mocked(getEmailAuthStatus).mockResolvedValue({
      connected: true,
      accounts: [{
        id: 'account-1', email: 'ludo@example.test', provider: 'imap', scopes: [],
        created_at: '2026-07-13', last_sync: null,
      }],
    });
    vi.mocked(listEmailMessages).mockResolvedValue({
      messages: [
        {
          id: 'message-1', threadId: 'thread-1', subject: 'Sujet réel',
          from: 'Camille <camille@example.test>', date: '2026-07-13T08:30:00+02:00',
          labelIds: ['INBOX', 'UNREAD'], snippet: 'Aperçu réel',
        },
        { id: 'message-invalide', error: 'Fournisseur indisponible' },
      ],
    });
    vi.mocked(getEmailMessage).mockResolvedValue(detailedMessage);
    vi.mocked(generateEmailResponse).mockResolvedValue({
      message_id: 'message-1', draft: 'Réponse proposée', tone: 'formal', length: 'medium',
    });
    vi.mocked(createDraft).mockResolvedValue({ id: 'draft-1', labelIds: ['DRAFT'] });

    const { result } = renderHook(() => usePrototypeEmailData(true));
    await waitFor(() => expect(result.current.inboxResource.status).toBe('ready'));

    expect(result.current.inboxResource.data?.messages).toHaveLength(1);
    expect(result.current.inboxResource.data?.failedMessages).toBe(1);
    expect(listEmailMessages).toHaveBeenCalledWith('account-1', {
      maxResults: 30,
      labelIds: ['INBOX'],
    });

    await act(async () => result.current.openMessage('message-1'));
    expect(result.current.messageResource).toEqual({ status: 'ready', data: detailedMessage, error: null });

    let generated = '';
    await act(async () => {
      generated = await result.current.generateDraft('message-1', 'formal', 'medium');
    });
    expect(generated).toBe('Réponse proposée');

    await act(async () => {
      await result.current.saveDraft({
        to: ['camille@example.test'], subject: 'Re: Sujet réel', body: generated, html: false,
      });
    });
    expect(createDraft).toHaveBeenCalledWith('account-1', {
      to: ['camille@example.test'], subject: 'Re: Sujet réel', body: 'Réponse proposée', html: false,
    });
  });

  it('ne consulte pas la boîte tant que le parcours Email n’est pas actif', () => {
    renderHook(() => usePrototypeEmailData(false));
    expect(getEmailAuthStatus).not.toHaveBeenCalled();
  });
});
