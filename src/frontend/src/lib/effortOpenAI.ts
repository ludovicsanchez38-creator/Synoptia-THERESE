/**
 * P-045 (lecteur c4-R11, B-594) : sur /v1/chat/completions, la famille GPT-5
 * et o-series d'OpenAI refuse les outils de fonction dès qu'un effort de
 * raisonnement s'applique ; le backend (`providers/openai.py`,
 * `_uses_max_completion_tokens`) pose alors l'effort à « none » pour ce
 * message, sans le dire à l'écran. Même prédicat ici, prouvé égal par des
 * témoins partagés (`effortOpenAI.temoins.json`, test de parité pytest).
 */
export function modeleOpenAIRaisonnant(modele: string): boolean {
  const m = modele.toLowerCase();
  return m.startsWith('gpt-5') || m.startsWith('o1') || m.startsWith('o3') || m.startsWith('o4');
}

/** Sans outils, l'effort n'est transmis qu'aux modèles dont le support est
 * vérifié dans le catalogue backend (fiches GPT-5.6 « tel quel »). */
const EFFORT_TRANSMIS_SANS_OUTILS = new Set(['gpt-5.6-sol', 'gpt-5.6-terra', 'gpt-5.6-luna']);

export function effortTransmisSansOutils(modele: string): boolean {
  return EFFORT_TRANSMIS_SANS_OUTILS.has(modele.toLowerCase());
}
