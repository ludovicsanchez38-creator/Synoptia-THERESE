import { describe, expect, it } from 'vitest';

import { resolveModelForProvider } from './modelResolution';

describe('resolveModelForProvider', () => {
  it('conserve le modèle demandé s il appartient bien au provider', () => {
    expect(
      resolveModelForProvider('openrouter', 'meta-llama/llama-4-maverick', null)
    ).toBe('meta-llama/llama-4-maverick');
  });

  it('retombe sur le premier modèle du provider si le modèle chargé est incohérent', () => {
    expect(
      resolveModelForProvider('openrouter', 'mistral-nemo', null)
    ).toBe('anthropic/claude-sonnet-4-6');
  });

  it('conserve un modèle custom absent de la liste statique si présent dans backendAvailableModels (R1 v0.11.4)', () => {
    expect(
      resolveModelForProvider(
        'openrouter',
        'myorg/custom-model-xyz',
        null,
        ['myorg/custom-model-xyz']
      )
    ).toBe('myorg/custom-model-xyz');
  });

  it('déduplique la fusion backendAvailableModels et liste statique', () => {
    const result = resolveModelForProvider(
      'openrouter',
      'anthropic/claude-sonnet-4-6',
      null,
      ['anthropic/claude-sonnet-4-6', 'custom/model']
    );
    expect(result).toBe('anthropic/claude-sonnet-4-6');
  });
});
