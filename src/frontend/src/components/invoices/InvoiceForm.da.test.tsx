/**
 * DA « Application affinée », lot 5 : le formulaire Devis et factures
 * (`docs/plans/2026-09-11-da-lot5-devis-design.md`, § 6).
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { useStatusStore } from '../../stores/statusStore';
import type { Invoice } from '../../services/api';

const { createInvoiceMock, getBillingProfileStatusMock } = vi.hoisted(() => ({
  createInvoiceMock: vi.fn(),
  getBillingProfileStatusMock: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([
      { id: 'contact-1', first_name: 'Jean', last_name: 'Dupont', email: 'jean@example.com' },
    ]),
    createInvoice: createInvoiceMock,
    getBillingProfileStatus: getBillingProfileStatusMock,
  };
});

const devisSent: Invoice = {
  id: 'devis-1',
  invoice_number: 'DEV-2026-001',
  contact_id: 'contact-1',
  document_type: 'devis',
  tva_applicable: true,
  currency: 'EUR',
  issue_date: '2026-07-01T00:00:00Z',
  due_date: '2026-07-31T00:00:00Z',
  status: 'sent',
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
  created_at: '2026-07-01T08:00:00Z',
  updated_at: '2026-07-01T08:00:00Z',
  lines: [
    {
      id: 'line-1',
      invoice_id: 'devis-1',
      description: 'Accompagnement',
      quantity: 1,
      unit_price_ht: 100,
      tva_rate: 20,
      total_ht: 100,
      total_ttc: 120,
    },
  ],
};

function boutonsSubmit(container: HTMLElement): HTMLButtonElement[] {
  return Array.from(container.querySelectorAll('button')).filter(
    (b) => (b.getAttribute('type') ?? 'submit') === 'submit',
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  createInvoiceMock.mockResolvedValue({ id: 'inv-1' });
  getBillingProfileStatusMock.mockResolvedValue({ is_complete: true, missing: [] });
  useBillingProfileStore.setState({ missing: null, statutLecture: 'ok' });
  useStatusStore.setState({ notifications: [] });
});

describe('Lot 5 DA : types des Button', () => {
  it('le seul submit porte form=invoice-form ; les autres Button sont type=button ; Refuser est secondary', async () => {
    const { container } = render(
      <InvoiceForm invoice={devisSent} onClose={vi.fn()} onSave={vi.fn()} />,
    );
    await screen.findByLabelText('Client *');

    const submits = boutonsSubmit(container);
    expect(submits).toHaveLength(1);
    expect(submits[0].getAttribute('form')).toBe('invoice-form');
    expect(submits[0].getAttribute('type')).toBe('submit');

    for (const bouton of container.querySelectorAll('button')) {
      if (bouton === submits[0]) continue;
      expect(bouton, bouton.textContent ?? '').toHaveAttribute('type', 'button');
    }

    const refuser = screen.getByRole('button', { name: 'Refuser' });
    expect(refuser.className).toMatch(/\btext-text\b/);
    expect(refuser.className).not.toMatch(/\btext-accent\b/);

    fireEvent.click(screen.getByRole('button', { name: 'Convertir en facture' }));
    const dialogue = await screen.findByRole('dialog', { name: 'Confirmer la conversion' });
    for (const bouton of dialogue.querySelectorAll('button')) {
      expect(bouton, bouton.textContent ?? '').toHaveAttribute('type', 'button');
    }
  });
});

describe('Lot 5 DA : BUG-132 par ligne', () => {
  it('toutes les lignes vides : notification conservée et erreur sur chaque ligne', async () => {
    const notif = vi.fn();
    useStatusStore.setState({ addNotification: notif });
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByRole('option', { name: 'Jean Dupont' });
    fireEvent.change(screen.getByLabelText('Client *'), { target: { value: 'contact-1' } });
    fireEvent.click(screen.getByRole('button', { name: /Ajouter une ligne/i }));

    fireEvent.click(screen.getByRole('button', { name: /Créer/i }));

    expect(createInvoiceMock).not.toHaveBeenCalled();
    const messages = notif.mock.calls.map((c) => (c[0]?.message as string) ?? '');
    expect(messages.some((m) => /description d.un moins une ligne|description d’au moins une ligne/i.test(m) || /au moins une ligne/i.test(m))).toBe(true);

    const l1 = screen.getByLabelText('Description ligne 1');
    const l2 = screen.getByLabelText('Description ligne 2');
    expect(l1).toHaveAttribute('aria-invalid', 'true');
    expect(l2).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getAllByText('Renseigne la description de cette ligne, ou supprime-la.')).toHaveLength(2);
  });

  it('ligne 1 remplie, ligne 2 vide : pas de notif BUG-132, focus sur la ligne 2, l’erreur tombe à la saisie', async () => {
    const notif = vi.fn();
    useStatusStore.setState({ addNotification: notif });
    const { container } = render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByRole('option', { name: 'Jean Dupont' });
    fireEvent.change(screen.getByLabelText('Client *'), { target: { value: 'contact-1' } });
    fireEvent.click(screen.getByRole('button', { name: /Ajouter une ligne/i }));
    fireEvent.change(screen.getByLabelText('Description ligne 1'), { target: { value: 'Prestation' } });

    const formulaire = container.querySelector('#invoice-form') as HTMLFormElement;
    formulaire.requestSubmit();

    await waitFor(() => {
      expect(screen.getByLabelText('Description ligne 2')).toHaveAttribute('aria-invalid', 'true');
    });
    expect(createInvoiceMock).not.toHaveBeenCalled();
    const messages = notif.mock.calls.map((c) => (c[0]?.message as string) ?? '');
    expect(messages.some((m) => /au moins une ligne/i.test(m))).toBe(false);
    expect(screen.getByLabelText('Description ligne 1')).not.toHaveAttribute('aria-invalid');
    expect(screen.getByText('Renseigne la description de cette ligne, ou supprime-la.')).toBeInTheDocument();
    expect(document.activeElement).toBe(screen.getByLabelText('Description ligne 2'));
    expect(document.activeElement).toHaveAttribute('id', 'invoiceform-description-1');

    fireEvent.change(screen.getByLabelText('Description ligne 2'), { target: { value: 'Fourniture' } });
    expect(screen.getByLabelText('Description ligne 2')).not.toHaveAttribute('aria-invalid');
    expect(screen.queryByText('Renseigne la description de cette ligne, ou supprime-la.')).toBeNull();
  });
});

describe('Lot 5 DA : Segments, noms, ids', () => {
  it('Segments Type de document en création', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);
    const groupe = await screen.findByRole('group', { name: 'Type de document' });
    expect(groupe.querySelector('[aria-pressed="true"]')).toHaveTextContent('Facture');
    expect(screen.getByRole('button', { name: 'Devis' })).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByRole('button', { name: 'Avoir' })).toHaveAttribute('aria-pressed', 'false');
  });

  it('Fermer et Supprimer la ligne 1 restent nommés, icônes 18 px', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);
    const fermer = await screen.findByRole('button', { name: 'Fermer' });
    const supprimer = screen.getByRole('button', { name: 'Supprimer la ligne 1' });
    expect(fermer.querySelector('svg')?.getAttribute('class')).toMatch(/h-\[18px\]/);
    expect(fermer.querySelector('svg')?.getAttribute('class')).toMatch(/w-\[18px\]/);
    expect(supprimer.querySelector('svg')?.getAttribute('class')).toMatch(/h-\[18px\]/);
    expect(supprimer.querySelector('svg')?.getAttribute('class')).toMatch(/w-\[18px\]/);
  });

  it('ids uniques, libellés conservés, titre des lignes', async () => {
    const { container } = render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText('Client *');

    expect(container.querySelector('#invoiceform-description-0')).not.toBeNull();
    expect(container.querySelector('#invoiceform-prix-0')).not.toBeNull();
    expect(container.querySelector('#invoiceform-tva-0')).not.toBeNull();
    expect(screen.getByLabelText('Quantité ligne 1')).toBeInTheDocument();
    expect(screen.getByLabelText('Prix HT ligne 1')).toBeInTheDocument();
    expect(screen.getByLabelText('TVA ligne 1')).toBeInTheDocument();
    expect(screen.getByLabelText('Client *')).toBeInTheDocument();
    expect(screen.getByLabelText("Date d'émission *")).toBeInTheDocument();
    expect(screen.getByText('Lignes de facturation *')).toBeInTheDocument();

    const ids = [...container.querySelectorAll('[id]')].map((n) => n.id);
    const doublons = ids.filter((id, i) => ids.indexOf(id) !== i);
    expect(doublons).toEqual([]);
  });
});
