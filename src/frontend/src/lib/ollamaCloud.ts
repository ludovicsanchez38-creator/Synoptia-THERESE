/**
 * B-1146 : un modèle Ollama Cloud (« gpt-oss:120b-cloud », « kimi-k2.6:cloud »)
 * figure parmi les modèles installés, mais Ollama transmet ses requêtes à
 * ollama.com. Même règle que le moteur (ollama_capabilites.est_modele_ollama_cloud).
 */
export function estModeleOllamaCloud(nom: string): boolean {
  const n = nom.trim().toLowerCase();
  return n.endsWith(':cloud') || n.endsWith('-cloud');
}
