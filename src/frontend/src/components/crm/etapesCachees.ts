/**
 * P-157 : à 800 px la grille ne montre que ses premières colonnes.
 * Une étape compte dès qu'elle dépasse le cadre de plus d'un pixel
 * (un sous-pixel de rendu ne doit pas allumer l'indice).
 */

const TOLERANCE_PX = 1;

export interface MesureColonne {
  gauche: number;
  largeur: number;
}

export interface VuePipeline {
  scrollLeft: number;
  clientWidth: number;
}

export interface EtapesHorsCadre {
  aGauche: number;
  aDroite: number;
}

export function decompteEtapesCachees(
  vue: VuePipeline,
  colonnes: readonly MesureColonne[],
): EtapesHorsCadre {
  const bordGauche = vue.scrollLeft;
  const bordDroit = vue.scrollLeft + vue.clientWidth;
  let aGauche = 0;
  let aDroite = 0;
  for (const colonne of colonnes) {
    if (colonne.gauche < bordGauche - TOLERANCE_PX) aGauche += 1;
    if (colonne.gauche + colonne.largeur > bordDroit + TOLERANCE_PX) aDroite += 1;
  }
  return { aGauche, aDroite };
}

/** « 1 étape à droite », « 3 étapes à gauche ». */
export function mentionDEtapesCachees(nombre: number, cote: 'gauche' | 'droite'): string {
  const mot = nombre > 1 ? 'étapes' : 'étape';
  return `${nombre} ${mot} à ${cote}`;
}

/**
 * Décalage qui aligne la colonne cachée la plus proche du cadre.
 * À droite : la première qui dépasse. À gauche : la dernière encore coupée.
 */
export function defilementVersEtapesCachees(
  vue: VuePipeline,
  colonnes: readonly MesureColonne[],
  cote: 'gauche' | 'droite',
): number | null {
  const bordGauche = vue.scrollLeft;
  const bordDroit = vue.scrollLeft + vue.clientWidth;
  let destination: number | null = null;
  for (const colonne of colonnes) {
    if (cote === 'droite') {
      const cachee = colonne.gauche + colonne.largeur > bordDroit + TOLERANCE_PX;
      if (cachee && (destination === null || colonne.gauche < destination)) destination = colonne.gauche;
    } else if (colonne.gauche < bordGauche - TOLERANCE_PX && (destination === null || colonne.gauche > destination)) {
      destination = colonne.gauche;
    }
  }
  return destination;
}
