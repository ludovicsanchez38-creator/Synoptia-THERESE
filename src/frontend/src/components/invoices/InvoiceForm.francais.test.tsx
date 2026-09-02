/**
 * B-221 : le document de facturation ne parlait pas français.
 *
 * Sept libellés sans accents (« Date d'emission », « Quantite »,
 * « Selectionner un contact », les taux de TVA) et des montants en notation
 * anglaise : 2400.00 €, là où quatre autres surfaces de l'application formatent
 * déjà en fr-FR. C'est l'écran qui écrit des sommes au client.
 *
 * Les assertions de montant comparent à `Intl.NumberFormat('fr-FR')` plutôt
 * qu'à une chaîne tapée au clavier : le séparateur de milliers français est une
 * espace fine insécable (U+202F) et l'espace avant le symbole une insécable
 * (U+00A0). Une chaîne écrite à la main aurait été fausse ou, pire, verte par
 * la normalisation des espaces.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Invoice } from '../../services/api';
import { useBillingProfileStore } from '../../stores/billingProfileStore';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listContacts: vi.fn().mockResolvedValue([
      { id: 'contact-1', first_name: 'Camille', last_name: 'Martin', email: 'camille@example.fr' },
    ]),
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  };
});

import { InvoiceForm } from './InvoiceForm';

/** Un devis à une ligne : 2 400 € HT, TVA 20 % → 480 € de taxe, 2 880 € TTC. */
const devis: Invoice = {
  id: 'inv-1', invoice_number: 'DEV-2026-001', contact_id: 'contact-1',
  document_type: 'devis', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-08-01T00:00:00Z', due_date: '2026-09-01T00:00:00Z', status: 'draft',
  subtotal_ht: 2400, total_tax: 480, total_ttc: 2880, notes: null, payment_terms: null,
  payment_method: null, late_penalty_rate: null, legal_mentions: null, converted_from_id: null,
  validite_jours: 30, payment_date: null, created_at: '2026-08-01T08:00:00Z',
  updated_at: '2026-08-01T08:00:00Z',
  lines: [{
    id: 'l-1', invoice_id: 'inv-1', description: 'Accompagnement',
    quantity: 1, unit_price_ht: 2400, tva_rate: 20, total_ht: 2400, total_ttc: 2880,
  }],
};

const nombreFr = (montant: number) =>
  new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    .format(montant);

/** L'espace qui précède le symbole est une insécable (U+00A0), comme celle que
 *  pose `Intl.NumberFormat('fr-FR', {style: 'currency'})`. Écrite au clavier,
 *  l'assertion aurait échoué sur du code correct. */
const montantFr = (montant: number) => `${nombreFr(montant)}\u00A0€`;

const LIBELLES_FAUTIFS = [
  "Date d'emission",
  'Quantite',
  'Selectionner un contact',
  '10% (intermediaire)',
  '5,5% (reduite)',
  '2,1% (super reduite)',
  '0% (exonere)',
];

describe('B-221 : le devis parle français', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useBillingProfileStore.setState({ missing: null });
  });

  it('aucun libellé ne perd ses accents', async () => {
    const { container } = render(
      <InvoiceForm invoice={devis} onClose={vi.fn()} onSave={vi.fn()} />,
    );
    await waitFor(() => expect(screen.getByText(/Camille Martin/)).toBeInTheDocument());

    const rendu = container.textContent ?? '';
    const fautifs = LIBELLES_FAUTIFS.filter((libelle) => rendu.includes(libelle));
    expect(fautifs, `libellés sans accents à l'écran : ${fautifs.join(' | ')}`).toEqual([]);
  });

  it('les libellés accentués sont bien là', async () => {
    render(<InvoiceForm invoice={devis} onClose={vi.fn()} onSave={vi.fn()} />);
    await waitFor(() => expect(screen.getByText(/Camille Martin/)).toBeInTheDocument());

    // Sans ces présences, le test précédent passerait au vert en supprimant
    // simplement les libellés de l'écran.
    expect(screen.getByText(/Date d'émission/)).toBeInTheDocument();
    expect(screen.getByText('Quantité')).toBeInTheDocument();
    expect(screen.getByText('Sélectionner un contact')).toBeInTheDocument();
  });

  it('les totaux sont écrits à la française', async () => {
    const { container } = render(
      <InvoiceForm invoice={devis} onClose={vi.fn()} onSave={vi.fn()} />,
    );
    await waitFor(() => expect(screen.getByText(/Camille Martin/)).toBeInTheDocument());

    const rendu = container.textContent ?? '';
    for (const montant of [2400, 480, 2880]) {
      expect(rendu, `${montantFr(montant)} attendu`).toContain(montantFr(montant));
      expect(rendu).not.toContain(montant.toFixed(2));
    }
  });
});
