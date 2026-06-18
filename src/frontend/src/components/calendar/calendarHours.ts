// Calcule la plage horaire à afficher dans les vues Semaine/Jour de l'agenda.
// Part d'une fenêtre par défaut et l'ÉLARGIT pour englober tous les événements
// horodatés visibles, afin qu'aucun RDV (tôt le matin ou tard le soir) ne
// disparaisse. Bornée à 0h-24h.

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
    const eventEndHour = end.getHours() + (end.getMinutes() > 0 ? 1 : 0);

    if (eventStartHour < startHour) startHour = eventStartHour;
    if (eventEndHour > endHour) endHour = eventEndHour;
  }

  return {
    startHour: Math.max(0, startHour),
    endHour: Math.min(24, endHour),
  };
}
