/**
 * DA « Application affinée », lot 5 : l'écran Devis et factures
 * (`docs/plans/2026-09-11-da-lot5-devis-design.md`, § 6).
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { filtresAvecType, useInvoiceStore } from '../../stores/invoiceStore';
import type { Invoice } from '../../services/api';

const mockListInvoices = vi.fn();

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listInvoices: (...args: unknown[]) => mockListInvoices(...args),
    deleteInvoice: vi.fn(),
    generateInvoicePDF: vi.fn(),
    sendInvoiceByEmail: vi.fn(),
  };
});

vi.mock('./InvoiceForm', () => ({
  InvoiceForm: ({ invoice }: { invoice?: { invoice_number: string } | null }) => (
    <div data-testid="invoice-form">{invoice ? invoice.invoice_number : 'nouveau'}</div>
  ),
}));

import { InvoicesPanel } from './InvoicesPanel';

const COULEUR_EN_DUR =
  /#[0-9A-Fa-f]{3,8}\b|(?<![A-Za-z])rgba?\(|(?<![A-Za-z])hsla?\(|\bcolor-mix\(/;
const COMMENTAIRE = /^\s*(\/\/|\*|\/\*)/;

function piece(patch: Partial<Invoice> = {}): Invoice {
  return {
    id: 'inv-1',
    invoice_number: 'FAC-001',
    contact_id: 'c1',
    contact_name: 'Marie Test',
    document_type: 'facture',
    tva_applicable: true,
    currency: 'EUR',
    issue_date: '2026-03-14T00:00:00Z',
    due_date: '2026-03-31T00:00:00Z',
    status: 'draft',
    subtotal_ht: 100,
    total_tax: 20,
    total_ttc: 120,
    notes: null,
    payment_terms: null,
    payment_method: null,
    late_penalty_rate: null,
    legal_mentions: null,
    converted_from_id: null,
    validite_jours: null,
    payment_date: null,
    created_at: '2026-03-14T00:00:00Z',
    updated_at: '2026-03-14T00:00:00Z',
    lines: [],
    ...patch,
  };
}

function classesDUnNoeud(n: Element): string {
  const brut = (n as HTMLElement).className;
  if (typeof brut === 'string') return brut;
  const svg = (n as SVGElement).className;
  return typeof svg === 'object' && svg && 'baseVal' in svg ? svg.baseVal : '';
}

function interactifsSousLePlancher(racine: HTMLElement): string[] {
  const fautifs: string[] = [];
  for (const el of racine.querySelectorAll(
    'button, input, select, textarea, a, [role="button"]',
  )) {
    const noeuds = [el, ...Array.from(el.querySelectorAll('*'))];
    for (const n of noeuds) {
      if (/\btext-xs\b/.test(classesDUnNoeud(n))) {
        fautifs.push(((el as HTMLElement).textContent ?? el.tagName).trim().slice(0, 48));
        break;
      }
    }
  }
  return fautifs;
}

function poser(invoices: Invoice[] = []) {
  mockListInvoices.mockResolvedValue(invoices);
  useInvoiceStore.setState({
    invoices: [],
    listeTronquee: false,
    currentInvoiceId: null,
    filters: { status: 'all' },
    isInvoicePanelOpen: true,
    draftInvoice: null,
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.spyOn(console, 'error').mockImplementation(() => {});
  poser([]);
});

describe('Lot 5 DA : une ligne est un tr', () => {
  it('invoice-item est un tr sans tabIndex, le clic Pièce ouvre, client + PDF + Supprimer', async () => {
    poser([piece()]);
    render(<InvoicesPanel standalone />);
    const row = await screen.findByTestId('invoice-item');
    expect(row.tagName).toBe('TR');
    expect(row.getAttribute('tabindex')).toBeNull();
    expect(row.getAttribute('tabIndex')).toBeNull();

    expect(within(row).getByRole('button', { name: 'Marie Test' })).toBeInTheDocument();
    expect(within(row).getByTitle('Générer et ouvrir le PDF')).toBeInTheDocument();
    expect(within(row).getByRole('button', { name: 'Générer et ouvrir le PDF' })).toHaveTextContent(
      'PDF',
    );
    expect(within(row).getByTitle('Supprimer')).toBeInTheDocument();
    expect(within(row).getByRole('button', { name: 'Supprimer' })).toBeInTheDocument();

    const tdPiece = row.querySelector('td');
    expect(tdPiece).not.toBeNull();
    fireEvent.click(tdPiece!);
    expect(await screen.findByTestId('invoice-form')).toHaveTextContent('FAC-001');
  });
});

describe('Lot 5 DA : trois colonnes de statut', () => {
  it('une facture overdue a deux étiquettes et une td d’échéance échue', async () => {
    poser([
      piece({
        status: 'overdue',
        issue_date: '2026-07-28T00:00:00Z',
        due_date: '2026-08-25T00:00:00Z',
      }),
    ]);
    render(<InvoicesPanel standalone />);
    const row = await screen.findByTestId('invoice-item');
    const etiquettes = row.querySelectorAll('[data-etiquette]');
    expect(etiquettes).toHaveLength(2);
    expect(etiquettes[0].className).toMatch(/\btext-info\b/);
    expect(etiquettes[1].className).toMatch(/\btext-error\b/);
    expect(etiquettes[1]).toHaveTextContent('Impayée');

    const tdEchue = Array.from(row.querySelectorAll('td')).find((td) =>
      (td.textContent ?? '').includes('· échue'),
    );
    expect(tdEchue).toBeDefined();
    expect(tdEchue!.className).toMatch(/\btext-error\b/);
    expect(tdEchue!.querySelector('[data-etiquette]')).toBeNull();

    const tdMontant = Array.from(row.querySelectorAll('td')).find((td) =>
      /\btabular-nums\b/.test(td.className) && (td.textContent ?? '').includes('€'),
    );
    expect(tdMontant).toBeDefined();
    expect(tdMontant!.className).toMatch(/\btabular-nums\b/);
  });

  it('un devis sent, un avoir sent/paid/overdue accordent envoi et paiement', async () => {
    poser([
      piece({
        id: 'd1',
        invoice_number: 'DEV-001',
        document_type: 'devis',
        status: 'sent',
        contact_name: 'Paul Durand',
      }),
      piece({
        id: 'a1',
        invoice_number: 'AV-001',
        document_type: 'avoir',
        status: 'sent',
        contact_name: 'Nadia Benali',
      }),
      piece({
        id: 'a2',
        invoice_number: 'AV-002',
        document_type: 'avoir',
        status: 'paid',
        payment_date: '2026-04-02T00:00:00Z',
        contact_name: 'Garage Benali',
      }),
      piece({
        id: 'a3',
        invoice_number: 'AV-003',
        document_type: 'avoir',
        status: 'overdue',
        contact_name: 'Claire Roux',
      }),
    ]);
    render(<InvoicesPanel standalone />);
    const rows = await screen.findAllByTestId('invoice-item');
    expect(rows).toHaveLength(4);

    const devis = rows[0];
    expect(devis).toHaveTextContent('Envoyé le');
    expect(devis).not.toHaveTextContent('Envoyée le');
    expect(devis).toHaveTextContent("En attente d'accord");
    expect(devis).toHaveTextContent('Valable jusqu\'au');

    const avoirSent = rows[1];
    expect(avoirSent).toHaveTextContent('Envoyé le');
    expect(avoirSent).not.toHaveTextContent('Envoyée le');
    expect(within(avoirSent).getByText('Impayé')).toBeInTheDocument();
    expect(within(avoirSent).queryByText('Impayée')).toBeNull();

    const avoirPaid = rows[2];
    expect(avoirPaid.textContent ?? '').toMatch(/Payé le/);
    expect(avoirPaid).not.toHaveTextContent('Payée');

    const avoirOverdue = rows[3];
    expect(within(avoirOverdue).getByText('Impayé')).toBeInTheDocument();
    expect(avoirOverdue).toHaveTextContent('· échue');
  });
});

describe('Lot 5 DA : compteur et dates', () => {
  it('accorde pièce / pièces, dont échues, et 100+ sans dont', async () => {
    poser([piece()]);
    const { unmount } = render(<InvoicesPanel standalone />);
    expect(await screen.findByTestId('invoices-compteur')).toHaveTextContent('1 pièce');
    expect(screen.getByTestId('invoices-compteur')).not.toHaveTextContent('dont');
    unmount();

    poser([piece({ id: 'a' }), piece({ id: 'b', invoice_number: 'FAC-002' })]);
    const r2 = render(<InvoicesPanel standalone />);
    expect(await screen.findByTestId('invoices-compteur')).toHaveTextContent('2 pièces');
    r2.unmount();

    poser([]);
    const r0 = render(<InvoicesPanel standalone />);
    expect(await screen.findByTestId('invoices-compteur')).toHaveTextContent('0 pièce');
    r0.unmount();

    poser([
      piece({ id: 'ok', status: 'draft' }),
      piece({ id: 'late', invoice_number: 'FAC-002', status: 'overdue' }),
    ]);
    const rDont = render(<InvoicesPanel standalone />);
    expect(await screen.findByTestId('invoices-compteur')).toHaveTextContent(
      '2 pièces, dont 1 pièce échue',
    );
    rDont.unmount();

    poser([
      piece({ id: 'l1', status: 'overdue' }),
      piece({ id: 'l2', invoice_number: 'FAC-002', status: 'overdue' }),
    ]);
    const rDont2 = render(<InvoicesPanel standalone />);
    expect(await screen.findByTestId('invoices-compteur')).toHaveTextContent(
      'dont 2 pièces échues',
    );
    rDont2.unmount();

    const cent = Array.from({ length: 100 }, (_, i) =>
      piece({ id: `inv-${i}`, invoice_number: `FAC-${i}`, status: 'draft' }),
    );
    poser(cent);
    render(<InvoicesPanel standalone />);
    const compteur = await screen.findByTestId('invoices-compteur');
    expect(compteur).toHaveTextContent('100+ pièces');
    expect(compteur).not.toHaveTextContent('dont');
  }, 20000);

  it('un brouillon devis montre l’échéance avec l’année et la validité, pas « Non envoyé »', async () => {
    poser([
      piece({
        id: 'd-draft',
        invoice_number: 'DEV-009',
        document_type: 'devis',
        status: 'draft',
        validite_jours: 45,
        due_date: '2026-10-05T00:00:00Z',
      }),
    ]);
    render(<InvoicesPanel standalone />);
    const row = await screen.findByTestId('invoice-item');
    expect(row.tagName).toBe('TR');
    const tdEcheance = Array.from(row.querySelectorAll('td')).find((td) =>
      /2026/.test(td.textContent ?? ''),
    );
    expect(tdEcheance, 'l’échéance avec l’année vit dans une td').toBeDefined();
    expect(row).toHaveTextContent('Validité : 45 jours');
    expect(row).not.toHaveTextContent('Non envoyé');
  });
});

describe('Lot 5 DA : Segments Type et Statut', () => {
  it('Tout et Toutes sont pressés au départ ; Devis assainit comme aujourd’hui', async () => {
    mockListInvoices.mockResolvedValue([]);
    useInvoiceStore.setState({
      invoices: [],
      listeTronquee: false,
      currentInvoiceId: null,
      filters: { status: 'paid' },
      isInvoicePanelOpen: true,
      draftInvoice: null,
    });
    render(<InvoicesPanel standalone />);
    await waitFor(() => expect(mockListInvoices).toHaveBeenCalled());

    fireEvent.click(screen.getByRole('button', { name: 'Tout' }));
    fireEvent.click(screen.getByRole('button', { name: 'Toutes' }));

    const type = screen.getByRole('group', { name: 'Type' });
    expect(within(type).getByRole('button', { name: 'Tout' })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
    const statut = screen.getByRole('group', { name: 'Statut' });
    expect(within(statut).getByRole('button', { name: 'Toutes' })).toHaveAttribute(
      'aria-pressed',
      'true',
    );

    useInvoiceStore.setState({ filters: { status: 'paid', document_type: 'facture' } });
    const avant = useInvoiceStore.getState().filters;
    fireEvent.click(screen.getByRole('button', { name: 'Devis' }));
    expect(useInvoiceStore.getState().filters).toEqual(filtresAvecType(avant, 'devis'));
  });
});

describe('Lot 5 DA : états dans la Carte', () => {
  it('un seul Réessayer sur l’erreur ; squelettes 7 pistes ; trois vides distincts', async () => {
    mockListInvoices.mockReturnValue(new Promise(() => {}));
    const { unmount: unmountLoad } = render(<InvoicesPanel standalone />);
    const status = await screen.findByRole('status');
    expect(status).toHaveTextContent('Chargement...');
    const carteLoad = status.closest('section');
    expect(carteLoad).not.toBeNull();
    expect(carteLoad!.querySelector('table')).toBeNull();
    const rangees = carteLoad!.querySelectorAll('[aria-hidden].grid');
    expect(rangees.length).toBe(3);
    for (const rangee of rangees) {
      expect(rangee.className).toMatch(/\bgrid-cols-7\b/);
      expect(rangee.querySelectorAll('[aria-hidden]')).toHaveLength(7);
    }
    expect(screen.queryByRole('button', { name: 'Réessayer' })).toBeNull();
    unmountLoad();

    poser([]);
    mockListInvoices.mockRejectedValue(new Error('500'));
    const { unmount: unmountErr } = render(<InvoicesPanel standalone />);
    expect(await screen.findByTestId('invoices-load-error')).toHaveTextContent(
      /Impossible de charger les factures/,
    );
    expect(screen.getByTestId('invoices-load-error').closest('section')).not.toBeNull();
    expect(screen.getAllByRole('button', { name: 'Réessayer' })).toHaveLength(1);
    expect(screen.queryByTestId('invoices-empty')).toBeNull();
    unmountErr();

    poser([]);
    useInvoiceStore.setState({ filters: { status: 'overdue' } });
    const { unmount: unmountOverdue } = render(<InvoicesPanel standalone />);
    const videOverdue = await screen.findByTestId('invoices-empty-overdue');
    expect(videOverdue.closest('section')).not.toBeNull();
    expect(within(videOverdue).getByRole('heading', { name: 'Aucune pièce en retard' })).toBeInTheDocument();
    expect(videOverdue).toHaveTextContent('Les factures échues et impayées apparaîtront ici.');
    expect(screen.queryByTestId('invoices-empty')).toBeNull();
    expect(screen.queryByTestId('invoices-empty-filtre')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Réessayer' })).toBeNull();
    unmountOverdue();

    poser([]);
    useInvoiceStore.setState({ filters: { status: 'paid' } });
    const { unmount: unmountFiltre } = render(<InvoicesPanel standalone />);
    const videFiltre = await screen.findByTestId('invoices-empty-filtre');
    expect(videFiltre.closest('section')).not.toBeNull();
    expect(videFiltre).toHaveTextContent('Aucun document ne correspond à ce filtre.');
    expect(screen.queryByTestId('invoices-empty-overdue')).toBeNull();
    expect(screen.queryByTestId('invoices-empty')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Réessayer' })).toBeNull();
    unmountFiltre();

    poser([]);
    useInvoiceStore.setState({ filters: { status: 'all' } });
    render(<InvoicesPanel standalone />);
    const vide = await screen.findByTestId('invoices-empty');
    expect(vide.closest('section')).not.toBeNull();
    expect(within(vide).getByRole('heading', { name: 'Aucune facture' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Créer une facture' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Réessayer' })).toBeNull();
  });
});

describe('Lot 5 DA : plancher, jetons, hauteurs', () => {
  it('aucun interactif en text-xs ; source sans couleur en dur hors voile /60', async () => {
    poser([piece({ status: 'overdue' })]);
    render(<InvoicesPanel standalone />);
    const panneau = await screen.findByTestId('invoices-panel');
    expect(interactifsSousLePlancher(panneau)).toEqual([]);

    for (const fichier of ['InvoicesPanel.tsx', 'InvoiceForm.tsx']) {
      const source = readFileSync(join(__dirname, fichier), 'utf8');
      const fautifs: string[] = [];
      source.split('\n').forEach((ligne, i) => {
        if (COMMENTAIRE.test(ligne)) return;
        if (COULEUR_EN_DUR.test(ligne)) fautifs.push(`${fichier}:${i + 1}`);
        if (/\bbg-gray-/.test(ligne) || /\btext-agent-/.test(ligne) || /\bbg-agent-/.test(ligne)) {
          fautifs.push(`${fichier}:${i + 1}`);
        }
        const noirs = ligne.match(/\bbg-black(?:\/[\d.]+)?/g) ?? [];
        if (noirs.some((n) => n !== 'bg-black/60')) fautifs.push(`${fichier}:${i + 1}`);
      });
      expect(fautifs, fichier).toEqual([]);
    }
  });

  it('Nouveau devis est h-11 ; les autres Button du panneau sont h-9 (hors Segments)', async () => {
    poser([piece()]);
    render(<InvoicesPanel standalone />);
    await screen.findByTestId('invoice-item');
    const geste = screen.getByRole('button', { name: /Nouveau devis|Nouvelle facture/ });
    expect(geste.className).toMatch(/\bh-11\b/);

    for (const bouton of screen.getAllByRole('button')) {
      if (bouton.closest('[role="group"]')) continue;
      if (bouton === geste) continue;
      // Commande client (B-208) : <button> texte, pas le primitive Button.
      if (!/\bh-9\b|\bh-11\b|\bh-8\b/.test(bouton.className)) continue;
      expect(bouton.className, bouton.textContent ?? '').toMatch(/\bh-9\b/);
      expect(bouton.className).not.toMatch(/\bh-11\b/);
    }
  });
});
