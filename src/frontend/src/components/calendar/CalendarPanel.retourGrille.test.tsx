/**
 * B-238 : après une création, l'agenda restait bloqué sur la fiche de
 * l'événement.
 *
 * `EventForm` pose `setCurrentEvent(created.id)` après la création, et la
 * cascade de rendu du panneau donne la priorité à `currentEventId` sur
 * `viewMode` : les quatre boutons de vue ne changeaient que `viewMode`, donc
 * la fiche restait à l'écran pendant que l'intitulé de période, lui, changeait
 * — l'utilisateur voyait l'agenda répondre sans jamais revenir à la grille.
 *
 * Le test part de l'état exact laissé par la création (fiche ouverte) et
 * exige, pour CHACUN des quatre boutons, que la grille correspondante revienne
 * ET que la fiche soit rangée.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';

const { CALENDRIER, EVENEMENT, RESUME } = vi.hoisted(() => {
  const resume = 'Coaching Marie L. - Séance 1';
  return {
    RESUME: resume,
    CALENDRIER: {
      id: 'cal-1',
      account_id: null,
      summary: 'Mon calendrier',
      description: null,
      timezone: 'Europe/Paris',
      primary: true,
      provider: 'local',
      synced_at: null,
    } as never,
    EVENEMENT: {
      id: 'evt-1',
      calendar_id: 'cal-1',
      summary: resume,
      description: null,
      location: null,
      start_datetime: '2026-09-07T10:00:00',
      end_datetime: '2026-09-07T11:00:00',
      start_date: null,
      end_date: null,
      all_day: false,
      attendees: null,
      recurrence: null,
      status: 'confirmed',
      synced_at: null,
    } as never,
  };
});

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    getEmailAuthStatus: vi.fn().mockResolvedValue({ authenticated: false, accounts: [] }),
    listCalendars: vi.fn().mockResolvedValue([CALENDRIER]),
    listEvents: vi.fn().mockResolvedValue([EVENEMENT]),
  };
});

import { CalendarPanel } from './CalendarPanel';

/** La fiche est reconnue à son titre : seule `EventDetail` rend le résumé de
 *  l'événement en titre de niveau 3 (les grilles le rendent dans un bouton). */
function ficheVisible(): boolean {
  return screen.queryByRole('heading', { level: 3, name: RESUME }) !== null;
}

/** Un marqueur PROPRE à chaque grille : sans lui, un panneau vide (fiche
 *  rangée, rien rendu à la place) passerait pour un retour à la grille. */
const MARQUEURS: Record<string, () => boolean> = {
  Mois: () => screen.queryAllByText('Mer').length > 0,
  Semaine: () => screen.queryAllByText('Mer').length > 0,
  Jour: () => screen.queryAllByText('06:00').length > 0,
  Liste: () => screen.queryByRole('heading', { level: 4, name: RESUME }) !== null,
};

describe('B-238 : choisir une vue ramène toujours la grille', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCalendarStore.setState({
      calendars: [CALENDRIER],
      currentCalendarId: 'cal-1',
      events: [EVENEMENT],
      currentEventId: null,
      isEventFormOpen: false,
      viewMode: 'month',
      selectedDate: new Date(2026, 8, 2),
      draftEvent: {},
      showCancelled: false,
      searchQuery: '',
    });
    useEmailStore.setState({ accounts: [], currentAccountId: null, needsReauth: false });
  });

  it('les quatre boutons de vue rangent la fiche et rendent leur grille', async () => {
    render(<CalendarPanel standalone />);
    await waitFor(() => expect(screen.getByText('Agenda')).toBeInTheDocument());
    await waitFor(() => expect(MARQUEURS.Mois()).toBe(true));

    for (const libelle of ['Semaine', 'Jour', 'Liste', 'Mois']) {
      // État laissé par EventForm.tsx:218 après `api.createEvent`.
      act(() => {
        useCalendarStore.getState().setCurrentEvent('evt-1');
      });
      await waitFor(() => expect(ficheVisible()).toBe(true));

      fireEvent.click(screen.getByRole('button', { name: libelle }));

      await waitFor(() => {
        expect(
          useCalendarStore.getState().currentEventId,
          `« ${libelle} » laisse la fiche ouverte`,
        ).toBeNull();
      });
      expect(ficheVisible(), `« ${libelle} » : la fiche est encore à l'écran`).toBe(false);
      expect(MARQUEURS[libelle](), `« ${libelle} » : la grille n'est pas revenue`).toBe(true);
    }
  });
});
