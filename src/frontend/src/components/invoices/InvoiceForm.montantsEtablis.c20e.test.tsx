/** Contre-relecture Claude : les pièces antérieures gardent les centimes annoncés. */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';

import type { Invoice } from '../../services/api';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';
import { InvoiceForm } from './InvoiceForm';

const { convertir, modifier } = vi.hoisted(() => ({ convertir: vi.fn(), modifier: vi.fn() }));
vi.mock('../../services/api', async () => ({
  ...await vi.importActual<typeof import('../../services/api')>('../../services/api'),
  listContacts: vi.fn().mockResolvedValue([{ id: 'c1', first_name: 'Jean', last_name: 'Client' }]),
  getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  convertDevisToInvoice: convertir,
  updateInvoice: modifier,
}));

const piece: Invoice = {
  id: 'dev-1', invoice_number: 'DEV-2026-001', contact_id: 'c1', document_type: 'devis',
  tva_applicable: true, currency: 'EUR', status: 'accepted',
  issue_date: '2026-09-01', due_date: '2026-10-01', subtotal_ht: 123.4, total_tax: 6.8, total_ttc: 130.2,
  notes: null, payment_terms: null, payment_method: null, late_penalty_rate: null, legal_mentions: null,
  converted_from_id: null, validite_jours: 30, payment_date: null,
  created_at: '2026-09-01T08:00:00Z', updated_at: '2026-09-01T08:00:00Z',
  lines: Array.from({ length: 10 }, (_, i) => ({
    id: `l${i}`, invoice_id: 'dev-1', description: 'Repas', quantity: 1,
    unit_price_ht: 12.34, tva_rate: 5.5, total_ht: 12.34, total_ttc: 13.02,
  })),
};

function rendre(invoice: Invoice) {
  return render(<PrototypeExternalActionConfirmationProvider>
    <InvoiceForm invoice={invoice} onClose={vi.fn()} onSave={vi.fn()} />
  </PrototypeExternalActionConfirmationProvider>);
}

beforeEach(() => {
  vi.clearAllMocks();
  useBillingProfileStore.setState({ missing: null });
  convertir.mockResolvedValue({ ...piece, document_type: 'facture' });
  modifier.mockResolvedValue(piece);
});

it.each([
  ['devis', 'accepted'], ['devis', 'draft'], ['facture', 'draft'], ['facture', 'sent'],
] as const)('%s %s antérieur affiche son TTC établi', async (document_type, status) => {
  rendre({ ...piece, document_type, status });
  await screen.findByLabelText('Statut');
  expect(document.body.textContent).toMatch(/130[,.]20/);
  expect(document.body.textContent).not.toMatch(/130[,.]19/);
});

it('le changement de statut confirme le TTC établi du brouillon', async () => {
  rendre({ ...piece, status: 'draft' });
  fireEvent.change(await screen.findByLabelText('Statut'), { target: { value: 'accepted' } });
  fireEvent.click(screen.getByRole('button', { name: 'Mettre à jour' }));
  expect(await screen.findByTestId('external-action-confirmation')).toHaveTextContent(/130[,.]20/);
});

it('le devis accepté garde le même montant dans la conversion affichée', async () => {
  rendre(piece);
  fireEvent.click(await screen.findByRole('button', { name: 'Convertir en facture' }));
  expect(document.body.textContent).toMatch(/130[,.]20/);
  expect(document.body.textContent).not.toMatch(/130[,.]19/);
  fireEvent.click(screen.getByRole('button', { name: 'Convertir' }));
  await waitFor(() => expect(convertir).toHaveBeenCalledWith('dev-1', {
    payment_terms: '30 jours', payment_method: 'Virement bancaire',
  }));
});

it.each([
  [[[3, 7.77, 5.5, 8.2]], 23.31, 1.29, 24.6],
  [[[9, 0.07, 20, 0.08]], 0.63, 0.09, 0.72],
  [[[4, 0.15, 10, 0.17]], 0.6, 0.08, 0.68],
  [[[6, 2.35, 2.1, 2.4]], 14.1, 0.3, 14.4],
  [[[2, 49.99, 20, 59.99]], 99.98, 20, 119.98],
  [[[5, 3.33, 5.5, 3.51]], 16.65, 0.9, 17.55],
  [[[8, 0.26, 10, 0.29]], 2.08, 0.24, 2.32],
  [[[7, 0.23, 2.1, 0.23]], 1.61, 0, 1.61],
  [[[3, 17.11, 0, 17.11]], 51.33, 0, 51.33],
  [[[4, 6.66, 5.5, 7.03], [3, 0.29, 20, 0.35]], 27.51, 1.66, 29.17],
] as [number[][], number, number, number][])(
  'après revert : %j affiche les mêmes centimes que les routes et le PDF', async (groupes, ht, taxe, ttc) => {
    const lines = groupes.flatMap(([nombre, prix, taux, totalLigne], groupe) => Array.from({ length: nombre }, (_, i) => ({
      ...piece.lines[0], id: `${groupe}-${i}`, unit_price_ht: prix, tva_rate: taux, total_ht: prix, total_ttc: totalLigne,
    })));
    rendre({ ...piece, lines, subtotal_ht: ht, total_tax: taxe, total_ttc: ttc });
    await screen.findByLabelText('Statut');
    expect(document.body.textContent).toContain(`Total HT${ht.toFixed(2).replace('.', ',')}`);
    expect(document.body.textContent).toContain(`Total TVA${taxe.toFixed(2).replace('.', ',')}`);
    expect(document.body.textContent).toContain(`Total TTC${ttc.toFixed(2).replace('.', ',')}`);
  },
);
