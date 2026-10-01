/**
 * B-1615 : la facturation affichée dans les livrables ne montre pas le jeton PROV-.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('./usePrototypeDeliverablesData', () => ({
  usePrototypeDeliverablesProjects: () => ({
    resource: {
      status: 'ready',
      data: [{ id: 'p1', name: 'Site vitrine', contact_id: 'c1', status: 'active' }],
      error: null,
    },
    refresh: vi.fn(),
    limitReached: false,
  }),
  usePrototypeDeliverableProjectData: () => ({
    data: {
      projectId: 'p1',
      contact: {
        status: 'ready',
        data: { id: 'c1', first_name: 'Claire', last_name: 'Roux', company: null },
        error: null,
      },
      deliverables: { status: 'ready', data: [], error: null },
      invoices: {
        status: 'ready',
        data: [{
          id: 'inv-prov',
          invoice_number: 'PROV-abc123',
          document_type: 'facture',
          status: 'draft',
          total_ttc: 120,
          currency: 'EUR',
          issue_date: '2026-09-29T00:00:00Z',
        }],
        error: null,
      },
      tasks: { status: 'ready', data: [], error: null },
    },
    refresh: vi.fn(),
    appliquerLivrable: vi.fn(),
  }),
}));

vi.mock('./BoutonOuvrirLaVue', () => ({
  BoutonOuvrirLaVue: () => <button type="button">Ouvrir</button>,
}));

import { DeliverablesWorkspaceCanvas } from './DeliverablesWorkspaceCanvas';

describe('B-1615 : livrables, numéro provisoire masqué', () => {
  it('la facture du contact ne montre pas le jeton PROV-', async () => {
    render(<DeliverablesWorkspaceCanvas onClose={vi.fn()} onOpenProjects={vi.fn()} onOpenInvoices={vi.fn()} />);
    expect(await screen.findByText(/Brouillon, numéro à l'émission/)).toBeInTheDocument();
    expect(screen.queryByText(/PROV-abc123/)).not.toBeInTheDocument();
  });
});
