/**
 * Persona Nadia, c4, onglet Agents :
 * - B-649 : le sélecteur présélectionnait `qwen3.5:9b` (défaut du profil)
 *   alors qu'aucun modèle de la liste n'était installé ; le défaut doit être
 *   un modèle réellement proposé ;
 * - B-650 : seul écran de l'application écrit sans accents.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/agents', () => ({
  getAgentProfiles: vi.fn().mockResolvedValue([
    { id: 'researcher', name: 'Chercheur Web', description: 'Recherche sur le web et synthétise les résultats', icon: 'search', color: 'cyan', tools: [], default_model: 'qwen3.5:9b' },
  ]),
  getAgentConfig: vi.fn().mockResolvedValue({
    katia_model: '', zezette_model: '', katia_enabled: true, zezette_enabled: true,
    available_models: [{ id: 'qwen3:8b', name: 'qwen3:8b (local)', provider: 'ollama' }],
  }),
}));

import { AgentCatalog } from './AgentCatalog';

describe('B-649 / B-650 : catalogue des agents', () => {
  it('présélectionne un modèle réellement proposé quand le défaut du profil n’y est pas', async () => {
    vi.mocked(window.localStorage.setItem).mockClear();
    render(<AgentCatalog onSelectAgent={vi.fn()} />);
    const selecteur = (await screen.findByLabelText('Modèle de l’agent')) as HTMLSelectElement;
    expect(selecteur.value).toBe('qwen3:8b');
    // Le setup vitest remplace localStorage par des vi.fn : on vérifie l'écriture, pas la lecture.
    await waitFor(() => expect(window.localStorage.setItem).toHaveBeenCalledWith('therese-agent-model', 'qwen3:8b'));
    expect(window.localStorage.setItem).not.toHaveBeenCalledWith('therese-agent-model', 'qwen3.5:9b');
  });

  it('écrit ses consignes avec les accents', async () => {
    render(<AgentCatalog onSelectAgent={vi.fn()} />);
    expect(await screen.findByText(/Chaque agent est spécialisé dans un domaine\. Sélectionne celui qui correspond à ta tâche\./)).toBeInTheDocument();
  });
});
