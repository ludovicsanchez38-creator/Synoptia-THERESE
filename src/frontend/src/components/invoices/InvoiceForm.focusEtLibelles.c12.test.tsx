/**
 * Cycle 12, ronde B4 du cycle 11 (D-B4-1, D-B4-2, D-B4-3, D-B4-8, D-B4-9) :
 * B-1031 la modale ne prenait ni ne retenait le focus ; B-1035 elle restait
 * annoncée « Nouvelle facture » pour un devis ; B-1036 le focus tombait sur
 * BODY après « Créer » ; B-1038 un devis était « Facture créée » ; B-1039 la
 * notification « Champ requis » recouvrait le bouton « Créer ».
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { useState } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { useStatusStore } from '../../stores/statusStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import type { Invoice } from '../../services/api';

const { createInvoice, updateInvoice } = vi.hoisted(() => ({ createInvoice: vi.fn(), updateInvoice: vi.fn() }));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([
      { id: 'contact-1', first_name: 'Jean', last_name: 'Dupont', email: 'jean@example.com' },
    ]),
    createInvoice,
    updateInvoice,
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  };
});

const devis: Invoice = {
  id: 'devis-1', invoice_number: 'DEV-2026-001', contact_id: 'contact-1',
  document_type: 'devis', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-07-01T00:00:00Z', due_date: '2026-07-31T00:00:00Z', status: 'draft',
  subtotal_ht: 100, total_tax: 20, total_ttc: 120, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: null,
  validite_jours: null, payment_date: null, created_at: '2026-07-01T08:00:00Z',
  updated_at: '2026-07-01T08:00:00Z',
  lines: [{
    id: 'line-1', invoice_id: 'devis-1', description: 'Accompagnement',
    quantity: 1, unit_price_ht: 100, tva_rate: 20, total_ht: 100, total_ttc: 120,
  }],
};

const addNotification = vi.fn();

/** Un déclencheur réel, comme « Nouveau devis ou facture » dans la vue. */
function Banc({ piece, type }: { piece?: Invoice; type?: 'devis' | 'facture' }) {
  const [ouvert, setOuvert] = useState(false);
  return (
    <div>
      <button type="button" onClick={() => setOuvert(true)}>Nouveau devis ou facture</button>
      <button type="button">Filtre Tout</button>
      {ouvert && (
        <InvoiceForm
          invoice={piece ?? null}
          defaultDocumentType={type}
          onClose={() => setOuvert(false)}
          onSave={() => setOuvert(false)}
        />
      )}
    </div>
  );
}

function ouvrir(props: { piece?: Invoice; type?: 'devis' | 'facture' } = {}) {
  render(<Banc {...props} />);
  const declencheur = screen.getByRole('button', { name: 'Nouveau devis ou facture' });
  declencheur.focus();
  fireEvent.click(declencheur);
  return { declencheur, dialogue: screen.getByRole('dialog') };
}

describe('cycle 12 : formulaire devis/facture, focus et libellés', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    useBillingProfileStore.setState({ missing: null });
    useStatusStore.setState({ notifications: [], addNotification } as never);
  });

  it('B-1031 : à l’ouverture, le focus entre dans la modale', async () => {
    const { dialogue } = ouvrir();
    await waitFor(() => expect(dialogue.contains(document.activeElement)).toBe(true));
  });

  it('B-1031 : Tab depuis le dernier élément reste dans la modale', async () => {
    const { dialogue } = ouvrir();
    await waitFor(() => expect(dialogue.contains(document.activeElement)).toBe(true));
    const focalisables = [...dialogue.querySelectorAll<HTMLElement>('button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled])')];
    const dernier = focalisables[focalisables.length - 1];
    dernier.focus();
    fireEvent.keyDown(dernier, { key: 'Tab' });
    // Lecteur F (B-1070) : jsdom ne déplace jamais le focus sur un keyDown ;
    // seul le piège le ramène au premier élément.
    expect(document.activeElement).toBe(focalisables[0]);
  });

  it('B-1035 : un devis est annoncé « Nouveau devis », pas « Nouvelle facture »', async () => {
    ouvrir({ type: 'devis' });
    expect(await screen.findByRole('dialog', { name: 'Nouveau devis' })).toBeInTheDocument();
  });

  it('B-1035 : changer le type renomme la modale', async () => {
    const { dialogue } = ouvrir({ type: 'facture' });
    expect(dialogue).toHaveAccessibleName('Nouvelle facture');
    fireEvent.click(within(dialogue).getByRole('button', { name: 'Devis' }));
    expect(dialogue).toHaveAccessibleName('Nouveau devis');
  });

  it('B-1036 et B-1038 : après « Créer » un devis, le focus revient au déclencheur et la notification dit « Devis créé »', async () => {
    createInvoice.mockResolvedValue({ ...devis, id: 'devis-2', invoice_number: 'DEV-2026-002' });
    const { declencheur, dialogue } = ouvrir({ type: 'devis' });
    await waitFor(() => expect(dialogue.contains(document.activeElement)).toBe(true));
    const contact = await within(dialogue).findByRole('option', { name: /Jean Dupont/ });
    fireEvent.change(contact.closest('select') as HTMLSelectElement, { target: { value: 'contact-1' } });
    fireEvent.change(within(dialogue).getAllByLabelText(/Description/)[0], { target: { value: 'Atelier' } });
    fireEvent.click(within(dialogue).getByRole('button', { name: /^Créer/ }));
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    // CI Linux : le focus revient dans un requestAnimationFrame, après la
    // disparition du dialogue ; on l'attend au lieu de le lire aussitôt.
    await waitFor(() => expect(declencheur).toHaveFocus());
    expect(addNotification).toHaveBeenCalledWith(expect.objectContaining({ title: 'Devis créé' }));
  });

  it('B-1038 : la mise à jour d’un devis dit « Devis mis à jour »', async () => {
    updateInvoice.mockResolvedValue(devis);
    render(<InvoiceForm invoice={devis} onClose={vi.fn()} onSave={vi.fn()} />);
    const dialogue = screen.getByRole('dialog');
    await within(dialogue).findByRole('option', { name: /Jean Dupont/ });
    fireEvent.click(within(dialogue).getByRole('button', { name: /Mettre à jour/ }));
    await waitFor(() => expect(updateInvoice).toHaveBeenCalled());
    expect(addNotification).toHaveBeenCalledWith(expect.objectContaining({ title: 'Devis mis à jour' }));
  });

  it('B-1039 : un champ requis manquant se dit dans le pied de la modale, pas dans une notification qui couvre « Créer »', async () => {
    // Scénario F05 de la ronde B4 : client choisi, aucune description de ligne.
    const { dialogue } = ouvrir({ type: 'facture' });
    const contact = await within(dialogue).findByRole('option', { name: /Jean Dupont/ });
    fireEvent.change(contact.closest('select') as HTMLSelectElement, { target: { value: 'contact-1' } });
    fireEvent.click(within(dialogue).getByRole('button', { name: /^Créer/ }));
    expect(addNotification).not.toHaveBeenCalledWith(expect.objectContaining({ title: 'Champ requis' }));
    expect(within(dialogue).getByTestId('invoiceform-validation')).toHaveTextContent(/description/i);
  });

  it('B-1068 : « Valeur invalide » se dit aussi dans le pied, et le message s’efface quand on corrige', async () => {
    const { dialogue } = ouvrir({ type: 'facture' });
    const contact = await within(dialogue).findByRole('option', { name: /Jean Dupont/ });
    fireEvent.change(contact.closest('select') as HTMLSelectElement, { target: { value: 'contact-1' } });
    const description = within(dialogue).getAllByLabelText(/Description/)[0];
    fireEvent.change(description, { target: { value: 'Atelier' } });
    const quantite = within(dialogue).getAllByLabelText(/Quantité/)[0];
    fireEvent.change(quantite, { target: { value: '0' } });
    fireEvent.click(within(dialogue).getByRole('button', { name: /^Créer/ }));
    expect(addNotification).not.toHaveBeenCalledWith(expect.objectContaining({ title: 'Valeur invalide' }));
    expect(within(dialogue).getByTestId('invoiceform-validation')).toHaveTextContent(/quantité/i);
    fireEvent.change(quantite, { target: { value: '2' } });
    expect(within(dialogue).queryByTestId('invoiceform-validation')).toBeNull();
  });
});
