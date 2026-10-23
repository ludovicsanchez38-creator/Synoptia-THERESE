import { fireEvent, render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { InvoiceForm } from './InvoiceForm';
vi.mock('../../services/api', async (original) => ({ ...await original<typeof import('../../services/api')>(), listContacts: vi.fn().mockResolvedValue([]), getContact: vi.fn().mockResolvedValue({ id: 'client-1', first_name: 'Léa', last_name: 'Fictive' }), getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }) }));
it('B-1079 : le pied et ses groupes peuvent revenir à la ligne sans comprimer les actions', async () => {
  render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);
  fireEvent.change(screen.getByLabelText('Description ligne 1'), { target: { value: 'Prestation' } });
  fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
  const question = screen.getByText('Abandonner les modifications ?');
  const pied = question.parentElement!.parentElement!;
  expect(pied).toHaveClass('flex-wrap', 'gap-3');
  expect(question.parentElement).toHaveClass('basis-full');
  expect(screen.getByRole('button', { name: 'Créer' }).parentElement).toHaveClass('shrink-0');
});

it('B-1079 : facture émise, paiement et abandon restent des groupes indépendants', async () => {
  const facture = {
    id: 'facture-emise', invoice_number: 'FAC-2026-019', contact_id: 'client-1',
    document_type: 'facture', status: 'sent', currency: 'EUR', tva_applicable: true,
    issue_date: '2026-10-01T00:00:00Z', due_date: '2026-10-31T00:00:00Z',
    subtotal_ht: 100, total_tax: 20, total_ttc: 120, lines: [],
    notes: null, payment_terms: null, payment_method: null, late_penalty_rate: null,
    legal_mentions: null, converted_from_id: null, validite_jours: null, payment_date: null,
    created_at: '2026-10-01T00:00:00Z', updated_at: '2026-10-01T00:00:00Z',
  } as import('../../services/api').Invoice;
  render(<InvoiceForm invoice={facture} onClose={vi.fn()} onSave={vi.fn()} />);
  fireEvent.change(screen.getByLabelText('Statut'), { target: { value: 'paid' } });
  fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
  const question = screen.getByText('Abandonner les modifications ?');
  expect(question.parentElement).toHaveClass('basis-full');
  const paiement = screen.getByRole('button', { name: 'Marquer comme payée' }).parentElement;
  expect(paiement).toHaveClass('flex-wrap', '[&>button]:shrink-0', '[&>button]:whitespace-nowrap');
  expect(screen.getByText('Payée le')).toHaveClass('whitespace-nowrap');
  expect(screen.getByRole('button', { name: 'Mettre à jour' }).parentElement).toHaveClass('shrink-0');
});
