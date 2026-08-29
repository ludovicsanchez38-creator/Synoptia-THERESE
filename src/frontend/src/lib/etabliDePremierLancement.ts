import { ACTIONS_ETABLI, type ActionEtabli } from './etabli';

/**
 * Les verbes de l'établi, selon ce que l'installation contient déjà.
 *
 * Campagne dix personas : huit sur dix ne se reconnaissent pas dans le premier
 * écran. Le médecin, l'écrivaine, la magistrate et le responsable administratif
 * voyaient « Facturer » au quatrième rang d'une installation vide, avant
 * d'avoir demandé quoi que ce soit.
 *
 * Ce n'est PAS le chantier « accueil par métier », qui attend un arbitrage de
 * cap et refera tout ce qu'on écrirait avant. C'est la plus petite chose
 * honnête, et la seule qui survive aux deux réponses possibles : ne pas
 * costumer quelqu'un en commerçant tant qu'il n'a rien facturé.
 *
 * `Facturer` REVIENT dès qu'il existe une pièce ou que les infos de société
 * sont renseignées - il ne disparaît pas, il attend son tour. Et il reste
 * accessible en permanence par la palette de commandes : masquer un verbe de
 * l'établi ne retire aucune capacité.
 */
export function actionsDeLEtabli(options: {
  auMoinsUneFacture: boolean;
  infosSocieteCompletes: boolean;
}): readonly ActionEtabli[] {
  const facturationEngagee = options.auMoinsUneFacture || options.infosSocieteCompletes;
  if (facturationEngagee) return ACTIONS_ETABLI;
  return ACTIONS_ETABLI.filter((action) => action.id !== 'invoice');
}
