/**
 * B-1980 : le dialogue modal porte le même nom que le titre visible.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoicesPanel } from './InvoicesPanel';
import { useInvoiceStore } from '../../stores/invoiceStore';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, listInvoices: vi.fn().mockResolvedValue([]) };
});

describe('B-1980 : nom accessible du panneau', () => {
  beforeEach(() => {
    useInvoiceStore.setState({
      invoices: [],
      currentInvoiceId: null,
      filters: { status: 'all' },
      isInvoicePanelOpen: true,
      draftInvoice: null,
    });
  });

  it('le dialogue s’appelle Devis et factures', async () => {
    render(<InvoicesPanel />);
    expect(await screen.findByRole('dialog', { name: 'Devis et factures' })).toBeInTheDocument();
  });
});
