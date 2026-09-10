/**
 * Cycle 6, lecteur D62 (EventDetail.tsx) : la corbeille passait par le
 * `confirm()` natif du moteur de rendu. Dans une fenêtre Tauri cette boîte
 * n'est pas garantie (ignorée ou fausse) : le clic ne ferait rien et
 * l'utilisateur conclurait à une panne. Même schéma que le fichier joint de
 * ProjectModal : une confirmation EN LIGNE, fail-closed.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ deleteEvent: vi.fn() }));
vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, deleteEvent: (...a: unknown[]) => api.deleteEvent(...a) };
});

import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';
import { EventDetail } from './EventDetail';

const evenement = {
  id: 'e1', calendar_id: 'cal-1', summary: 'Point client Ruiz', description: null, location: null,
  start_datetime: '2026-09-12T09:00:00Z', end_datetime: '2026-09-12T10:00:00Z', start_date: null, end_date: null,
  all_day: false, attendees: [], recurrence: null, status: 'confirmed', synced_at: '2026-09-10T00:00:00Z',
} as never;

describe('D62 : supprimer un rendez-vous se confirme dans l’application', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.deleteEvent.mockResolvedValue(undefined);
    useCalendarStore.setState({ events: [evenement], currentEventId: 'e1', isEventFormOpen: false, draftEvent: {} });
    useEmailStore.setState({ currentAccountId: null });
  });

  it('le premier clic ne supprime rien et annonce le rendez-vous par son titre', () => {
    render(<EventDetail />);
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer l’événement' }));
    expect(api.deleteEvent).not.toHaveBeenCalled();
    expect(screen.getByText(/Supprimer « Point client Ruiz » \?/)).toBeInTheDocument();
  });

  it('on peut renoncer ; confirmer appelle l’API une fois', async () => {
    render(<EventDetail />);
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer l’événement' }));
    fireEvent.click(screen.getByRole('button', { name: 'Conserver le rendez-vous' }));
    expect(screen.queryByText(/Supprimer « Point client Ruiz » \?/)).toBeNull();
    expect(api.deleteEvent).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Supprimer l’événement' }));
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer définitivement' }));
    await waitFor(() => expect(api.deleteEvent).toHaveBeenCalledTimes(1));
    expect(api.deleteEvent).toHaveBeenCalledWith('e1', 'cal-1', undefined);
  });
});
