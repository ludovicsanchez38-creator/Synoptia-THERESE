/**
 * B-1534 (revue du diff P-132b, constat 6) : la carte d'un rendez-vous
 * affichait l'étape brute du contact (« lost », « discovery ») à côté de son
 * entreprise, là où la carte des contacts passe par libelleDEtape.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { ActivityResponse, Calendar, CalendarEvent, Contact } from '../../services/api';
import { MeetingWorkspaceCanvas } from './MeetingConversationCard';
import { meetingEventKey, type MeetingEventContext, type MeetingWorkspaceData } from './usePrototypeMeetingData';

const calendar: Calendar = {
  id: 'cal-1', account_id: null, summary: 'Agenda local', description: null,
  timezone: 'Europe/Paris', primary: true, provider: 'local', synced_at: null,
};
const event: CalendarEvent = {
  id: 'event-1', calendar_id: calendar.id, summary: 'Rendez-vous réel', description: 'Objectif réel',
  location: 'Manosque', start_datetime: '2026-07-14T10:00:00', end_datetime: '2026-07-14T11:00:00',
  start_date: null, end_date: null, all_day: false, attendees: ['camille@example.com'],
  recurrence: null, status: 'confirmed', synced_at: '2026-07-13T10:00:00Z',
};
const contact: Contact = {
  id: 'contact-1', first_name: 'Camille', last_name: 'Martin', company: 'Cliente',
  email: 'camille@example.com', phone: null, address: null, notes: 'Contexte réel', tags: [], stage: 'lost',
  score: 0, source: 'local', last_interaction: null, created_at: '2026-07-01', updated_at: '2026-07-12',
};
const activity: ActivityResponse = {
  id: 'a-1', contact_id: contact.id, type: 'note', title: 'Historique réel',
  description: 'Détail réel', extra_data: null, created_at: '2026-07-12T10:00:00Z',
};
const workspace: MeetingWorkspaceData = {
  calendars: [calendar], events: [event], contacts: [contact], accounts: [], unavailableSources: [],
};
const context: MeetingEventContext = {
  event, relatedContacts: [contact], activities: [activity], unavailableSources: [],
};

describe('étape du contact lue en français sur la carte de rendez-vous (B-1534)', () => {
  it('affiche « Perdu », jamais l’identifiant « lost »', () => {
    render(<MeetingWorkspaceCanvas
      resource={{ status: 'ready', data: workspace, error: null }}
      eventResource={{ status: 'ready', data: context, error: null }}
      target={meetingEventKey(event)}
      onRetry={vi.fn()} onRetryEvent={vi.fn()} onCreateEvent={vi.fn()}
      onCreateNote={vi.fn()} onAbandon={vi.fn()} onOpenClassic={vi.fn()} onEnsureCalendar={vi.fn()}
    />);
    expect(screen.getAllByText('Cliente · Perdu · camille@example.com').length).toBeGreaterThan(0);
    expect(document.body.textContent ?? '').not.toMatch(/·\s*lost\b/);
  });
});
