/**
 * B-1942 : un point manquant (objectif, lieu, participants) est dessiné avec
 * une coche, seulement recolorée. L’icône dit le contraire de la phrase.
 * Le même écran réserve la coche au cas où tout est renseigné.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Calendar, CalendarEvent, Contact } from '../../services/api';
import { MeetingWorkspaceCanvas } from './MeetingConversationCard';
import { meetingEventKey, type MeetingEventContext, type MeetingWorkspaceData } from './usePrototypeMeetingData';

const calendar: Calendar = {
  id: 'cal-1', account_id: null, summary: 'Agenda local', description: null,
  timezone: 'Europe/Paris', primary: true, provider: 'local', synced_at: null,
};

function evenement(partiel: Partial<CalendarEvent>): CalendarEvent {
  return {
    id: 'event-1', calendar_id: calendar.id, summary: 'Point client',
    description: 'Ordre du jour', location: 'Manosque',
    start_datetime: '2026-12-01T09:00:00.000Z', end_datetime: '2026-12-01T10:00:00.000Z',
    start_date: null, end_date: null, all_day: false, attendees: ['helene@example.com'],
    recurrence: null, status: 'confirmed', synced_at: '2026-11-01T08:00:00Z',
    ...partiel,
  };
}

const contact: Contact = {
  id: 'contact-1', first_name: 'Hélène', last_name: 'Ménard', company: null,
  email: 'helene@example.com', phone: null, address: null, notes: null, tags: [], stage: 'prospect',
  score: 0, source: 'local', last_interaction: null, created_at: '2026-07-01', updated_at: '2026-07-12',
};

function rendre(event: CalendarEvent, avecContact = false) {
  const workspace: MeetingWorkspaceData = {
    calendars: [calendar], events: [event], contacts: avecContact ? [contact] : [], accounts: [], unavailableSources: [],
  };
  const context: MeetingEventContext = {
    event, relatedContacts: avecContact ? [contact] : [], activities: [], unavailableSources: [],
  };
  render(
    <MeetingWorkspaceCanvas
      resource={{ status: 'ready', data: workspace, error: null }}
      eventResource={{ status: 'ready', data: context, error: null }}
      target={meetingEventKey(event)}
      onRetry={vi.fn()} onRetryEvent={vi.fn()} onCreateEvent={vi.fn()}
      onCreateNote={vi.fn()} onAbandon={vi.fn()} onOpenClassic={vi.fn()} onEnsureCalendar={vi.fn()}
    />,
  );
}

function iconeDe(texte: string): SVGElement {
  const ligne = screen.getByText(texte).closest('div');
  const svg = ligne?.querySelector('svg');
  if (!svg) throw new Error(`pas d’icône pour « ${texte} »`);
  return svg;
}

describe('B-1942 : un point manquant n’a pas une coche', () => {
  it('objectif, lieu et participants absents portent une alerte', () => {
    rendre(evenement({ description: null, location: null, attendees: [] }));

    for (const texte of [
      'Objectif ou ordre du jour non renseigné',
      'Lieu ou lien de connexion non renseigné',
      'Aucun participant renseigné',
    ]) {
      const icone = iconeDe(texte);
      expect(icone).toHaveClass('lucide-circle-alert');
      expect(icone).not.toHaveClass('lucide-circle-check');
    }
  });

  it('quand tout est renseigné, la ligne porte une coche', () => {
    rendre(evenement({}), true);
    const icone = iconeDe('L’événement contient une date, un contexte et au moins un participant.');
    expect(icone).toHaveClass('lucide-circle-check');
  });
});
