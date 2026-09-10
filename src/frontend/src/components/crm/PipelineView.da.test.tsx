/**
 * DA « Application affinée », lot 4 : les colonnes du pipeline
 * (`docs/plans/2026-09-11-da-lot4-contacts-design.md`, § 9).
 */
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import type { ContactResponse } from '../../services/api';
import { PipelineView } from './PipelineView';

const COLONNES = [
  'Contact',
  'Découverte',
  'Proposition',
  'Signature',
  'Livraison',
  'Actif',
  'Archive',
] as const;

function contact(patch: Partial<ContactResponse> = {}): ContactResponse {
  return {
    id: 'ct-1',
    first_name: 'Alain',
    last_name: 'Moreau',
    company: 'Moreau SARL',
    email: 'alain@moreau.test',
    phone: null,
    address: null,
    notes: null,
    tags: null,
    stage: 'contact',
    score: 145,
    source: 'site-web',
    last_interaction: null,
    created_at: '2026-08-28T10:00:00Z',
    updated_at: '2026-08-28T10:00:00Z',
    ...patch,
  } as ContactResponse;
}

beforeEach(() => {
  _clearEscapeHandlers();
});

afterEach(() => {
  _clearEscapeHandlers();
});

describe('Lot 4 DA : colonnes', () => {
  it('sept h3 aux libellés exacts, le compte hors du h3', () => {
    render(
      <PipelineView
        contacts={[contact(), contact({ id: 'ct-2', first_name: 'Paul', last_name: 'Girard' })]}
        onContactClick={vi.fn()}
        onStageChange={vi.fn()}
      />,
    );
    const entetes = screen.getAllByRole('heading', { level: 3 });
    expect(entetes.map((h) => h.textContent)).toEqual([...COLONNES]);
    const contactCol = entetes[0];
    expect(contactCol.textContent).toBe('Contact');
    expect(contactCol.textContent).not.toMatch(/2/);
    const tete = contactCol.parentElement as HTMLElement;
    expect(within(tete).getByText('2')).toBeInTheDocument();
  });

  it('le conteneur défile en x, en colonnes minmax 15 rem', () => {
    const { container } = render(
      <PipelineView contacts={[]} onContactClick={vi.fn()} onStageChange={vi.fn()} />,
    );
    const piste = container.querySelector('[class*="overflow-x"]') as HTMLElement;
    expect(piste).not.toBeNull();
    expect(piste.className).toMatch(/overflow-x-auto/);
    expect(piste.className).toMatch(/grid-flow-col/);
    expect(piste.className).toMatch(/minmax\(15rem/);
  });
});

describe('Lot 4 DA : fiches', () => {
  it('une carte porte crm-contact-item, le score 145 dans son nœud, pas « de 0 à 100 »', () => {
    render(
      <PipelineView contacts={[contact()]} onContactClick={vi.fn()} onStageChange={vi.fn()} />,
    );
    expect(screen.getAllByTestId('crm-contact-item')).toHaveLength(1);
    expect(screen.getByText('145')).toBeInTheDocument();
    expect(screen.queryByText(/de 0 à 100/i)).toBeNull();
    expect(screen.queryByTitle(/de 0 à 100/i)).toBeNull();
    expect(screen.queryByLabelText(/de 0 à 100/i)).toBeNull();
  });

  it('le badge data-etiquette n’existe que si source est présent', () => {
    const { rerender } = render(
      <PipelineView contacts={[contact()]} onContactClick={vi.fn()} onStageChange={vi.fn()} />,
    );
    const avecSource = screen.getByTestId('crm-contact-item');
    const badge = avecSource.querySelector('[data-etiquette]');
    expect(badge).not.toBeNull();
    expect(badge?.textContent).toBe('site-web');

    rerender(
      <PipelineView
        contacts={[contact({ source: null })]}
        onContactClick={vi.fn()}
        onStageChange={vi.fn()}
      />,
    );
    expect(screen.getByTestId('crm-contact-item').querySelector('[data-etiquette]')).toBeNull();
  });

  it('l’overlay de glissé porte aria-grabbed="true"', async () => {
    render(
      <PipelineView contacts={[contact()]} onContactClick={vi.fn()} onStageChange={vi.fn()} />,
    );
    const carte = screen.getByRole('button', { name: /Alain Moreau/i });
    carte.focus();
    fireEvent.keyDown(carte, { key: ' ', code: 'Space' });
    await act(async () => {
      await new Promise((resoudre) => setTimeout(resoudre, 0));
    });
    expect(document.querySelector('[aria-grabbed="true"]')).not.toBeNull();
  });
});
