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

  // BUG-152 : le tri « non-lus d'abord » faisait remonter de VIEUX messages
  // non lus (8-14/07) devant les récents - la carte d'accueil paraissait
  // figée alors que la vue complète allait jusqu'à la veille. La carte
  // reflète désormais les DERNIERS messages (date décroissante), le non-lu
  // reste un indicateur visuel.
  it('BUG-152 : trie par date décroissante, même face à de vieux non-lus', () => {
    const selected = selectInboxMessages([
      cachedMessage({ id: 'vieux-non-lu', is_read: false, date: '2026-07-08T09:00:00Z' }),
      cachedMessage({ id: 'recent-lu', is_read: true, date: '2026-07-20T18:00:00Z' }),
      cachedMessage({ id: 'moyen-non-lu', is_read: false, date: '2026-07-14T10:00:00Z' }),
      cachedMessage({ id: 'draft', is_read: false, is_draft: true, date: '2026-07-21T08:00:00Z' }),
    ]);
    expect(selected.map((message) => message.id)).toEqual(['recent-lu', 'moyen-non-lu', 'vieux-non-lu']);
  });
});
