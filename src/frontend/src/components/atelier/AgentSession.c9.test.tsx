/**
 * B-777 et B-778 (cycle 9) : le modèle annoncé et envoyé était figé au premier
 * rendu depuis la table locale, avant l'arrivée du profil serveur ; et si le
 * serveur ne répondait pas, la carte de consentement annonçait les outils de la
 * table locale comme s'ils étaient accordés.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const agentsApi = vi.hoisted(() => ({
  getAgentProfiles: vi.fn(),
  streamAgentSpawn: vi.fn(async function* () { yield { type: 'chunk', content: 'ok' }; }),
}));
vi.mock('../../services/api/agents', () => agentsApi);

import { AgentSession } from './AgentSession';

async function demanderUnAppel() {
  render(<AgentSession profileId="researcher" onBack={vi.fn()} />);
  fireEvent.change(screen.getByLabelText(/Message à l/), { target: { value: 'Analyse ce site' } });
  fireEvent.click(screen.getByTitle('Envoyer'));
  return screen.findByTestId('agent-profile-confirmation');
}

describe('AgentSession - B-777, le modèle suit le profil serveur', () => {
  beforeEach(() => vi.clearAllMocks());

  it('annonce le modèle par défaut du serveur, pas celui de la table locale', async () => {
    agentsApi.getAgentProfiles.mockResolvedValue([
      { id: 'researcher', name: 'Chercheur Web', description: 'Recherche', icon: '', color: 'cyan', tools: ['read_file'], default_model: 'gpt-6-astra' },
    ]);
    const carte = await demanderUnAppel();
    await screen.findByText(/Modèle : gpt-6-astra/);
    expect(carte.textContent).not.toMatch(/claude-sonnet-4-6/);
  });
});

describe('AgentSession - B-778, sans profil serveur les outils ne sont pas inventés', () => {
  beforeEach(() => vi.clearAllMocks());

  it('dit que les outils ne sont pas confirmés quand le serveur ne répond pas', async () => {
    agentsApi.getAgentProfiles.mockRejectedValue(new Error('HTTP 503'));
    const carte = await demanderUnAppel();
    await screen.findByText(/Outils déclarés : non confirmés par le serveur/);
    expect(carte.textContent).not.toMatch(/web_search/);
  });
});
