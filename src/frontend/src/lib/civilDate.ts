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

const parisFormatter = new Intl.DateTimeFormat('fr-FR', {
  timeZone: 'Europe/Paris',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
});

/** Jour civil de Paris porté par une valeur ISO éventuellement zonée. */
export function parisDateKey(value: string): string {
  const literal = value.slice(0, 10);
  const hasExplicitTimezone = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value);
  if (!hasExplicitTimezone) return literal;

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return literal;
  const parts = Object.fromEntries(
    parisFormatter.formatToParts(parsed).map((part) => [part.type, part.value]),
  );
  return `${parts.year}-${parts.month}-${parts.day}`;
}

/** Une échéance est dépassée seulement si son JOUR civil est antérieur. */
export function isPastParisCivilDate(value: string, now: Date = new Date()): boolean {
  return parisDateKey(value) < parisDateKey(now.toISOString());
}


/** B-369 : une clé civile « YYYY-MM-DD » se lit en composants LOCAUX. `new
 * Date('YYYY-MM-DD')` construit minuit UTC : à l'ouest de Greenwich, c'est la
 * veille. */
export function parseLocalDateKey(key: string): Date {
  const [y, m, d] = key.slice(0, 10).split('-').map(Number);
  return new Date(y, (m || 1) - 1, d || 1);
}

interface EvenementCivil {
  all_day?: boolean | null;
  start_date?: string | null;
  end_date?: string | null;
  start_datetime?: string | null;
  end_datetime?: string | null;
}

/** B-379 : toutes les clés de jour qu'un événement occupe. Une journée entière
 * couvre [start_date, end_date] (fin INCLUSIVE dans l'application, cf.
 * BUG-144) ; un rendez-vous horodaté garde sa clé de début (la grille le
 * positionne par sa durée, cf. B-058). */
export function clesDeJoursCouverts(evenement: EvenementCivil): string[] {
  const debut = evenement.start_date || evenement.start_datetime?.slice(0, 10) || '';
  if (!debut) return [];
  if (!evenement.all_day || !evenement.end_date || evenement.end_date <= debut) return [debut];
  const cles: string[] = [];
  const fin = parseLocalDateKey(evenement.end_date);
  for (let jour = parseLocalDateKey(debut); jour <= fin && cles.length < 366; jour.setDate(jour.getDate() + 1)) {
    cles.push(localDateKey(jour));
  }
  return cles;
}
