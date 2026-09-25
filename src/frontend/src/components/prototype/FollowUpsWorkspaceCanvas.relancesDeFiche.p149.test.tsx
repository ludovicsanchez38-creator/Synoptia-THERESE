/**
 * P-149 (recette P-146, lot 1 ; acceptée le 25/09) : une relance posée sur
 * une fiche (P-133, `next_follow_up`) n'apparaissait pas dans « Relances et
 * alertes », qui ne lisait que les relances d'e-mail ; elle ne se terminait
 * qu'en vidant le champ de la fiche. Elle y figure, avec un geste « Faite ».
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/follow-ups', () => ({
  listFollowUps: vi.fn().mockResolvedValue([]),
  updateFollowUp: vi.fn(),
  deleteFollowUp: vi.fn(),
}));
const memoire = vi.hoisted(() => ({ listContacts: vi.fn(), updateContact: vi.fn() }));
vi.mock('../../services/api/memory', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  ...memoire,
}));

import { FollowUpsWorkspaceCanvas } from './FollowUpsWorkspaceCanvas';

describe('P-149 : les relances posées sur une fiche', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    memoire.listContacts.mockResolvedValue([
      { id: 'c1', first_name: 'Julien', last_name: 'Garnier', company: null, email: null, next_follow_up: '2026-09-30T00:00:00' },
      { id: 'c2', first_name: 'Nadia', last_name: 'Roux', company: null, email: null, next_follow_up: null },
    ]);
    memoire.updateContact.mockImplementation(async (id: string, data: object) => ({ id, ...data }));
  });

  it('figurent dans le panneau et se terminent d’un geste', async () => {
    render(<FollowUpsWorkspaceCanvas onClose={vi.fn()} onOpenEmail={vi.fn()} />);
    expect(await screen.findByText('Julien Garnier')).toBeInTheDocument();
    expect(screen.queryByText('Nadia Roux')).toBeNull();
    // Le sous-titre ne dit plus « liées aux emails » seulement.
    expect(screen.getByText(/e-mails et des fiches/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Relance faite : Julien Garnier' }));
    await waitFor(() => expect(memoire.updateContact).toHaveBeenCalledWith('c1', { next_follow_up: null }));
    await waitFor(() => expect(screen.queryByText('Julien Garnier')).toBeNull());
  });
});
