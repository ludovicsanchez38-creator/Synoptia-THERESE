/**
 * B-1146 : un modèle Ollama Cloud (« gpt-oss:120b-cloud », « kimi-k2.6:cloud »)
 * figure parmi les modèles installés, mais Ollama transmet ses requêtes à
 * ollama.com. Même règle que le moteur (ollama_capabilites.est_modele_ollama_cloud).
 */
export function estModeleOllamaCloud(nom: string): boolean {
  const n = nom.trim().toLowerCase();
  return n.endsWith(':cloud') || n.endsWith('-cloud');
}

/** B-1158 : clé d'accord d'un modèle Ollama Cloud (destination : ollama.com). */
export const FOURNISSEUR_OLLAMA_CLOUD = 'ollama-cloud';

/**
 * B-1158 : la destination réelle d'un envoi, pour l'accord. `null` = local,
 * aucun accord ; un modèle Ollama Cloud part chez ollama.com et demande le
 * même accord qu'un fournisseur en ligne ; sinon, le fournisseur lui-même.
 */
export function fournisseurDAccord(fournisseur: string | null, modele: string | null): string | null {
  if (!fournisseur) return null;
  if (fournisseur !== 'ollama') return fournisseur;
  return modele && estModeleOllamaCloud(modele) ? FOURNISSEUR_OLLAMA_CLOUD : null;
}
