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
  return [...messages]
    .filter((message) => !message.is_draft)
    .sort((left, right) => {
      if (left.is_read !== right.is_read) return left.is_read ? 1 : -1;
      const priority = { high: 0, medium: 1, low: 2 } as const;
      const leftPriority = left.priority ? priority[left.priority] : 3;
      const rightPriority = right.priority ? priority[right.priority] : 3;
      if (leftPriority !== rightPriority) return leftPriority - rightPriority;
      return (right.date || '').localeCompare(left.date || '');
    })
    .slice(0, limit);
}
