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
});
