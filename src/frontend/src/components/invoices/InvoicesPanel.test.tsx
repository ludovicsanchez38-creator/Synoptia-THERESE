import React from 'react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { InvoicesPanel } from './InvoicesPanel';
import { useInvoiceStore } from '../../stores/invoiceStore';
import { open as openLocalFile } from '@tauri-apps/plugin-shell';

const mockListInvoices = vi.fn();
const mockDeleteInvoice = vi.fn();
const mockGenerateInvoicePDF = vi.fn();

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');

  return {
    ...actual,
    listInvoices: (...args: unknown[]) => mockListInvoices(...args),
    deleteInvoice: (...args: unknown[]) => mockDeleteInvoice(...args),
    generateInvoicePDF: (...args: unknown[]) => mockGenerateInvoicePDF(...args),
    sendInvoiceByEmail: vi.fn(),
  };
});

vi.mock('./InvoiceForm', () => ({
  InvoiceForm: () => <div data-testid="invoice-form" />,
}));

const invoice = {
  id: 'inv-1',
  invoice_number: 'FAC-001',
  contact_id: 'contact-1',
  currency: 'EUR',
  issue_date: '2026-03-14T00:00:00Z',
  due_date: '2026-03-31T00:00:00Z',
  status: 'draft' as const,
  subtotal_ht: 100,
  total_tax: 20,
  total_ttc: 120,
  notes: null,
  payment_date: null,
  created_at: '2026-03-14T00:00:00Z',
  updated_at: '2026-03-14T00:00:00Z',
  lines: [],
};

describe('InvoicesPanel suppression', () => {
  const onSubmit = vi.fn((event: React.FormEvent) => event.preventDefault());

  beforeEach(() => {
    vi.clearAllMocks();
    onSubmit.mockClear();
    mockListInvoices.mockResolvedValue([invoice]);
    mockDeleteInvoice.mockResolvedValue({ success: true });
    mockGenerateInvoicePDF.mockResolvedValue({
      pdf_path: '/tmp/FAC-001.pdf',
      invoice_number: 'FAC-001',
    });
    vi.mocked(openLocalFile).mockResolvedValue(undefined);

    useInvoiceStore.setState({
      invoices: [],
      currentInvoiceId: null,
      filters: { status: 'all' },
      isInvoicePanelOpen: true,
      draftInvoice: null,
    });
  });

  it('n appelle pas l API de suppression avant la confirmation explicite', async () => {
    render(<InvoicesPanel standalone />);

    await screen.findByText('FAC-001');

    fireEvent.click(screen.getByTitle('Supprimer'));

    expect(await screen.findByRole('dialog', { name: 'Confirmer la suppression' })).toBeInTheDocument();
    expect(mockDeleteInvoice).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));

    await waitFor(() => {
      expect(screen.queryByRole('dialog', { name: 'Confirmer la suppression' })).not.toBeInTheDocument();
    });
    expect(mockDeleteInvoice).not.toHaveBeenCalled();
  });

  it('supprime seulement après clic sur confirmer', async () => {
    render(<InvoicesPanel standalone />);

    await screen.findByText('FAC-001');
    fireEvent.click(screen.getByTitle('Supprimer'));
    const dialog = await screen.findByRole('dialog', { name: 'Confirmer la suppression' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Supprimer' }));

    await waitFor(() => {
      expect(mockDeleteInvoice).toHaveBeenCalledWith('inv-1');
    });
  });

  it('ne soumet pas un formulaire parent avant confirmation explicite', async () => {
    render(
      <form onSubmit={onSubmit}>
        <InvoicesPanel standalone />
      </form>
    );

    await screen.findByText('FAC-001');

    fireEvent.click(screen.getByTitle('Supprimer'));

    expect(await screen.findByRole('dialog', { name: 'Confirmer la suppression' })).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
    expect(mockDeleteInvoice).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));

    await waitFor(() => {
      expect(screen.queryByRole('dialog', { name: 'Confirmer la suppression' })).not.toBeInTheDocument();
    });
    expect(onSubmit).not.toHaveBeenCalled();
    expect(mockDeleteInvoice).not.toHaveBeenCalled();
  });

  it('génère puis ouvre réellement le PDF local', async () => {
    render(<InvoicesPanel standalone />);

    await screen.findByText('FAC-001');
    fireEvent.click(screen.getByTitle('Générer et ouvrir le PDF'));

    await waitFor(() => {
      expect(mockGenerateInvoicePDF).toHaveBeenCalledWith('inv-1');
      expect(openLocalFile).toHaveBeenCalledWith('/tmp/FAC-001.pdf');
    });
  });

  it('ne présente pas un envoi email que le backend ne sait pas encore exécuter', async () => {
    render(<InvoicesPanel standalone />);

    await screen.findByText('FAC-001');
    expect(screen.queryByTitle('Envoyer par email')).not.toBeInTheDocument();
  });
});
