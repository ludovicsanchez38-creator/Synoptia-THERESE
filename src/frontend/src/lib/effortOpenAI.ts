/**
 * P-045 (lecteur c4-R11, B-594) : sur /v1/chat/completions, la famille GPT-5
 * et o-series d'OpenAI refuse les outils de fonction dès qu'un effort de
 * raisonnement s'applique ; le backend (`providers/openai.py`,
 * `_uses_max_completion_tokens`) pose alors l'effort à « none » pour ce
 * message, sans le dire à l'écran. Deux prédicats ici, prouvés par des
 * témoins partagés (`effortOpenAI.temoins.json`, test de parité pytest) :
 * la famille de paramètres (`familleDeParametres`, Astra compris) et le
 * transport avec outils (`effortConserveAvecOutils`).
 */
/** Ces modèles gardent l'effort choisi quand des outils sont là : leurs
 * appels passent par Responses, qui accepte l'effort. gpt-6.1-sol refuse
 * none et minimal (fiche du 09/10/2026). gpt-6-astra exige Responses pour
 * les outils et refuse none (guides du 09/10/2026, B-1774). */
const EFFORT_CONSERVE_AVEC_OUTILS = new Set(['gpt-6.1-sol', 'gpt-6-astra']);

export function effortConserveAvecOutils(modele: string): boolean {
  return EFFORT_CONSERVE_AVEC_OUTILS.has(modele.toLowerCase());
}

/** Fiche gpt-6.1-sol : xhigh est un palier à part, entre élevé et maximal. */
export function effortXhighPropose(modele: string): boolean {
  return modele.trim().toLowerCase() === 'gpt-6.1-sol';
}

/** Famille qui envoie max_completion_tokens. Astra y reste, témoin compris.
 * Ce n'est pas le transport : les outils d'Astra passent par Responses. */
export function familleDeParametres(modele: string): boolean {
  const m = modele.toLowerCase();
  return m.startsWith('gpt-6') || m.startsWith('gpt-5') || m.startsWith('o1') || m.startsWith('o3') || m.startsWith('o4');
}

export function modeleOpenAIRaisonnant(modele: string): boolean {
  const m = modele.toLowerCase();
  // L'écran dit que l'effort est coupé seulement si les outils restent sur
  // Chat Completions. Responses conserve l'effort : le prédicat est faux.
  if (effortConserveAvecOutils(m)) return false;
  return familleDeParametres(m);
}

/** Sans outils, l'effort n'est transmis qu'aux modèles dont le support est
 * vérifié dans le catalogue backend (fiches GPT-5.6 « tel quel »). */
// P-122 (25/09/2026) : gpt-6-sol et gpt-6-luna, même contrat que gpt-6-astra.
const EFFORT_TRANSMIS_SANS_OUTILS = new Set(['gpt-6-sol', 'gpt-6-astra', 'gpt-6-luna', 'gpt-6.1-sol', 'gpt-5.6-sol', 'gpt-5.6-terra', 'gpt-5.6-luna']);

export function effortTransmisSansOutils(modele: string): boolean {
  return EFFORT_TRANSMIS_SANS_OUTILS.has(modele.toLowerCase());
}
