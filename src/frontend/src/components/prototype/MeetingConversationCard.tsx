import { useMemo, useState, type ReactNode } from 'react';
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  ChevronRight,
  Clock3,
  FileText,
  Loader2,
  MapPin,
  Plus,
  RefreshCw,
  ShieldCheck,
  Users,
} from 'lucide-react';
import type { CalendarEvent, CreateEventRequest } from '../../services/api';
import { contactDisplayName, contactInitials } from './prototypeReadModels';
import type { ReadResource } from './usePrototypeReadData';
import {
  meetingEventKey,
  type MeetingEventContext,
  type MeetingWorkspaceData,
} from './usePrototypeMeetingData';

export type MeetingTarget = string | 'new-event' | null;

function StateShell({ children }: { children: ReactNode }) {
  return <div className="flex min-h-48 items-center justify-center px-5 py-8">{children}</div>;
}

function eventDateValue(event: CalendarEvent): Date | null {
  const value = event.start_datetime || event.start_date;
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatEventDate(event: CalendarEvent, includeDate = true): string {
  const date = eventDateValue(event);
  if (!date) return 'Date à confirmer';
  if (event.all_day) {
    return date.toLocaleDateString('fr-FR', includeDate
      ? { weekday: 'short', day: '2-digit', month: 'short' }
      : { day: '2-digit', month: 'short' });
  }
  return date.toLocaleString('fr-FR', includeDate
    ? { weekday: 'short', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }
    : { hour: '2-digit', minute: '2-digit' });
}

function localDateTimeValue(date: Date): string {
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

function nextStartValue(): string {
  const start = new Date();
  start.setMinutes(0, 0, 0);
  start.setHours(start.getHours() + 1);
  return localDateTimeValue(start);
}

function nextEndValue(): string {
  const end = new Date();
  end.setMinutes(0, 0, 0);
  end.setHours(end.getHours() + 2);
  return localDateTimeValue(end);
}

function sortedEvents(events: CalendarEvent[]): CalendarEvent[] {
  return [...events].sort((left, right) => {
    const leftDate = eventDateValue(left)?.getTime() ?? Number.POSITIVE_INFINITY;
    const rightDate = eventDateValue(right)?.getTime() ?? Number.POSITIVE_INFINITY;
    return leftDate - rightDate;
  });
}

export function MeetingAgendaCard({
  resource,
  onRetry,
  onOpenEvent,
  onNewEvent,
  onOpenClassic,
}: {
  resource: ReadResource<MeetingWorkspaceData>;
  onRetry: () => void;
  onOpenEvent: (eventId: string) => void;
  onNewEvent: () => void;
  onOpenClassic: () => void;
}) {
  const events = resource.status === 'ready' ? sortedEvents(resource.data.events).slice(0, 6) : [];

  return (
    <section aria-labelledby="meeting-agenda-title" className="overflow-hidden rounded-[16px] border border-border bg-surface shadow-[0_12px_28px_-22px_rgba(16,28,54,0.45)]" data-testid="meeting-agenda-card">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-[9px] border border-text bg-[var(--k3bg)] text-[var(--k3)]">
            <Calendar className="h-4 w-4" />
          </span>
          <div>
            <h2 id="meeting-agenda-title" className="text-sm font-semibold text-text">Prochains rendez-vous</h2>
            <p className="text-[11px] text-text-muted">
              {resource.status === 'ready'
                ? `${resource.data.events.length} événement${resource.data.events.length > 1 ? 's' : ''} sur 90 jours`
                : 'Lecture des calendriers disponibles'}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={onNewEvent} className="inline-flex items-center gap-1.5 rounded-[8px] bg-text px-2.5 py-1.5 text-[11px] font-semibold text-white">
            <Plus className="h-3.5 w-3.5" />
            Nouvel événement
          </button>
          <button type="button" onClick={onOpenClassic} className="rounded-[8px] border border-border px-2.5 py-1.5 text-[11px] font-semibold text-text hover:bg-surface-2">
            Agenda complet
          </button>
        </div>
      </div>

      {resource.status === 'loading' ? (
        <StateShell><div className="flex items-center gap-2 text-sm text-text-muted" role="status"><Loader2 className="h-4 w-4 animate-spin text-[var(--k3)]" />Je consulte l’agenda…</div></StateShell>
      ) : resource.status === 'error' ? (
        <StateShell>
          <div className="max-w-sm text-center" data-testid="meeting-agenda-error">
            <AlertCircle className="mx-auto h-5 w-5 text-warning" />
            <p className="mt-2 text-sm font-semibold text-text">Agenda indisponible</p>
            <p className="mt-1 text-xs text-text-muted">{resource.error}</p>
            <div className="mt-4 flex justify-center gap-2">
              <button type="button" onClick={onRetry} className="inline-flex items-center gap-1.5 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white"><RefreshCw className="h-3.5 w-3.5" />Réessayer</button>
              <button type="button" onClick={onOpenClassic} className="rounded-[9px] border border-border px-3 py-2 text-xs font-semibold text-text">Ouvrir Agenda</button>
            </div>
          </div>
        </StateShell>
      ) : events.length === 0 ? (
        <StateShell>
          <div className="text-center" data-testid="meeting-agenda-empty">
            <Calendar className="mx-auto h-6 w-6 text-text-muted" />
            <p className="mt-2 text-sm font-semibold text-text">Aucun rendez-vous à venir</p>
            <p className="mt-1 text-xs text-text-muted">L’agenda est disponible. Tu peux y préparer un nouvel événement.</p>
            <button type="button" onClick={onNewEvent} className="mt-4 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">Préparer un événement</button>
          </div>
        </StateShell>
      ) : (
        <div className="divide-y divide-border">
          {events.map((event) => (
            <button key={meetingEventKey(event)} type="button" onClick={() => onOpenEvent(meetingEventKey(event))} className="flex w-full items-center gap-3 px-4 py-3.5 text-left hover:bg-surface-2">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-[10px] bg-[var(--k3bg)] text-[var(--k3)]"><Clock3 className="h-4 w-4" /></span>
              <span className="min-w-0 flex-1">
                <strong className="block truncate text-sm text-text">{event.summary || 'Événement sans titre'}</strong>
                <span className="mt-0.5 block truncate text-xs text-text-muted">{formatEventDate(event)}{event.location ? ` · ${event.location}` : ''}</span>
              </span>
              {event.attendees && event.attendees.length > 0 && <span className="shrink-0 text-[10px] font-semibold text-text-muted">{event.attendees.length} participant{event.attendees.length > 1 ? 's' : ''}</span>}
              <ChevronRight className="h-4 w-4 shrink-0 text-text-muted" />
            </button>
          ))}
        </div>
      )}

      {resource.status === 'ready' && resource.data.unavailableSources.length > 0 && (
        <div className="border-t border-border bg-[var(--color-warning-tint)] px-4 py-2 text-[10px] text-warning">
          Source{resource.data.unavailableSources.length > 1 ? 's' : ''} indisponible{resource.data.unavailableSources.length > 1 ? 's' : ''} : {resource.data.unavailableSources.join(', ')}.
        </div>
      )}
    </section>
  );
}

function NewEventForm({
  data,
  onCreate,
}: {
  data: MeetingWorkspaceData;
  onCreate: (request: CreateEventRequest) => Promise<CalendarEvent>;
}) {
  const defaultCalendar = data.calendars.find((calendar) => calendar.primary) || data.calendars[0];
  const [calendarId, setCalendarId] = useState(defaultCalendar?.id || '');
  const [summary, setSummary] = useState('');
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  const [attendees, setAttendees] = useState('');
  const [start, setStart] = useState(nextStartValue);
  const [end, setEnd] = useState(nextEndValue);
  const [confirming, setConfirming] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const parsedAttendees = useMemo(() => attendees.split(/[;,\n]/).map((value) => value.trim()).filter(Boolean), [attendees]);
  const selectedCalendar = data.calendars.find((calendar) => calendar.id === calendarId);
  const selectedAccount = data.accounts.find((account) => account.id === selectedCalendar?.account_id);

  function prepare() {
    setError(null);
    if (!calendarId || !summary.trim() || !start || !end) {
      setError('Le calendrier, le titre, le début et la fin sont obligatoires.');
      return;
    }
    if (new Date(end).getTime() <= new Date(start).getTime()) {
      setError('La fin doit être postérieure au début.');
      return;
    }
    setConfirming(true);
  }

  async function confirm() {
    setPending(true);
    setError(null);
    try {
      await onCreate({
        calendar_id: calendarId,
        summary: summary.trim(),
        description: description.trim() || undefined,
        location: location.trim() || undefined,
        start_datetime: start,
        end_datetime: end,
        attendees: parsedAttendees,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/Paris',
      });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'La création a échoué.');
      setConfirming(false);
    } finally {
      setPending(false);
    }
  }

  if (data.calendars.length === 0) {
    return <div className="rounded-[12px] border border-warning/40 bg-[var(--color-warning-tint)] p-4 text-sm text-warning">Aucun calendrier n’est disponible. Ouvre Agenda pour terminer la configuration.</div>;
  }

  return (
    <div className="space-y-4" data-testid="meeting-new-event-form">
      <section className="rounded-[13px] border border-border bg-surface p-4">
        <h3 className="text-sm font-bold text-text">Préparer un événement</h3>
        <p className="mt-1 text-xs leading-5 text-text-muted">Aucune donnée n’est écrite avant la confirmation finale.</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <label className="text-xs font-semibold text-text sm:col-span-2">Titre<input value={summary} onChange={(event) => { setSummary(event.target.value); setConfirming(false); }} className="mt-1.5 w-full rounded-[9px] border border-border px-3 py-2 text-sm font-normal outline-none focus:border-[#22D3EE]" /></label>
          <label className="text-xs font-semibold text-text">Début<input type="datetime-local" value={start} onChange={(event) => { setStart(event.target.value); setConfirming(false); }} className="mt-1.5 w-full rounded-[9px] border border-border px-3 py-2 text-sm font-normal outline-none focus:border-[#22D3EE]" /></label>
          <label className="text-xs font-semibold text-text">Fin<input type="datetime-local" value={end} onChange={(event) => { setEnd(event.target.value); setConfirming(false); }} className="mt-1.5 w-full rounded-[9px] border border-border px-3 py-2 text-sm font-normal outline-none focus:border-[#22D3EE]" /></label>
          <label className="text-xs font-semibold text-text">Calendrier<select value={calendarId} onChange={(event) => { setCalendarId(event.target.value); setConfirming(false); }} className="mt-1.5 w-full rounded-[9px] border border-border bg-surface px-3 py-2 text-sm font-normal outline-none focus:border-[#22D3EE]">{data.calendars.map((calendar) => <option key={calendar.id} value={calendar.id}>{calendar.summary}</option>)}</select></label>
          <label className="text-xs font-semibold text-text">Lieu ou lien<input value={location} onChange={(event) => { setLocation(event.target.value); setConfirming(false); }} className="mt-1.5 w-full rounded-[9px] border border-border px-3 py-2 text-sm font-normal outline-none focus:border-[#22D3EE]" /></label>
          <label className="text-xs font-semibold text-text sm:col-span-2">Participants, séparés par une virgule<input value={attendees} onChange={(event) => { setAttendees(event.target.value); setConfirming(false); }} placeholder="contact@exemple.fr" className="mt-1.5 w-full rounded-[9px] border border-border px-3 py-2 text-sm font-normal outline-none focus:border-[#22D3EE]" /></label>
          <label className="text-xs font-semibold text-text sm:col-span-2">Description<textarea value={description} onChange={(event) => { setDescription(event.target.value); setConfirming(false); }} rows={4} className="mt-1.5 w-full resize-y rounded-[9px] border border-border px-3 py-2 text-sm font-normal leading-5 outline-none focus:border-[#22D3EE]" /></label>
        </div>
      </section>
      {error && <div role="alert" className="rounded-[10px] border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-xs text-warning">{error}</div>}
      {!confirming ? (
        <button type="button" onClick={prepare} className="w-full rounded-[10px] bg-text px-4 py-3 text-sm font-semibold text-white">Vérifier avant création</button>
      ) : (
        <div className="rounded-[12px] border border-accent-cyan/30 bg-accent-tint p-4">
          <div className="flex gap-2 text-xs leading-5 text-accent"><ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" /><span>Créer « {summary.trim()} » le {new Date(start).toLocaleString('fr-FR')} dans « {selectedCalendar?.summary || 'calendrier sélectionné'} » ({selectedCalendar?.provider === 'google' ? 'Google Calendar' : selectedCalendar?.provider === 'caldav' ? 'CalDAV' : 'local'}){selectedAccount ? `, compte ${selectedAccount.email}` : ''}{parsedAttendees.length ? `, avec ${parsedAttendees.length} participant${parsedAttendees.length > 1 ? 's' : ''}` : ''}. Fuseau : {Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/Paris'}.</span></div>
          <div className="mt-3 flex gap-2">
            <button type="button" disabled={pending} onClick={() => setConfirming(false)} className="flex-1 rounded-[9px] border border-border bg-surface px-3 py-2 text-xs font-semibold text-text">Annuler</button>
            <button type="button" disabled={pending} onClick={() => setConfirming(false)} className="flex-1 rounded-[9px] border border-border bg-surface px-3 py-2 text-xs font-semibold text-text">Modifier</button>
            <button type="button" disabled={pending} onClick={() => void confirm()} className="flex flex-1 items-center justify-center gap-2 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white disabled:opacity-60">{pending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}Confirmer la création</button>
          </div>
        </div>
      )}
    </div>
  );
}

function EventPreparation({
  context,
  onCreateNote,
}: {
  context: MeetingEventContext;
  onCreateNote: (eventId: string, contactId: string, description: string) => Promise<unknown>;
}) {
  const { event, relatedContacts, activities } = context;
  const [contactId, setContactId] = useState(relatedContacts[0]?.id || '');
  const [note, setNote] = useState('');
  const [confirming, setConfirming] = useState(false);
  const [pending, setPending] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const checks = [
    !event.description && 'Objectif ou ordre du jour non renseigné',
    !event.location && 'Lieu ou lien de connexion non renseigné',
    (!event.attendees || event.attendees.length === 0) && 'Aucun participant renseigné',
    event.attendees && event.attendees.length > 0 && relatedContacts.length === 0 && 'Aucun participant ne correspond exactement à un contact local',
  ].filter((value): value is string => Boolean(value));

  async function confirmNote() {
    setPending(true);
    setFeedback(null);
    try {
      await onCreateNote(meetingEventKey(event), contactId, note);
      setNote('');
      setConfirming(false);
      setFeedback('Note enregistrée dans l’historique CRM du contact.');
    } catch (cause) {
      setFeedback(cause instanceof Error ? cause.message : 'La note n’a pas pu être enregistrée.');
      setConfirming(false);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="space-y-5" data-testid="meeting-event-preparation">
      <section className="rounded-[13px] border border-border bg-surface p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold text-text">{event.summary || 'Événement sans titre'}</h3>
            <p className="mt-1 flex items-center gap-1.5 text-xs text-text-muted"><Clock3 className="h-3.5 w-3.5" />{formatEventDate(event)}</p>
          </div>
          <span className="rounded-full bg-[var(--k3bg)] px-2.5 py-1 text-[10px] font-semibold text-[var(--k3)]">{event.all_day ? 'Journée entière' : 'Rendez-vous'}</span>
        </div>
        {event.location && <p className="mt-3 flex items-center gap-2 rounded-[9px] bg-surface-2 px-3 py-2 text-xs text-text"><MapPin className="h-3.5 w-3.5 text-[var(--k3)]" />{event.location}</p>}
        {event.description && <div className="mt-3 whitespace-pre-wrap rounded-[9px] bg-surface-2 px-3 py-3 text-xs leading-5 text-text">{event.description}</div>}
      </section>

      <section>
        <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-text-muted">Participants et contacts reliés</div>
        {event.attendees && event.attendees.length > 0 ? (
          <div className="space-y-2">
            {event.attendees.map((attendee) => {
              const contact = relatedContacts.find((item) => item.email?.trim().toLowerCase() === attendee.replace(/^.*<|>.*$/g, '').trim().toLowerCase());
              return (
                <div key={attendee} className="rounded-[11px] border border-border bg-surface p-3">
                  <div className="flex items-center gap-3">
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-[9px] bg-accent-tint text-[11px] font-bold text-accent">{contact ? contactInitials(contact) : <Users className="h-4 w-4" />}</span>
                    <div className="min-w-0 flex-1"><strong className="block truncate text-sm text-text">{contact ? contactDisplayName(contact) : attendee}</strong><span className="block truncate text-xs text-text-muted">{contact ? [contact.company, contact.stage, contact.email].filter(Boolean).join(' · ') : 'Pas de correspondance CRM exacte'}</span></div>
                  </div>
                  {contact?.notes && <p className="mt-3 whitespace-pre-wrap border-t border-border pt-3 text-xs leading-5 text-text-muted">{contact.notes}</p>}
                </div>
              );
            })}
          </div>
        ) : <p className="rounded-[10px] border border-border bg-surface p-3 text-xs text-text-muted">Aucun participant n’est renseigné dans l’événement.</p>}
      </section>

      <section>
        <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-text-muted">Points à vérifier</div>
        <div className="space-y-2">
          {(checks.length > 0 ? checks : ['L’événement contient une date, un contexte et au moins un participant.']).map((item) => (
            <div key={item} className="flex gap-2.5 rounded-[10px] border border-border bg-surface px-3 py-2.5 text-xs leading-5 text-text"><CheckCircle2 className={`mt-0.5 h-4 w-4 shrink-0 ${checks.length ? 'text-warning' : 'text-accent'}`} />{item}</div>
          ))}
        </div>
      </section>

      {relatedContacts.length > 0 && (
        <section className="rounded-[13px] border border-border bg-surface p-4">
          <div className="flex items-center gap-2"><FileText className="h-4 w-4 text-[var(--k3)]" /><h3 className="text-sm font-bold text-text">Ajouter une note de rendez-vous</h3></div>
          <p className="mt-1 text-xs text-text-muted">La note sera ajoutée au CRM du contact choisi après confirmation.</p>
          <select value={contactId} onChange={(event) => { setContactId(event.target.value); setConfirming(false); }} className="mt-3 w-full rounded-[9px] border border-border bg-surface px-3 py-2 text-xs outline-none focus:border-[#22D3EE]">{relatedContacts.map((contact) => <option key={contact.id} value={contact.id}>{contactDisplayName(contact)}</option>)}</select>
          <textarea value={note} onChange={(event) => { setNote(event.target.value); setConfirming(false); }} rows={4} placeholder="Tes notes factuelles après le rendez-vous…" className="mt-2 w-full resize-y rounded-[9px] border border-border px-3 py-2 text-xs leading-5 outline-none focus:border-[#22D3EE]" />
          {!confirming ? (
            <button type="button" disabled={!note.trim()} onClick={() => setConfirming(true)} className="mt-2 w-full rounded-[9px] bg-text px-3 py-2.5 text-xs font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40">Vérifier la note</button>
          ) : (
            <div className="mt-2 rounded-[10px] border border-accent-cyan/30 bg-accent-tint p-3">
              <p className="text-xs leading-5 text-accent">Confirmer l’ajout de cette note au contact sélectionné. L’événement Agenda ne sera pas modifié.</p>
              <div className="mt-2 flex gap-2"><button type="button" onClick={() => setConfirming(false)} className="flex-1 rounded-[8px] border border-border bg-surface px-3 py-2 text-xs font-semibold text-text">Modifier</button><button type="button" disabled={pending} onClick={() => void confirmNote()} className="flex flex-1 items-center justify-center gap-2 rounded-[8px] bg-text px-3 py-2 text-xs font-semibold text-white">{pending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}Confirmer l’ajout</button></div>
            </div>
          )}
          {feedback && <p className="mt-2 text-xs text-accent" role="status">{feedback}</p>}
        </section>
      )}

      <section>
        <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-text-muted">Historique CRM disponible</div>
        {activities.length > 0 ? <div className="space-y-2">{activities.slice(0, 5).map((activity) => <div key={activity.id} className="rounded-[10px] border border-border bg-surface px-3 py-2.5"><strong className="block text-xs text-text">{activity.title}</strong><span className="mt-0.5 block text-[10px] text-text-muted">{new Date(activity.created_at).toLocaleDateString('fr-FR')} · {activity.type}</span>{activity.description && <p className="mt-1 whitespace-pre-wrap text-xs leading-5 text-text-muted">{activity.description}</p>}</div>)}</div> : <p className="rounded-[10px] border border-border bg-surface p-3 text-xs text-text-muted">Aucune activité CRM reliée n’est disponible.</p>}
      </section>

      {context.unavailableSources.length > 0 && <div className="rounded-[10px] border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-xs text-warning">Source indisponible : {context.unavailableSources.join(', ')}.</div>}
      <div className="flex items-start gap-2 rounded-[10px] border border-accent-cyan/30 bg-accent-tint p-3 text-xs leading-5 text-accent"><ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />Les contacts sont reliés uniquement par adresse email exacte. Aucun contexte absent n’est inventé.</div>
    </div>
  );
}

export function MeetingWorkspaceCanvas({
  resource,
  eventResource,
  target,
  onRetry,
  onRetryEvent,
  onCreateEvent,
  onCreateNote,
  onOpenClassic,
}: {
  resource: ReadResource<MeetingWorkspaceData>;
  eventResource: ReadResource<MeetingEventContext> | null;
  target: MeetingTarget;
  onRetry: () => void;
  onRetryEvent: () => void;
  onCreateEvent: (request: CreateEventRequest) => Promise<CalendarEvent>;
  onCreateNote: (eventId: string, contactId: string, description: string) => Promise<unknown>;
  onOpenClassic: () => void;
}) {
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-5 py-4 pr-16">
        <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-text-muted"><Calendar className="h-3.5 w-3.5" />Agenda et CRM</div>
        <h2 className="mt-2 text-xl font-bold tracking-[-0.02em] text-text">{target === 'new-event' ? 'Nouvel événement' : 'Préparation du rendez-vous'}</h2>
        <p className="mt-1 text-sm text-text-muted">Événement réel, contexte local vérifiable et actions confirmées.</p>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
        {resource.status === 'loading' ? <div className="flex h-full items-center justify-center gap-2 text-sm text-text-muted"><Loader2 className="h-4 w-4 animate-spin text-[var(--k3)]" />Chargement de l’agenda…</div>
          : resource.status === 'error' ? <div className="flex h-full items-center justify-center text-center"><div><AlertCircle className="mx-auto h-5 w-5 text-warning" /><p className="mt-2 text-sm font-semibold text-text">{resource.error}</p><button type="button" onClick={onRetry} className="mt-4 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">Réessayer</button></div></div>
            : target === 'new-event' ? <NewEventForm data={resource.data} onCreate={onCreateEvent} />
              : eventResource?.status === 'loading' ? <div className="flex h-full items-center justify-center gap-2 text-sm text-text-muted"><Loader2 className="h-4 w-4 animate-spin text-[var(--k3)]" />Je rassemble le contexte exact…</div>
                : eventResource?.status === 'error' ? <div className="flex h-full items-center justify-center text-center"><div><AlertCircle className="mx-auto h-5 w-5 text-warning" /><p className="mt-2 text-sm font-semibold text-text">{eventResource.error}</p><button type="button" onClick={onRetryEvent} className="mt-4 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">Réessayer</button></div></div>
                  : eventResource?.status === 'ready' ? <EventPreparation context={eventResource.data} onCreateNote={onCreateNote} />
                    : <div className="flex h-full items-center justify-center text-center"><div><Calendar className="mx-auto h-6 w-6 text-text-muted" /><p className="mt-2 text-sm font-semibold text-text">Aucun rendez-vous sélectionné</p><p className="mt-1 text-xs text-text-muted">Choisis un événement dans la conversation ou prépare-en un nouveau.</p></div></div>}
      </div>

      <div className="border-t border-border bg-surface p-4"><button type="button" onClick={onOpenClassic} className="w-full rounded-[10px] border border-border px-4 py-2.5 text-xs font-semibold text-text hover:bg-surface-2">Ouvrir l’Agenda complet pour modifier ou supprimer</button></div>
    </div>
  );
}
