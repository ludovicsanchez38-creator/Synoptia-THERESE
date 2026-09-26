/** Nom affiché d'un fournisseur d'images (Accueil, panneau de saisie). */
export function libelleFournisseurImage(provider: string): string {
  if (provider === 'gpt-image-2') return 'GPT Image 2';
  if (provider === 'fal-flux-pro') return 'Fal Flux Pro';
  return 'Nano Banana 2';
}
