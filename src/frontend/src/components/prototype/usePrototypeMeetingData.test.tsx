import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../services/api')>();
  return {
    ...actual,
    createActivity: vi.fn(), createEvent: vi.fn(), getEmailAuthStatus: vi.fn(),
    listActivities: vi.fn(), listCalendars: vi.fn(), listContacts: vi.fn(), listEvents: vi.fn(),
  };
});

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
} from '../../services/api';
import { meetingEventKey, usePrototypeMeetingData } from './usePrototypeMeetingData';

const calendar: Calendar = {
  id: 'cal-1', account_id: null, summary: 'Synoptïa', description: null,
  timezone: 'Europe/Paris', primary: true, provider: 'local', synced_at: null,
};
const event: CalendarEvent = {
  id: 'event-1', calendar_id: calendar.id, summary: 'Point réel', description: 'Ordre du jour réel',
  location: 'Visio', start_datetime: '2026-07-14T10:00:00', end_datetime: '2026-07-14T11:00:00',
  start_date: null, end_date: null, all_day: false, attendees: ['client@example.com'],
  recurrence: null, status: 'confirmed', synced_at: '2026-07-13T10:00:00Z',
};
const contact: Contact = {
  id: 'contact-1', first_name: 'Camille', last_name: 'Martin', company: 'Client',
  email: 'CLIENT@example.com', phone: null, notes: 'Contexte vérifié', tags: [], stage: 'prospect',
  score: 0, source: 'local', last_interaction: null, created_at: '2026-07-01', updated_at: '2026-07-12',
};
const activity: ActivityResponse = {
  id: 'activity-1', contact_id: contact.id, type: 'note', title: 'Échange réel',
  description: 'Détail réel', extra_data: null, created_at: '2026-07-12T10:00:00Z',
};

describe('usePrototypeMeetingData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getEmailAuthStatus).mockResolvedValue({ connected: false, accounts: [] });
    vi.mocked(listCalendars).mockResolvedValue([calendar]);
    vi.mocked(listContacts).mockResolvedValue([contact]);
    vi.mocked(listEvents).mockResolvedValue([event]);
    vi.mocked(listActivities).mockResolvedValue([activity]);
    vi.mocked(createActivity).mockResolvedValue(activity);
    vi.mocked(createEvent).mockResolvedValue(event);
  });

  it('charge en lecture pure et relie le contact par email exact normalisé', async () => {
    const { result } = renderHook(() => usePrototypeMeetingData(true));
    await waitFor(() => expect(result.current.eventResource?.status).toBe('ready'));

    expect(listCalendars).toHaveBeenCalledWith(undefined, { createDefault: false });
    expect(result.current.resource.data?.events).toEqual([event]);
    expect(result.current.eventResource?.data?.relatedContacts).toEqual([contact]);
    expect(result.current.eventResource?.data?.activities).toEqual([activity]);
    expect(createEvent).not.toHaveBeenCalled();
    expect(createActivity).not.toHaveBeenCalled();
  });

  it('n’écrit qu’après un appel explicite et refuse une note vide', async () => {
    const { result } = renderHook(() => usePrototypeMeetingData(true));
    await waitFor(() => expect(result.current.eventResource?.status).toBe('ready'));

    await expect(result.current.createMeetingNote(meetingEventKey(event), contact.id, '  ')).rejects.toThrow('vide');
    expect(createActivity).not.toHaveBeenCalled();

    await act(async () => {
      await result.current.createMeetingNote(meetingEventKey(event), contact.id, 'Compte rendu factuel');
    });
    expect(createActivity).toHaveBeenCalledTimes(1);
    expect(createActivity).toHaveBeenCalledWith(expect.objectContaining({ description: 'Compte rendu factuel' }));

    await act(async () => {
      await result.current.createCalendarEvent({
        calendar_id: calendar.id, summary: event.summary,
        start_datetime: event.start_datetime || undefined, end_datetime: event.end_datetime || undefined,
      });
    });
    expect(createEvent).toHaveBeenCalledWith(expect.objectContaining({ calendar_id: calendar.id }), undefined);
  });

  // BUG-143 : sans calendrier (lecture pure createDefault:false sur une base vierge),
  // « Préparer un événement » finissait sur un cul-de-sac. Le provisionnement du
  // calendrier local n'a lieu qu'au geste explicite de création.
  describe('ensureDefaultCalendar (BUG-143)', () => {
    it('provisionne le calendrier par défaut à la demande et met à jour la ressource', async () => {
      vi.mocked(listCalendars).mockResolvedValue([]);
      vi.mocked(listEvents).mockResolvedValue([]);
      const { result } = renderHook(() => usePrototypeMeetingData(true));
      await waitFor(() => expect(result.current.resource.status).toBe('ready'));
      expect(result.current.resource.data?.calendars).toEqual([]);

      vi.mocked(listCalendars).mockResolvedValueOnce([calendar]);
      await act(async () => {
        await result.current.ensureDefaultCalendar();
      });

      expect(listCalendars).toHaveBeenLastCalledWith(undefined);
      expect(result.current.resource.data?.calendars).toEqual([calendar]);
    });

    it('ne rappelle pas l’API quand un calendrier existe déjà', async () => {
      const { result } = renderHook(() => usePrototypeMeetingData(true));
      await waitFor(() => expect(result.current.resource.status).toBe('ready'));
      const callsAvant = vi.mocked(listCalendars).mock.calls.length;

      await act(async () => {
        await result.current.ensureDefaultCalendar();
      });

      expect(vi.mocked(listCalendars).mock.calls.length).toBe(callsAvant);
    });

    it('échoue clairement si aucun calendrier ne peut être préparé', async () => {
      vi.mocked(listCalendars).mockResolvedValue([]);
      vi.mocked(listEvents).mockResolvedValue([]);
      const { result } = renderHook(() => usePrototypeMeetingData(true));
      await waitFor(() => expect(result.current.resource.status).toBe('ready'));

      await expect(result.current.ensureDefaultCalendar()).rejects.toThrow('calendrier');
    });
  });
});
