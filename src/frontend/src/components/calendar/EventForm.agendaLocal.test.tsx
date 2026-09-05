/**
 * B-573 (05/09/2026) : l'aperçu promettait « Les invitations ne partiront
 * qu'après ta confirmation » même sur un agenda local, qui ne sait pas en
 * envoyer. Le message dit ce que l'agenda fait vraiment des participants.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';
import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';
import { EventForm } from './EventForm';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, createEvent: vi.fn(), updateEvent: vi.fn() };
});

describe('EventForm : participants sur un agenda local (B-573)', () => {
  beforeEach(() => {
    useCalendarStore.setState({
      calendars: [{ id: 'local-1', account_id: null, summary: 'Mon calendrier', description: null, timezone: 'Europe/Paris', primary: true, provider: 'local', synced_at: null }],
      currentCalendarId: 'local-1', currentEventId: null, events: [], isEventFormOpen: true, draftEvent: {},
    });
    useEmailStore.setState({ currentAccountId: null });
  });

  it('l’aperçu ne promet pas d’invitation et dit que les participants sont seulement enregistrés', async () => {
    render(<PrototypeExternalActionConfirmationProvider><EventForm /></PrototypeExternalActionConfirmationProvider>);
    fireEvent.change(screen.getByPlaceholderText("Titre de l'événement"), { target: { value: 'Point projet' } });
    fireEvent.change(screen.getByLabelText(/Participants/i), { target: { value: 'invite@example.fr' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    const apercu = await screen.findByTestId('external-action-confirmation');
    expect(apercu).not.toHaveTextContent('Les invitations ne partiront');
    expect(apercu).toHaveTextContent('ne peut pas leur envoyer d’invitation');
  });

  it('le bouton de retour du formulaire porte un nom (B-578)', () => {
    render(<PrototypeExternalActionConfirmationProvider><EventForm /></PrototypeExternalActionConfirmationProvider>);
    expect(screen.getByRole('button', { name: 'Retour' })).toBeInTheDocument();
  });
});
