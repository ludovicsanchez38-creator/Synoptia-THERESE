/**
 * B-388 (05/09/2026) : depuis la liste filtrée « Devis », « Nouveau devis »
 * ouvrait un formulaire de FACTURE : le type courant n'était pas transmis.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/invoices', () => ({
  createInvoice: vi.fn(),
  updateInvoice: vi.fn(),
  getInvoice: vi.fn(),
}));
vi.mock('../../services/api/memory', () => ({
  getContacts: vi.fn(async () => []),
  listContacts: vi.fn(async () => []),
}));
vi.mock('../../stores/billingProfileStore', () => ({
  useBillingProfileStore: (selector: (s: unknown) => unknown) =>
    selector({ refresh: vi.fn(), isComplete: true, missing: [], loaded: true }),
}));

import { InvoiceForm } from './InvoiceForm';

describe('B-388 - le formulaire ouvre le type demandé', () => {
  it('ouvre un devis quand la liste est filtrée sur les devis', async () => {
    render(<InvoiceForm invoice={null} defaultDocumentType="devis" onClose={vi.fn()} onSave={vi.fn()} />);
    expect(await screen.findByText(/Nouveau devis/)).toBeTruthy();
  });
});
