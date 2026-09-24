/**
 * B-1173 : sans modèle local capable d'agir, la mise en route ne présélectionne ni un modèle grisé ni un modèle Cloud.
 *
 * Règle écrite dans le code (LLMStep.tsx:254-255) : « Ne jamais pré-sélectionner
 * un modèle incapable d'agir ». B-1156 (699c2903) a ajouté : jamais un modèle
 * Ollama Cloud par défaut. Quand le seul modèle capable d'actions est un modèle
 * Cloud, les deux règles se croisent : on mesure ce que l'écran présélectionne
 * et si « Continuer » laisse enregistrer ce choix.
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

describe('B-1173 : mise en route, seul modèle capable = Ollama Cloud', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('ne présélectionne pas un modèle grisé (incapable d’agir) avec « Continuer » actif', async () => {
    const { select, continuer } = await ouvrirOllama([
      {
        name: 'gemma2:2b', size: 2 * gib, modified_at: null, digest: null,
        gere_les_outils: false,
        motif_indisponible: 'gemma2 ne sait pas déclencher d’actions : il est grisé.',
      },
      {
        name: 'kimi-k2.6:cloud', size: 1000, modified_at: null, digest: null,
        gere_les_outils: true, motif_indisponible: null,
      },
    ]);

    const choisie = select.selectedOptions[0];
    const etat = {
      preselection: select.value,
      optionPreselectionneeGrisee: choisie?.disabled ?? null,
      continuerActif: !continuer.disabled,
    };
    // Attendu : jamais un modèle grisé présélectionné avec « Continuer » actif.
    // (Ce qu'il faut présélectionner à la place - rien, ou le modèle Cloud
    // badgé - relève du métier ; la combinaison mesurée ici est exclue par
    // la règle écrite l.254.)
    expect({
      ...etat,
      combinaisonInterdite: Boolean(etat.optionPreselectionneeGrisee && etat.continuerActif),
    }).toMatchObject({ combinaisonInterdite: false });
    // Ni le modèle grisé, ni le modèle Cloud : l'utilisateur choisit lui-même.
    expect({ preselection: etat.preselection, continuerActif: etat.continuerActif })
      .toEqual({ preselection: '', continuerActif: false });
  });

  it('le modèle Cloud reste choisissable explicitement, et « Continuer » l’enregistre', async () => {
    const { select, continuer } = await ouvrirOllama([
      {
        name: 'gemma2:2b', size: 2 * gib, modified_at: null, digest: null,
        gere_les_outils: false,
        motif_indisponible: 'gemma2 ne sait pas déclencher d’actions : il est grisé.',
      },
      {
        name: 'kimi-k2.6:cloud', size: 1000, modified_at: null, digest: null,
        gere_les_outils: true, motif_indisponible: null,
      },
    ]);
    fireEvent.change(select, { target: { value: 'kimi-k2.6:cloud' } });
    expect(continuer.disabled).toBe(false);
    await act(async () => {
      fireEvent.click(continuer);
    });
    expect(apiMocks.setLLMConfig.mock.calls.map((c) => [c[0], c[1]])).toEqual([['ollama', 'kimi-k2.6:cloud']]);
  });

  it('« Continuer » n’enregistre jamais le modèle grisé', async () => {
    const { continuer } = await ouvrirOllama([
      {
        name: 'gemma2:2b', size: 2 * gib, modified_at: null, digest: null,
        gere_les_outils: false,
        motif_indisponible: 'gemma2 ne sait pas déclencher d’actions : il est grisé.',
      },
      {
        name: 'kimi-k2.6:cloud', size: 1000, modified_at: null, digest: null,
        gere_les_outils: true, motif_indisponible: null,
      },
    ]);
    await act(async () => {
      fireEvent.click(continuer);
    });
    const appels = apiMocks.setLLMConfig.mock.calls.map((c) => [c[0], c[1]]);
    // Attendu : on n'enregistre jamais un modèle incapable d'agir.
    expect(appels).not.toContainEqual(['ollama', 'gemma2:2b']);
  });

  it('témoin : un modèle local capable présent est présélectionné (B-1156 sain)', async () => {
    const { select, continuer } = await ouvrirOllama([
      { name: 'kimi-k2.6:cloud', size: 1000, modified_at: null, digest: null, gere_les_outils: true },
      { name: 'gemma2:2b', size: 2 * gib, modified_at: null, digest: null, gere_les_outils: false, motif_indisponible: 'grisé' },
      { name: 'qwen3:8b', size: 5 * gib, modified_at: null, digest: null, gere_les_outils: true },
    ]);
    expect({
      preselection: select.value,
      grisee: select.selectedOptions[0]?.disabled,
      continuerActif: !continuer.disabled,
    }).toEqual({ preselection: 'qwen3:8b', grisee: false, continuerActif: true });
  });
});
