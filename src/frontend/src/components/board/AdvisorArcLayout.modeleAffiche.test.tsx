/**
 * B-110 : le modèle lu dans le sélecteur est celui qui délibérera.
 *
 * Le sélecteur affichait `selectedModels[role] || defaultModel`, mais
 * `selectedModels` restait vide tant que personne ne touchait un menu : le
 * Board envoyait alors `ollama_models: {}` et le serveur retombait sur son
 * propre calcul (préférence LLM, puis modèle Ollama détecté). L'écran
 * annonçait donc un modèle, un autre répondait.
 *
 * La garde : ce qui est affiché est déclaré au parent, donc envoyé.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { AdvisorArcLayout, type OllamaModelInfo } from './AdvisorArcLayout';

const MODELES: OllamaModelInfo[] = [
  { name: 'qwen2.5:3b', size: 2_000_000_000 },
  { name: 'mistral-nemo', size: 7_000_000_000 },
];

const ROLES = ['analyst', 'strategist', 'devil', 'pragmatic', 'visionary'];

describe('B-110 : le modèle affiché est celui qui sera envoyé', () => {
  it('déclare au parent le modèle par défaut de chaque conseiller', () => {
    const onModelChange = vi.fn();
    render(
      <AdvisorArcLayout
        mode="sovereign"
        ollamaModels={MODELES}
        selectedModels={{}}
        onModelChange={onModelChange}
      />,
    );

    const declares = new Map(
      onModelChange.mock.calls.map(([role, modele]) => [role, modele]),
    );
    expect([...declares.keys()].sort()).toEqual([...ROLES].sort());
    for (const role of ROLES) {
      expect(declares.get(role)).toBe('qwen2.5:3b');
    }
  });

  it('ne réécrit pas un choix déjà fait', () => {
    const onModelChange = vi.fn();
    render(
      <AdvisorArcLayout
        mode="sovereign"
        ollamaModels={MODELES}
        selectedModels={{
          analyst: 'mistral-nemo',
          strategist: 'mistral-nemo',
          devil: 'mistral-nemo',
          pragmatic: 'mistral-nemo',
          visionary: 'mistral-nemo',
        }}
        onModelChange={onModelChange}
      />,
    );
    expect(onModelChange).not.toHaveBeenCalled();
  });

  it('ne déclare rien en mode cloud, où aucun modèle Ollama ne sert', () => {
    const onModelChange = vi.fn();
    render(
      <AdvisorArcLayout
        mode="cloud"
        ollamaModels={MODELES}
        selectedModels={{}}
        onModelChange={onModelChange}
      />,
    );
    expect(onModelChange).not.toHaveBeenCalled();
    expect(screen.queryByLabelText(/Modèle du conseiller/)).toBeNull();
  });
});
