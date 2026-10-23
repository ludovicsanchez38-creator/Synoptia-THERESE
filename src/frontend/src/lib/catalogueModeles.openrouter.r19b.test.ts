import { describe, expect, it } from 'vitest';

import { FOURNISSEURS, decorer } from './catalogueModeles';

describe('R1-9b : noms OpenRouter issus du catalogue', () => {
  it.each([
    ['anthropic/claude-sonnet-4-6', 'Claude Sonnet 4.6'],
    ['anthropic/claude-opus-4-8', 'Claude Opus 4.8'],
    ['openai/gpt-5.5', 'GPT-5.5'],
    ['google/gemini-3.5-flash', 'Gemini 3.5 Flash'],
  ])('%s reprend le nom lisible connu', (id, name) => {
    const fournisseur = FOURNISSEURS.find((p) => p.id === 'openrouter')!;
    expect(fournisseur.models.find((m) => m.id === id)?.name).toBe(name);
    expect(decorer([id])[0].name).toBe(name);
  });

  it('retire le préfixe des modèles du catalogue et conserve les inconnus', () => {
    expect(decorer(['meta-llama/llama-4-maverick'])[0].name).toBe('Llama 4 Maverick');
    expect(decorer(['inconnu/modele-1-2'])[0].name).toBe('Modele 1.2 (inconnu)');
  });
});


it.each([
  ['google/gemini-8-2-pro-20261023', 'Gemini 8.2 Pro'],
  ['meta-llama/llama-8-scout', 'Llama 8 Scout'],
  ['deepseek-v8-pro', 'DeepSeek V8 Pro'],
  ['ministral-24b-2611', 'Ministral 24B'],
  ['inconnu/modele-1-2', 'Modele 1.2 (inconnu)'],
  ['autre/modele-1-2', 'Modele 1.2 (autre)'],
])('B-1097 : decorer formate aussi le modèle absent du catalogue %s', (id, attendu) => {
  expect(decorer([id])[0].name).toBe(attendu);
});


it.each(['qwen3:8b', 'llama3.2:latest', 'mistral:7b-instruct-q4_K_M', 'gemma4:12b', 'deepseek-r2:14b'])(
  'B-1097 : un modèle local à étiquette garde son nom exact (%s)', (id) => {
    expect(decorer([id])[0].name).toBe(id);
  },
);
