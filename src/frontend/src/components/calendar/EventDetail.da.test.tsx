/**
 * DA « Application affinée », lot 8 : la fiche d'un rendez-vous
 * (`docs/plans/2026-09-11-da-lot8-agenda-design.md`, § 9).
 * Mêmes données, mêmes états, mêmes destinations.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, deleteEvent: vi.fn() };
});

import { EventDetail } from './EventDetail';

function evenement(statut: string) {
  return {
    id: 'evt-1', calendar_id: 'cal-1', summary: 'Séance 1 · Garage Benali', description: null,
    location: 'sur place', start_datetime: '2026-09-02T09:00:00', end_datetime: '2026-09-02T10:30:00',
    start_date: null, end_date: null, all_day: false, attendees: null, recurrence: null,
    status: statut, synced_at: null,
  } as never;
}

function semer(statut = 'confirmed', currentEventId: string | null = 'evt-1') {
  useCalendarStore.setState({
    events: [evenement(statut)], currentEventId, isEventFormOpen: false, draftEvent: {},
  } as never);
  useEmailStore.setState({ currentAccountId: null } as never);
}

beforeEach(() => {
  vi.clearAllMocks();
  semer();
});

describe('lot 8 : la tête de la fiche', () => {
  it('le titre reste un h3 et le retour range le rendez-vous', () => {
    render(<EventDetail />);
    expect(screen.getByRole('heading', { level: 3, name: 'Séance 1 · Garage Benali' })).toBeInTheDocument();

    const retour = screen.getByRole('button', { name: 'Retour' });
    expect(retour.className).toMatch(/\bh-9\b/);
    expect(retour.className).toMatch(/\bw-9\b/);
    fireEvent.click(retour);
    expect(useCalendarStore.getState().currentEventId).toBeNull();
  });

  it('un identifiant inconnu laisse « Événement introuvable »', () => {
    semer('confirmed', 'evt-absent');
    render(<EventDetail />);
    expect(screen.getByText('Événement introuvable')).toBeInTheDocument();
  });
});

describe('lot 8 : le statut ne se dit que s’il n’est pas confirmé', () => {
  it('un rendez-vous confirmé ne porte aucune étiquette', () => {
    render(<EventDetail />);
    expect(screen.queryByText('Annulé')).toBeNull();
    expect(screen.queryByText('Provisoire')).toBeNull();
  });

  it('« Provisoire » prend le ton d’attention', () => {
    semer('tentative');
    render(<EventDetail />);
    const etiquette = screen.getByText('Provisoire');
    expect(etiquette.getAttribute('data-etiquette')).not.toBeNull();
    expect(etiquette.className).toMatch(/\btext-warning\b/);
  });

  it('« Annulé » prend le ton d’erreur', () => {
    semer('cancelled');
    render(<EventDetail />);
    const etiquette = screen.getByText('Annulé');
    expect(etiquette.getAttribute('data-etiquette')).not.toBeNull();
    expect(etiquette.className).toMatch(/\btext-error\b/);
  });
});

describe('lot 8 : la confirmation de suppression n’est pas une erreur', () => {
  it('elle ne porte pas `role="alert"` et ses deux gestes sont des boutons `md`', () => {
    const { container } = render(<EventDetail />);
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer l’événement' }));

    expect(container.querySelectorAll('[role="alert"]')).toHaveLength(0);
    for (const nom of ['Conserver le rendez-vous', 'Supprimer définitivement']) {
      expect(screen.getByRole('button', { name: nom }).className).toMatch(/\bh-9\b/);
    }
  });

  it('les gestes de la tête restent des boutons en icône', () => {
    render(<EventDetail />);
    for (const nom of ['Modifier l’événement', 'Supprimer l’événement']) {
      const bouton = screen.getByRole('button', { name: nom });
      expect(bouton.className).toMatch(/\bh-9\b/);
      expect(bouton.className).toMatch(/\bw-9\b/);
    }
  });
});
