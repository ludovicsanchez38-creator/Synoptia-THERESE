import type {
  DashboardEvent,
  DashboardFollowUp,
  DashboardInvoice,
  DashboardProspect,
  DashboardTask,
  TodayDashboard,
} from '../../services/api/dashboard';
import type { Contact } from '../../services/api/memory';
import type { AppView } from '../../stores/navigationStore';

export type AttentionKind = 'event' | 'task' | 'follow_up' | 'invoice' | 'prospect';

export interface TodayAttentionItem {
  id: string;
  kind: AttentionKind;
  title: string;
  detail: string;
  badge: string;
  urgent: boolean;
  targetView: Extract<AppView, 'calendar' | 'tasks' | 'email' | 'invoices' | 'crm'>;
}

function isOverdue(dueDate: string | null, today: string): boolean {
  return Boolean(dueDate && dueDate.slice(0, 10) < today);
}

function formatCivilDate(value: string | null): string {
  if (!value || value.length < 10) return '';
  return `${value.slice(8, 10)}/${value.slice(5, 7)}`;
}

function formatEventTime(event: DashboardEvent): string {
  if (event.all_day) return 'Toute la journée';
  if (!event.start_datetime) return 'Horaire à confirmer';
  const date = new Date(event.start_datetime);
  if (Number.isNaN(date.getTime())) return 'Horaire à confirmer';
  return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}

function formatMoney(invoice: DashboardInvoice): string {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: invoice.currency || 'EUR',
    maximumFractionDigits: 2,
  }).format(invoice.total_ttc || 0);
}

function taskToAttention(task: DashboardTask, today: string): TodayAttentionItem {
  const overdue = isOverdue(task.due_date, today);
  const dueLabel = formatCivilDate(task.due_date);
  return {
    id: `task-${task.id}`,
    kind: 'task',
    title: task.title,
    detail: dueLabel ? `Échéance ${dueLabel}` : `Priorité ${task.priority || 'à préciser'}`,
    badge: overdue ? 'En retard' : 'À traiter',
    urgent: overdue,
    targetView: 'tasks',
  };
}

function invoiceToAttention(invoice: DashboardInvoice): TodayAttentionItem {
  const dueLabel = formatCivilDate(invoice.due_date);
  return {
    id: `invoice-${invoice.id}`,
    kind: 'invoice',
    title: `Facture ${invoice.invoice_number}`,
    detail: [formatMoney(invoice), dueLabel ? `échéance ${dueLabel}` : 'échéance non renseignée'].join(' · '),
    badge: 'À relancer',
    urgent: true,
    targetView: 'invoices',
  };
}

function eventToAttention(event: DashboardEvent): TodayAttentionItem {
  const linkedToCrm = event.crm_contact_ids.length > 0;
  const hasParticipants = event.attendees_count > 0;
  return {
    id: `event-${event.id}`,
    kind: 'event',
    title: event.summary,
    detail: [
      formatEventTime(event),
      event.location,
      linkedToCrm
        ? `${event.crm_contact_ids.length} contact${event.crm_contact_ids.length > 1 ? 's' : ''} CRM`
        : hasParticipants
          ? `${event.attendees_count} participant${event.attendees_count > 1 ? 's' : ''}`
          : null,
    ].filter(Boolean).join(' · '),
    badge: linkedToCrm ? 'Contact CRM' : hasParticipants ? 'Avec participants' : 'Agenda',
    urgent: false,
    targetView: 'calendar',
  };
}

function followUpToAttention(followUp: DashboardFollowUp, today: string): TodayAttentionItem {
  const overdue = isOverdue(followUp.due_date, today);
  const subject = followUp.email_subject || followUp.note || 'Relance email';
  return {
    id: `follow-up-${followUp.id}`,
    kind: 'follow_up',
    title: followUp.contact_name ? `Relancer ${followUp.contact_name}` : subject,
    detail: [subject, `échéance ${formatCivilDate(followUp.due_date)}`].filter(Boolean).join(' · '),
    badge: overdue ? 'Relance en retard' : 'Relance proche',
    urgent: overdue,
    targetView: 'email',
  };
}

function isLowStakeSoloEvent(event: DashboardEvent): boolean {
  if (event.attendees_count > 0 || event.crm_contact_ids.length > 0) return false;
  const normalized = event.summary.toLocaleLowerCase('fr-FR');
  return /\b(d[eé]jeuner|courses?|sport|gym|pause|personnel|perso)\b/.test(normalized);
}

function eventTimestamp(event: DashboardEvent): string {
  return event.start_datetime || event.start_date || '';
}

function prospectToAttention(prospect: DashboardProspect): TodayAttentionItem {
  return {
    id: `prospect-${prospect.id}`,
    kind: 'prospect',
    title: `Relancer ${prospect.name}`,
    detail: [prospect.company, prospect.stage].filter(Boolean).join(' · ') || 'Contexte CRM disponible',
    badge: 'CRM',
    urgent: false,
    targetView: 'crm',
  };
}

export function buildTodayAttentionItems(data: TodayDashboard): TodayAttentionItem[] {
  const overdueTasks = data.urgent_tasks.filter((task) => isOverdue(task.due_date, data.date));
  const otherTasks = data.urgent_tasks.filter((task) => !isOverdue(task.due_date, data.date));
  const overdueFollowUps = data.due_follow_ups.filter((followUp) => isOverdue(followUp.due_date, data.date));
  const otherFollowUps = data.due_follow_ups.filter((followUp) => !isOverdue(followUp.due_date, data.date));
  const curatedEvents = data.events
    .filter((event) => !isLowStakeSoloEvent(event))
    .sort((left, right) => eventTimestamp(left).localeCompare(eventTimestamp(right)));
  const engagedEvents = curatedEvents.filter(
    (event) => event.attendees_count > 0 || event.crm_contact_ids.length > 0,
  );
  const otherEvents = curatedEvents.filter(
    (event) => event.attendees_count === 0 && event.crm_contact_ids.length === 0,
  );

  return [
    ...overdueTasks.map((task) => taskToAttention(task, data.date)),
    ...overdueFollowUps.map((followUp) => followUpToAttention(followUp, data.date)),
    ...data.overdue_invoices.map(invoiceToAttention),
    ...engagedEvents.map(eventToAttention),
    ...otherFollowUps.map((followUp) => followUpToAttention(followUp, data.date)),
    ...otherTasks.map((task) => taskToAttention(task, data.date)),
    ...data.stale_prospects.map(prospectToAttention),
    ...otherEvents.map(eventToAttention),
  ];
}

export function todayBriefTitle(itemCount: number): string {
  if (itemCount === 0) return 'Aucune priorité détectée';
  if (itemCount === 1) return 'Un point mérite ton attention';
  return 'Ton attention aujourd’hui';
}

export function contactDisplayName(contact: Contact): string {
  const name = [contact.first_name, contact.last_name].filter(Boolean).join(' ').trim();
  return name || contact.company || contact.email || 'Contact sans nom';
}

export function contactInitials(contact: Contact): string {
  const parts = [contact.first_name, contact.last_name].filter(Boolean) as string[];
  if (parts.length > 0) return parts.map((part) => part[0]).join('').slice(0, 2).toUpperCase();
  return contactDisplayName(contact).slice(0, 2).toUpperCase();
}

export function selectRecentContacts(contacts: Contact[], limit = 4): Contact[] {
  return [...contacts]
    .sort((left, right) => {
      const leftDate = left.last_interaction || left.updated_at || left.created_at || '';
      const rightDate = right.last_interaction || right.updated_at || right.created_at || '';
      return rightDate.localeCompare(leftDate);
    })
    .slice(0, limit);
}
