/**
 * Heure locale d'un horodatage du moteur (P-097).
 *
 * Le registre des travaux sérialise des dates UTC SANS fuseau
 * (« 2026-09-24T08:57:46.552141 ») : `new Date()` les lirait comme heure
 * locale, deux heures d'écart à Paris l'été. Sans désignateur, on ajoute Z.
 */
export function heureDuServeur(horodatage: string | null | undefined): string | null {
  if (!horodatage) return null;
  const avecFuseau = /(?:[zZ]|[+-]\d{2}:?\d{2})$/.test(horodatage) ? horodatage : `${horodatage}Z`;
  const date = new Date(avecFuseau);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}
