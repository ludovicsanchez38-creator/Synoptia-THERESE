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
