/**
 * B-236 — l'agenda demandait les événements d'un calendrier qui n'existe pas
 * dans la liste qu'il venait lui-même de recevoir.
 *
 * `calendarStore` persiste `currentCalendarId` sous « calendar-storage » : un
 * poste ayant servi une autre base ramène l'identifiant d'une base morte. Or
 * `calendarsReady` était semé depuis ce cache (`useState(hasCachedCalendars)`),
 * si bien que le chargement des événements partait AVANT la réponse de
 * `loadCalendars`. La réconciliation existe pourtant (`currentStillExists`),
 * mais elle arrivait après : la requête prenait un 400, puis le rechargement
 * propre effaçait l'erreur (`loadEvents` commence par `setError(null)`).
 * L'utilisatrice ne voyait rien, et le message du serveur parlait d'un
 * `account_id` Google sur une base 100 % locale.
 *
 * Le test verrouille l'ORDRE : le tout premier `calendar_id` demandé est celui
 * d'un calendrier réellement rendu par le serveur.
 */
import { act, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    getEmailAuthStatus: vi.fn().mockResolvedValue({ authenticated: false, accounts: [] }),
    listCalendars: vi.fn().mockResolvedValue([
      { id: 'frais-8c9f6db7', provider: 'local', account_id: null, summary: 'Mon calendrier', primary: true },
    ]),
    listEvents: vi.fn().mockResolvedValue([]),
  };
});

import * as api from '../../services/api';
import { CalendarPanel } from './CalendarPanel';

describe('B-236 — aucune requête d’événements avant réconciliation de la liste', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // État rehydraté depuis « calendar-storage » : l'identifiant vient d'une
    // base qui n'existe plus.
    useCalendarStore.setState({
      calendars: [{ id: 'perime-be06b033', provider: 'local', summary: 'Ancien' }] as never,
      currentCalendarId: 'perime-be06b033',
      events: [], currentEventId: null, isEventFormOpen: false, draftEvent: {},
    });
    useEmailStore.setState({ accounts: [], currentAccountId: null, needsReauth: false });
  });

  it('le premier calendar_id demandé est celui d’un calendrier réellement rendu', async () => {
    render(<CalendarPanel standalone />);
    await act(async () => { await Promise.resolve(); });
    await waitFor(() => expect(screen.getByText('Agenda')).toBeInTheDocument());
    await waitFor(() => expect(vi.mocked(api.listEvents)).toHaveBeenCalled());

    const idsDemandes = vi.mocked(api.listEvents).mock.calls.map((appel) => appel[1]);
    expect(idsDemandes[0]).toBe('frais-8c9f6db7');
    expect(idsDemandes).not.toContain('perime-be06b033');
  });
});
