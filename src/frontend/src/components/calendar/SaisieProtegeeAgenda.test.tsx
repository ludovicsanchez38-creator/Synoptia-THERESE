/**
 * Revue Codex n°13 du cycle 11 (23/09/2026), agenda.
 *
 * B-989 (R-2) : « Nouveau rendez-vous », visible pendant la modification
 * d'un rendez-vous, passait le formulaire en création sans question et en
 * gardant le titre, le lieu et la description de la fiche ouverte.
 *
 * B-990 (R-3) : changer de période pendant la modification rechargeait une
 * liste sans la fiche ; le formulaire reprenait alors les dates du jour,
 * puis, au retour de la fiche, réécrivait toute la saisie.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';

const api = vi.hoisted(() => ({
  getEmailAuthStatus: vi.fn(),
  listCalendars: vi.fn(),
  listEvents: vi.fn(),
  syncCalendar: vi.fn(),
  updateEvent: vi.fn(),
  createEvent: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    getEmailAuthStatus: (...a: unknown[]) => api.getEmailAuthStatus(...a),
    listCalendars: (...a: unknown[]) => api.listCalendars(...a),
    listEvents: (...a: unknown[]) => api.listEvents(...a),
    syncCalendar: (...a: unknown[]) => api.syncCalendar(...a),
    updateEvent: (...a: unknown[]) => api.updateEvent(...a),
    createEvent: (...a: unknown[]) => api.createEvent(...a),
    listContacts: vi.fn().mockResolvedValue([]),
  };
});

import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';
import { CalendarPanel } from './CalendarPanel';

const AGENDA = {
  id: 'cal-1', account_id: null, summary: 'Agenda Atelier', description: null,
  timezone: 'Europe/Paris', primary: true, provider: 'local', synced_at: null,
} as never;

const RENDEZ_VOUS = {
  id: 'evt-1', calendar_id: 'cal-1', summary: 'Séance 1 · Garage Benali', description: 'Diagnostic',
  location: 'sur place', start_datetime: '2026-09-02T09:00:00', end_datetime: '2026-09-02T10:30:00',
  start_date: null, end_date: null, all_day: false, attendees: null, recurrence: null,
  status: 'confirmed', synced_at: null,
} as never;

const moisDemande = (p: { time_min: string }) => new Date(p.time_min).getMonth() + (new Date(p.time_min).getDate() > 1 ? 1 : 0);

beforeEach(() => {
  vi.clearAllMocks();
  _clearEscapeHandlers();
  api.getEmailAuthStatus.mockResolvedValue({ authenticated: false, accounts: [] });
  api.listCalendars.mockResolvedValue([AGENDA]);
  // La fiche n'appartient qu'à septembre 2026.
  api.listEvents.mockImplementation(async (_compte: unknown, _agenda: unknown, p: { time_min: string }) => (moisDemande(p) === 8 ? [RENDEZ_VOUS] : []));
  api.syncCalendar.mockResolvedValue({ synced_at: '2026-09-11T10:00:00Z' });
  useCalendarStore.setState({
    calendars: [AGENDA], currentCalendarId: 'cal-1', events: [RENDEZ_VOUS],
    currentEventId: 'evt-1', isEventFormOpen: true, viewMode: 'month',
    selectedDate: new Date(2026, 8, 2), draftEvent: {}, showCancelled: false,
    searchQuery: '', lastSyncAt: null,
  } as never);
  useEmailStore.setState({ accounts: [], currentAccountId: null, needsReauth: false } as never);
});

async function monter() {
  render(<PrototypeExternalActionConfirmationProvider><CalendarPanel standalone /></PrototypeExternalActionConfirmationProvider>);
  await waitFor(() => expect(screen.getByLabelText(/Titre/)).toHaveValue('Séance 1 · Garage Benali'));
  for (let tour = 0; tour < 6; tour++) {
    await act(async () => { await Promise.resolve(); });
  }
}

const titre = () => screen.getByLabelText(/Titre/) as HTMLInputElement;
const dateDeDebut = () => screen.getByLabelText(/Date de début/) as HTMLInputElement;

describe('B-989 : « Nouveau rendez-vous » pendant une modification', () => {
  it('fiche intacte : le formulaire repart vierge, sans reprendre le titre ni le lieu', async () => {
    await monter();
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /Nouveau rendez-vous/ })); });
    await waitFor(() => expect(titre()).toHaveValue(''));
    expect((screen.getByLabelText(/Lieu ou visio/) as HTMLInputElement).value).toBe('');
    expect((screen.getByLabelText(/Description/) as HTMLTextAreaElement).value).toBe('');
  });

  it('fiche modifiée : la question est posée et la saisie reste', async () => {
    await monter();
    fireEvent.change(titre(), { target: { value: 'Séance 1 · Garage Benali, reportée' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /Nouveau rendez-vous/ })); });
    expect(screen.getByText(/Abandonner les modifications/)).toBeInTheDocument();
    expect(titre()).toHaveValue('Séance 1 · Garage Benali, reportée');
    expect(useCalendarStore.getState().currentEventId).toBe('evt-1');
  });
});

describe('B-990 : changer de période pendant une modification', () => {
  it('aller-retour de période : ni les dates ni la saisie ne sont réécrites', async () => {
    await monter();
    fireEvent.change(titre(), { target: { value: 'Séance 1 · Garage Benali, reportée' } });
    const dateAvant = dateDeDebut().value;
    expect(dateAvant).toBe('2026-09-02');

    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Période suivante' })); });
    await waitFor(() => expect(api.listEvents.mock.calls.some((appel) => moisDemande(appel[2] as { time_min: string }) === 9)).toBe(true));
    for (let tour = 0; tour < 6; tour++) { await act(async () => { await Promise.resolve(); }); }
    expect(dateDeDebut().value).toBe(dateAvant);
    expect(titre()).toHaveValue('Séance 1 · Garage Benali, reportée');

    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Période précédente' })); });
    for (let tour = 0; tour < 6; tour++) { await act(async () => { await Promise.resolve(); }); }
    await waitFor(() => expect(useCalendarStore.getState().events).toHaveLength(1));
    expect(titre()).toHaveValue('Séance 1 · Garage Benali, reportée');
    expect(dateDeDebut().value).toBe(dateAvant);
  });
});

describe('B-998 : enregistrer une modification dont la fiche est hors de la liste', () => {
  it('après « Période suivante », « Enregistrer » met à jour le rendez-vous au lieu d’en créer un', async () => {
    api.updateEvent.mockResolvedValue({ ...(RENDEZ_VOUS as object), summary: 'Séance 1 · Garage Benali, reportée' });
    api.createEvent.mockResolvedValue({ ...(RENDEZ_VOUS as object), id: 'evt-doublon' });
    await monter();
    fireEvent.change(titre(), { target: { value: 'Séance 1 · Garage Benali, reportée' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Période suivante' })); });
    for (let tour = 0; tour < 6; tour++) { await act(async () => { await Promise.resolve(); }); }
    await waitFor(() => expect(useCalendarStore.getState().events).toHaveLength(0));

    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /^Confirmer la/ })); });
    await waitFor(() => expect(api.updateEvent).toHaveBeenCalled());
    expect(api.updateEvent.mock.calls[0][0]).toBe('evt-1');
    expect(api.createEvent).not.toHaveBeenCalled();
  });
});
