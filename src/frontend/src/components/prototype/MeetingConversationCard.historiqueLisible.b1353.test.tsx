/**
 * B-1353 (persona Claire, cycle 13) : l'historique CRM affichait des
 * identifiants internes : « Score: 50 → 85 », « 25/09/2026 · score_change »,
 * « Raison: initial_creation », et « · note » sous chaque note. Le type se lit
 * en français, le changement de score devient une phrase et son motif aussi.
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
  email: 'camille@example.com', phone: null, address: null, notes: 'Contexte réel', tags: [], stage: 'prospect',
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

const recalcul: ActivityResponse = {
  id: 'a-2', contact_id: contact.id, type: 'score_change', title: 'Score: 50 → 85',
  description: 'Raison: initial_creation',
  extra_data: '{"old_score": 50, "new_score": 85, "reason": "initial_creation"}',
  created_at: '2026-09-25T10:00:00Z',
};

describe('historique CRM sans identifiants internes (B-1353)', () => {
  it('le panneau Préparer lit le type et le motif en français', () => {
    render(<MeetingWorkspaceCanvas
      resource={{ status: 'ready', data: workspace, error: null }}
      eventResource={{ status: 'ready', data: { ...context, activities: [activity, recalcul] }, error: null }}
      target={meetingEventKey(event)}
      onRetry={vi.fn()} onRetryEvent={vi.fn()} onCreateEvent={vi.fn()}
      onCreateNote={vi.fn()} onAbandon={vi.fn()} onOpenClassic={vi.fn()} onEnsureCalendar={vi.fn()}
    />);
    const texte = document.body.textContent ?? '';
    for (const brut of ['score_change', 'initial_creation', 'Raison:', 'Score:', '· note']) {
      expect(texte, brut).not.toContain(brut);
    }
    expect(screen.getByText('Score recalculé : 50 → 85')).toBeInTheDocument();
    expect(screen.getByText('Motif : création de la fiche')).toBeInTheDocument();
    expect(texte).toContain('· Note');
  });
});
