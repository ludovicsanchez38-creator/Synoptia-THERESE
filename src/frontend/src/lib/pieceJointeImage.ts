/**
 * Une image se montre au modèle, elle ne s'indexe pas.
 *
 * 31/08/2026 : déposer une capture d'écran dans le chat répondait « Type de
 * fichier non autorisé pour l'indexation : '.png' [...] Ce fichier ne sera
 * pas utilisé pour répondre. » Le composeur envoyait toute pièce jointe à la
 * chaîne d'extraction de texte, qui ne sait rien faire d'une image.
 *
 * La liste est volontairement courte et alignée sur celle du backend
 * (`app/services/images_jointes.py`) : promettre une extension que le
 * fournisseur refusera ne rendrait service à personne.
 */
export const EXTENSIONS_IMAGE = ['.png', '.jpg', '.jpeg', '.webp', '.gif'] as const;

export function estUneImage(chemin: string): boolean {
  const minuscules = chemin.toLowerCase();
  return EXTENSIONS_IMAGE.some((extension) => minuscules.endsWith(extension));
}
