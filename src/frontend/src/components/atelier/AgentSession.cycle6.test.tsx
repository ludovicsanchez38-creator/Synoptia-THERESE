/**
 * Cycle 6, lecteur D193 (AgentSession.tsx) : quand le profil d'agent est
 * introuvable, l'écran dit de revenir à la liste mais le composeur et Envoyer
 * restaient actifs : on pouvait poster une instruction sur un profileId que
 * ni le serveur ni la table locale ne connaissent.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/agents', () => ({
  streamAgentSpawn: async function* () { yield { type: 'chunk', content: 'ok' }; },
  getAgentProfiles: async () => [],
}));

import { AgentSession } from './AgentSession';

describe('D193 : un profil introuvable ferme le composeur', () => {
  it('le champ et Envoyer sont désactivés quand l’alerte est affichée', async () => {
    render(<AgentSession profileId="profil-inconnu" onBack={vi.fn()} />);
    await screen.findByRole('alert');
    expect(screen.getByLabelText(/Message à l/)).toBeDisabled();
    expect(screen.getByTitle('Envoyer')).toBeDisabled();
  });
});
