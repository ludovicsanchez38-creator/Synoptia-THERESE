import { describe, expect, it } from 'vitest';
import type { EmailMessage } from '../../services/api/email';
import { mapEmailList, parseEmailSender, selectInboxMessages } from './emailReadModels';

const cachedMessage = (over: Partial<EmailMessage> = {}): EmailMessage => ({
  id: 'm1',
  thread_id: 't1',
  subject: 'Sujet',
  from_email: 'client@example.test',
  from_name: 'Client',
  to_emails: [],
  date: '2026-07-13T08:00:00Z',
  labels: [],
  is_read: true,
  is_starred: false,
  is_draft: false,
  has_attachments: false,
  snippet: 'Aperçu',
  body_plain: 'Corps déjà chargé',
  body_html: null,
  ...over,
});

describe('emailReadModels', () => {
  it('parse correctement un expéditeur Gmail ou IMAP', () => {
    expect(parseEmailSender('"Camille Martin" <camille@example.test>')).toEqual({
      email: 'camille@example.test',
      name: 'Camille Martin',
    });
    expect(parseEmailSender('brut@example.test')).toEqual({ email: 'brut@example.test', name: null });
  });

  it('mappe la réponse enrichie et conserve le corps déjà chargé', () => {
    const messages = mapEmailList([
      {
        id: 'm1', threadId: 't1', subject: 'Nouveau sujet',
        from: 'Camille <camille@example.test>', labelIds: ['UNREAD'], snippet: 'Nouveau',
      },
      { id: 'broken', error: 'provider error' },
    ], [cachedMessage()]);

    expect(messages).toHaveLength(1);
    expect(messages[0]).toMatchObject({
      subject: 'Nouveau sujet', from_email: 'camille@example.test', is_read: false,
      body_plain: 'Corps déjà chargé',
    });
  });

  it('place les non lus puis les priorités hautes en premier et exclut les brouillons', () => {
    const selected = selectInboxMessages([
      cachedMessage({ id: 'read', is_read: true, priority: 'high' }),
      cachedMessage({ id: 'unread-low', is_read: false, priority: 'low' }),
      cachedMessage({ id: 'unread-high', is_read: false, priority: 'high' }),
      cachedMessage({ id: 'draft', is_read: false, is_draft: true }),
    ]);
    expect(selected.map((message) => message.id)).toEqual(['unread-high', 'unread-low', 'read']);
  });
});
