/**
 * P-111 (persona Claire, cycle 13) : le seul choix qui tient la promesse
 * « Données locales » était le 14e sur 14, sous un Claude présélectionné.
 *
 * Quand Ollama répond, il passe en tête de la liste, avec la mention que les
 * données restent sur la machine. Il n'est présélectionné que si un modèle
 * local capable d'agir tient en mémoire : proposer d'office un modèle que
 * l'écran déconseille serait pire que le service en ligne.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { LLMStep } from './LLMStep';

const apiMocks = vi.hoisted(() => ({
  getApiKeysWithCorrupted: vi.fn(),
  getOllamaStatus: vi.fn(),
  getSystemResources: vi.fn(),
  setApiKey: vi.fn(),
  setLLMConfig: vi.fn(),
}));

vi.mock('../../services/api', () => apiMocks);

const catalogueMocks = vi.hoisted(() => ({ chargerCatalogue: vi.fn() }));
vi.mock('../../lib/catalogueModeles', async (importOriginal) => {
  const reel = await importOriginal<typeof import('../../lib/catalogueModeles')>();
  return {
    ...reel,
    chargerCatalogue: (...args: Parameters<typeof reel.chargerCatalogue>) =>
      catalogueMocks.chargerCatalogue(...args) ?? Promise.resolve(null),
  };
});

const gib = 1024 ** 3;

function modele(name: string, taille: number, gereLesOutils = true) {
  return { name, size: taille * gib, modified_at: null, digest: null, gere_les_outils: gereLesOutils, motif_indisponible: null };
}

async function ouvrir(ollama: { available: boolean; models: Array<Record<string, unknown>> }) {
  apiMocks.getApiKeysWithCorrupted.mockResolvedValue({ keys: {}, corrupted: [], sources: {} });
  apiMocks.getOllamaStatus.mockResolvedValue({ base_url: 'http://ollama.test', error: null, ...ollama });
  apiMocks.getSystemResources.mockResolvedValue({
    total_ram_bytes: 16 * gib,
    safe_local_model_ram_bytes: 8 * gib,
    ollama_context_margin_bytes: 2 * gib,
    detection_method: 'test',
  });
  render(<LLMStep onNext={vi.fn()} onBack={vi.fn()} />);
  await act(async () => Promise.resolve());
  await act(async () => Promise.resolve());
}

describe('P-111 : le choix local proposé d’abord', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('Ollama détecté avec un modèle qui tient en mémoire : en tête, présélectionné, promesse dite', async () => {
    await ouvrir({ available: true, models: [modele('qwen3:8b', 4.9)] });
    const radios = screen.getAllByRole('radio');
    expect(radios[0]).toHaveAccessibleName(/Ollama \(Local\)/);
    expect(radios[0]).toHaveAttribute('aria-checked', 'true');
    expect(radios[0]).toHaveTextContent(/Tes données restent sur ta machine/);
    expect((screen.getByLabelText('Modèle') as HTMLSelectElement).value).toBe('qwen3:8b');
  });

  it('aucun modèle local ne tient en mémoire : Ollama en tête, mais le service en ligne reste présélectionné', async () => {
    await ouvrir({ available: true, models: [modele('gros-modele:70b', 40)] });
    const radios = screen.getAllByRole('radio');
    expect(radios[0]).toHaveAccessibleName(/Ollama \(Local\)/);
    expect(radios[0]).toHaveAttribute('aria-checked', 'false');
    expect(screen.getByRole('radio', { name: /Claude \(Anthropic\)/ })).toHaveAttribute('aria-checked', 'true');
  });

  it('Ollama absent : la liste garde son ordre, rien ne change', async () => {
    await ouvrir({ available: false, models: [] });
    const radios = screen.getAllByRole('radio');
    expect(radios[0]).toHaveAccessibleName(/Claude \(Anthropic\)/);
    expect(radios[radios.length - 1]).toHaveAccessibleName(/Ollama \(Local\)/);
  });

  it('un service choisi avant une revérification n’est pas repris', async () => {
    await ouvrir({ available: false, models: [] });
    fireEvent.click(screen.getByRole('radio', { name: /Mistral/ }));
    apiMocks.getOllamaStatus.mockResolvedValue({
      available: true, base_url: 'http://ollama.test', error: null, models: [modele('qwen3:8b', 4.9)],
    });
    fireEvent.click(screen.getByRole('button', { name: 'Revérifier la disponibilité' }));
    await act(async () => Promise.resolve());
    await act(async () => Promise.resolve());
    expect(screen.getByRole('radio', { name: /Mistral/ })).toHaveAttribute('aria-checked', 'true');
  });
});
