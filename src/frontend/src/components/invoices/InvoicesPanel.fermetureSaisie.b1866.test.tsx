/**
 * B-1866 : en mode modal, Fermer et le fond démontent le panneau avant le
 * formulaire. Une saisie ouverte doit poser « Abandonner les modifications ? »
 * et rester à l'écran. Un formulaire intact se ferme avec le panneau.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoicesPanel } from './InvoicesPanel';
import { useInvoiceStore } from '../../stores/invoiceStore';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { _viderSaisiesEnCours } from '../../lib/saisieEnCours';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listInvoices: vi.fn().mockResolvedValue([]),
    listContacts: vi.fn().mockResolvedValue([]),
    getContact: vi.fn(),
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [], tva_intra_renseigne: false }),
  };
});

function fermerDuPanneau() {
  return within(screen.getByTestId('invoices-panel')).getByRole('button', { name: 'Fermer' });
}

function fondDuPanneau() {
  const fond = screen.getByTestId('invoices-panel').parentElement;
  if (!fond) throw new Error('fond du panneau introuvable');
  return fond;
}

describe('B-1866 : fermer le panneau modal avec une saisie ouverte', () => {
  beforeEach(() => {
    _viderSaisiesEnCours();
    useBillingProfileStore.setState({ missing: null, statutLecture: 'lu', tvaIntraRenseigne: false });
    useInvoiceStore.setState({
      invoices: [],
      currentInvoiceId: null,
      filters: { status: 'all' },
      isInvoicePanelOpen: true,
      draftInvoice: null,
    });
  });

  afterEach(() => {
    _viderSaisiesEnCours();
  });

  async function ouvrirEtRetoucher() {
    render(<InvoicesPanel />);
    fireEvent.click(await screen.findByRole('button', { name: 'Nouveau devis ou facture' }));
    const description = await screen.findByLabelText('Description ligne 1');
    fireEvent.change(description, { target: { value: 'Consultation' } });
  }

  it.each([
    ['Fermer', fermerDuPanneau],
    ['le fond', fondDuPanneau],
  ])('%s pose la question et garde la saisie', async (_nom, cible) => {
    await ouvrirEtRetoucher();
    fireEvent.click(cible());
    expect(await screen.findByText('Abandonner les modifications ?')).toBeInTheDocument();
    expect(screen.getByTestId('invoices-panel')).toBeInTheDocument();
    expect(screen.getByLabelText('Description ligne 1')).toHaveValue('Consultation');
  });

  it('un formulaire intact se ferme avec le panneau', async () => {
    render(<InvoicesPanel />);
    fireEvent.click(await screen.findByRole('button', { name: 'Nouveau devis ou facture' }));
    await screen.findByLabelText('Description ligne 1');
    fireEvent.click(fermerDuPanneau());
    await waitFor(() => expect(screen.queryByTestId('invoices-panel')).not.toBeInTheDocument());
  });
});
