/**
 * Décision du 25/09 (délégation de Ludo) : Décision part en « Souverain »
 * quand le service choisi est Ollama local (un modèle Ollama Cloud part en
 * ligne, B-1156). En cas de doute (configuration illisible), « Cloud », le
 * comportement d'avant.
 */
import { getLLMConfig } from '../services/api/config';
import { estModeleOllamaCloud } from './ollamaCloud';

export type ModeDuBoard = 'cloud' | 'sovereign';

export async function modeDuBoardParDefaut(): Promise<ModeDuBoard> {
  try {
    const cfg = await getLLMConfig();
    return cfg.provider === 'ollama' && cfg.model && !estModeleOllamaCloud(cfg.model) ? 'sovereign' : 'cloud';
  } catch {
    return 'cloud';
  }
}
