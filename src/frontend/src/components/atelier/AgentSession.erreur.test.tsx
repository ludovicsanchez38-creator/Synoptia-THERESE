/**
 * B-361 (05/09/2026) : le message d'erreur d'un agent était rendu par une
 * branche de liste sans role="alert", invisible aux lecteurs d'écran et à
 * la garde 0.49 (erreursAnnoncees).
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/agents', () => ({
  streamAgentSpawn: async function* () {
    yield { type: 'error', content: 'Le fournisseur a refusé la requête.' };
  },
  getAgentProfiles: async () => [],
}));

import { AgentSession } from './AgentSession';

describe("B-361 - l'erreur d'un agent est annoncée", () => {
  it('porte role="alert"', async () => {
    render(<AgentSession profileId="researcher" onBack={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/Message à l/), { target: { value: 'Analyse' } });
    fireEvent.click(screen.getByTitle('Envoyer'));
    fireEvent.click(screen.getByRole('button', { name: /Confirmer l.appel/ }));

    const alerte = await screen.findByRole('alert');
    expect(alerte.textContent).toMatch(/refusé la requête/);
  });
});
