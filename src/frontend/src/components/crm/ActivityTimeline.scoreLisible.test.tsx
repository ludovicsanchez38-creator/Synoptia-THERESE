/**
 * B-566 (05/09/2026) : l'historique affichait la chaîne JSON brute de
 * `extra_data` pour un changement de score. Une phrase lisible la remplace.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listActivities: vi.fn().mockResolvedValue([
      { id: 'a1', contact_id: 'c1', type: 'score_change', title: 'Score: 80 → 90', description: 'Raison: devis accepté',
        extra_data: '{"old_score": 80, "new_score": 90, "reason": "devis accepté"}', created_at: '2026-09-05T10:00:00Z' },
    ]),
  };
});

import { ActivityTimeline } from './ActivityTimeline';

describe('ActivityTimeline : changement de score lisible (B-566)', () => {
  it('n’affiche jamais le JSON brut', async () => {
    render(<ActivityTimeline contactId="c1" />);
    await waitFor(() => expect(screen.getByText(/Score recalculé : 80 → 90/)).toBeInTheDocument());
    expect(document.body.textContent).not.toContain('"old_score"');
  });

  it('B-1353 : ni « Score: », ni « Raison: », et le motif est une phrase', async () => {
    render(<ActivityTimeline contactId="c1" />);
    await waitFor(() => expect(screen.getByText(/Score recalculé : 80 → 90/)).toBeInTheDocument());
    const texte = document.body.textContent ?? '';
    expect(texte).not.toContain('Score:');
    expect(texte).not.toContain('Raison:');
    expect(texte).toContain('Motif : devis accepté');
  });
});
