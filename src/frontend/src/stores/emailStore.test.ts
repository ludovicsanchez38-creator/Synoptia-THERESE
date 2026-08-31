/**
 * Finding 4 (revue 30/08) : changer de compte e-mail laissait la liste,
 * les labels et le brouillon de l'autre. Label Gmail collé sur IMAP,
 * UID qui se recoupent, envoi du brouillon A depuis B.
 */
import { beforeEach, describe, expect, it } from 'vitest';
import { useEmailStore } from './emailStore';
import type { EmailMessage, EmailLabel } from '../services/api';

const messageA: EmailMessage = {
  id: 'uid-1',
  thread_id: 't1',
  subject: 'De A',
  from_email: 'x@y.fr',
  from_name: 'X',
  to_emails: ['a@gmail.com'],
  date: '2026-08-30T10:00:00Z',
  labels: ['INBOX'],
  is_read: true,
  is_starred: false,
  is_draft: false,
  has_attachments: false,
  snippet: 'bonjour',
  body_plain: 'bonjour',
  body_html: null,
};

const labelA: EmailLabel = {
  id: 'Label_xxx',
  name: 'Clients',
  type: 'user',
  messagesTotal: 3,
  messagesUnread: 1,
};

describe('emailStore — bascule de compte', () => {
  beforeEach(() => {
    useEmailStore.setState({
      accounts: [
        { id: 'acc-a', email: 'a@gmail.com', provider: 'gmail', scopes: [], created_at: '', last_sync: null },
        { id: 'acc-b', email: 'b@imap.fr', provider: 'imap', scopes: [], created_at: '', last_sync: null },
      ],
      currentAccountId: 'acc-a',
      messages: [messageA],
      currentMessageId: 'uid-1',
      labels: [labelA],
      currentLabelId: 'Label_xxx',
      selectedLabels: ['Label_xxx'],
      pageToken: 'page-a',
      hasMore: true,
      draftSubject: 'Brouillon A',
      draftBody: 'Corps A',
      draftRecipients: ['z@z.fr'],
      isComposing: true,
    });
  });

  it('vider ce qui appartenait à A quand on passe à B', () => {
    useEmailStore.getState().setCurrentAccount('acc-b');
    const etat = useEmailStore.getState();
    expect(etat.currentAccountId).toBe('acc-b');
    expect(etat.messages).toEqual([]);
    expect(etat.currentMessageId).toBeNull();
    expect(etat.labels).toEqual([]);
    expect(etat.currentLabelId).toBeNull();
    expect(etat.selectedLabels).toEqual([]);
    expect(etat.pageToken).toBeNull();
    expect(etat.hasMore).toBe(false);
    expect(etat.draftSubject).toBe('');
    expect(etat.draftBody).toBe('');
    expect(etat.draftRecipients).toEqual([]);
    expect(etat.isComposing).toBe(false);
  });

  it('rester sur le même compte ne vide pas la liste', () => {
    useEmailStore.getState().setCurrentAccount('acc-a');
    expect(useEmailStore.getState().messages).toHaveLength(1);
    expect(useEmailStore.getState().draftSubject).toBe('Brouillon A');
  });
});
