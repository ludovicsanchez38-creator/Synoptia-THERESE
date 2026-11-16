/**
 * B-1978 : le champ de l'agent demande la tâche avec les accents.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/agents', () => ({
  getAgentConsent: async (_profile: string, model: string) => ({ model, provider: null, label: null, purposes: [], granted_purposes: [] }),
  getAgentProfiles: vi.fn(async () => [{ id: 'researcher', name: 'Chercheur Web', description: 'Recherche', icon: '', color: 'cyan', tools: [], default_model: 'gpt-6-astra' }]),
  streamAgentSpawn: vi.fn(async function* () { yield { type: 'chunk', content: '' }; }),
}));

import { AgentSession } from './AgentSession';

describe('B-1978 : le placeholder de l’agent est accentué', () => {
  it('demande de décrire la tâche', () => {
    render(<AgentSession profileId="researcher" onBack={vi.fn()} />);
    expect(screen.getByLabelText('Message à l’agent')).toHaveAttribute(
      'placeholder',
      expect.stringMatching(/Décris ta tâche/),
    );
  });
});
