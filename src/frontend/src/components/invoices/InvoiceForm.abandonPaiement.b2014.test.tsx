import { fireEvent, render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { InvoiceForm } from './InvoiceForm';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';
import type { Invoice } from '../../services/api';

vi.mock('../../services/api', async original => ({
  ...await original<typeof import('../../services/api')>(),
  listContacts: vi.fn().mockResolvedValue([]),
  getContact: vi.fn().mockResolvedValue({ id: 'client-1', first_name: 'Léa', last_name: 'Fictive' }),
  getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
}));

it('écarte le paiement pendant la question d’abandon et le rétablit ensuite', () => {
  const facture = {
    id: 'facture-emise', invoice_number: 'FAC-TEST', contact_id: 'client-1',
    document_type: 'facture', status: 'sent', currency: 'EUR', tva_applicable: true,
    issue_date: '2026-10-01T00:00:00Z', due_date: '2026-10-31T00:00:00Z',
    subtotal_ht: 100, total_tax: 20, total_ttc: 120, lines: [],
    notes: null, payment_terms: null, payment_method: null, late_penalty_rate: null,
    legal_mentions: null, converted_from_id: null, validite_jours: null, payment_date: null,
    created_at: '2026-10-01T00:00:00Z', updated_at: '2026-10-01T00:00:00Z',
  } as Invoice;
  render(<PrototypeExternalActionConfirmationProvider>
    <InvoiceForm invoice={facture} onClose={vi.fn()} onSave={vi.fn()} />
  </PrototypeExternalActionConfirmationProvider>);
  fireEvent.change(screen.getByLabelText('Statut'), { target: { value: 'paid' } });
  const annuler = screen.getByRole('button', { name: 'Annuler' });
  annuler.focus();
  fireEvent.click(annuler);

  expect(screen.getByText('Abandonner les modifications ?')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Marquer comme payée' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Mettre à jour' })).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Continuer la saisie' })).toHaveFocus();
  fireEvent.submit(screen.getByLabelText('Statut').closest('form')!);
  expect(screen.queryByTestId('external-action-confirmation')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Continuer la saisie' }));
  expect(screen.getByRole('button', { name: 'Marquer comme payée' })).toBeEnabled();
  expect(annuler).toHaveFocus();
});
