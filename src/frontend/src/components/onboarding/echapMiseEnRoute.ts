/**
 * Ce que fait Échap pendant la mise en route.
 *
 * 01/09/2026 : `onEscape` était branché sur `getCurrentWindow().close()`.
 * Un nouvel utilisateur qui faisait le geste réflexe de fermer une boîte de
 * dialogue quittait l'application entière, à son tout premier contact, et
 * aucune autre sortie clavier n'existait.
 *
 * Échap recule d'une étape. Sur la première, il ne fait rien : à ce moment-là
 * l'utilisateur n'a encore rien configuré, et quitter serait le pire des
 * résultats possibles pour une touche pressée par réflexe.
 */
export function echapPendantLaMiseEnRoute(options: {
  etape: number;
  reculer: () => void;
  fermer?: () => void;
}): void {
  if (options.etape > 0) {
    options.reculer();
  }
}
