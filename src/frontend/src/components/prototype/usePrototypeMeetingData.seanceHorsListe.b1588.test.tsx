/**
 * B-1588 : le compte rendu d'une séance ouverte depuis l'Agenda, hors de la
 * liste chargée, ne s'enregistrait pas (findEvent au lieu de trouver, P-117).
 */
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
  email: 'CLIENT@example.com', phone: null, address: null, notes: 'Contexte vérifié', tags: [], stage: 'prospect',
  score: 0, source: 'local', last_interaction: null, created_at: '2026-07-01', updated_at: '2026-07-12',
};
const activity: ActivityResponse = {
  id: 'activity-1', contact_id: contact.id, type: 'note', title: 'Échange réel',
  description: 'Détail réel', extra_data: null, created_at: '2026-07-12T10:00:00Z',
};

describe('B-1588 : compte rendu d’une séance hors de la liste chargée', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getEmailAuthStatus).mockResolvedValue({ connected: false, accounts: [] });
    vi.mocked(listCalendars).mockResolvedValue([calendar]);
    vi.mocked(listContacts).mockResolvedValue([contact]);
    vi.mocked(listEvents).mockResolvedValue([]);
    vi.mocked(listActivities).mockResolvedValue([]);
    vi.mocked(createActivity).mockResolvedValue(activity);
  });

  it('une séance ouverte depuis l’Agenda reçoit son compte rendu', async () => {
    const { result } = renderHook(() => usePrototypeMeetingData(true));
    await waitFor(() => expect(result.current.resource.status).toBe('ready'));
    await act(async () => { await result.current.openEvent(meetingEventKey(event), event); });

    await act(async () => {
      await result.current.createMeetingNote(meetingEventKey(event), contact.id, 'Compte rendu factuel');
    });

    expect(createActivity).toHaveBeenCalledWith(expect.objectContaining({ contact_id: contact.id, description: 'Compte rendu factuel' }));
  });
});
