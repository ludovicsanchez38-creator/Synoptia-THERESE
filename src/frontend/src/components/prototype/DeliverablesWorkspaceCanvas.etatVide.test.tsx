/**
 * B-635 (persona Sophie, c4) : la vue « Livrables et suivi client » affichait
 * cinq filtres de statut et trois compteurs pour un projet sans aucun
 * livrable, sans dire que la création n'existe pas encore dans l'interface
 * (createDeliverable n'a aucun appelant). Sans livrable : pas de filtres, et
 * un état vide honnête. La création elle-même est au portail humain (P-048).
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { DeliverableResponse } from '../../services/api/crm-extended';

const etat = vi.hoisted(() => ({ livrables: [] as DeliverableResponse[] }));

vi.mock('./usePrototypeDeliverablesData', () => ({
  usePrototypeDeliverablesProjects: () => ({
    resource: {
      status: 'ready',
      data: [{ id: 'p1', name: 'Site vitrine', contact_id: null, status: 'active' }],
      error: null,
    },
    refresh: vi.fn(),
    limitReached: false,
  }),
  usePrototypeDeliverableProjectData: () => ({
    data: {
      projectId: 'p1',
      contact: { status: 'ready', data: null, error: null },
      deliverables: { status: 'ready', data: etat.livrables, error: null },
      invoices: { status: 'ready', data: [], error: null },
      tasks: { status: 'ready', data: [], error: null },
    },
    refresh: vi.fn(),
  }),
}));
vi.mock('./BoutonOuvrirLaVue', () => ({
  BoutonOuvrirLaVue: ({ onClick, children }: { onClick: () => void; children?: React.ReactNode }) => (
    <button type="button" onClick={onClick}>{children ?? 'Ouvrir'}</button>
  ),
}));

import { DeliverablesWorkspaceCanvas } from './DeliverablesWorkspaceCanvas';

function renderCanevas() {
  return render(
    <DeliverablesWorkspaceCanvas onClose={vi.fn()} onOpenProjects={vi.fn()} onOpenInvoices={vi.fn()} />
  );
}

describe('B-635 : un projet sans livrable ne propose pas de filtres et dit ce qui manque', () => {
  it('sans livrable : aucun filtre de statut, un état vide qui annonce l’absence de création', () => {
    etat.livrables = [];
    renderCanevas();
    expect(screen.queryByRole('toolbar', { name: 'Filtrer les livrables' })).toBeNull();
    const vide = screen.getByText(/Aucun livrable/);
    expect(vide).toHaveTextContent(/pas encore possible depuis l’interface|pas encore possible depuis l'interface/i);
  });

  it('avec au moins un livrable : les filtres de statut reviennent', () => {
    etat.livrables = [
      {
        id: 'l1',
        project_id: 'p1',
        title: 'Maquette',
        description: null,
        status: 'en_cours',
        due_date: null,
        created_at: '2026-09-01T00:00:00Z',
        updated_at: '2026-09-01T00:00:00Z',
      } as unknown as DeliverableResponse,
    ];
    renderCanevas();
    expect(screen.getByRole('toolbar', { name: 'Filtrer les livrables' })).toBeInTheDocument();
    expect(screen.getByText('Maquette')).toBeInTheDocument();
  });
});
