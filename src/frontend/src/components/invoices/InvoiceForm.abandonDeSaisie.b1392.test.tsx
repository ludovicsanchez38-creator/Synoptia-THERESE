/**
 * B-1392 (persona Zoé, cycle 13) : Échap, la croix ou un clic sur le fond
 * jetaient un devis en cours de saisie (une ligne à 1 800 €), sans demander.
 * Comme Tâche et Rendez-vous, la modale pose « Abandonner les modifications ? »
 * quand la saisie a changé ; intacte, elle se ferme seule (contrat B-228 : la
 * pile consomme Échap, le panneau dessous reste).
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';

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


const QUESTION = 'Abandonner les modifications ?';

describe('B-1392 : le devis demande avant de jeter la saisie', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
    useBillingProfileStore.setState({ missing: null });
  });
  afterEach(() => _clearEscapeHandlers());

  it('Échap sur une saisie modifiée pose la question, sans fermer', async () => {
    const fermer = vi.fn();
    render(<InvoiceForm invoice={null} onClose={fermer} onSave={vi.fn()} />);
    await screen.findByLabelText(/Client/i);
    fireEvent.change(screen.getByLabelText('Description ligne 1'), { target: { value: 'Vitrine réfrigérée' } });

    let consomme = false;
    act(() => { consomme = runTopEscapeHandler(); });
    expect(consomme).toBe(true);
    expect(screen.getByText(QUESTION)).toBeInTheDocument();
    expect(fermer).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Abandonner' }));
    expect(fermer).toHaveBeenCalledTimes(1);
  });

  it('la croix sur une saisie modifiée pose la question', async () => {
    const fermer = vi.fn();
    render(<InvoiceForm invoice={null} onClose={fermer} onSave={vi.fn()} />);
    await screen.findByLabelText(/Client/i);
    fireEvent.change(screen.getByLabelText('Description ligne 1'), { target: { value: 'Pose' } });
    fireEvent.click(screen.getByRole('button', { name: 'Fermer' }));
    expect(screen.getByText(QUESTION)).toBeInTheDocument();
    expect(fermer).not.toHaveBeenCalled();
  });

  it('intacte, Échap ferme la modale seule, sans question', async () => {
    const fermer = vi.fn();
    render(<InvoiceForm invoice={null} onClose={fermer} onSave={vi.fn()} />);
    await screen.findByLabelText(/Client/i);
    let consomme = false;
    act(() => { consomme = runTopEscapeHandler(); });
    expect(consomme).toBe(true);
    expect(fermer).toHaveBeenCalledTimes(1);
  });
});
