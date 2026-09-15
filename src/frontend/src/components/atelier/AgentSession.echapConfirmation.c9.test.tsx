/**
 * B-896 (cycle 9, relecteur V3) : la carte de confirmation d'appel d'un agent
 * (alertdialog) n'avait aucune fermeture clavier : Échap ne faisait rien, il
 * fallait atteindre « Retour » à la souris ou à la tabulation.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';

const streamAgentSpawn = vi.fn((..._args: unknown[]) => (async function* () { yield { type: 'chunk', content: 'ok' }; })());
vi.mock('../../services/api/agents', () => ({
  streamAgentSpawn: (...args: unknown[]) => streamAgentSpawn(...args),
  getAgentProfiles: async () => [
    { id: 'researcher', name: 'Chercheur Web', description: 'Recherche', icon: '', color: 'cyan', tools: ['read_file'], default_model: 'claude-sonnet-4-6' },
  ],
}));

import { AgentSession } from './AgentSession';

describe('AgentSession - B-896, Échap referme la confirmation sans appeler l’agent', () => {
  beforeEach(() => { vi.clearAllMocks(); _clearEscapeHandlers(); });

  it('Échap équivaut à « Retour »', async () => {
    render(<AgentSession profileId="researcher" onBack={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/Message à l/), { target: { value: 'Analyse ce site' } });
    fireEvent.click(screen.getByTitle('Envoyer'));
    await screen.findByRole('alertdialog', { name: /Confirmer l’appel de l’agent/ });

    let traite = false;
    act(() => { traite = runTopEscapeHandler(); });
    expect(traite).toBe(true);
    expect(screen.queryByRole('alertdialog')).toBeNull();
    expect(streamAgentSpawn).not.toHaveBeenCalled();
  });
});
