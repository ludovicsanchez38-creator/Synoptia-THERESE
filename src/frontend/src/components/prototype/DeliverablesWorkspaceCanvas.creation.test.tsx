/** P-048 (Sophie sophie-07, B-635 ; accepté par Ludo le 08/09) : créer un livrable et changer son statut depuis « Livrables et suivi client ». */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { useState } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { DeliverableResponse } from '../../services/api/crm-extended';

const api = vi.hoisted(() => ({ createDeliverable: vi.fn(), updateDeliverable: vi.fn() }));
vi.mock('../../services/api/crm-extended', () => api);

const etat = vi.hoisted(() => ({ livrables: [] as DeliverableResponse[] }));

vi.mock('./usePrototypeDeliverablesData', () => ({
  usePrototypeDeliverablesProjects: () => ({
    resource: { status: 'ready', data: [{ id: 'p1', name: 'Site vitrine', contact_id: null, status: 'active' }], error: null },
    refresh: vi.fn(),
    limitReached: false,
  }),
  usePrototypeDeliverableProjectData: () => {
    const [livrables, setLivrables] = useState<DeliverableResponse[]>(etat.livrables);
    return {
      data: {
        projectId: 'p1',
        contact: { status: 'ready', data: null, error: null },
        deliverables: { status: 'ready', data: livrables, error: null },
        invoices: { status: 'ready', data: [], error: null },
        tasks: { status: 'ready', data: [], error: null },
      },
      refresh: vi.fn(),
      appliquerLivrable: (_projectId: string, livrable: DeliverableResponse) =>
        setLivrables((courant) => (courant.some((c) => c.id === livrable.id) ? courant.map((c) => (c.id === livrable.id ? livrable : c)) : [livrable, ...courant])),
    };
  },
}));
vi.mock('./BoutonOuvrirLaVue', () => ({
  BoutonOuvrirLaVue: ({ onClick, children }: { onClick: () => void; children?: React.ReactNode }) => (
    <button type="button" onClick={onClick}>{children ?? 'Ouvrir'}</button>
  ),
}));

import { DeliverablesWorkspaceCanvas } from './DeliverablesWorkspaceCanvas';

const livrable = (surcharges: Partial<DeliverableResponse>): DeliverableResponse => ({
  id: 'l1', project_id: 'p1', title: 'Maquette', description: null, status: 'a_faire', due_date: null, completed_at: null,
  created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z', ...surcharges,
} as DeliverableResponse);

function renderCanevas() {
  return render(<DeliverablesWorkspaceCanvas onClose={vi.fn()} onOpenProjects={vi.fn()} onOpenInvoices={vi.fn()} />);
}

describe('Livrables : création et statut (P-048)', () => {
  beforeEach(() => {
    api.createDeliverable.mockReset();
    api.updateDeliverable.mockReset();
    etat.livrables = [];
  });

  it('« Ajouter un livrable » ouvre un formulaire ; un titre vide ne part pas ; un titre part avec le projet et le statut par défaut', async () => {
    api.createDeliverable.mockResolvedValue(livrable({ id: 'l-nouveau', title: 'Maquette' }));
    renderCanevas();
    fireEvent.click(await screen.findByRole('button', { name: 'Ajouter un livrable' }));
    const formulaire = screen.getByRole('form', { name: 'Nouveau livrable' });
    fireEvent.submit(formulaire);
    expect(api.createDeliverable).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText('Titre'), { target: { value: '  Maquette ' } });
    fireEvent.submit(formulaire);
    await waitFor(() => expect(api.createDeliverable).toHaveBeenCalledWith({ project_id: 'p1', title: 'Maquette', status: 'a_faire' }));
    expect(await screen.findByRole('status')).toHaveTextContent('Livrable « Maquette » ajouté.');
    expect(screen.getByRole('heading', { name: 'Maquette' })).toBeInTheDocument();
    expect(screen.queryByText(/ajoute le premier/)).toBeNull();
  });

  it('un échec de création s’affiche dans le formulaire, qui garde la saisie', async () => {
    api.createDeliverable.mockRejectedValue(new Error('Le titre du livrable ne peut pas être vide'));
    renderCanevas();
    fireEvent.click(await screen.findByRole('button', { name: 'Ajouter un livrable' }));
    fireEvent.change(screen.getByLabelText('Titre'), { target: { value: 'Maquette' } });
    fireEvent.submit(screen.getByRole('form', { name: 'Nouveau livrable' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Le titre du livrable ne peut pas être vide');
    expect(screen.getByLabelText('Titre')).toHaveValue('Maquette');
  });

  it('changer le statut d’une ligne appelle l’API avec le bon identifiant et prend le DTO renvoyé', async () => {
    etat.livrables = [livrable({ id: 'l1', title: 'Maquette', status: 'a_faire' })];
    let resoudre: (v: DeliverableResponse) => void = () => {};
    api.updateDeliverable.mockImplementation(() => new Promise<DeliverableResponse>((resolve) => { resoudre = resolve; }));
    renderCanevas();
    const selecteur = await screen.findByLabelText('Statut de Maquette');
    fireEvent.change(selecteur, { target: { value: 'en_cours' } });
    expect(api.updateDeliverable).toHaveBeenCalledWith('l1', { status: 'en_cours' });
    expect(selecteur).toBeDisabled();
    resoudre(livrable({ id: 'l1', title: 'Maquette', status: 'en_cours' }));
    await waitFor(() => expect(screen.getByLabelText('Statut de Maquette')).toHaveValue('en_cours'));
    expect(screen.getByLabelText('Statut de Maquette')).not.toBeDisabled();
  });

  it('un échec de changement de statut laisse la ligne telle quelle et le dit', async () => {
    etat.livrables = [livrable({ id: 'l1', title: 'Maquette', status: 'a_faire' })];
    api.updateDeliverable.mockRejectedValue(new Error('Statut inconnu'));
    renderCanevas();
    const selecteur = await screen.findByLabelText('Statut de Maquette');
    fireEvent.change(selecteur, { target: { value: 'valide' } });
    expect(await screen.findByRole('alert')).toHaveTextContent('Statut inconnu');
    expect(screen.getByLabelText('Statut de Maquette')).toHaveValue('a_faire');
  });

  it('un statut existant inconnu reste affiché et proposé tel quel', async () => {
    etat.livrables = [livrable({ id: 'l2', title: 'Ancien', status: 'livre' })];
    renderCanevas();
    const selecteur = await screen.findByLabelText('Statut de Ancien');
    expect(selecteur).toHaveValue('livre');
    expect(screen.getByRole('option', { name: 'livre' })).toBeInTheDocument();
  });
});
