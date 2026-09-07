/**
 * État d'une étape du fil de la mise en route (B-612, persona Jean).
 * Une étape passée par « Configurer plus tard » n'est pas « faite » : le fil
 * ne doit pas lui coller une coche verte que le récapitulatif contredit.
 */
export type EtatEtape = 'faite' | 'passee' | 'courante' | 'a-venir';

/**
 * B-607 : « Configurer plus tard » après un fournisseur enregistré un écran
 * plus tôt doit défaire cet enregistrement (LLMStep est remonté après « Retour »,
 * seul le wizard se souvient du choix précédent).
 */
export function doitEffacerLeChoixDeServiceIa(precedent: string | null, nouveau: string | null): boolean {
  return precedent !== null && nouveau === null;
}

export function etatDeLEtape(index: number, courante: number, passees: readonly number[] = []): EtatEtape {
  if (index === courante) return 'courante';
  if (index > courante) return 'a-venir';
  return passees.includes(index) ? 'passee' : 'faite';
}
