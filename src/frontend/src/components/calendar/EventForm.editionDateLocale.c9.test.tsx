/**
 * B-901 (cycle 9, relecteur V4) : le préremplissage d'une édition mêlait une
 * date UTC (`toISOString()`) et une heure locale (`toTimeString()`) : un
 * rendez-vous à 00:30 s'ouvrait à la date de la veille. La branche création
 * utilise déjà `localDateKey` contre ce décalage (BUG-144).
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { CalendarEvent } from '../../services/api';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';
import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';
import { EventForm } from './EventForm';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, createEvent: vi.fn(), updateEvent: vi.fn() };
});

const tot: CalendarEvent = {
  id: 'event-1', calendar_id: 'calendar-1', summary: 'Point du matin', description: null, location: null,
  start_datetime: '2026-07-16T00:30:00', end_datetime: '2026-07-16T01:00:00', start_date: null, end_date: null,
  all_day: false, attendees: [], recurrence: null, status: 'confirmed', synced_at: '2026-07-15T08:00:00Z',
};

describe('EventForm - B-901, l’édition préremplit la date locale', () => {
  beforeEach(() => {
    useCalendarStore.setState({
      calendars: [{ id: 'calendar-1', account_id: 'account-1', summary: 'Agenda principal', description: null, timezone: 'Europe/Paris', primary: true, provider: 'google', synced_at: '2026-07-15T08:00:00Z' }],
      currentCalendarId: 'calendar-1', currentEventId: 'event-1', events: [tot], isEventFormOpen: true, draftEvent: {},
    });
    useEmailStore.setState({ currentAccountId: 'account-1' });
  });

  it('un rendez-vous à 00:30 garde sa date, pas celle de la veille en UTC', async () => {
    render(<PrototypeExternalActionConfirmationProvider><EventForm /></PrototypeExternalActionConfirmationProvider>);
    await waitFor(() => expect(screen.getByLabelText(/Titre/)).toHaveValue('Point du matin'));
    const dateDebut = screen.getByLabelText(/Date de début/) as HTMLInputElement;
    const heureDebut = screen.getByLabelText(/Heure de début/) as HTMLInputElement;
    expect(dateDebut.value).toBe('2026-07-16');
    expect(heureDebut.value).toBe('00:30');
  });
});
