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

/** B-1216 : libellés des moteurs d'images, comme à l'écran de génération. */
const MOTEURS_D_IMAGES: Record<string, string> = {
  'gpt-image-2': 'GPT Image 2',
  'fal-flux-pro': 'Fal Flux Pro',
  // B-1226 : le nom de l'écran Images, où cet accord est donné.
  'nanobanan-pro': 'Nano Banana',
};

/** Le libellé d'un fournisseur ; l'identifiant lui-même s'il est inconnu. */
export function libelleDuFournisseur(fournisseur: string): string {
  // B-1158 : clé d'accord des modèles Ollama Cloud (lib/ollamaCloud.ts).
  if (fournisseur === 'ollama-cloud') return 'Ollama Cloud (ollama.com)';
  // B-1216 : les moteurs d'images ont aussi leurs accords (Confidentialité).
  const moteurDImages = MOTEURS_D_IMAGES[fournisseur];
  if (moteurDImages) return moteurDImages;
  return (LIBELLES_FOURNISSEURS as Record<string, string>)[fournisseur] ?? fournisseur;
}
