/**
 * Une trace annulée se voit, et ne pèse pas comme une trace en vigueur
 * (tranche B du 29/08).
 *
 * Sans marque à l'écran, la note fausse et sa correction s'affichent à
 * l'identique, avec la même icône. Ludo lit les deux et ne sait pas laquelle
 * a été retirée.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ActivityTimeline } from './ActivityTimeline';

// Le composant charge ses activités lui-même : on lui sert la réponse de l'API.
const traces: unknown[] = [];
vi.mock('../../services/api', () => ({
  listActivities: () => Promise.resolve(traces),
}));

function servir(t: unknown) {
  traces.length = 0;
  traces.push(t);
}

const BASE = {
  id: 'a1', contact_id: 'c1', type: 'note', description: 'FORGER 490 EUR',
  extra_data: null, created_at: '2026-08-27T08:00:00Z',
};

describe('Une trace annulée est marquée', () => {
  it("barre le titre d'une trace retirée", async () => {
    servir({ ...BASE, title: 'Seance FORGER calee', statut: 'annulee' });
    render(<ActivityTimeline contactId="c1" />);

    const titre = await screen.findByText('Seance FORGER calee');
    expect(titre.className).toMatch(/line-through/);
  });

  it("le dit en toutes lettres, pas seulement par un style", async () => {
    servir({ ...BASE, title: 'Seance FORGER calee', statut: 'annulee' });
    render(<ActivityTimeline contactId="c1" />);

    // Un texte barré ne se lit pas au lecteur d'écran. Le mot doit être là.
    expect(await screen.findByText(/annul/i)).toBeInTheDocument();
  });

  it('ne marque pas une trace en vigueur', async () => {
    servir({ ...BASE, title: 'Note normale', statut: 'en_vigueur' });
    render(<ActivityTimeline contactId="c1" />);

    const titre = await screen.findByText('Note normale');
    expect(titre.className).not.toMatch(/line-through/);
    await waitFor(() => expect(screen.queryByText(/annul/i)).not.toBeInTheDocument());
  });
});
