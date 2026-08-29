/**
 * Le variateur du brief du jour (plan du 29/08/2026).
 *
 * Trois mots règlent combien de lignes le brief développe le matin. C'est un
 * réglage d'affichage, et rien d'autre.
 *
 * Ce qu'il n'est pas, parce que deux revues de design l'ont refusé le 29/08 :
 *  - ce n'est pas une « capacité du jour ». Le mot interprète un état du corps ;
 *    ces trois-là décrivent une action sur une liste ;
 *  - il ne détecte rien et ne s'adapte à rien. Il enregistre un geste déjà fait ;
 *  - il ne cache rien. Le reste est replié, et le repli annonce ses retards.
 *
 * CE MODULE NE DOIT ÊTRE IMPORTÉ PAR AUCUNE COUCHE QUI PARLE AU MODÈLE.
 * Un test d'architecture le vérifie (`variateurDuBrief.etancheite.test.ts`).
 * Le jour où le chat serait « aligné » sur le brief réduit, il y aurait soit
 * une fuite, soit un assistant qui ratifie des échéances invisibles.
 */

export type ReglageDuBrief = 'tout' | 'essentiel' | 'minimum';

/** Le comportement d'aujourd'hui : personne ne change d'écran sans un geste. */
export const REGLAGE_PAR_DEFAUT: ReglageDuBrief = 'essentiel';

/** Les mots sont écrits en toutes lettres. Pas de pastille, pas d'infobulle. */
export const MOTS_DU_VARIATEUR: ReadonlyArray<{ valeur: ReglageDuBrief; mot: string }> = [
  { valeur: 'tout', mot: 'tout' },
  { valeur: 'essentiel', mot: "l'essentiel" },
  { valeur: 'minimum', mot: 'le minimum' },
];

/** `null` = aucun seuil, la liste entière est développée. */
const SEUILS: Record<ReglageDuBrief, number | null> = {
  tout: null,
  essentiel: 6,
  minimum: 2,
};

export function seuilDuReglage(reglage: ReglageDuBrief): number | null {
  return SEUILS[reglage];
}

const PREFIXE = 'therese.brief.variateur';

function estUnReglage(valeur: unknown): valeur is ReglageDuBrief {
  return valeur === 'tout' || valeur === 'essentiel' || valeur === 'minimum';
}

/**
 * Efface tout réglage qui n'est pas celui du jour annoncé par le backend.
 *
 * Sans ça, une valeur par jour s'accumulerait en silence, et une accumulation
 * sans restitution est déjà un historique. Il n'y en aura pas.
 */
function oublierLesAutresJours(jour: string): void {
  const aJeter: string[] = [];
  for (let i = 0; i < window.localStorage.length; i += 1) {
    const cle = window.localStorage.key(i);
    if (cle && cle.startsWith(`${PREFIXE}.`) && cle !== `${PREFIXE}.${jour}`) {
      aJeter.push(cle);
    }
  }
  for (const cle of aJeter) window.localStorage.removeItem(cle);
}

/**
 * `jour` vient de `TodayDashboard.date`, la journée civile calculée par le
 * backend. Jamais d'un `new Date()` du navigateur : c'est la leçon BUG-125, et
 * c'est ce qui garantit que l'accueil et le backend parlent du même jour.
 */
export function lireLeReglage(jour: string): ReglageDuBrief {
  try {
    oublierLesAutresJours(jour);
    const brut = window.localStorage.getItem(`${PREFIXE}.${jour}`);
    return estUnReglage(brut) ? brut : REGLAGE_PAR_DEFAUT;
  } catch {
    // Fenêtre privée, données de site bloquées, capture de vignette : le
    // variateur sert quand même pour la séance.
    return REGLAGE_PAR_DEFAUT;
  }
}

export function ecrireLeReglage(jour: string, reglage: ReglageDuBrief): void {
  try {
    window.localStorage.setItem(`${PREFIXE}.${jour}`, reglage);
  } catch {
    // Rien à signaler : ce réglage ne porte aucune donnée, et son oubli ne
    // coûte qu'un clic demain matin.
  }
}

/**
 * Le repli annonce ses retards.
 *
 * Arbitrage du 29/08 : Grok voulait un seuil purement mécanique, Soso voulait
 * qu'aucun retard ne disparaisse en silence. Le seuil reste mécanique (donc
 * prévisible, donc testable) et le libellé dit ce qu'il replie.
 */
export function libelleDuRepli(nbReplies: number, nbRetardsReplies: number): string {
  const base = `Voir les ${nbReplies} autre${nbReplies > 1 ? 's' : ''} élément${nbReplies > 1 ? 's' : ''}`;
  if (nbRetardsReplies <= 0) return base;
  return `${base}, dont ${nbRetardsReplies} en retard`;
}
