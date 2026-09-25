/**
 * B-1393 et B-1400 (persona Zoé, cycle 13) : la saisie des montants d'un devis.
 *
 * - Quantité « 1 » sélectionnée, « -2 » tapé : le « - » était refusé, le champ
 *   redessiné plaçait le curseur en fin, et le « 2 » s'ajoutait : 12, soit
 *   14 407 € TTC au lieu de 1 200 €, sans alerte. Une touche refusée rend
 *   désormais la sélection d'avant.
 * - « 1 000,50 € » collé dans un prix ne faisait rien (espaces et symbole
 *   refusés en bloc) ; ils sont retirés avant validation.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';

const { getBillingProfileStatusMock } = vi.hoisted(() => ({
  getBillingProfileStatusMock: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([
      { id: 'contact-1', first_name: 'Jean', last_name: 'Dupont', email: 'jean@example.com' },
    ]),
    createInvoice: vi.fn(),
    getBillingProfileStatus: getBillingProfileStatusMock,
  };
});


describe('B-1393 et B-1400 : saisie des montants du devis', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    useBillingProfileStore.setState({ missing: null });
  });
  afterEach(() => _clearEscapeHandlers());

  it('une touche refusée rend la sélection d’avant', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText(/Client/i);
    const quantite = screen.getByLabelText('Quantité ligne 1') as HTMLInputElement;
    quantite.focus();
    quantite.setSelectionRange(0, 1);
    fireEvent.select(quantite);

    fireEvent.change(quantite, { target: { value: '-' } });
    await act(async () => { await new Promise((r) => requestAnimationFrame(() => r(null))); });

    expect(quantite.value).toBe('1');
    expect([quantite.selectionStart, quantite.selectionEnd]).toEqual([0, 1]);
  });

  it('« 1 000,50 € » collé dans un prix devient 1000,50', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText(/Client/i);
    const prix = screen.getByLabelText('Prix HT ligne 1') as HTMLInputElement;
    fireEvent.change(prix, { target: { value: '1\u202f000,50\u00a0€' } });
    expect(prix.value).toBe('1000,50');
    fireEvent.change(prix, { target: { value: '2 400 €' } });
    expect(prix.value).toBe('2400');
  });
});
