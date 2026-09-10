/**
 * DA « Application affinée », lot 4 : la timeline d'un contact
 * (`docs/plans/2026-09-11-da-lot4-contacts-design.md`, § 9).
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockListActivities } = vi.hoisted(() => ({
  mockListActivities: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, listActivities: (...a: unknown[]) => mockListActivities(...a) };
});

import { ActivityTimeline } from './ActivityTimeline';

const BASE = {
  id: 'a1',
  contact_id: 'c1',
  type: 'note',
  description: 'FORGER 490 EUR',
  extra_data: null,
  created_at: '2026-08-27T08:00:00Z',
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('Lot 4 DA : états de la timeline', () => {
  it('le vide est un EtatVide au titre actuel', async () => {
    mockListActivities.mockResolvedValue([]);
    render(<ActivityTimeline contactId="c1" />);
    const titre = await screen.findByRole('heading', {
      level: 3,
      name: 'Aucune activité pour ce contact',
    });
    expect(titre.closest('div')).toHaveClass('px-4', 'py-8', 'text-center');
    expect(screen.queryByRole('button', { name: 'Réessayer' })).toBeNull();
  });

  it('le chargement est un Squelette aria-hidden', () => {
    mockListActivities.mockReturnValue(new Promise(() => undefined));
    render(<ActivityTimeline contactId="c1" />);
    const squelettes = document.querySelectorAll('[aria-hidden="true"]');
    expect(
      Array.from(squelettes).some((n) => (n as HTMLElement).className.includes('flex-col')),
    ).toBe(true);
    expect(document.querySelector('[class*="animate-spin"]')).toBeNull();
  });
});

describe('Lot 4 DA : traces conservées', () => {
  it('barre une trace annulée et dit Score recalculé', async () => {
    mockListActivities.mockResolvedValue([
      { ...BASE, title: 'Seance FORGER calee', statut: 'annulee' },
      {
        id: 'a2',
        contact_id: 'c1',
        type: 'score_change',
        title: 'Score: 80 → 90',
        description: null,
        extra_data: '{"old_score": 80, "new_score": 90}',
        created_at: '2026-09-05T10:00:00Z',
      },
    ]);
    render(<ActivityTimeline contactId="c1" />);
    const titre = await screen.findByText('Seance FORGER calee');
    expect(titre.className).toMatch(/line-through/);
    await waitFor(() =>
      expect(screen.getByText(/Score recalculé : 80 → 90/)).toBeInTheDocument(),
    );
  });
});
