/**
 * P-117 (persona Claire, cycle 13) : « Écrire » ouvrait un brouillon
 * d'e-mail, pas un document ; et l'action d'après séance (« Ajouter une note
 * de rendez-vous ») était la dernière section de la préparation, trouvée par
 * hasard après deux fausses pistes. Le verbe dit ce qu'il ouvre, et pour une
 * séance passée le compte rendu vient en premier, sous un nom qui le dit.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Calendar, CalendarEvent, Contact } from '../../services/api';
import { ACTIONS_ETABLI } from '../../lib/etabli';
import { MeetingWorkspaceCanvas } from './MeetingConversationCard';
import { meetingEventKey, type MeetingEventContext, type MeetingWorkspaceData } from './usePrototypeMeetingData';

const calendar: Calendar = {
  id: 'cal-1', account_id: null, summary: 'Agenda local', description: null,
  timezone: 'Europe/Paris', primary: true, provider: 'local', synced_at: null,
};
function seance(debut: Date): CalendarEvent {
  const fin = new Date(debut.getTime() + 3_600_000);
  return {
    id: 'event-1', calendar_id: calendar.id, summary: 'Séance Hélène', description: 'Objectif',
    location: 'Manosque', start_datetime: debut.toISOString(), end_datetime: fin.toISOString(),
    start_date: null, end_date: null, all_day: false, attendees: ['helene@example.com'],
    recurrence: null, status: 'confirmed', synced_at: '2026-09-25T08:00:00Z',
  };
}
const contact: Contact = {
  id: 'contact-1', first_name: 'Hélène', last_name: 'Ménard', company: null,
  email: 'helene@example.com', phone: null, address: null, notes: null, tags: [], stage: 'prospect',
  score: 0, source: 'local', last_interaction: null, created_at: '2026-07-01', updated_at: '2026-07-12',
};

function rendre(event: CalendarEvent) {
  const workspace: MeetingWorkspaceData = { calendars: [calendar], events: [event], contacts: [contact], accounts: [], unavailableSources: [] };
  const context: MeetingEventContext = { event, relatedContacts: [contact], activities: [], unavailableSources: [] };
  render(<MeetingWorkspaceCanvas
    resource={{ status: 'ready', data: workspace, error: null }}
    eventResource={{ status: 'ready', data: context, error: null }}
    target={meetingEventKey(event)}
    onRetry={vi.fn()} onRetryEvent={vi.fn()} onCreateEvent={vi.fn()}
    onCreateNote={vi.fn()} onAbandon={vi.fn()} onOpenClassic={vi.fn()} onEnsureCalendar={vi.fn()}
  />);
}

function ordreDesSections(): string[] {
  const titres = ['Après la séance : compte rendu', 'Points à vérifier'];
  const texte = document.body.textContent ?? '';
  return titres.filter((t) => texte.includes(t)).sort((a, b) => texte.indexOf(a) - texte.indexOf(b));
}

describe('P-117 : le verbe dit ce qu’il ouvre, le compte rendu se trouve', () => {
  it('le premier verbe de l’établi est « Écrire un e-mail »', () => {
    expect(ACTIONS_ETABLI.find((a) => a.id === 'email')?.label).toBe('Écrire un e-mail');
  });

  it('séance passée : « Après la séance : compte rendu » vient en premier', () => {
    rendre(seance(new Date(Date.now() - 2 * 3_600_000)));
    expect(screen.getByRole('heading', { name: 'Après la séance : compte rendu' })).toBeInTheDocument();
    expect(ordreDesSections()).toEqual(['Après la séance : compte rendu', 'Points à vérifier']);
  });

  it('séance à venir : la préparation reste en premier', () => {
    rendre(seance(new Date(Date.now() + 24 * 3_600_000)));
    expect(ordreDesSections()).toEqual(['Points à vérifier', 'Après la séance : compte rendu']);
  });
});
