/**
 * B-648 (persona Nadia, c4) : sur une installation sans clé cloud, l'Atelier
 * annonçait « Katia: claude-sonnet-4-6 » et « Zézette: claude-sonnet-4-6 »
 * sans un mot sur leur indisponibilité. Un modèle absent de la liste des
 * modèles utilisables est annoncé comme tel.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const config = vi.hoisted(() => ({
  valeur: {
    source_path: '/tmp/depot',
    katia_enabled: true,
    zezette_enabled: true,
    katia_model: 'claude-sonnet-4-6',
    zezette_model: 'qwen3:8b',
    available_models: [{ id: 'qwen3:8b', name: 'qwen3:8b (local)', provider: 'ollama' }],
  },
}));

vi.mock('../../services/api/agents', () => ({
  streamAgentRequest: vi.fn(),
  cancelTask: vi.fn(),
  getAgentConfig: vi.fn().mockImplementation(async () => config.valeur),
}));

import { useAtelierStore } from '../../stores/atelierStore';
import { AtelierPanel } from './AtelierPanel';

describe('B-648 : un modèle d’agent hors de portée est annoncé', () => {
  beforeEach(() => {
    useAtelierStore.setState({ isOpen: true, activeView: 'chat', messages: [], isStreaming: false });
  });

  it('le badge du modèle absent dit « non disponible », celui du modèle installé reste sobre', async () => {
    render(<AtelierPanel />);
    const katia = await screen.findByText(/Katia: claude-sonnet-4-6/);
    expect(katia).toHaveTextContent(/non disponible/i);
    expect(katia).toHaveAttribute('title', expect.stringMatching(/clé|installé|Réglages/i));
    const zezette = screen.getByText(/Zézette: qwen3:8b/);
    expect(zezette).not.toHaveTextContent(/non disponible/i);
  });
});
