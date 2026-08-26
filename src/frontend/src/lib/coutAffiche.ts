/**
 * L'unité des coûts affichés (revue Soso S2-4, hotfix 0.48.1).
 *
 * Tous les tarifs de `token_tracker.TOKEN_PRICES` sont relevés en USD dans
 * les documentations officielles (Anthropic, OpenAI, Google, Mistral, xAI).
 * Le backend les additionne tels quels : le champ s'appelle `cost_eur` pour
 * des raisons historiques, mais la VALEUR est en dollars. L'afficher avec
 * « € » annonçait un chiffre faux d'environ 9 %.
 *
 * Tant qu'aucun taux de change n'est sourcé dans l'application (et un taux
 * inventé serait pire), on affiche la vérité : des dollars.
 * Dette : renommer `cost_eur` / `monthly_budget_eur` côté API et base.
 */
export const UNITE_COUT = '$';

/** Formate un coût en USD, ou « — » quand il n'y en a pas. */
export function formaterCout(
  montant: number | null | undefined,
  decimales = 2,
): string {
  if (typeof montant !== 'number' || Number.isNaN(montant)) return '—';
  return `${montant.toFixed(decimales)} ${UNITE_COUT}`;
}
