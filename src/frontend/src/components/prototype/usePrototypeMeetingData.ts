import { useCallback, useEffect, useRef, useState } from 'react';
import {
  createActivity,
  createEvent,
  getEmailAuthStatus,
  listActivities,
  listCalendars,
  listContacts,
  listEvents,
  type ActivityResponse,
  type Calendar,
  type CalendarEvent,
  type Contact,
  type CreateEventRequest,
  type EmailAccount,
} from '../../services/api';
import type { ReadResource } from './usePrototypeReadData';

export interface MeetingWorkspaceData {
  calendars: Calendar[];
  events: CalendarEvent[];
  contacts: Contact[];
  accounts: EmailAccount[];
  unavailableSources: string[];
}

export interface MeetingEventContext {
  event: CalendarEvent;
  relatedContacts: Contact[];
  activities: ActivityResponse[];
  unavailableSources: string[];
}

function uniqueCalendars(calendars: Calendar[]): Calendar[] {
  return [...new Map(calendars.map((calendar) => [calendar.id, calendar])).values()];
}

function uniqueEvents(events: CalendarEvent[]): CalendarEvent[] {
  return [...new Map(events.map((event) => [meetingEventKey(event), event])).values()];
}

export function meetingEventKey(event: Pick<CalendarEvent, 'calendar_id' | 'id'>): string {
  return `${encodeURIComponent(event.calendar_id)}::${encodeURIComponent(event.id)}`;
}

function findEvent(events: CalendarEvent[], key: string): CalendarEvent | undefined {
  return events.find((event) => meetingEventKey(event) === key)
    || events.find((event) => event.id === key);
}

function eventStart(event: CalendarEvent): number {
  const value = event.start_datetime || event.start_date;
  if (!value) return Number.POSITIVE_INFINITY;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? Number.POSITIVE_INFINITY : date.getTime();
}

function attendeeAddress(value: string): string {
  const bracketed = value.match(/<([^>]+)>/);
  return (bracketed?.[1] || value).trim().toLowerCase();
}

async function listAllContacts(): Promise<Contact[]> {
  const contacts: Contact[] = [];
  const pageSize = 200;
  for (let offset = 0; offset < 1000; offset += pageSize) {
    const page = await listContacts(offset, pageSize);
    contacts.push(...page);
    if (page.length < pageSize) break;
  }
  return contacts;
}

export function contactsForEvent(event: CalendarEvent, contacts: Contact[]): Contact[] {
  const attendees = new Set((event.attendees || []).map(attendeeAddress));
  return contacts.filter((contact) => Boolean(contact.email && attendees.has(contact.email.trim().toLowerCase())));
}

export function usePrototypeMeetingData(enabled = true) {
  const [resource, setResource] = useState<ReadResource<MeetingWorkspaceData>>({
    status: 'loading', data: null, error: null,
  });
  const [eventResource, setEventResource] = useState<ReadResource<MeetingEventContext> | null>(null);
  const requestId = useRef(0);
  const detailRequestId = useRef(0);
  const selectedEventId = useRef<string | null>(null);
  const workspace = useRef<MeetingWorkspaceData | null>(null);
  const createEventPending = useRef(false);
  const createNotePending = useRef(false);

  const loadEventContext = useCallback(async (eventKey: string, data = workspace.current) => {
    if (!data) return;
    const event = findEvent(data.events, eventKey);
    if (!event) {
      setEventResource({ status: 'error', data: null, error: 'Ce rendez-vous n’est plus disponible.' });
      return;
    }

    selectedEventId.current = meetingEventKey(event);
    const activeRequest = ++detailRequestId.current;
    setEventResource({ status: 'loading', data: null, error: null });
    const relatedContacts = contactsForEvent(event, data.contacts);
    const activityResults = await Promise.allSettled(
      relatedContacts.map((contact) => listActivities({ contact_id: contact.id, limit: 20 })),
    );
    if (activeRequest !== detailRequestId.current) return;

    const activities = activityResults
      .flatMap((result) => result.status === 'fulfilled' ? result.value : [])
      .sort((left, right) => right.created_at.localeCompare(left.created_at));
    const unavailableSources = activityResults.some((result) => result.status === 'rejected')
      ? ['historique CRM']
      : [];
    setEventResource({
      status: 'ready',
      data: { event, relatedContacts, activities, unavailableSources },
      error: null,
    });
  }, []);

  const refresh = useCallback(async () => {
    const activeRequest = ++requestId.current;
    setResource({ status: 'loading', data: null, error: null });

    const [authResult, contactsResult] = await Promise.allSettled([
      getEmailAuthStatus(),
      listAllContacts(),
    ]);
    if (activeRequest !== requestId.current) return;

    const accounts = authResult.status === 'fulfilled' ? authResult.value.accounts : [];
    const calendarResults = await Promise.allSettled([
      listCalendars(undefined, { createDefault: false }),
      ...accounts.map((account) => listCalendars(account.id, { createDefault: false })),
    ]);
    if (activeRequest !== requestId.current) return;

    const calendars = uniqueCalendars(
      calendarResults.flatMap((result) => result.status === 'fulfilled' ? result.value : []),
    );
    if (calendars.length === 0 && calendarResults.every((result) => result.status === 'rejected')) {
      setResource({
        status: 'error', data: null,
        error: 'Impossible de charger les calendriers pour le moment.',
      });
      return;
    }

    const now = new Date();
    const horizon = new Date(now);
    horizon.setDate(horizon.getDate() + 90);
    const eventResults = await Promise.allSettled(
      calendars.map((calendar) => listEvents(calendar.account_id || undefined, calendar.id, {
        time_min: now.toISOString(),
        time_max: horizon.toISOString(),
        max_results: 50,
      })),
    );
    if (activeRequest !== requestId.current) return;

    const events = uniqueEvents(
      eventResults.flatMap((result) => result.status === 'fulfilled' ? result.value : []),
    )
      .filter((event) => event.status !== 'cancelled')
      .sort((left, right) => eventStart(left) - eventStart(right));
    const unavailableSources: string[] = [];
    if (authResult.status === 'rejected') unavailableSources.push('comptes connectés');
    if (contactsResult.status === 'rejected') unavailableSources.push('contacts');
    const failedCalendars = eventResults.filter((result) => result.status === 'rejected').length;
    if (failedCalendars > 0) unavailableSources.push(`${failedCalendars} calendrier${failedCalendars > 1 ? 's' : ''}`);

    const data: MeetingWorkspaceData = {
      calendars,
      events,
      contacts: contactsResult.status === 'fulfilled' ? contactsResult.value : [],
      accounts,
      unavailableSources,
    };
    workspace.current = data;
    setResource({ status: 'ready', data, error: null });

    const requestedEvent = selectedEventId.current ? findEvent(events, selectedEventId.current) : events[0];
    if (requestedEvent) void loadEventContext(meetingEventKey(requestedEvent), data);
    else setEventResource(null);
  }, [loadEventContext]);

  const createCalendarEvent = useCallback(async (request: CreateEventRequest) => {
    if (createEventPending.current) throw new Error('La création de cet événement est déjà en cours.');
    createEventPending.current = true;
    try {
      const data = workspace.current;
      if (!data) throw new Error('Les calendriers ne sont pas encore disponibles.');
      const calendar = data.calendars.find((item) => item.id === request.calendar_id);
      if (!calendar) throw new Error('Sélectionne un calendrier disponible.');

      const created = await createEvent(request, calendar.account_id || undefined);
      const events = uniqueEvents([...data.events, created]).sort((left, right) => eventStart(left) - eventStart(right));
      const nextData = { ...data, events };
      workspace.current = nextData;
      setResource({ status: 'ready', data: nextData, error: null });
      await loadEventContext(meetingEventKey(created), nextData);
      return created;
    } finally {
      createEventPending.current = false;
    }
  }, [loadEventContext]);

  const createMeetingNote = useCallback(async (eventId: string, contactId: string, description: string) => {
    const cleanDescription = description.trim();
    if (!cleanDescription) throw new Error('La note ne peut pas être vide.');
    if (createNotePending.current) throw new Error('L’enregistrement de la note est déjà en cours.');
    createNotePending.current = true;
    try {
      const data = workspace.current;
      const event = data ? findEvent(data.events, eventId) : undefined;
      const contact = data?.contacts.find((item) => item.id === contactId);
      if (!data || !event || !contact || !contactsForEvent(event, data.contacts).some((item) => item.id === contactId)) {
        throw new Error('Le contact n’est pas relié à ce rendez-vous par son adresse email.');
      }
      const created = await createActivity({
        contact_id: contactId,
        type: 'note',
        title: `Note rendez-vous : ${event.summary}`,
        description: cleanDescription,
        extra_data: JSON.stringify({ calendar_event_id: event.id, calendar_id: event.calendar_id }),
      });
      setEventResource((current) => current?.status === 'ready'
        ? { ...current, data: { ...current.data, activities: [created, ...current.data.activities] } }
        : current);
      return created;
    } finally {
      createNotePending.current = false;
    }
  }, []);

  useEffect(() => {
    if (!enabled) return undefined;
    void refresh();
    return () => {
      requestId.current += 1;
      detailRequestId.current += 1;
    };
  }, [enabled, refresh]);

  return {
    resource,
    eventResource,
    refresh,
    openEvent: loadEventContext,
    retryEvent: () => selectedEventId.current ? loadEventContext(selectedEventId.current) : Promise.resolve(),
    createCalendarEvent,
    createMeetingNote,
  };
}
