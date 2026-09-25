/**
 * P-118 (persona Claire, cycle 13) : « mes notes partent-elles ? » Le Centre
 * de confiance donnait des principes généraux, avec du jargon (« mutation »,
 * « outil MCP », « Board », « sans carte »). Une ligne d'état, en tête, dit ce
 * qui se passe maintenant : service d'IA actif, local ou en ligne, et état de
 * la recherche web.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  getLLMConfig: vi.fn(),
  getWebSearchStatus: vi.fn(),
}));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  getLLMConfig: apiMocks.getLLMConfig,
  getWebSearchStatus: apiMocks.getWebSearchStatus,
}));

import { TrustCenter } from './CapabilityCenter';

function ouvrir() {
  return render(<TrustCenter onClose={vi.fn()} onOpenPrivacy={vi.fn()} onOpenAdvanced={vi.fn()} />);
}

function web(enabled: boolean) {
  return { enabled, providers: { gemini: 'google', others: 'duckduckgo' }, description: '' };
}

describe('P-118 : le Centre de confiance dit ce qui se passe maintenant', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('modèle local, recherche web coupée : rien ne sort', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: 'gemma4-tia:latest', available: true, available_models: [] });
    apiMocks.getWebSearchStatus.mockResolvedValue(web(false));
    ouvrir();
    const etat = await screen.findByTestId('confiance-etat-actuel');
    expect(etat).toHaveTextContent('Ton assistante répond en local avec gemma4-tia:latest');
    expect(etat).toHaveTextContent('Tes messages ne quittent pas ta machine');
    expect(etat).toHaveTextContent('La recherche web est coupée');
  });

  it('service en ligne, recherche web active : les deux sorties sont dites', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'anthropic', model: 'claude-sonnet-5', available: true, available_models: [] });
    apiMocks.getWebSearchStatus.mockResolvedValue(web(true));
    ouvrir();
    const etat = await screen.findByTestId('confiance-etat-actuel');
    expect(etat).toHaveTextContent('Ton assistante répond avec Anthropic (claude-sonnet-5), un service en ligne');
    expect(etat).toHaveTextContent('tes messages lui sont envoyés');
    expect(etat).toHaveTextContent('La recherche web est active');
  });

  it('un modèle Ollama Cloud n’est pas local', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: 'gpt-oss:120b-cloud', available: true, available_models: [] });
    apiMocks.getWebSearchStatus.mockResolvedValue(web(false));
    ouvrir();
    const etat = await screen.findByTestId('confiance-etat-actuel');
    expect(etat).not.toHaveTextContent('en local');
    expect(etat).toHaveTextContent('un service en ligne');
  });

  it('aucun service prêt : il le dit, sans rien affirmer d’autre', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'anthropic', model: 'claude-sonnet-5', available: false, available_models: [] });
    apiMocks.getWebSearchStatus.mockResolvedValue(web(false));
    ouvrir();
    expect(await screen.findByTestId('confiance-etat-actuel')).toHaveTextContent('Aucun service d’IA n’est prêt');
  });

  it('lecture impossible : il le dit au lieu de promettre', async () => {
    apiMocks.getLLMConfig.mockRejectedValue(new Error('réseau'));
    apiMocks.getWebSearchStatus.mockRejectedValue(new Error('réseau'));
    ouvrir();
    expect(await screen.findByTestId('confiance-etat-actuel')).toHaveTextContent('Impossible de lire le service d’IA actif');
  });

  it('les rubriques parlent français, pas jargon', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: 'qwen3:8b', available: true, available_models: [] });
    apiMocks.getWebSearchStatus.mockResolvedValue(web(false));
    const { container } = ouvrir();
    await screen.findByTestId('confiance-etat-actuel');
    expect(container.textContent).not.toMatch(/\b(mutation|MCP|Board|sans carte)\b/);
  });
});
