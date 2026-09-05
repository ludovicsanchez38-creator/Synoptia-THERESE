/**
 * B-393 (05/09/2026) : la carte de consentement annonçait les outils d'une
 * table recopiée dans le frontend (PROFILE_MAP), pas ceux que le serveur
 * accorde réellement (GET /api/agents/profiles, déjà filtrés côté routeur).
 * L'utilisatrice consentait à « web_search » alors que l'agent ne l'avait pas.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/agents', () => ({
  streamAgentSpawn: async function* () {
    yield { type: 'chunk', content: 'ok' };
  },
  getAgentProfiles: async () => [
    {
      id: 'researcher',
      name: 'Chercheur Web',
      description: 'Recherche',
      icon: '',
      color: 'cyan',
      tools: ['read_file'],
      default_model: 'claude-sonnet-4-6',
    },
  ],
}));

import { AgentSession } from './AgentSession';

describe('B-393 - la carte de consentement annonce les outils accordés par le serveur', () => {
  it('liste read_file seul, pas web_search de la table locale', async () => {
    render(<AgentSession profileId="researcher" onBack={vi.fn()} />);

    fireEvent.change(screen.getByLabelText(/Message à l/), { target: { value: 'Analyse ce site' } });
    fireEvent.click(screen.getByTitle('Envoyer'));

    const carte = await screen.findByTestId('agent-profile-confirmation');
    await screen.findByText(/Outils déclarés : read_file\./);
    expect(carte.textContent).not.toMatch(/web_search/);
  });
});
