import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { CalendarEvent } from '../../services/api';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';
import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';
import { EventForm } from './EventForm';

const { createEventMock, updateEventMock } = vi.hoisted(() => ({
  createEventMock: vi.fn(),
  updateEventMock: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    createEvent: createEventMock,
    updateEvent: updateEventMock,
  };
});

const existingEvent: CalendarEvent = {
  id: 'event-1',
  calendar_id: 'calendar-1',
  summary: 'Rendez-vous existant',
  description: 'Contexte initial',
  location: 'Manosque',
  start_datetime: '2026-07-16T10:00:00',
  end_datetime: '2026-07-16T11:00:00',
  start_date: null,
  end_date: null,
  all_day: false,
  attendees: ['invite@example.fr'],
  recurrence: null,
  status: 'confirmed',
  synced_at: '2026-07-15T08:00:00Z',
};

function seedCalendar(event: CalendarEvent | null = null) {
  useCalendarStore.setState({
    calendars: [{
      id: 'calendar-1', account_id: 'account-1', summary: 'Agenda principal',
      description: null, timezone: 'Europe/Paris', primary: true,
      provider: 'google', synced_at: '2026-07-15T08:00:00Z',
    }],
    currentCalendarId: 'calendar-1',
    currentEventId: event?.id ?? null,
    events: event ? [event] : [],
    isEventFormOpen: true,
    draftEvent: {},
  });
  useEmailStore.setState({ currentAccountId: 'account-1' });
}

describe('EventForm - confirmation 0.40', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    createEventMock.mockResolvedValue({ ...existingEvent, id: 'event-created', summary: 'Point projet' });
    updateEventMock.mockResolvedValue(existingEvent);
  });

  it('bloque la création avant confirmation et affiche les horaires', async () => {
    seedCalendar();
    render(
      <PrototypeExternalActionConfirmationProvider>
        <EventForm />
      </PrototypeExternalActionConfirmationProvider>,
    );

    fireEvent.change(screen.getByPlaceholderText("Titre de l'événement"), {
      target: { value: 'Point projet' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    const preview = await screen.findByTestId('external-action-confirmation');
    expect(preview).toHaveTextContent('Confirmer la création de l’événement');
    expect(preview).toHaveTextContent('Point projet');
    expect(preview).toHaveTextContent('Agenda principal');
    expect(preview).toHaveTextContent('google');
    expect(createEventMock).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Confirmer la création' }));

    await waitFor(() => {
      expect(createEventMock).toHaveBeenCalledWith(
        expect.objectContaining({ calendar_id: 'calendar-1', summary: 'Point projet' }),
        'account-1',
      );
    });
  });

  it('bloque aussi la modification avant confirmation', async () => {
    seedCalendar(existingEvent);
    render(
      <PrototypeExternalActionConfirmationProvider>
        <EventForm />
      </PrototypeExternalActionConfirmationProvider>,
    );

    expect(await screen.findByDisplayValue('Rendez-vous existant')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    expect(screen.getByTestId('external-action-confirmation')).toHaveTextContent('Confirmer la modification de l’événement');
    expect(updateEventMock).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Confirmer la modification' }));

    await waitFor(() => {
      expect(updateEventMock).toHaveBeenCalledWith(
        'event-1',
        expect.objectContaining({ summary: 'Rendez-vous existant' }),
        'calendar-1',
        'account-1',
      );
    });
  });
});
