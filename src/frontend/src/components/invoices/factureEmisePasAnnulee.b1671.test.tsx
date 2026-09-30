/**
 * B-1671 : une facture émise ne propose plus « Annulée ».
 * Un devis envoyé garde « Annulé ».
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';

const { listContacts, getContact } = vi.hoisted(() => ({
  listContacts: vi.fn().mockResolvedValue([]),
  getContact: vi.fn().mockResolvedValue({
    id: 'c-1', first_name: 'Claire', last_name: 'Roux', company: null, email: null,
  }),
}));

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<Record<string, unknown>>('../../services/api');
  return {
    ...reel,
    listContacts,
    getContact,
    listInvoices: vi.fn().mockResolvedValue([]),
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  };
});

beforeEach(() => {
  listContacts.mockClear();
  vi.stubGlobal('fetch', vi.fn());
});

afterEach(async () => {
  await waitFor(() => expect(listContacts).toHaveBeenCalled());
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
  expect(fetch).not.toHaveBeenCalled();
  vi.unstubAllGlobals();
});

function piece(documentType: 'devis' | 'facture' | 'avoir', status: 'draft' | 'sent' | 'cancelled') {
  return {
    id: 'inv-1',
    invoice_number: documentType === 'devis' ? 'DEV-2026-001' : 'FACT-2026-001',
    contact_id: 'c-1',
    document_type: documentType,
    tva_applicable: true,
    currency: 'EUR',
    issue_date: '2026-08-01T00:00:00Z',
    due_date: '2026-09-01T00:00:00Z',
    status,
    subtotal_ht: 1000,
    total_tax: 200,
    total_ttc: 1200,
    notes: null,
    payment_terms: null,
    payment_method: null,
    late_penalty_rate: null,
    legal_mentions: null,
    converted_from_id: null,
    validite_jours: 30,
    payment_date: null,
    created_at: '2026-08-01T00:00:00Z',
    updated_at: '2026-08-01T00:00:00Z',
    lines: [{
      id: 'l-1', invoice_id: 'inv-1', description: 'Prestation', quantity: 1,
      unit_price_ht: 1000, tva_rate: 20, total_ht: 1000, total_ttc: 1200,
    }],
  };
}

function valeursStatut(): string[] {
  const statut = screen.getByLabelText('Statut') as HTMLSelectElement;
  return Array.from(statut.querySelectorAll('option')).map((option) => option.value);
}

describe('B-1671 : Annulée sort du sélecteur d’une facture émise', () => {
  it('une facture envoyée ne propose pas cancelled', async () => {
    render(<InvoiceForm invoice={piece('facture', 'sent') as never} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText('Statut');
    expect(valeursStatut()).not.toContain('cancelled');
    expect(valeursStatut()).toEqual(expect.arrayContaining(['sent', 'paid', 'overdue']));
  });

  it('un avoir envoyé ne propose pas cancelled', async () => {
    render(<InvoiceForm invoice={piece('avoir', 'sent') as never} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText('Statut');
    expect(valeursStatut()).not.toContain('cancelled');
    expect(valeursStatut()).toEqual(expect.arrayContaining(['sent', 'paid', 'overdue']));
    expect(screen.getByText(/expert-comptable/)).toBeVisible();
    expect(screen.queryByText(/émets un avoir/)).toBeNull();
  });

  it('un devis envoyé propose encore cancelled', async () => {
    render(<InvoiceForm invoice={piece('devis', 'sent') as never} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText('Statut');
    expect(valeursStatut()).toContain('cancelled');
  });

  it('une facture déjà annulée affiche Annulée, puis ne la propose plus', async () => {
    render(<InvoiceForm invoice={piece('facture', 'cancelled') as never} onClose={vi.fn()} onSave={vi.fn()} />);
    const statut = await screen.findByLabelText('Statut') as HTMLSelectElement;
    expect(statut).toHaveValue('cancelled');
    expect(statut.selectedOptions[0]?.textContent).toBe('Annulée');
    fireEvent.change(statut, { target: { value: 'sent' } });
    expect(statut).toHaveValue('sent');
    expect(valeursStatut()).not.toContain('cancelled');
  });

  it('un avoir déjà annulé affiche Annulée', async () => {
    render(<InvoiceForm invoice={piece('avoir', 'cancelled') as never} onClose={vi.fn()} onSave={vi.fn()} />);
    const statut = await screen.findByLabelText('Statut') as HTMLSelectElement;
    expect(statut).toHaveValue('cancelled');
    expect(statut.selectedOptions[0]?.textContent).toBe('Annulée');
  });

  it('un devis déjà annulé affiche Annulé', async () => {
    render(<InvoiceForm invoice={piece('devis', 'cancelled') as never} onClose={vi.fn()} onSave={vi.fn()} />);
    const statut = await screen.findByLabelText('Statut') as HTMLSelectElement;
    expect(statut).toHaveValue('cancelled');
    expect(statut.selectedOptions[0]?.textContent).toBe('Annulé');
  });

  it('un brouillon de facture propose encore cancelled', async () => {
    render(<InvoiceForm invoice={piece('facture', 'draft') as never} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText('Statut');
    expect(valeursStatut()).toContain('cancelled');
  });

  it('un brouillon PROV annulé peut revenir au brouillon et reste modifiable', async () => {
    render(<InvoiceForm invoice={{ ...piece('facture', 'cancelled'), invoice_number: 'PROV-jetable' } as never} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText('Statut');
    expect(valeursStatut()).toContain('draft');
    expect(screen.getByLabelText(/Date d.émission/)).not.toBeDisabled();
  });

  it('un PROV avec un horodatage d’envoi reste figé malgré son statut annulé', async () => {
    render(<InvoiceForm invoice={{ ...piece('facture', 'cancelled'), invoice_number: 'PROV-ancien', sent_at: '2026-08-01T00:00:00Z' } as never} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText('Statut');
    expect(valeursStatut()).not.toContain('draft');
    expect(screen.getByLabelText(/Date d.émission/)).toBeDisabled();
  });
});
