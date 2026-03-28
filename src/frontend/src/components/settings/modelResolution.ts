import * as api from '../../services/api';
import { PROVIDERS } from './LLMTab';

export function resolveModelForProvider(
  provider: api.LLMProvider,
  requestedModel: string,
  ollamaStatusData: api.OllamaStatus | null
) {
  const providerConfig = PROVIDERS.find((p) => p.id === provider);
  const providerModels = provider === 'ollama'
    ? (ollamaStatusData?.available ? ollamaStatusData.models.map((m) => m.name) : [])
    : (providerConfig?.models.map((m) => m.id) || []);

  return providerModels.includes(requestedModel)
    ? requestedModel
    : providerModels[0] || requestedModel;
}
