import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { ActivityResponse, Calendar, CalendarEvent, Contact } from '../../services/api';
import { MeetingAgendaCard, MeetingWorkspaceCanvas } from './MeetingConversationCard';
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
  email: 'camille@example.com', phone: null, notes: 'Contexte réel', tags: [], stage: 'prospect',
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

describe('Rendez-vous 0.40 conversationnel', () => {
  it('affiche uniquement les événements réels et ouvre avec une clé multi-calendrier', () => {
    const onOpenEvent = vi.fn();
    render(<MeetingAgendaCard
      resource={{ status: 'ready', data: workspace, error: null }} onRetry={vi.fn()}
      onOpenEvent={onOpenEvent} onNewEvent={vi.fn()} onOpenClassic={vi.fn()}
    />);
    expect(screen.getByText('Rendez-vous réel')).toBeInTheDocument();
    expect(screen.queryByText(/Claire Fontaine|PROPULSER|4 emails/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByText('Rendez-vous réel'));
    expect(onOpenEvent).toHaveBeenCalledWith(meetingEventKey(event));
  });

  it('exige une confirmation avant la création Agenda', async () => {
    const onCreateEvent = vi.fn().mockResolvedValue(event);
    render(<MeetingWorkspaceCanvas
      resource={{ status: 'ready', data: workspace, error: null }} eventResource={null}
      target="new-event" onRetry={vi.fn()} onRetryEvent={vi.fn()} onCreateEvent={onCreateEvent}
      onCreateNote={vi.fn()} onOpenClassic={vi.fn()}
    />);
    fireEvent.change(screen.getByLabelText('Titre'), { target: { value: 'Point confirmé' } });
    fireEvent.click(screen.getByText('Vérifier avant création'));
    expect(onCreateEvent).not.toHaveBeenCalled();
    expect(screen.getByText(/Agenda local.*local/)).toBeInTheDocument();
    fireEvent.click(screen.getByText('Confirmer la création'));
    await waitFor(() => expect(onCreateEvent).toHaveBeenCalledTimes(1));
  });

  it('montre le contexte sourcé et confirme séparément la note CRM', async () => {
    const onCreateNote = vi.fn().mockResolvedValue(activity);
    render(<MeetingWorkspaceCanvas
      resource={{ status: 'ready', data: workspace, error: null }}
      eventResource={{ status: 'ready', data: context, error: null }} target={meetingEventKey(event)}
      onRetry={vi.fn()} onRetryEvent={vi.fn()} onCreateEvent={vi.fn()}
      onCreateNote={onCreateNote} onOpenClassic={vi.fn()}
    />);
    expect(screen.getByText('Contexte réel')).toBeInTheDocument();
    expect(screen.getByText('Historique réel')).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText('Tes notes factuelles après le rendez-vous…'), { target: { value: 'Note réelle' } });
    fireEvent.click(screen.getByText('Vérifier la note'));
    expect(onCreateNote).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText('Confirmer l’ajout'));
    await waitFor(() => expect(onCreateNote).toHaveBeenCalledWith(meetingEventKey(event), contact.id, 'Note réelle'));
  });
});
