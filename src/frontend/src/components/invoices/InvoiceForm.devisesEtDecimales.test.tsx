/**
 * B-039 : remplace les gardes textuelles de tests/test_regression.py (BUG-091,
 * QW CAD, TVA) qui lisaient le source d'InvoiceForm. Ici on rend le
 * formulaire et on regarde ce qu'il offre réellement.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([]),
    getBillingProfileStatus: vi.fn().mockResolvedValue({ complete: true, missing: [] }),
  };
});

describe('InvoiceForm : devises, TVA et saisie décimale', () => {
  it('propose l’euro, le franc suisse, le dollar, la livre et le dollar canadien', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText('Prix HT ligne 1');
    const options = Array.from(document.querySelectorAll('option')).map((o) => o.value);
    for (const devise of ['EUR', 'CHF', 'USD', 'GBP', 'CAD']) {
      expect(options).toContain(devise);
    }
  });

  it('propose les taux de TVA français, dont le taux normal à 20 %', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);
    await screen.findByLabelText('Prix HT ligne 1');
    const libelles = Array.from(document.querySelectorAll('option')).map((o) => o.textContent ?? '');
    expect(libelles.some((l) => l.includes('20'))).toBe(true);
    expect(libelles.some((l) => l.includes('5,5') || l.includes('5.5'))).toBe(true);
  });

  it('accepte la virgule et le point comme séparateur décimal, sans clavier numérique strict', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);
    const quantite = await screen.findByLabelText<HTMLInputElement>('Quantité ligne 1');
    const prix = screen.getByLabelText<HTMLInputElement>('Prix HT ligne 1');
    expect(quantite.getAttribute('inputmode')).toBe('decimal');
    expect(quantite.type).not.toBe('number');
    fireEvent.change(quantite, { target: { value: '1,5' } });
    fireEvent.change(prix, { target: { value: '10.50' } });
    expect(quantite.value).toBe('1,5');
    expect(prix.value).toBe('10.50');
  });
});
