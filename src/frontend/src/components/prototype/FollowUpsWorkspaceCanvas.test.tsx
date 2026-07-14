import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { FollowUpsWorkspaceCanvas } from './FollowUpsWorkspaceCanvas';
import { deleteFollowUp, listFollowUps, updateFollowUp } from '../../services/api/follow-ups';

vi.mock('../../services/api/follow-ups', () => ({
  listFollowUps: vi.fn(),
  updateFollowUp: vi.fn(),
  deleteFollowUp: vi.fn(),
}));

const followUp = {
  id: 'follow-up-1',
  email_message_id: 'message-1',
  contact_id: null,
  due_date: '2026-07-16T09:00:00',
  note: 'Relancer pour la proposition',
  status: 'pending' as const,
  created_at: '2026-07-14T09:00:00',
  email_subject: 'Proposition à valider',
  email_from: 'Camille Martin',
  contact_name: null,
};

describe('FollowUpsWorkspaceCanvas', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(listFollowUps).mockResolvedValue([followUp]);
    vi.mocked(updateFollowUp).mockImplementation(async (_id, update) => ({ ...followUp, ...update }));
    vi.mocked(deleteFollowUp).mockResolvedValue({ deleted: true, id: followUp.id });
  });

  it('charge, termine, modifie et supprime une relance réelle', async () => {
    render(<FollowUpsWorkspaceCanvas onClose={vi.fn()} onOpenEmail={vi.fn()} />);

    expect(await screen.findByText('Proposition à valider')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Terminer Proposition à valider' }));
    await waitFor(() => expect(updateFollowUp).toHaveBeenCalledWith(followUp.id, { status: 'done' }));

    fireEvent.click(screen.getByRole('button', { name: 'Toutes' }));
    fireEvent.click(screen.getByRole('button', { name: 'Modifier Proposition à valider' }));
    fireEvent.change(screen.getByLabelText('Nouvelle échéance'), { target: { value: '2026-07-20' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));
    await waitFor(() => expect(updateFollowUp).toHaveBeenLastCalledWith(
      followUp.id,
      expect.objectContaining({ due_date: '2026-07-20T09:00:00' }),
    ));

    fireEvent.click(screen.getByRole('button', { name: 'Supprimer Proposition à valider' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer' }));
    await waitFor(() => expect(deleteFollowUp).toHaveBeenCalledWith(followUp.id));
    expect(screen.queryByText('Proposition à valider')).not.toBeInTheDocument();
  });
});
