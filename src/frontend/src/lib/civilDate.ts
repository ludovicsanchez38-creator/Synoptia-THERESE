/**
 * Clé de date CIVILE locale (YYYY-MM-DD).
 *
 * Harmonisation 17/07 : ne JAMAIS dériver une clé de jour via
 * `toISOString().split('T')[0]` - c'est la date UTC. En France (UTC+1/+2),
 * minuit local appartient encore à la veille UTC : toutes les cellules du
 * calendrier étaient décalées d'un jour (anneau « aujourd'hui » sur demain,
 * événements du vendredi rangés dans la case du samedi).
 */
export function localDateKey(d: Date): string {
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${month}-${day}`;
}
