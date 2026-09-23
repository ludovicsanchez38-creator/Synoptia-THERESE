/**
 * B-973 et B-974 (cycle 11, 23/09/2026, ronde B du ZERO_CHECK).
 *
 * B-973 : Échap, le geste clavier le plus naturel pour répondre à « Abandonner
 * les modifications ? », fermait toute la vue Tâches ou Agenda et jetait la
 * saisie, avec ou sans la question affichée. Les formulaires n'inscrivaient
 * rien dans la pile d'Échap : la cascade de la coque refermait la vue.
 *
 * B-974 : la question était posée sur un formulaire vierge (choix fail-closed
 * de B-872), où la phrase « Abandonner les modifications ? » est fausse.
 *
 * La coque appelle `runTopEscapeHandler()` en tête de sa cascade ; ces tests
 * font de même.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listProjects: vi.fn().mockResolvedValue([]),
  listContacts: vi.fn().mockResolvedValue([]),
  createEvent: vi.fn(),
  updateEvent: vi.fn(),
}));

import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';
import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';
import { useTaskStore } from '../../stores/taskStore';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';
import { EventForm } from '../calendar/EventForm';
import { TaskForm } from './TaskForm';

const echap = () => {
  let agi = false;
  act(() => { agi = runTopEscapeHandler(); });
  return agi;
};

describe('TaskForm : Échap et question d’abandon (B-973, B-974)', () => {
  beforeEach(() => {
    _clearEscapeHandlers();
    useTaskStore.setState({ tasks: [], currentTaskId: null, isTaskFormOpen: true, searchQuery: '' });
  });
  afterEach(() => _clearEscapeHandlers());

  it('B-974 : « Retour » sur un formulaire vierge ferme sans poser la question', () => {
    render(<TaskForm />);
    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));
    expect(screen.queryByText(/Abandonner les modifications/)).toBeNull();
    expect(useTaskStore.getState().isTaskFormOpen).toBe(false);
  });

  it('B-973 : Échap sur une saisie en cours pose la question au lieu de tout jeter', () => {
    render(<TaskForm />);
    fireEvent.change(screen.getByLabelText(/Titre/), { target: { value: 'Relancer Ruiz' } });
    expect(echap()).toBe(true);
    expect(useTaskStore.getState().isTaskFormOpen).toBe(true);
    expect(screen.getByText(/Abandonner les modifications/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Titre/)).toHaveValue('Relancer Ruiz');
  });

  it('B-973 : Échap sur la question affichée garde la saisie', () => {
    render(<TaskForm />);
    fireEvent.change(screen.getByLabelText(/Titre/), { target: { value: 'Relancer Ruiz' } });
    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));
    expect(screen.getByText(/Abandonner les modifications/)).toBeInTheDocument();
    expect(echap()).toBe(true);
    expect(screen.queryByText(/Abandonner les modifications/)).toBeNull();
    expect(useTaskStore.getState().isTaskFormOpen).toBe(true);
    expect(screen.getByLabelText(/Titre/)).toHaveValue('Relancer Ruiz');
  });

  it('Échap sur un formulaire vierge le ferme, sans question', () => {
    render(<TaskForm />);
    expect(echap()).toBe(true);
    expect(useTaskStore.getState().isTaskFormOpen).toBe(false);
  });
});

describe('EventForm : Échap et question d’abandon (B-973, B-974)', () => {
  beforeEach(() => {
    _clearEscapeHandlers();
    useCalendarStore.setState({
      calendars: [{ id: 'calendar-1', account_id: null, summary: 'Mon calendrier', description: null, timezone: 'Europe/Paris', primary: true, provider: 'local', synced_at: null }] as never,
      currentCalendarId: 'calendar-1', currentEventId: null, events: [], isEventFormOpen: true, draftEvent: {},
    });
    useEmailStore.setState({ currentAccountId: null });
  });
  afterEach(() => _clearEscapeHandlers());

  const rendre = () => render(<PrototypeExternalActionConfirmationProvider><EventForm /></PrototypeExternalActionConfirmationProvider>);

  it('B-974 : « Retour » sur un rendez-vous vierge (dates par défaut) ferme sans question', () => {
    rendre();
    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));
    expect(screen.queryByText(/Abandonner les modifications/)).toBeNull();
    expect(useCalendarStore.getState().isEventFormOpen).toBe(false);
  });

  it('B-973 : Échap sur un titre saisi pose la question, puis Échap la referme en gardant la saisie', () => {
    rendre();
    fireEvent.change(screen.getByLabelText(/Titre/), { target: { value: 'Rendez-vous Ruiz' } });
    expect(echap()).toBe(true);
    expect(useCalendarStore.getState().isEventFormOpen).toBe(true);
    expect(screen.getByText(/Abandonner les modifications/)).toBeInTheDocument();
    expect(echap()).toBe(true);
    expect(screen.queryByText(/Abandonner les modifications/)).toBeNull();
    expect(screen.getByLabelText(/Titre/)).toHaveValue('Rendez-vous Ruiz');
    expect(useCalendarStore.getState().isEventFormOpen).toBe(true);
  });
});

describe('EventForm : un rechargement de la liste n’écrase pas la saisie (B-979)', () => {
  const evenement = {
    id: 'evt-1', calendar_id: 'calendar-1', summary: 'Point Ruiz', description: null, location: null,
    start_datetime: '2026-09-24T09:00:00', end_datetime: '2026-09-24T10:00:00', start_date: null, end_date: null,
    all_day: false, attendees: ['a@exemple.invalid'], recurrence: null, status: 'confirmed',
  };
  beforeEach(() => {
    _clearEscapeHandlers();
    useCalendarStore.setState({
      calendars: [{ id: 'calendar-1', account_id: null, summary: 'Mon calendrier', description: null, timezone: 'Europe/Paris', primary: true, provider: 'local', synced_at: null }] as never,
      currentCalendarId: 'calendar-1', currentEventId: 'evt-1', events: [evenement] as never, isEventFormOpen: true, draftEvent: {},
    });
  });
  afterEach(() => _clearEscapeHandlers());

  it('la saisie survit au rafraîchissement, et la question reste posée', () => {
    render(<PrototypeExternalActionConfirmationProvider><EventForm /></PrototypeExternalActionConfirmationProvider>);
    expect(screen.getByLabelText(/Titre/)).toHaveValue('Point Ruiz');
    fireEvent.change(screen.getByLabelText(/Titre/), { target: { value: 'Point Ruiz, reporté' } });

    // Synchronisation : même rendez-vous, nouvel objet (et participants vidés côté serveur).
    act(() => { useCalendarStore.setState({ events: [{ ...evenement, attendees: [] }] as never }); });

    expect(screen.getByLabelText(/Titre/)).toHaveValue('Point Ruiz, reporté');
    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));
    expect(screen.getByText(/Abandonner les modifications/)).toBeInTheDocument();
    expect(useCalendarStore.getState().isEventFormOpen).toBe(true);
  });
});

describe('TaskForm : Échap sous une surface de la coque (B-980)', () => {
  beforeEach(async () => {
    _clearEscapeHandlers();
    useTaskStore.setState({ tasks: [], currentTaskId: null, isTaskFormOpen: true, searchQuery: '' });
  });
  afterEach(async () => {
    _clearEscapeHandlers();
    const { usePanelStore } = await import('../../stores/panelStore');
    usePanelStore.setState({ showSettings: false } as never);
  });

  it('Réglages ouverts : le formulaire laisse passer Échap et ne bouge pas', async () => {
    const { usePanelStore } = await import('../../stores/panelStore');
    render(<TaskForm />);
    fireEvent.change(screen.getByLabelText(/Titre/), { target: { value: 'Relancer Ruiz' } });
    act(() => { usePanelStore.setState({ showSettings: true } as never); });
    expect(echap()).toBe(false);
    expect(screen.queryByText(/Abandonner les modifications/)).toBeNull();
    expect(useTaskStore.getState().isTaskFormOpen).toBe(true);
  });
});

describe('EventForm : Échap sous une modale posée par-dessus (B-980)', () => {
  beforeEach(() => { _clearEscapeHandlers(); });
  afterEach(() => { _clearEscapeHandlers(); document.querySelectorAll('[data-test-modale-dessus]').forEach((n) => n.remove()); });

  it('une modale distincte ouverte (palette, centre) : le formulaire laisse passer Échap', () => {
    render(<PrototypeExternalActionConfirmationProvider><EventForm /></PrototypeExternalActionConfirmationProvider>);
    fireEvent.change(screen.getByLabelText(/Titre/), { target: { value: 'Visite chantier' } });
    const modale = document.createElement('div');
    modale.setAttribute('role', 'dialog');
    modale.setAttribute('aria-modal', 'true');
    modale.setAttribute('data-test-modale-dessus', '');
    document.body.appendChild(modale);
    expect(echap()).toBe(false);
    expect(screen.queryByText(/Abandonner les modifications/)).toBeNull();
  });

  it('la modale qui contient le formulaire ne le fait pas décliner', () => {
    render(<div role="dialog" aria-modal="true"><PrototypeExternalActionConfirmationProvider><EventForm /></PrototypeExternalActionConfirmationProvider></div>);
    fireEvent.change(screen.getByLabelText(/Titre/), { target: { value: 'Visite chantier' } });
    expect(echap()).toBe(true);
    expect(screen.getByText(/Abandonner les modifications/)).toBeTruthy();
  });
});

describe('EventForm : rendez-vous « toute la journée » arrivé après l’ouverture (B-982)', () => {
  beforeEach(() => {
    _clearEscapeHandlers();
    useCalendarStore.setState({
      calendars: [{ id: 'calendar-1', account_id: null, summary: 'Mon calendrier', description: null, timezone: 'Europe/Paris', primary: true, provider: 'local', synced_at: null }] as never,
      currentCalendarId: 'calendar-1', currentEventId: 'evt-1', events: [], isEventFormOpen: true, draftEvent: {},
    });
  });
  afterEach(() => _clearEscapeHandlers());

  it('aucun champ touché : « Retour » ferme sans question', () => {
    render(<PrototypeExternalActionConfirmationProvider><EventForm /></PrototypeExternalActionConfirmationProvider>);
    act(() => {
      useCalendarStore.setState({ events: [{
        id: 'evt-1', calendar_id: 'calendar-1', summary: 'Séminaire', description: null, location: null,
        start_datetime: null, end_datetime: null, start_date: '2026-09-24', end_date: '2026-09-24',
        all_day: true, attendees: [], recurrence: null, status: 'confirmed',
      }] as never });
    });
    expect(screen.getByLabelText(/Titre/)).toHaveValue('Séminaire');
    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));
    expect(screen.queryByText(/Abandonner les modifications/)).toBeNull();
    expect(useCalendarStore.getState().isEventFormOpen).toBe(false);
  });
});
