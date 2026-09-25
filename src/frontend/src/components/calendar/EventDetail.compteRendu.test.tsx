/**
 * P-117 (persona Claire, cycle 13) : la note d'après séance ne se trouvait
 * que dans la préparation d'un rendez-vous, par l'Accueil. Depuis la séance
 * elle-même, dans l'Agenda, un bouton y mène : « Compte rendu de la séance »
 * quand elle est passée, « Préparer la séance » avant. Il demande à la coque
 * d'ouvrir le parcours sur CETTE séance (l'événement voyage avec la demande :
 * une séance passée n'est pas dans la liste que charge la préparation).
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';
import { EventDetail } from './EventDetail';

function seance(decalageHeures: number) {
  const debut = new Date(Date.now() + decalageHeures * 3_600_000);
  return {
    id: 'e1', calendar_id: 'cal-1', summary: 'Séance Hélène', description: null, location: null,
    start_datetime: debut.toISOString(), end_datetime: new Date(debut.getTime() + 3_600_000).toISOString(),
    start_date: null, end_date: null, all_day: false, attendees: [], recurrence: null,
    status: 'confirmed', synced_at: '2026-09-10T00:00:00Z',
  } as never;
}

const recu = vi.fn();
const ecouter = (e: Event) => recu((e as CustomEvent).detail);

describe('P-117 : depuis l’Agenda, la séance mène à sa préparation ou à son compte rendu', () => {
  beforeEach(() => {
    recu.mockClear();
    window.addEventListener('therese:preparer-seance', ecouter);
    useEmailStore.setState({ currentAccountId: null });
  });
  afterEach(() => window.removeEventListener('therese:preparer-seance', ecouter));

  it('séance passée : « Compte rendu de la séance » demande le parcours sur cette séance', () => {
    const passee = seance(-3);
    useCalendarStore.setState({ events: [passee], currentEventId: 'e1', isEventFormOpen: false, draftEvent: {} });
    render(<EventDetail />);

    fireEvent.click(screen.getByRole('button', { name: 'Compte rendu de la séance' }));

    expect(recu).toHaveBeenCalledWith({ evenement: passee });
  });

  it('séance à venir : « Préparer la séance »', () => {
    useCalendarStore.setState({ events: [seance(24)], currentEventId: 'e1', isEventFormOpen: false, draftEvent: {} });
    render(<EventDetail />);

    expect(screen.getByRole('button', { name: 'Préparer la séance' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Compte rendu de la séance' })).toBeNull();
  });
});
