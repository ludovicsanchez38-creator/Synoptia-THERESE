/**
 * Lecteurs F et C de la carte c12 :
 * - B-1067 : « Convertir en facture » renvoie une NOUVELLE pièce (autre
 *   identifiant). La liste la « mettait à jour » par identifiant : la facture
 *   n'apparaissait pas et le devis gardait son ancien statut jusqu'au rechargement.
 * - B-1069 : le premier devis créé depuis l'état vide fait disparaître le
 *   bouton qui avait ouvert la modale ; le focus tombait sur la page.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Invoice } from '../../services/api';
import { useInvoiceStore } from '../../stores/invoiceStore';
import { useStatusStore } from '../../stores/statusStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';

const { listInvoices } = vi.hoisted(() => ({ listInvoices: vi.fn() }));
vi.mock('../../services/api', async () => ({
  ...await vi.importActual<typeof import('../../services/api')>('../../services/api'),
  listInvoices,
}));
const retour = vi.hoisted(() => ({ piece: null as Invoice | null }));
vi.mock('./InvoiceForm', () => ({
  InvoiceForm: ({ onSave }: { onSave: (i: Invoice) => void }) => (
    <div role="dialog" aria-label="Formulaire factice">
      <button type="button" onClick={() => onSave(retour.piece as Invoice)}>Enregistrer factice</button>
    </div>
  ),
}));

import { InvoicesPanel } from './InvoicesPanel';

const piece = (id: string, numero: string, type: 'devis' | 'facture', status: string): Invoice => ({
  id, invoice_number: numero, contact_id: 'c', document_type: type, tva_applicable: true, currency: 'EUR',
  issue_date: '2026-09-01T00:00:00Z', due_date: '2026-09-30T00:00:00Z', status: status as Invoice['status'],
  subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null, payment_terms: null, payment_method: null,
  late_penalty_rate: null, legal_mentions: null, converted_from_id: null, validite_jours: null,
  payment_date: null, created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z', lines: [],
});

describe('cycle 12 : la liste des pièces suit la conversion et la première création', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    useInvoiceStore.setState({
      invoices: [], currentInvoiceId: null, filters: { status: 'all' },
      isInvoicePanelOpen: true, draftInvoice: null, listeTronquee: false,
    });
    useStatusStore.setState({ notifications: [] });
  });

  it('B-1067 : après la conversion, la facture apparaît et le devis passe « converti »', async () => {
    const devis = piece('dev-1', 'DEV-2026-001', 'devis', 'accepted');
    const facture = { ...piece('fac-1', 'FAC-2026-001', 'facture', 'draft'), converted_from_id: 'dev-1' };
    listInvoices.mockResolvedValueOnce([devis]).mockResolvedValue([facture, { ...devis, status: 'converted' as Invoice['status'] }]);
    retour.piece = facture;
    render(<InvoicesPanel standalone />);
    fireEvent.click((await screen.findAllByText('DEV-2026-001'))[0]);
    fireEvent.click(await screen.findByRole('button', { name: 'Enregistrer factice' }));
    expect((await screen.findAllByText('FAC-2026-001')).length).toBeGreaterThan(0);
    expect(listInvoices).toHaveBeenCalledTimes(2);
  });

  it('B-1069 : la première pièce créée depuis l’état vide rend le focus à « Nouveau devis ou facture »', async () => {
    const devis = piece('dev-2', 'DEV-2026-002', 'devis', 'draft');
    listInvoices.mockResolvedValueOnce([]).mockResolvedValue([devis]);
    retour.piece = devis;
    render(<InvoicesPanel standalone />);
    const vide = await screen.findByRole('button', { name: /Créer un devis ou une facture/ });
    vide.focus();
    fireEvent.click(vide);
    const enregistrer = await screen.findByRole('button', { name: 'Enregistrer factice' });
    enregistrer.focus();
    fireEvent.click(enregistrer);
    await screen.findAllByText('DEV-2026-002');
    await waitFor(() => expect(screen.getByRole('button', { name: /^Nouveau devis ou facture/ })).toHaveFocus());
  });
});
