import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { OllamaModel, SystemResources } from '../../services/api';
import { LocalModelFeasibility } from './LocalModelFeasibility';
import { assessLocalModelFeasibility } from './modelFeasibility';

const GIB = 1024 ** 3;
const resources: SystemResources = {
  total_ram_bytes: 16 * GIB,
  safe_local_model_ram_bytes: 8 * GIB,
  ollama_context_margin_bytes: 2 * GIB,
  detection_method: 'test',
};

function model(size: number | null): OllamaModel {
  return { name: 'qwen:8b', size, modified_at: null, digest: null };
}

describe('LocalModelFeasibility', () => {
  it('est vert quand taille du modèle et contexte tiennent dans la moitié de la RAM', () => {
    expect(assessLocalModelFeasibility(model(6 * GIB), resources)).toEqual({
      status: 'feasible',
      estimatedRamBytes: 8 * GIB,
    });

    render(<LocalModelFeasibility model={model(6 * GIB)} resources={resources} />);
    expect(screen.getByTestId('local-model-feasibility')).toHaveAttribute('data-status', 'feasible');
  });

  it('avertit en rouge au-dessus du plafond sans bloquer le choix', () => {
    render(<LocalModelFeasibility model={model(7 * GIB)} resources={resources} />);

    const warning = screen.getByRole('alert');
    expect(warning).toHaveAttribute('data-status', 'too-large');
    expect(warning).toHaveTextContent('Le choix reste possible');
  });

  it('reste explicite quand Ollama ne fournit pas la taille', () => {
    render(<LocalModelFeasibility model={model(null)} resources={resources} />);
    expect(screen.getByTestId('local-model-feasibility')).toHaveAttribute('data-status', 'unknown');
  });
});
