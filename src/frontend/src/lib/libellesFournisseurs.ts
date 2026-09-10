/**
 * Libellés lisibles des fournisseurs d'IA, partagés par l'assistant de mise
 * en route (consentement) et le composeur (bandeau cloud).
 *
 * #294 / D202 (cycle 6) : deux tables partielles vivaient dans SecurityStep
 * et ChatInput ; les quatre fournisseurs compatibles OpenAI ajoutés en
 * 0.43.4 y manquaient et la phrase de consentement affichait « vers glm ».
 * Le type `Record<LLMProvider, string>` oblige à compléter la table à chaque
 * ajout de fournisseur.
 */
import type { LLMProvider } from '../services/api/config';

export const LIBELLES_FOURNISSEURS: Record<LLMProvider, string> = {
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  gemini: 'Google Gemini',
  mistral: 'Mistral',
  grok: 'xAI',
  openrouter: 'OpenRouter',
  perplexity: 'Perplexity',
  deepseek: 'DeepSeek',
  infomaniak: 'Infomaniak',
  ollama: 'Ollama local',
  glm: 'Zhipu GLM',
  kimi: 'Moonshot Kimi',
  qwen: 'Alibaba Qwen',
  minimax: 'MiniMax',
};

/** Le libellé d'un fournisseur ; l'identifiant lui-même s'il est inconnu. */
export function libelleDuFournisseur(fournisseur: string): string {
  return (LIBELLES_FOURNISSEURS as Record<string, string>)[fournisseur] ?? fournisseur;
}
