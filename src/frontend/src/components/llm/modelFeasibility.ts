import type { OllamaModel, SystemResources } from '../../services/api';

export type LocalModelFeasibilityStatus = 'feasible' | 'too-large' | 'unknown';

export interface LocalModelFeasibilityResult {
  status: LocalModelFeasibilityStatus;
  estimatedRamBytes: number | null;
}

export function assessLocalModelFeasibility(
  model: OllamaModel | undefined,
  resources: SystemResources | null,
): LocalModelFeasibilityResult {
  if (
    model?.size == null
    || model.size <= 0
    || resources?.safe_local_model_ram_bytes == null
  ) {
    return { status: 'unknown', estimatedRamBytes: null };
  }

  const estimatedRamBytes = model.size + resources.ollama_context_margin_bytes;
  return {
    status: estimatedRamBytes <= resources.safe_local_model_ram_bytes ? 'feasible' : 'too-large',
    estimatedRamBytes,
  };
}
