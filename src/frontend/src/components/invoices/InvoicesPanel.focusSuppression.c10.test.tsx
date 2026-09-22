/** B-938 : une confirmation destructive doit prendre et restituer le focus. */
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Invoice } from '../../services/api';
import { useInvoiceStore } from '../../stores/invoiceStore';
import { useStatusStore } from '../../stores/statusStore';
import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';

const { listInvoices, deleteInvoice } = vi.hoisted(() => ({
  listInvoices: vi.fn(), deleteInvoice: vi.fn(),
}));
vi.mock('../../services/api', async () => ({
  ...await vi.importActual<typeof import('../../services/api')>('../../services/api'),
  listInvoices, deleteInvoice,
}));
vi.mock('./InvoiceForm', () => ({ InvoiceForm: () => <div>Formulaire de facture</div> }));

import { InvoicesPanel } from './InvoicesPanel';

const facture: Invoice = {
  id: 'inv-c10', invoice_number: 'FAC-C10-001', contact_id: 'contact-c10',
  document_type: 'facture', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-09-01T00:00:00Z', due_date: '2026-09-30T00:00:00Z',
  status: 'draft', subtotal_ht: 100, total_tax: 20, total_ttc: 120,
  notes: null, payment_terms: null, payment_method: null, late_penalty_rate: null,
  legal_mentions: null, converted_from_id: null, validite_jours: null,
  payment_date: null, created_at: '2026-09-01T00:00:00Z',
  updated_at: '2026-09-01T00:00:00Z', lines: [],
};

async function ouvrirLaConfirmation() {
  render(<InvoicesPanel standalone />);
  const declencheur = await screen.findByTitle('Supprimer');
  // fireEvent.click ne simule pas le focus natif du clic : le reproduire
  // explicitement permet aussi de vérifier le retour au vrai déclencheur.
  declencheur.focus();
  fireEvent.click(declencheur);
  const dialogue = await screen.findByRole('dialog', { name: 'Confirmer la suppression' });
  return { declencheur, dialogue, annuler: within(dialogue).getByRole('button', { name: 'Annuler' }) };
}

describe('B-938 : confirmation de suppression de facture au clavier', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    listInvoices.mockResolvedValue([facture]);
    deleteInvoice.mockResolvedValue(undefined);
    useInvoiceStore.setState({
      invoices: [], currentInvoiceId: null, filters: { status: 'all' },
      isInvoicePanelOpen: true, draftInvoice: null, listeTronquee: false,
    });
    useStatusStore.setState({ notifications: [] });
  });

  it('place le focus sur Annuler sans appeler la suppression', async () => {
    const { annuler } = await ouvrirLaConfirmation();
    expect(deleteInvoice).not.toHaveBeenCalled();
    expect(annuler).toHaveFocus();
  });

  it('boucle Tab et Maj+Tab aux deux bords de la confirmation', async () => {
    const { dialogue, annuler } = await ouvrirLaConfirmation();
    const supprimer = within(dialogue).getByRole('button', { name: 'Supprimer' });
    annuler.focus();
    fireEvent.keyDown(annuler, { key: 'Tab', shiftKey: true });
    expect(supprimer).toHaveFocus();
    fireEvent.keyDown(supprimer, { key: 'Tab' });
    expect(annuler).toHaveFocus();
    expect(deleteInvoice).not.toHaveBeenCalled();
  });

  it('rend le focus au bouton de la facture après annulation', async () => {
    const { declencheur, dialogue, annuler } = await ouvrirLaConfirmation();
    annuler.focus();
    fireEvent.click(annuler);
    await waitFor(() => expect(dialogue).not.toBeInTheDocument());
    expect(declencheur).toHaveFocus();
    expect(deleteInvoice).not.toHaveBeenCalled();
  });

  it('appelle une seule suppression après confirmation explicite', async () => {
    const { dialogue } = await ouvrirLaConfirmation();
    expect(deleteInvoice).not.toHaveBeenCalled();
    fireEvent.click(within(dialogue).getByRole('button', { name: 'Supprimer' }));
    await waitFor(() => expect(deleteInvoice).toHaveBeenCalledExactlyOnceWith('inv-c10'));
    await waitFor(() => expect(dialogue).not.toBeInTheDocument());
  });

  it('isole le fond pendant la confirmation et le réactive à la fermeture', async () => {
    const { declencheur, dialogue, annuler } = await ouvrirLaConfirmation();
    expect(declencheur.closest('[inert]')).not.toBeNull();
    expect(declencheur.closest('[aria-hidden="true"]')).not.toBeNull();
    expect(dialogue.closest('[inert]')).toBeNull();
    fireEvent.click(annuler);
    await waitFor(() => expect(dialogue).not.toBeInTheDocument());
    expect(declencheur.closest('[inert]')).toBeNull();
    expect(declencheur.closest('[aria-hidden="true"]')).toBeNull();
    expect(declencheur).toHaveFocus();
  });

  it('consomme Échap sur la pile de la coque puis restitue le focus', async () => {
    const { declencheur, dialogue } = await ouvrirLaConfirmation();
    act(() => { expect(runTopEscapeHandler()).toBe(true); });
    await waitFor(() => expect(dialogue).not.toBeInTheDocument());
    expect(declencheur).toHaveFocus();
    expect(useInvoiceStore.getState().isInvoicePanelOpen).toBe(true);
    expect(runTopEscapeHandler()).toBe(false);
    expect(deleteInvoice).not.toHaveBeenCalled();
  });

  it('garde le dialogue et le clavier confinés pendant la suppression', async () => {
    deleteInvoice.mockReturnValue(new Promise(() => {}));
    const { dialogue, annuler } = await ouvrirLaConfirmation();
    fireEvent.click(within(dialogue).getByRole('button', { name: 'Supprimer' }));
    expect(dialogue).toHaveAttribute('aria-busy', 'true');
    expect(dialogue).toHaveFocus();
    expect(annuler).toBeDisabled();
    const tab = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true });
    fireEvent(dialogue, tab);
    expect(tab.defaultPrevented).toBe(true);
    expect(dialogue).toHaveFocus();
    act(() => { expect(runTopEscapeHandler()).toBe(true); });
    fireEvent.click(dialogue.parentElement!);
    expect(dialogue).toBeInTheDocument();
    expect(deleteInvoice).toHaveBeenCalledExactlyOnceWith('inv-c10');
  });
});
