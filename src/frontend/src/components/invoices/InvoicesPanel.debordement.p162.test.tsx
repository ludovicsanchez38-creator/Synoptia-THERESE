/**
 * P162 : le tableau annonce les colonnes hors cadre sans ajouter de commande.
 * Géométries contrôlées en jsdom ; les gestes natifs sont vérifiés séparément.
 * Le cadre original reste une cible valide pour le rouge : aucune absence de
 * rôle ne doit masquer l'assertion de l'indice réellement manquant.
 */
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useInvoiceStore } from '../../stores/invoiceStore';
import { useStatusStore } from '../../stores/statusStore';
import type { Invoice } from '../../services/api';

const mockListInvoices = vi.fn();
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, listInvoices: (...args: unknown[]) => mockListInvoices(...args) };
});
vi.mock('./InvoiceForm', () => ({ InvoiceForm: () => <div data-testid="invoice-form" /> }));

import { InvoicesPanel } from './InvoicesPanel';

const devis: Invoice = {
  id: 'piece-p162', invoice_number: 'DEV-2026-004', contact_id: 'c-p162', contact_name: 'Témoin largeur',
  document_type: 'devis', tva_applicable: true, currency: 'EUR',
  issue_date: '2026-10-01T00:00:00Z', due_date: '2026-10-25T00:00:00Z', status: 'draft',
  subtotal_ht: 300, total_tax: 60, total_ttc: 360, notes: null, payment_date: null,
  validite_jours: 30, payment_terms: null, payment_method: null, late_penalty_rate: null,
  legal_mentions: null, converted_from_id: null,
  created_at: '2026-10-01T00:00:00Z', updated_at: '2026-10-01T00:00:00Z', lines: [],
};

class ObservateurTemoin {
  static instances: ObservateurTemoin[] = [];
  readonly observe = vi.fn();
  readonly unobserve = vi.fn();
  readonly disconnect = vi.fn();
  constructor(readonly callback: ResizeObserverCallback) { ObservateurTemoin.instances.push(this); }
}

beforeEach(() => {
  vi.clearAllMocks();
  ObservateurTemoin.instances = [];
  vi.stubGlobal('ResizeObserver', ObservateurTemoin);
  mockListInvoices.mockResolvedValue([devis]);
  useInvoiceStore.setState({ invoices: [], currentInvoiceId: null, filters: { status: 'all' }, isInvoicePanelOpen: true, draftInvoice: null });
  useStatusStore.setState({ notifications: [] });
});
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

async function rendre(standalone = true) {
  const result = render(<InvoicesPanel standalone={standalone} />);
  await screen.findByTestId('invoice-item');
  const table = screen.getByRole('table');
  const frame = screen.queryByRole('region', { name: 'Tableau des devis et factures' }) ?? table.closest('section');
  expect(frame).not.toBeNull();
  return { ...result, table, frame: frame as HTMLElement };
}

function geometry(frame: HTMLElement, { width = 694, total = 1086, left = 0 } = {}) {
  Object.defineProperties(frame, {
    clientWidth: { configurable: true, value: width },
    scrollWidth: { configurable: true, value: total },
  });
  frame.scrollLeft = left;
}

function indication(frame: HTMLElement) {
  return (frame.getAttribute('aria-describedby') ?? '').split(/\s+/).filter(Boolean)
    .map(id => document.getElementById(id)).filter((e): e is HTMLElement => Boolean(e));
}
function mention(frame: HTMLElement) { return indication(frame).map(e => e.textContent).join(' '); }

describe('P162 : indice passif sur le vrai scroller du tableau', () => {
  it('annonce les colonnes à droite au cadrage initial de 800 px', async () => {
    const { frame } = await rendre();
    geometry(frame); fireEvent.scroll(frame);
    expect(mention(frame)).toMatch(/colonnes.*droite/i);
    expect(mention(frame)).not.toMatch(/gauche/i);
    expect(frame).toHaveAccessibleDescription(/droite/i);
  });

  it('annonce les deux côtés au milieu puis seulement la gauche au bord', async () => {
    const { frame } = await rendre();
    geometry(frame, { left: 200 }); fireEvent.scroll(frame);
    expect(mention(frame)).toMatch(/gauche/i);
    expect(mention(frame)).toMatch(/droite/i);
    geometry(frame, { left: 392 }); fireEvent.scroll(frame);
    expect(mention(frame)).toMatch(/gauche/i);
    expect(mention(frame)).not.toMatch(/droite/i);
  });

  it('nomme et focalise le cadre qui fait réellement défiler le tableau', async () => {
    const { frame, table } = await rendre();
    expect(frame).toHaveAttribute('role', 'region');
    expect(frame).toHaveAccessibleName('Tableau des devis et factures');
    expect(frame).toHaveAttribute('tabindex', '0');
    expect(frame.className).toMatch(/overflow-x-auto/);
    expect(frame.className).toMatch(/focus-visible:/);
    expect(frame.contains(table)).toBe(true);
  });

  it('décrit le défilement avant les lignes sans ajouter de bouton', async () => {
    const { frame, table } = await rendre();
    geometry(frame); fireEvent.scroll(frame);
    const hints = indication(frame);
    expect(hints.length).toBeGreaterThan(0);
    for (const hint of hints) {
      expect(hint.compareDocumentPosition(table) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
      expect(hint.tabIndex).toBeLessThan(0);
      expect(hint.tagName).not.toBe('BUTTON');
      expect(hint.querySelector('button, a, [tabindex="0"]')).toBeNull();
    }
  });

  it('réagit à un changement de cadre et retire toute description lorsque le tableau tient', async () => {
    const { frame } = await rendre();
    geometry(frame); fireEvent.scroll(frame);
    expect(mention(frame)).toMatch(/droite/i);
    geometry(frame, { width: 1200 }); fireEvent(window, new Event('resize'));
    expect(mention(frame)).toBe('');
    expect(frame).not.toHaveAttribute('aria-describedby');
    geometry(frame); fireEvent(window, new Event('resize'));
    expect(mention(frame)).toMatch(/droite/i);
  });

  it('recalcule la largeur de contenu observée même lorsque le cadre ne change pas', async () => {
    const { frame, table } = await rendre();
    geometry(frame, { total: 600 }); fireEvent.scroll(frame);
    expect(mention(frame)).toBe('');
    const observer = ObservateurTemoin.instances.find(o => o.observe.mock.calls.some(([e]) => e === table));
    expect(observer).toBeDefined();
    geometry(frame);
    act(() => { observer!.callback([], observer! as unknown as ResizeObserver); });
    expect(mention(frame)).toMatch(/droite/i);
  });

  it.each([
    { left: -10, right: true, leftHint: false },
    { left: 0.5, right: true, leftHint: false },
    { left: 391.5, right: false, leftHint: true },
    { left: 1000, right: false, leftHint: true },
  ])('borne le sous-pixel et la position $left', async ({ left, right, leftHint }) => {
    const { frame } = await rendre();
    geometry(frame, { left }); fireEvent.scroll(frame);
    expect(/gauche/i.test(mention(frame))).toBe(leftHint);
    expect(/droite/i.test(mention(frame))).toBe(right);
  });

  it('n’annonce aucune largeur cachée avant qu’un cadre mesurable existe', async () => {
    const { frame } = await rendre();
    geometry(frame, { width: 0 }); fireEvent.scroll(frame);
    expect(mention(frame)).toBe('');
  });

  it('garde exactement le focus lors de la disparition de l’indice', async () => {
    const { frame } = await rendre();
    geometry(frame); fireEvent.scroll(frame);
    expect(mention(frame)).toMatch(/droite/i);
    act(() => { frame.focus(); });
    expect(frame).toHaveFocus();
    geometry(frame, { width: 1200 }); fireEvent(window, new Event('resize'));
    expect(frame).toHaveFocus();
    expect(mention(frame)).toBe('');
  });

  it('préserve le focus d’un filtre pendant le défilement et le recalcul', async () => {
    const { frame } = await rendre();
    const filtre = screen.getByRole('button', { name: 'Avoirs' });
    act(() => { filtre.focus(); });
    geometry(frame, { left: 200 }); fireEvent.scroll(frame);
    expect(mention(frame)).toMatch(/gauche/i);
    expect(filtre).toHaveFocus();
    geometry(frame, { width: 1200 }); fireEvent(window, new Event('resize'));
    expect(filtre).toHaveFocus();
  });

  it('retire l’indice pendant le rechargement puis recalcule après une liste remplacée', async () => {
    const { frame } = await rendre();
    geometry(frame); fireEvent.scroll(frame);
    expect(mention(frame)).toMatch(/droite/i);
    let resolve: (value: Invoice[]) => void = () => {};
    mockListInvoices.mockImplementationOnce(() => new Promise<Invoice[]>(r => { resolve = r; }));
    fireEvent.click(screen.getByRole('button', { name: 'Devis' }));
    await screen.findByText('Chargement...');
    expect(mention(frame)).toBe('');
    expect(frame.tabIndex).toBe(-1);
    await act(async () => { resolve([devis]); });
    await screen.findByTestId('invoice-item');
    geometry(frame); fireEvent.scroll(frame);
    expect(mention(frame)).toMatch(/droite/i);
  });

  it('ne garde aucun indice périmé après un chargement échoué', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    const { frame } = await rendre();
    geometry(frame); fireEvent.scroll(frame);
    expect(mention(frame)).toMatch(/droite/i);
    mockListInvoices.mockRejectedValueOnce(new Error('Lecture témoin indisponible'));
    fireEvent.click(screen.getByRole('button', { name: 'Devis' }));
    await screen.findByTestId('invoices-load-error');
    expect(mention(frame)).toBe('');
    expect(frame.tabIndex).toBe(-1);
  });

  it('retire indice et arrêt clavier quand le filtre ne contient aucune pièce', async () => {
    const { frame } = await rendre();
    geometry(frame); fireEvent.scroll(frame);
    expect(mention(frame)).toMatch(/droite/i);
    mockListInvoices.mockResolvedValueOnce([]);
    fireEvent.click(screen.getByRole('button', { name: 'Avoirs' }));
    await screen.findByTestId('invoices-empty-filtre');
    expect(mention(frame)).toBe('');
    expect(frame.tabIndex).toBe(-1);
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('observe de nouveau après fermeture puis réouverture du panneau modal', async () => {
    const { frame } = await rendre(false);
    geometry(frame); fireEvent.scroll(frame);
    expect(mention(frame)).toMatch(/droite/i);
    act(() => { useInvoiceStore.getState().setIsInvoicePanelOpen(false); });
    await waitFor(() => expect(screen.queryByTestId('invoices-panel')).not.toBeInTheDocument());
    act(() => { useInvoiceStore.getState().setIsInvoicePanelOpen(true); });
    await screen.findByTestId('invoice-item');
    const nouveau = screen.getByRole('region', { name: 'Tableau des devis et factures' });
    geometry(nouveau); fireEvent.scroll(nouveau);
    expect(mention(nouveau)).toMatch(/droite/i);
  });

  it('nettoie son observateur au démontage et garde TTC/PDF/Supprimer collés', async () => {
    const { frame, unmount } = await rendre();
    geometry(frame); fireEvent.scroll(frame);
    const observers = ObservateurTemoin.instances.filter(o => o.observe.mock.calls.some(([e]) => e === frame));
    expect(observers.length).toBeGreaterThan(0);
    const ligne = screen.getByTestId('invoice-item');
    const cell = within(ligne).getAllByRole('cell').at(-1)!;
    expect(cell.className).toMatch(/sticky/);
    expect(cell.className).toMatch(/right-0/);
    expect(within(cell).getByRole('button', { name: 'Supprimer' })).toBeInTheDocument();
    expect(within(cell).getByRole('button', { name: /PDF/ })).toBeInTheDocument();
    unmount();
    expect(observers.every(o => o.disconnect.mock.calls.length > 0)).toBe(true);
  });
});
