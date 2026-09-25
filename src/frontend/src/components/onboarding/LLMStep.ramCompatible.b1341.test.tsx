/**
 * B-1341 (persona Claire, cycle 13) : le modèle local présélectionné était
 * celui que l'écran déconseille.
 *
 * Machine à 16 Gio (plafond prudent 8 Gio, marge de contexte 2 Gio) :
 * `gemma4-tia` (6,3 Gio, donc 8,3 Gio estimés) était présélectionné avec « RAM
 * déconseillée », alors que `qwen3:8b` (4,9 Gio, 6,9 Gio estimés) passe. Parmi
 * les modèles locaux capables d'agir, la présélection préfère ceux que la RAM
 * permet ; à défaut, elle garde le premier capable.
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

function statut(models: Array<Record<string, unknown>>) {
  return { available: true, base_url: 'http://ollama.test', models, error: null };
}

async function ouvrirOllama(models: Array<Record<string, unknown>>) {
  apiMocks.getApiKeysWithCorrupted.mockResolvedValue({ keys: {}, corrupted: [], sources: {} });
  apiMocks.getOllamaStatus.mockResolvedValue(statut(models));
  apiMocks.getSystemResources.mockResolvedValue({
    total_ram_bytes: 16 * gib,
    safe_local_model_ram_bytes: 8 * gib,
    ollama_context_margin_bytes: 2 * gib,
    detection_method: 'test',
  });
  apiMocks.setLLMConfig.mockResolvedValue({});
  const onNext = vi.fn();
  render(<LLMStep onNext={onNext} onBack={vi.fn()} />);
  await act(async () => Promise.resolve());
  await act(async () => Promise.resolve());
  fireEvent.click(screen.getByRole('radio', { name: /Ollama \(Local\)/ }));
  const select = screen.getByLabelText('Modèle') as HTMLSelectElement;
  const continuer = screen.getByTestId('onboarding-next-btn') as HTMLButtonElement;
  return { select, continuer, onNext };
}

describe('B-1341 : la présélection locale respecte la RAM', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('présélectionne le modèle que la RAM permet, pas celui qu’elle déconseille', async () => {
    const { select } = await ouvrirOllama([
      { name: 'gemma4-tia:latest', size: 6.3 * gib, modified_at: null, digest: null, gere_les_outils: true, motif_indisponible: null },
      { name: 'qwen3:8b', size: 4.9 * gib, modified_at: null, digest: null, gere_les_outils: true, motif_indisponible: null },
    ]);
    expect(select.value).toBe('qwen3:8b');
    expect(screen.getByTestId('local-model-feasibility')).toHaveAttribute('data-status', 'feasible');
  });

  it('sans modèle compatible, garde le premier modèle capable', async () => {
    const { select } = await ouvrirOllama([
      { name: 'gros-a:latest', size: 9 * gib, modified_at: null, digest: null, gere_les_outils: true, motif_indisponible: null },
      { name: 'gros-b:latest', size: 10 * gib, modified_at: null, digest: null, gere_les_outils: true, motif_indisponible: null },
    ]);
    expect(select.value).toBe('gros-a:latest');
  });
});
