/**
 * B-1372 (persona Hugo, cycle 13) : le journal de synchronisation affichait
 * « INDEXER specifications.md (obsolete - Fichier enregistre mais AUCUN chunk
 * indexe…) », état brut en anglais, motif coupé par des points de suspension.
 * L'état se lit en français et le motif se lit en entier.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  etatSync: vi.fn(),
  definirRacineSync: vi.fn(),
  retirerRacineSync: vi.fn(),
  preparerPlanSync: vi.fn(),
  appliquerPlanSync: vi.fn(),
  journalSync: vi.fn(),
}));

vi.mock('../../services/api', () => apiMocks);

import { ProjectSyncSection } from './ProjectSyncSection';

const MOTIF = 'Aucun texte n’a pu être lu dans ce fichier : il n’apparaîtra pas dans les recherches.';
const PLAN = {
  id: 'plan-1', etat: 'propose', generation_racine: 1,
  nb_indexer: 1, nb_reindexer: 0, nb_retirer: 0, nb_conflits: 0, nb_inchanges: 0,
  created_at: '2026-09-25T00:00:00Z',
  operations: [{ id: 'op-1', type: 'indexer', chemin: '/r/specifications.md', etat: 'a_faire', erreur: null, attempt_count: 0, last_attempt_at: null }],
};

describe('journal de synchronisation lisible (B-1372)', () => {
  it('l’état est en français et le motif se lit en entier', async () => {
    vi.useFakeTimers();
    apiMocks.etatSync.mockResolvedValue({ racine: '/r', generation: 1, dernier_plan: null, run: null });
    apiMocks.preparerPlanSync.mockResolvedValue(PLAN);
    apiMocks.appliquerPlanSync.mockResolvedValue(undefined);
    apiMocks.journalSync.mockResolvedValue({
      operations: [{ id: 'op-1', type: 'indexer', chemin: '/r/specifications.md', etat: 'obsolete', erreur: MOTIF, attempt_count: 1, last_attempt_at: null }],
    });

    render(<ProjectSyncSection projectId="p-1" />);
    await vi.waitFor(() => expect(screen.getByRole('button', { name: /Préparer/ })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /Préparer/ }));
    await vi.waitFor(() => expect(screen.getByRole('button', { name: /Appliquer/ })).toBeInTheDocument());
    apiMocks.etatSync.mockResolvedValue({
      racine: '/r', generation: 1, dernier_plan: { ...PLAN, etat: 'applique_partiel' }, run: { etat: 'done', progression: 1 },
    });
    fireEvent.click(screen.getByRole('button', { name: /Appliquer/ }));
    await vi.advanceTimersByTimeAsync(1000);
    const journal = await vi.waitFor(() => screen.getByTestId('sync-journal'));
    vi.useRealTimers();

    expect(journal.textContent).not.toContain('obsolete');
    expect(journal.textContent).toContain('écarté');
    const motif = screen.getByText(MOTIF);
    expect(motif.closest('.truncate')).toBeNull();
  });
});
