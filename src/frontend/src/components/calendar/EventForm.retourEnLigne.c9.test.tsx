/**
 * B-872 (cycle 9) : « Retour » sur le formulaire de rendez-vous demandait
 * « Abandonner les modifications ? » par `confirm()` natif (règle D62/D106).
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';
import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';
import { EventForm } from './EventForm';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, createEvent: vi.fn(), updateEvent: vi.fn() };
});

describe('EventForm - B-872, abandonner se confirme en ligne', () => {
  beforeEach(() => {
    useCalendarStore.setState({
      calendars: [{ id: 'calendar-1', account_id: 'account-1', summary: 'Agenda principal', description: null, timezone: 'Europe/Paris', primary: true, provider: 'google', synced_at: '2026-07-15T08:00:00Z' }],
      currentCalendarId: 'calendar-1', currentEventId: null, events: [], isEventFormOpen: true, draftEvent: {},
    });
    useEmailStore.setState({ currentAccountId: 'account-1' });
    vi.stubGlobal('confirm', vi.fn(() => { throw new Error('confirm() natif interdit'); }));
  });
  afterEach(() => vi.unstubAllGlobals());

  it('« Retour » pose la question dans le formulaire ; « Abandonner » ferme', () => {
    render(<PrototypeExternalActionConfirmationProvider><EventForm /></PrototypeExternalActionConfirmationProvider>);
    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));
    expect(useCalendarStore.getState().isEventFormOpen).toBe(true);
    expect(screen.getByText(/Abandonner les modifications/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Continuer la saisie' }));
    expect(screen.queryByText(/Abandonner les modifications/)).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));
    fireEvent.click(screen.getByRole('button', { name: 'Abandonner' }));
    expect(useCalendarStore.getState().isEventFormOpen).toBe(false);
  });
});
