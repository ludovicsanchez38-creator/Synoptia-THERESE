/**
 * B-1387 (persona Nathalie, cycle 13) : à 125 %, la description d'une ligne
 * de devis tombait à 61 px (« Vitri » pour « Vitrine réfrigérée, fourniture
 * et pose »), moins que le prix (100 px) ; 99 px à 100 %. En disposition
 * automatique, les champs numériques et la liste de TVA prenaient leur
 * largeur naturelle et la description recevait le reste.
 *
 * Le tableau des lignes passe en disposition fixe : les colonnes numériques
 * ont une largeur en rem (elle suit la taille du texte), la description prend
 * toute la place restante. jsdom ne mesure pas : la mesure a été faite dans
 * Chrome à 125 %.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([]),
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  };
});

import { InvoiceForm } from './InvoiceForm';

describe('B-1387 : la description d’une ligne prend la place restante', () => {
  it('disposition fixe, colonnes numériques en rem, description sans largeur', () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);
    const tableau = screen.getByLabelText('Description ligne 1').closest('table')!;

    expect(tableau.className).toMatch(/\btable-fixed\b/);
    const colonnes = Array.from(tableau.querySelectorAll('colgroup > col'));
    expect(colonnes).toHaveLength(6);
    expect(colonnes[0].className).toBe('');
    for (const col of colonnes.slice(1)) expect(col.className).toMatch(/^w-/);
  });
});
