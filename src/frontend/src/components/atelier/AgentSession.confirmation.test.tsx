/**
 * B-355 (05/09/2026) : la carte de confirmation d'appel d'un agent était une
 * div sans rôle. Le bandeau d'erreur voisin (B-361) porte role="alert" ; la
 * carte, qui interrompt le flux pour demander une validation, doit être
 * annoncée et repérable de la même façon.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/agents', () => ({
  streamAgentSpawn: async function* () {
    yield { type: 'chunk', content: 'ok' };
  },
  getAgentProfiles: async () => [
    { id: 'researcher', name: 'Chercheur Web', description: 'Recherche', icon: '', color: 'cyan',
      tools: ['read_file'], default_model: 'claude-sonnet-4-6' },
  ],
}));

import { AgentSession } from './AgentSession';

describe('AgentSession : carte de confirmation annoncée (B-355)', () => {
  it('la carte porte un rôle alert et un nom explicite', async () => {
    render(<AgentSession profileId="researcher" onBack={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/Message à l/), { target: { value: 'Analyse ce site' } });
    fireEvent.click(screen.getByTitle('Envoyer'));

    const carte = await screen.findByRole('alert', { name: /Confirmer l’appel de l’agent/ });
    expect(carte).toHaveAttribute('data-testid', 'agent-profile-confirmation');
    expect(screen.getByRole('button', { name: /^Retour$/ }).closest('[role="alert"]')).toBe(carte);
  });
});
