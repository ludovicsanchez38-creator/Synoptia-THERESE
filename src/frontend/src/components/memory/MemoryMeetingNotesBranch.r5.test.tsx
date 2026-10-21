import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { MemoryMeetingNotesBranch } from './MemoryMeetingNotesBranch';
import * as api from '../../services/api/meetingNotes';
import * as contactsApi from '../../services/api/memory';
import { useDemoStore } from '../../stores/demoStore';
vi.mock('../../services/api/meetingNotes', () => ({ listMeetingEvents: vi.fn(), createMeetingNote: vi.fn() }));
vi.mock('../../services/api/memory', () => ({ listContacts: vi.fn().mockResolvedValue([]) }));
vi.mock('../../services/api/crm-extended', () => ({ listActivities: vi.fn().mockResolvedValue([]) }));
beforeEach(() => {
  vi.clearAllMocks(); useDemoStore.setState({ enabled: false });
  vi.mocked(contactsApi.listContacts).mockResolvedValue([]);
  vi.mocked(api.listMeetingEvents).mockResolvedValue([{ id: 'rdv', calendar_id: 'agenda', summary: 'Séance fictive', date: '2026-10-21' }]);
  vi.mocked(api.createMeetingNote).mockResolvedValue({ id: 'note' });
});
it('crée une note sans inventer de contact et impose le rendez-vous', async () => {
  render(<MemoryMeetingNotesBranch />);
  fireEvent.click(screen.getByRole('button', { name: 'Ajouter une note de rendez-vous' }));
  await screen.findByRole('option', { name: /Séance fictive/ });
  expect(screen.getByRole('button', { name: 'Enregistrer la note' })).toBeDisabled();
  fireEvent.change(screen.getByLabelText('Rendez-vous'), { target: { value: 'rdv' } });
  fireEvent.change(screen.getByLabelText('Ta note'), { target: { value: 'Note professionnelle' } });
  fireEvent.click(screen.getByRole('button', { name: 'Enregistrer la note' }));
  await waitFor(() => expect(api.createMeetingNote).toHaveBeenCalledWith({ calendar_event_id: 'rdv', calendar_id: 'agenda', contact_id: null, description: 'Note professionnelle' }));
});
it('ne charge pas les rendez-vous ni les contacts avant le geste et bloque la démo', () => {
  useDemoStore.setState({ enabled: true }); render(<MemoryMeetingNotesBranch />);
  expect(screen.getByRole('button', { name: 'Ajouter une note de rendez-vous' })).toBeDisabled();
  expect(api.listMeetingEvents).not.toHaveBeenCalled();
});

it('permet de choisir un contact au-delà de la première page sans perdre le rendez-vous', async () => {
  vi.mocked(contactsApi.listContacts).mockResolvedValueOnce(Array.from({ length: 200 }, (_, i) => ({ id: String(i), first_name: `Contact ${i}` } as contactsApi.Contact)))
    .mockResolvedValue([{ id: 'ancien', first_name: 'Contact ancien' } as contactsApi.Contact]);
  render(<MemoryMeetingNotesBranch />);
  fireEvent.click(screen.getByRole('button', { name: 'Ajouter une note de rendez-vous' }));
  await screen.findByText('Contact 0', { selector: 'option' });
  fireEvent.change(screen.getByLabelText('Rendez-vous'), { target: { value: 'rdv' } });
  fireEvent.click(screen.getByRole('button', { name: 'Contacts suivants' }));
  await screen.findByText('Contact ancien', { selector: 'option' });
  fireEvent.change(screen.getByLabelText('Contact facultatif'), { target: { value: 'ancien' } });
  fireEvent.change(screen.getByLabelText('Ta note'), { target: { value: 'Note professionnelle' } });
  fireEvent.click(screen.getByRole('button', { name: 'Enregistrer la note' }));
  await waitFor(() => expect(api.createMeetingNote).toHaveBeenCalledWith(expect.objectContaining({ calendar_event_id: 'rdv', contact_id: 'ancien' })));
});
