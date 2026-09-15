/**
 * Relecture T5 (cycle 9) : un résultat d'outil était rattaché au DERNIER appel du
 * même nom ; deux appels identiques dans un tour laissaient le premier bloc vide
 * et le second recevait les deux résultats.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const agentsApi = vi.hoisted(() => ({
  getAgentProfiles: vi.fn(async () => [{ id: 'researcher', name: 'Chercheur Web', description: 'Recherche', icon: '', color: 'cyan', tools: ['read_file'], default_model: 'gpt-6-astra' }]),
  streamAgentSpawn: vi.fn(async function* () {
    yield { type: 'tool_call', tool_name: 'read_file', tool_args: { path: 'a.md' } };
    yield { type: 'tool_call', tool_name: 'read_file', tool_args: { path: 'b.md' } };
    yield { type: 'tool_result', tool_name: 'read_file', tool_result: 'contenu de a' };
    yield { type: 'tool_result', tool_name: 'read_file', tool_result: 'contenu de b' };
    yield { type: 'chunk', content: 'Fini' };
  }),
}));
vi.mock('../../services/api/agents', () => agentsApi);
import { AgentSession } from './AgentSession';

describe('AgentSession - deux appels du même outil reçoivent chacun leur résultat', () => {
  it('le premier bloc reçoit « contenu de a », le second « contenu de b »', async () => {
    render(<AgentSession profileId="researcher" onBack={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/Message à l/), { target: { value: 'Lis deux fichiers' } });
    fireEvent.click(screen.getByTitle('Envoyer'));
    await screen.findByTestId('agent-profile-confirmation');
    await screen.findByText(/Modèle : gpt-6-astra/);
    fireEvent.click(screen.getByRole('button', { name: /Confirmer l/ }));
    await screen.findByText('Fini');
    const blocs = screen.getAllByText(/read_file/);
    expect(blocs.length).toBeGreaterThanOrEqual(2);
    for (const bouton of screen.getAllByRole('button', { name: /read_file/ })) fireEvent.click(bouton);
    expect(await screen.findByText(/contenu de a/)).toBeInTheDocument();
    expect(await screen.findByText(/contenu de b/)).toBeInTheDocument();
  });
});
