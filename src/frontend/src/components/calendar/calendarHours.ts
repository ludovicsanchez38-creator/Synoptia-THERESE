// Calcule la plage horaire à afficher dans les vues Semaine/Jour de l'agenda.
// Part d'une fenêtre par défaut et l'ÉLARGIT pour englober tous les événements
// horodatés visibles, afin qu'aucun RDV (tôt le matin ou tard le soir) ne
// disparaisse. Bornée à 0h-24h.

import { localDateKey } from '../../lib/civilDate';

interface TimedEventLike {
  start_datetime?: string | null;
  end_datetime?: string | null;
  all_day?: boolean;
}

export function getVisibleHourRange(
  events: TimedEventLike[],
  defaultStartHour: number,
  defaultEndHour: number
): { startHour: number; endHour: number } {
  let startHour = defaultStartHour;
  let endHour = defaultEndHour;

  for (const event of events) {
    if (event.all_day) continue;
    if (!event.start_datetime || !event.end_datetime) continue;

    const start = new Date(event.start_datetime);
    const end = new Date(event.end_datetime);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) continue;

    const eventStartHour = start.getHours();
    // Arrondi à l'heure supérieure si l'événement finit en cours d'heure.
    // B-058 : une fin le JOUR SUIVANT (23:00 -> 01:00) rendait 1, c'est-à-dire
    // une borne haute plus basse que le début — la grille ne s'élargissait
    // même pas jusqu'à 23 h et le rendez-vous restait invisible. Sur le jour de
    // début, un tel rendez-vous court jusqu'à minuit.
    const finitApresLeJourDeDebut =
      localDateKey(end) !== localDateKey(start) && end.getTime() > start.getTime();
    const eventEndHour = finitApresLeJourDeDebut
      ? 24
      : end.getHours() + (end.getMinutes() > 0 ? 1 : 0);

    if (eventStartHour < startHour) startHour = eventStartHour;
    if (eventEndHour > endHour) endHour = eventEndHour;
  }

  return {
    startHour: Math.max(0, startHour),
    endHour: Math.min(24, endHour),
  };
}
