import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ToolConfirmationCard } from './ToolConfirmationCard';
import { useToolConfirmationStore } from '../../stores/toolConfirmationStore';

vi.mock('../../services/api/chat', () => ({
  confirmTool: vi
    .fn()
    .mockResolvedValue({ status: 'executed', tool_name: 'send_email', result: 'Email envoyé' }),
}));
import { confirmTool } from '../../services/api/chat';

describe('ToolConfirmationCard (US-002)', () => {
  beforeEach(() => {
    useToolConfirmationStore.setState({ pending: [] });
    vi.clearAllMocks();
  });

  it("n'affiche rien sans action en attente", () => {
    render(<ToolConfirmationCard />);
    expect(screen.queryByTestId('tool-confirmation')).toBeNull();
  });

  it('affiche le récap et envoie après clic sur Envoyer', async () => {
    useToolConfirmationStore.getState().add({
      confirmation_id: 'a',
      tool_name: 'send_email',
      arguments: { to: 'x@y.fr', subject: 'Sujet', body: 'Corps' },
    });
    render(<ToolConfirmationCard />);

    expect(screen.queryByText('x@y.fr')).toBeTruthy();

    fireEvent.click(screen.getByText('Envoyer'));

    await waitFor(() => expect(confirmTool).toHaveBeenCalledWith('a', true));
    await waitFor(() =>
      expect(useToolConfirmationStore.getState().pending).toHaveLength(0)
    );
  });

  it('annule sans exécuter quand on clique Annuler', async () => {
    useToolConfirmationStore.getState().add({
      confirmation_id: 'b',
      tool_name: 'send_email',
      arguments: { to: 'z@y.fr', subject: 'S', body: 'B' },
    });
    render(<ToolConfirmationCard />);

    fireEvent.click(screen.getByText('Annuler'));

    await waitFor(() => expect(confirmTool).toHaveBeenCalledWith('b', false));
    await waitFor(() =>
      expect(useToolConfirmationStore.getState().pending).toHaveLength(0)
    );
  });

  it('affiche la destination et confirme une création Agenda', async () => {
    useToolConfirmationStore.getState().add({
      confirmation_id: 'rdv-1',
      tool_name: 'create_calendar_event',
      arguments: {
        summary: 'Point projet',
        start: '2026-07-14T10:00:00',
        end: '2026-07-14T11:00:00',
        timezone: 'Europe/Paris',
        attendees: 'client@example.com',
        _confirmation_destination: {
          calendar_name: 'Synoptïa', provider: 'google', account: 'ludo@example.com',
        },
      },
    });
    render(<ToolConfirmationCard />);

    expect(screen.getByText('Confirmer la création du rendez-vous')).toBeTruthy();
    expect(screen.getByText('Google Calendar')).toBeTruthy();
    expect(screen.getByText('ludo@example.com')).toBeTruthy();
    expect(screen.getByText('client@example.com')).toBeTruthy();
    fireEvent.click(screen.getByText('Créer'));

    await waitFor(() => expect(confirmTool).toHaveBeenCalledWith('rdv-1', true));
  });
});
