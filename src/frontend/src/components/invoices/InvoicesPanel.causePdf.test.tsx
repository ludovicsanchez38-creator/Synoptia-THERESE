/**
 * B-218 : la cause renvoyée par le serveur n'arrivait pas à l'écran.
 *
 * `/api/invoices/{id}/pdf` répond 400 avec une phrase actionnable — « Profil
 * émetteur incomplet : renseigne SIRET, adresse dans Réglages > Profil » — et
 * `services/api/invoices.ts` la porte fidèlement dans l'`Error`. Le `catch` du
 * panneau la remplaçait par « Impossible de générer le PDF » : le message
 * n'existait plus que dans la console, où l'utilisatrice ne regarde pas.
 *
 * Le test lit la notification affichée, pas l'appel d'API : c'est l'écran qui
 * était fautif, pas le client HTTP.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useInvoiceStore } from '../../stores/invoiceStore';
import { useStatusStore } from '../../stores/statusStore';

const mockListInvoices = vi.fn();
const mockGenerateInvoicePDF = vi.fn();

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listInvoices: (...args: unknown[]) => mockListInvoices(...args),
    generateInvoicePDF: (...args: unknown[]) => mockGenerateInvoicePDF(...args),
    deleteInvoice: vi.fn(),
    sendInvoiceByEmail: vi.fn(),
  };
});

vi.mock('./InvoiceForm', () => ({ InvoiceForm: () => <div data-testid="invoice-form" /> }));

import { InvoicesPanel } from './InvoicesPanel';

const CAUSE_SERVEUR =
  'Profil émetteur incomplet : renseigne SIRET, adresse dans Réglages > Profil '
  + 'avant de générer un document de facturation.';

const facture = {
  id: 'inv-1', invoice_number: 'FAC-001', contact_id: 'contact-1', currency: 'EUR',
  issue_date: '2026-03-14T00:00:00Z', due_date: '2026-03-31T00:00:00Z',
  status: 'draft' as const, subtotal_ht: 100, total_tax: 20, total_ttc: 120,
  notes: null, payment_date: null, created_at: '2026-03-14T00:00:00Z',
  updated_at: '2026-03-14T00:00:00Z', lines: [],
};

describe('B-218 : la cause renvoyée par le serveur arrive à l’écran', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    mockListInvoices.mockResolvedValue([facture]);
    useInvoiceStore.setState({
      invoices: [], currentInvoiceId: null, filters: { status: 'all' },
      isInvoicePanelOpen: true, draftInvoice: null,
    });
    useStatusStore.setState({ notifications: [] });
  });

  it('affiche le message du serveur, pas le générique', async () => {
    mockGenerateInvoicePDF.mockRejectedValue(new Error(CAUSE_SERVEUR));
    render(<InvoicesPanel standalone />);

    await screen.findByText('FAC-001');
    fireEvent.click(screen.getByTitle('Générer et ouvrir le PDF'));

    await waitFor(() => {
      expect(useStatusStore.getState().notifications).toHaveLength(1);
    });
    const notification = useStatusStore.getState().notifications[0];
    expect(notification.type).toBe('error');
    expect(notification.message).toContain('SIRET');
    expect(notification.message).toContain('Réglages > Profil');
  });

  it('garde un message lisible quand le serveur n’en donne aucun', async () => {
    // Une panne réseau ne rejette pas toujours avec une phrase utile : la
    // notification ne doit pas devenir vide en voulant devenir précise.
    mockGenerateInvoicePDF.mockRejectedValue(new Error(''));
    render(<InvoicesPanel standalone />);

    await screen.findByText('FAC-001');
    fireEvent.click(screen.getByTitle('Générer et ouvrir le PDF'));

    await waitFor(() => {
      expect(useStatusStore.getState().notifications).toHaveLength(1);
    });
    expect(useStatusStore.getState().notifications[0].message).toBe(
      'Impossible de générer le PDF',
    );
  });
});
