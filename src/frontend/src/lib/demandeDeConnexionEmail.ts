/**
 * B-1436 (recette P-146, lot 1 ; décision du 25/09) : l'écran Email intégré
 * n'ouvre l'assistant de connexion que sur demande explicite (« Brancher mes
 * mails » à l'Accueil). La demande se consomme une fois : revenir sur l'écran
 * plus tard montre « Configurer un compte », sans assistant par-dessus.
 */
let demande = false;

export function demanderLaConnexionEmail(): void {
  demande = true;
}

export function consommerLaDemandeDeConnexionEmail(): boolean {
  const presente = demande;
  demande = false;
  return presente;
}
