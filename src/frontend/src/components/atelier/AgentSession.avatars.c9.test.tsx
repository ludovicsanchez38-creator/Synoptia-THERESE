/**
 * B-827 (cycle 9) : les avatars de la session d'agent affichaient des emoji
 * (🔍, 👤, 🤖) contraires à la charte (icônes SVG), que la garde B-293 n'appliquait
 * qu'au badge e-mail. Et l'invite initiale listait encore les outils de la
 * table locale (relecture S5, suite B-778).
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const agentsApi = vi.hoisted(() => ({
  getAgentProfiles: vi.fn(),
  streamAgentSpawn: vi.fn(async function* () { yield { type: 'agent_start', model: 'gpt-6-astra' }; yield { type: 'chunk', content: 'Bonjour' }; }),
}));
vi.mock('../../services/api/agents', () => agentsApi);
import { AgentSession } from './AgentSession';

const EMOJI = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u;

describe('AgentSession - B-827, aucun emoji dans les avatars ni l’invite', () => {
  beforeEach(() => vi.clearAllMocks());

  it('les avatars sont des icônes, pas des emoji', async () => {
    agentsApi.getAgentProfiles.mockResolvedValue([{ id: 'researcher', name: 'Chercheur Web', description: 'Recherche', icon: '', color: 'cyan', tools: ['read_file'], default_model: 'gpt-6-astra' }]);
    const { container } = render(<AgentSession profileId="researcher" onBack={vi.fn()} />);
    expect(container.textContent ?? '').not.toMatch(EMOJI);
    fireEvent.change(screen.getByLabelText(/Message à l/), { target: { value: 'Analyse ce site' } });
    fireEvent.click(screen.getByTitle('Envoyer'));
    await screen.findByTestId('agent-profile-confirmation');
    // Le modèle annoncé par la carte est celui qui part (relecture S5).
    await screen.findByText(/Modèle : gpt-6-astra/);
    fireEvent.click(screen.getByRole('button', { name: /Confirmer l/ }));
    await screen.findByText('Bonjour');
    expect(container.textContent ?? '').not.toMatch(EMOJI);
    expect(agentsApi.streamAgentSpawn).toHaveBeenCalledWith('researcher', 'Analyse ce site', expect.anything(), 'gpt-6-astra');
  });

  it('sans profil serveur, l’invite ne liste pas les outils de la table locale', async () => {
    agentsApi.getAgentProfiles.mockRejectedValue(new Error('HTTP 503'));
    render(<AgentSession profileId="researcher" onBack={vi.fn()} />);
    await screen.findByText(/Outils non confirmés par le serveur/);
    expect(screen.queryByText('web_search')).toBeNull();
  });
});
