import type { EmailMessage, EmailMessageListItem } from '../../services/api/email';

export function parseEmailSender(value: string | undefined): { email: string; name: string | null } {
  const source = (value || '').trim();
  const match = source.match(/^(.*?)\s*<([^<>]+)>$/);
  if (!match) return { email: source, name: null };

  const name = match[1].trim().replace(/^"|"$/g, '') || null;
  return { email: match[2].trim(), name };
}

export function mapEmailListItem(
  item: EmailMessageListItem,
  cached?: EmailMessage,
): EmailMessage | null {
  if (item.error) return null;
  const sender = parseEmailSender(item.from);
  const labelIds = item.labelIds || [];

  return {
    id: item.id,
    thread_id: item.threadId || item.id,
    subject: item.subject || '(Sans objet)',
    from_email: sender.email,
    from_name: sender.name,
    to_emails: cached?.to_emails || [],
    cc_emails: cached?.cc_emails || [],
    bcc_emails: cached?.bcc_emails || [],
    date: item.date || cached?.date || '',
    labels: labelIds,
    is_read: item.is_read ?? !labelIds.includes('UNREAD'),
    is_starred: item.is_starred ?? labelIds.includes('STARRED'),
    is_draft: labelIds.includes('DRAFT'),
    has_attachments: cached?.has_attachments || false,
    snippet: item.snippet || cached?.snippet || null,
    body_plain: cached?.body_plain || null,
    body_html: cached?.body_html || null,
    priority: cached?.priority || null,
    priority_score: cached?.priority_score || null,
    priority_reason: cached?.priority_reason || null,
    category: cached?.category || null,
  };
}

export function mapEmailList(
  items: EmailMessageListItem[],
  cachedMessages: EmailMessage[] = [],
): EmailMessage[] {
  const cachedById = new Map(cachedMessages.map((message) => [message.id, message]));
  return items
    .map((item) => mapEmailListItem(item, cachedById.get(item.id)))
    .filter((message): message is EmailMessage => Boolean(message));
}

export function emailSenderLabel(message: EmailMessage): string {
  return message.from_name || message.from_email || 'Expéditeur inconnu';
}

export function formatEmailDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Date inconnue';
  return date.toLocaleString('fr-FR', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function selectInboxMessages(messages: EmailMessage[], limit = 6): EmailMessage[] {
  // BUG-152 : trier « non-lus d'abord » faisait remonter de VIEUX messages
  // non lus devant les récents - la carte d'accueil paraissait figée des
  // jours en arrière alors que la vue complète était à jour. La carte
  // montre les DERNIERS messages ; le non-lu reste un indicateur visuel.
  // F5 revue : tri sur le TIMESTAMP parsé - Gmail transmet des dates
  // RFC 2822 (« Tue, 21 Jul... ») que localeCompare triait par nom de jour.
  const timestamp = (message: EmailMessage): number => {
    const parsed = Date.parse(message.date || '');
    return Number.isNaN(parsed) ? Number.NEGATIVE_INFINITY : parsed;
  };
  return [...messages]
    .filter((message) => !message.is_draft)
    .sort((left, right) => timestamp(right) - timestamp(left))
    .slice(0, limit);
}
