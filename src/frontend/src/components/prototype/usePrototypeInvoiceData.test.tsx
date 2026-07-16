import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../services/api')>();
  return {
    ...actual,
    createContact: vi.fn(),
    createInvoice: vi.fn(),
    getBillingProfileStatus: vi.fn(),
    getInvoice: vi.fn(),
    listContacts: vi.fn(),
    listInvoices: vi.fn(),
  };
});

import {
  createContact,
  createInvoice,
  getBillingProfileStatus,
  getInvoice,
  listContacts,
  listInvoices,
  type Contact,
  type Invoice,
} from '../../services/api';
import { useInvoiceStore } from '../../stores/invoiceStore';
import { useContactsStore } from '../../stores/contactsStore';
import { usePrototypeInvoiceData } from './usePrototypeInvoiceData';

const contact: Contact = {
  id: 'contact-1', first_name: 'Camille', last_name: 'Martin', company: null,
  email: 'camille@example.test', phone: null, notes: null, tags: [], stage: 'client', score: 0,
  source: 'local', last_interaction: null, created_at: '2026-07-01', updated_at: '2026-07-12',
};

const invoice: Invoice = {
  id: 'invoice-1', invoice_number: 'DEV-2026-014', contact_id: contact.id,
  document_type: 'devis', tva_applicable: true, currency: 'EUR', issue_date: '2026-07-13',
  due_date: '2026-08-12', status: 'draft', subtotal_ht: 100, total_tax: 20, total_ttc: 120,
  notes: null, payment_terms: null, payment_method: null, late_penalty_rate: null,
  legal_mentions: null, converted_from_id: null, validite_jours: 30, payment_date: null,
  created_at: '2026-07-13', updated_at: '2026-07-13', lines: [],
};

describe('usePrototypeInvoiceData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useInvoiceStore.setState({ invoices: [], currentInvoiceId: null });
    useContactsStore.setState({ contacts: [], searchResults: null, loaded: false, loading: false, error: null });
    vi.mocked(listInvoices).mockResolvedValue([invoice]);
    vi.mocked(listContacts).mockResolvedValue([contact]);
    vi.mocked(getBillingProfileStatus).mockResolvedValue({ is_complete: true, missing: [] });
    vi.mocked(getInvoice).mockResolvedValue(invoice);
    vi.mocked(createInvoice).mockResolvedValue(invoice);
    vi.mocked(createContact).mockResolvedValue(contact);
  });

  it('charge les sources, rafraîchit le détail et crée un unique brouillon explicite', async () => {
    const { result } = renderHook(() => usePrototypeInvoiceData(true));
    await waitFor(() => expect(result.current.resource.status).toBe('ready'));

    expect(result.current.resource.data?.contacts).toEqual([contact]);
    expect(useInvoiceStore.getState().invoices).toEqual([invoice]);

    await act(async () => result.current.openInvoice(invoice.id));
    expect(getInvoice).toHaveBeenCalledWith(invoice.id);
    expect(result.current.invoiceResource).toEqual({ status: 'ready', data: invoice, error: null });

    await act(async () => {
      await result.current.createDevisDraft({
        contact_id: contact.id, document_type: 'devis', currency: 'EUR',
        lines: [{ description: 'Diagnostic', quantity: 1, unit_price_ht: 490, tva_rate: 20 }],
      });
    });
    expect(createInvoice).toHaveBeenCalledTimes(1);
    expect(createInvoice).toHaveBeenCalledWith(expect.objectContaining({ document_type: 'devis' }));

    await act(async () => {
      await result.current.createInvoiceContact({ company: 'Atelier Martin' });
    });
    expect(createContact).toHaveBeenCalledWith(expect.objectContaining({
      company: 'Atelier Martin',
      source: 'facturation',
      stage: 'contact',
    }));
    expect(result.current.resource.data?.contacts).toContainEqual(contact);
    expect(useContactsStore.getState().contacts).toContainEqual(contact);
  });

  it('ne charge rien hors du scénario Facturation', () => {
    renderHook(() => usePrototypeInvoiceData(false));
    expect(listInvoices).not.toHaveBeenCalled();
    expect(createInvoice).not.toHaveBeenCalled();
  });
});
