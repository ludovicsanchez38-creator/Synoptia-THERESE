/**
 * P-152 (recette P-146, lot 2, O5 ; acceptée le 25/09) : l'explication du
 * score était une infobulle d'icône SVG, ni focalisable ni lisible au
 * clavier, et générale : rien ne disait pourquoi CE score avait changé.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ listActivities: vi.fn() }));
vi.mock('../../services/api/crm-extended', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  ...api,
}));

import { SCORE_AIDE } from './pipelineEtapes';
import { ExplicationDuScore } from './ExplicationDuScore';

describe('P-152 : l’explication du score', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.listActivities.mockResolvedValue([{
      id: 'a1', contact_id: 'c1', type: 'score_change', title: 'Score: 50 → 80', description: 'Raison: initial_creation',
      extra_data: JSON.stringify({ old_score: 50, new_score: 80, reason: 'initial_creation' }), created_at: '2026-09-25T10:00:00',
    }]);
  });

  it('s’ouvre au clavier, depuis un vrai bouton', () => {
    render(<ExplicationDuScore />);
    const bouton = screen.getByRole('button', { name: 'Expliquer le score' });
    expect(bouton).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(bouton);
    expect(bouton).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText(SCORE_AIDE)).toBeInTheDocument();
  });

  it('dit le motif du dernier changement de la fiche', async () => {
    render(<ExplicationDuScore contactId="c1" />);
    fireEvent.click(screen.getByRole('button', { name: 'Expliquer le score' }));
    expect(await screen.findByText(/Dernier changement : Score recalculé : 50 → 80 · Motif : création de la fiche/)).toBeInTheDocument();
    expect(api.listActivities).toHaveBeenCalledWith({ contact_id: 'c1', type: 'score_change', limit: 1 });
  });
});

describe('P-152 : branché sur la carte du Pipeline', () => {
  it('la carte porte le bouton, plus l’icône à infobulle', async () => {
    const { PipelineView } = await import('./PipelineView');
    const ouvrirLaFiche = vi.fn();
    render(
      <PipelineView
        contacts={[{
          id: 'ct-1', first_name: 'Alain', last_name: 'Moreau', company: null, email: null, phone: null, address: null,
          notes: null, tags: null, stage: 'contact', score: 145, source: null, last_interaction: null,
          created_at: '2026-08-28T10:00:00Z', updated_at: '2026-08-28T10:00:00Z',
        } as never]}
        onContactClick={ouvrirLaFiche}
        onStageChange={vi.fn()}
      />,
    );
    const bouton = screen.getByRole('button', { name: 'Expliquer le score' });
    // La carte ouvre la fiche au clic et part en glisser sur Entrée ou Espace :
    // déplier l'explication ne doit faire ni l'un ni l'autre.
    fireEvent.keyDown(bouton, { key: 'Enter' });
    fireEvent.click(bouton);
    expect(ouvrirLaFiche).not.toHaveBeenCalled();
    expect(bouton).toHaveAttribute('aria-expanded', 'true');
  });
});
