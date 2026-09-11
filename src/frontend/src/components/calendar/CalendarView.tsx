/**
 * THÉRÈSE v2 - Calendar View
 *
 * Vue calendrier (mois/semaine/jour/liste).
 * Phase 2 - Calendar
 */

import { useMemo, useEffect, useRef } from 'react';
import { clesDeJoursCouverts, localDateKey, parseLocalDateKey } from '../../lib/civilDate';
import { useCalendarStore } from '../../stores/calendarStore';
import type { CalendarEvent } from '../../services/api';
import { getVisibleHourRange } from './calendarHours';
import { getTimedEventLayout } from './calendarEventLayout';
import { trierLesEvenementsDuJour } from '../../lib/ordreDesEvenements';
import { Carte } from '../ui/Carte';
import { EtatVide } from '../ui/EtatVide';

/** B-247 : la semaine française commence le LUNDI. Une seule liste pour les
 *  deux vues — le Mois et la Semaine tenaient chacun la leur, et le Mois avait
 *  gardé la convention américaine (dimanche d'abord).
 *  DA lot 8 : la maquette écrit « lun. » … « dim. » (`agenda.html:75`, `:85`). */
const ETIQUETTES_JOURS = ['lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.', 'dim.'];

/* DA « Application affinée », lot 8 (§ 3.0) : partout où un conteneur défile,
   l'anneau du socle (3 px, offset 2, soit 5 px hors boîte) serait coupé. Les
   interactifs des quatre vues portent donc un anneau RENTRANT, et le même
   partout, pour que le focus se dessine pareil sur toute la surface. */
const ANNEAU_RENTRANT =
  'focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-[-3px] focus-visible:outline-ring';

/* Les trois gabarits de la Semaine partagent la colonne de gouttière et les
   sept `1fr`. Ils réservent aussi la même gouttière de barre de défilement :
   sans elle, seule la piste (le seul des trois à défiler) perdrait la largeur
   de la barre sur une plateforme à barres classiques, et ses sept traits ne
   tomberaient plus sous ceux de l'en-tête (§ 3.1). */
const GABARIT_SEMAINE = 'grid grid-cols-[3.5rem_repeat(7,1fr)]';
const GOUTTIERE_STABLE = '[scrollbar-gutter:stable]';

/* Un rendez-vous est un objet du domaine « agenda » : teinte, encre et bord
   du domaine, jamais le cyan ni le magenta d'accent. `hover:brightness-95`
   est le motif déjà posé sur une surface teintée (`Button variant="danger"`). */
const CLASSE_BLOC =
  `absolute z-10 rounded-sm border-l-[3px] border-domaine-agenda bg-domaine-agenda-tint text-domaine-agenda px-2 py-0.5 text-left overflow-hidden hover:brightness-95 ${ANNEAU_RENTRANT}`;
const CLASSE_JETON =
  `w-full text-left text-sm truncate border-l-[3px] border-domaine-agenda bg-domaine-agenda-tint text-domaine-agenda px-2 py-0.5 rounded-sm hover:brightness-95 ${ANNEAU_RENTRANT}`;
const CLASSE_PUCE =
  `w-full text-left text-sm truncate border-l-2 border-domaine-agenda bg-domaine-agenda-tint text-domaine-agenda px-1.5 py-0.5 rounded-sm hover:brightness-95 ${ANNEAU_RENTRANT}`;

/** L'horaire d'un bloc : « 09:00 à 10:30 », plus le lieu sur la même ligne
 *  quand il existe (maquette `agenda.html:78`). */
function horaireDuBloc(event: CalendarEvent): string {
  const plage = `${formatTime(event.start_datetime!)} à ${formatTime(event.end_datetime!)}`;
  return event.location ? `${plage} · ${event.location}` : plage;
}

/** Index de la colonne d'un jour dans une semaine qui commence au lundi
 *  (`getDay()` rend 0 pour dimanche). */
function colonneLundiDabord(date: Date): number {
  return (date.getDay() + 6) % 7;
}

export function CalendarView() {
  const { events, viewMode, selectedDate, showCancelled, searchQuery, setCurrentEvent } =
    useCalendarStore();

  // Filter events
  const filteredEvents = useMemo(() => {
    let filtered = events;

    if (!showCancelled) {
      filtered = filtered.filter((evt) => evt.status !== 'cancelled');
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (evt) =>
          evt.summary?.toLowerCase().includes(query) ||
          evt.description?.toLowerCase().includes(query) ||
          evt.location?.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [events, showCancelled, searchQuery]);

  if (viewMode === 'list') {
    return <ListView events={filteredEvents} onEventClick={setCurrentEvent} />;
  }

  if (viewMode === 'month') {
    return <MonthView events={filteredEvents} selectedDate={selectedDate} onEventClick={setCurrentEvent} />;
  }

  if (viewMode === 'week') {
    return <WeekView events={filteredEvents} selectedDate={selectedDate} onEventClick={setCurrentEvent} />;
  }

  if (viewMode === 'day') {
    return <DayView events={filteredEvents} selectedDate={selectedDate} onEventClick={setCurrentEvent} />;
  }

  return (
    <div className="flex items-center justify-center h-full">
      <p className="text-text-muted">Vue {viewMode} bientôt disponible</p>
    </div>
  );
}

// =============================================================================
// LIST VIEW
// =============================================================================

function ListView({
  events,
  onEventClick,
}: {
  events: CalendarEvent[];
  onEventClick: (eventId: string) => void;
}) {
  const groupedEvents = useMemo(() => {
    const groups: Record<string, CalendarEvent[]> = {};

    events.forEach((event) => {
      // B-379 : chaque jour couvert reçoit l'événement.
      for (const dateKey of clesDeJoursCouverts(event).length ? clesDeJoursCouverts(event) : ['unknown']) {
        if (!groups[dateKey]) {
          groups[dateKey] = [];
        }
        groups[dateKey].push(event);
      }
    });

    // Sort by date descending
    return Object.entries(groups).sort(([a], [b]) => b.localeCompare(a));
  }, [events]);

  return (
    <Carte as="section" aria-labelledby="agenda-periode" className="flex-1 min-h-0 overflow-y-auto">
      {groupedEvents.length === 0 ? (
        <EtatVide titre="Aucun événement" />
      ) : (
        groupedEvents.map(([date, evts]) => (
          <div key={date}>
            {/* Le titre de jour partage le `px-4` de ses lignes : les deux
                s'alignent sur la même marge gauche. L'écart entre groupes vient
                de son `pt-3`, plus d'un `space-y-*` concurrent. */}
            <h3 className="text-sm font-semibold text-accent px-4 pt-3 pb-1">
              {parseLocalDateKey(date).toLocaleDateString('fr-FR', {
                weekday: 'long',
                day: 'numeric',
                month: 'long',
              })}
            </h3>
            {evts.map((event) => (
              <button
                key={event.id}
                type="button"
                onClick={() => onEventClick(event.id)}
                className={`w-full text-left grid grid-cols-[2rem_1fr_auto] gap-3 items-center px-4 py-3 border-t border-border hover:bg-surface-2 ${ANNEAU_RENTRANT}`}
              >
                <span aria-hidden="true" className="h-8 w-8 rounded-sm bg-domaine-agenda-tint text-domaine-agenda" />
                <span className="min-w-0">
                  <span className="block font-semibold text-text truncate">{event.summary}</span>
                  {event.location && (
                    <span className="block text-sm text-text-muted truncate">{event.location}</span>
                  )}
                </span>
                <span className="text-text-muted">
                  {event.all_day ? 'Toute la journée' : formatTime(event.start_datetime!)}
                </span>
              </button>
            ))}
          </div>
        ))
      )}
    </Carte>
  );
}

// =============================================================================
// MONTH VIEW
// =============================================================================

function MonthView({
  events,
  selectedDate,
  onEventClick,
}: {
  events: CalendarEvent[];
  selectedDate: Date;
  onEventClick: (eventId: string) => void;
}) {
  const { days, monthStart } = useMemo(() => {
    const year = selectedDate.getFullYear();
    const month = selectedDate.getMonth();
    const monthStart = new Date(year, month, 1);
    const monthEnd = new Date(year, month + 1, 0);
    const startDay = colonneLundiDabord(monthStart); // 0 = lundi (B-247)
    const daysInMonth = monthEnd.getDate();

    // Build calendar grid (6 weeks max)
    const days: Date[] = [];

    // Previous month days
    const prevMonthEnd = new Date(year, month, 0);
    const prevMonthDays = prevMonthEnd.getDate();
    for (let i = startDay - 1; i >= 0; i--) {
      days.push(new Date(year, month - 1, prevMonthDays - i));
    }

    // Current month days
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(new Date(year, month, i));
    }

    // Next month days (fill to 42 cells = 6 weeks)
    const remainingCells = 42 - days.length;
    for (let i = 1; i <= remainingCells; i++) {
      days.push(new Date(year, month + 1, i));
    }

    return { days, monthStart };
  }, [selectedDate]);

  // Map events to dates
  const eventsByDate = useMemo(() => {
    const map: Record<string, CalendarEvent[]> = {};

    events.forEach((event) => {
      for (const dateKey of clesDeJoursCouverts(event)) {
        if (!map[dateKey]) {
          map[dateKey] = [];
        }
        map[dateKey].push(event);
      }
    });
    // B-577 : l'ordre reçu de l'API n'est pas celui des heures du jour.
    for (const dateKey of Object.keys(map)) map[dateKey] = trierLesEvenementsDuJour(map[dateKey]);

    return map;
  }, [events]);

  const weekDays = ETIQUETTES_JOURS;
  const currentMonth = monthStart.getMonth();
  const today = new Date();
  const todayStr = localDateKey(today);

  return (
    // C'est la CARTE qui défile, et la grille qui la remplit : six rangées de
    // 5,5 rem valent 33 rem, que la zone de contenu clippe en overflow-hidden.
    // Sans cela, sur une fenêtre courte, la dernière semaine devenait invisible
    // ET inatteignable. `min-h-full` + `1fr` évitent la bande vide sur une
    // fenêtre haute.
    <Carte as="section" aria-labelledby="agenda-periode" className="flex-1 min-h-0 overflow-y-auto">
      <div className="grid grid-cols-7 min-h-full grid-rows-[auto_repeat(6,minmax(5.5rem,1fr))]">
        {/* Sept en-têtes, puis quarante-deux cases : 49 enfants directs, sans
            conteneur intermédiaire (un `display:contents` casserait le décompte
            et le `nth-child(7n+1)` des bordures). */}
        {weekDays.map((day) => (
          <div
            key={day}
            className="sticky top-0 z-10 bg-surface px-2 py-2 text-left text-sm text-text-muted border-b border-border"
          >
            {day}
          </div>
        ))}

        {days.map((day, index) => {
          const dateKey = localDateKey(day);
          const dayEvents = eventsByDate[dateKey] || [];
          const isCurrentMonth = day.getMonth() === currentMonth;
          const isToday = dateKey === todayStr;

          return (
            <div
              key={index}
              className="grid gap-1 content-start p-1.5 border-t border-l border-border text-sm [&:nth-child(7n+1)]:border-l-0"
            >
              {/* B-414 : hors mois, l'encre atténuée reste lisible (AA), sans opacité sur la cellule. */}
              <div
                className={`font-medium ${
                  isToday
                    ? 'h-[1.4rem] w-[1.4rem] rounded-full bg-accent-fill text-accent-ink grid place-items-center'
                    : isCurrentMonth ? 'text-text' : 'text-text-muted'
                }`}
              >
                {day.getDate()}
              </div>
              {dayEvents.slice(0, 3).map((event) => (
                <button
                  key={event.id}
                  type="button"
                  onClick={() => onEventClick(event.id)}
                  className={CLASSE_PUCE}
                >
                  {event.summary}
                </button>
              ))}
              {dayEvents.length > 3 && (
                <div className="text-xs text-text-muted px-1.5">
                  +{dayEvents.length - 3} autre{dayEvents.length - 3 > 1 ? 's' : ''}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Carte>
  );
}

// =============================================================================
// WEEK VIEW
// =============================================================================

// Fenêtre horaire par défaut (élargie dynamiquement par getVisibleHourRange
// pour qu'aucun RDV tôt/tard ne disparaisse de la grille).
const WEEK_START_HOUR = 8;
const WEEK_END_HOUR = 20;
const HOUR_HEIGHT_PX = 60;

function WeekView({
  events,
  selectedDate,
  onEventClick,
}: {
  events: CalendarEvent[];
  selectedDate: Date;
  onEventClick: (eventId: string) => void;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const weekDates = useMemo(() => getWeekDates(selectedDate), [selectedDate]);

  // Map events par jour de la semaine
  const { allDayByDate, timedByDate } = useMemo(() => {
    const allDayByDate: Record<string, CalendarEvent[]> = {};
    const timedByDate: Record<string, CalendarEvent[]> = {};

    // B-144 : les bornes se comparent en CLÉS CIVILES, jamais en objets Date.
    // `new Date('2026-09-06')` vaut minuit UTC (spécification ECMAScript)
    // tandis que `new Date(2026, 8, 6)` vaut minuit LOCAL : à Paris le dernier
    // jour de la semaine dépassait la borne haute et sa colonne se rendait
    // vide (en UTC- c'était le premier jour). Deux chaînes « YYYY-MM-DD » se
    // comparent dans l'ordre chronologique, sans fuseau.
    const debutSemaine = localDateKey(weekDates[0]);
    const finSemaine = localDateKey(weekDates[6]);

    events.forEach((event) => {
      for (const dateKey of clesDeJoursCouverts(event)) {
      // Vérifier si le jour est dans la semaine visible
      if (dateKey < debutSemaine || dateKey > finSemaine) {
        continue;
      }

      if (event.all_day) {
        if (!allDayByDate[dateKey]) allDayByDate[dateKey] = [];
        allDayByDate[dateKey].push(event);
      } else {
        if (!timedByDate[dateKey]) timedByDate[dateKey] = [];
        timedByDate[dateKey].push(event);
      }
      }
    });

    return { allDayByDate, timedByDate };
  }, [events, weekDates]);

  // Plage horaire dynamique : élargit la fenêtre par défaut pour englober
  // les événements tôt/tard de la semaine (sinon ils disparaissent).
  const timedEventsThisWeek = useMemo(
    () => Object.values(timedByDate).flat(),
    [timedByDate]
  );
  const { startHour: weekStartHour, endHour: weekEndHour } = useMemo(
    () => getVisibleHourRange(timedEventsThisWeek, WEEK_START_HOUR, WEEK_END_HOUR),
    [timedEventsThisWeek]
  );
  const weekHours = useMemo(
    () => Array.from({ length: weekEndHour - weekStartHour }, (_, i) => weekStartHour + i),
    [weekStartHour, weekEndHour]
  );
  const layoutByEventId = useMemo(() => {
    const layoutMap: Record<string, ReturnType<typeof getTimedEventLayout>> = {};

    Object.entries(timedByDate).forEach(([dateKey, dayEvents]) => {
      layoutMap[dateKey] = getTimedEventLayout(dayEvents, weekStartHour, weekEndHour, HOUR_HEIGHT_PX);
    });

    return layoutMap;
  }, [timedByDate, weekStartHour, weekEndHour]);

  // Scroll vers l'heure courante au montage (utilise la plage dynamique :
  // se réajuste si la grille s'élargit pour un événement tôt/tard).
  useEffect(() => {
    if (scrollRef.current) {
      const hour = new Date().getHours();
      const scrollTo = Math.max(0, (hour - weekStartHour - 1)) * HOUR_HEIGHT_PX;
      scrollRef.current.scrollTop = scrollTo;
    }
  }, [selectedDate, weekStartHour]);

  const today = new Date();
  const todayStr = localDateKey(today);
  const now = new Date();
  const currentHour = now.getHours();
  const currentMinute = now.getMinutes();

  // La semaine contient-elle aujourd'hui ?
  const weekContainsToday = weekDates.some(
    (d) => localDateKey(d) === todayStr
  );

  // Position de la ligne rouge (en px depuis le haut de la grille)
  const nowLineTop =
    weekContainsToday && currentHour >= weekStartHour && currentHour < weekEndHour
      ? (currentHour - weekStartHour) * HOUR_HEIGHT_PX + (currentMinute / 60) * HOUR_HEIGHT_PX
      : null;

  const hasAnyAllDay = Object.keys(allDayByDate).length > 0;

  const weekDayLabels = ETIQUETTES_JOURS;

  return (
    // L'`overflow-hidden` vient de la maquette (`.semaine{overflow:hidden}`) :
    // il ne tue pas le défilement interne (la zone parente clippe déjà et la
    // piste défile dessous), il donne aux coins arrondis de quoi clipper le
    // fond teinté de l'en-tête et les traits des sept colonnes.
    <Carte
      as="section"
      aria-labelledby="agenda-periode"
      className="flex-1 min-h-0 flex flex-col overflow-hidden"
    >
      {/* En-tête colonnes */}
      <div className={`${GABARIT_SEMAINE} ${GOUTTIERE_STABLE} shrink-0 overflow-hidden border-b border-border`}>
        {/* Colonne heures (gutter) : aucune bordure, elle n'est pas un jour */}
        <div />
        {/* Colonnes jours */}
        {weekDates.map((date, i) => {
          const dateStr = localDateKey(date);
          const isToday = dateStr === todayStr;
          return (
            <div
              key={i}
              className={`px-2 py-2 text-left border-l border-border ${
                isToday ? 'bg-accent-tint' : ''
              }`}
            >
              <div className="text-sm text-text-muted">{weekDayLabels[i]}</div>
              <div
                className={`text-base font-semibold tabular-nums ${
                  isToday ? 'text-accent' : 'text-text'
                }`}
              >
                {date.getDate()}
              </div>
            </div>
          );
        })}
      </div>

      {/* Bannière événements journée entière : MÊME gabarit que l'en-tête et
          que la piste, sans quoi les jetons tombent sous le mauvais jour. */}
      {hasAnyAllDay && (
        <div className={`${GABARIT_SEMAINE} ${GOUTTIERE_STABLE} shrink-0 overflow-hidden border-b border-border`}>
          {/* 12 px comme les heures de la même gouttière : deux échelles dans
              une colonne de 3,5 rem, ce sont deux rythmes dans la même bande. */}
          <div className="py-2 text-left text-xs text-text-muted">Journée</div>
          {weekDates.map((date, i) => {
            const dateStr = localDateKey(date);
            const isToday = dateStr === todayStr;
            const dayAllDay = allDayByDate[dateStr] || [];
            return (
              <div
                key={i}
                className={`border-l border-border p-1 min-h-[2rem] ${isToday ? 'bg-surface-2' : ''}`}
              >
                {dayAllDay.map((event) => (
                  <button
                    key={event.id}
                    type="button"
                    onClick={() => onEventClick(event.id)}
                    className={`${CLASSE_JETON} mb-0.5`}
                  >
                    {event.summary}
                  </button>
                ))}
              </div>
            );
          })}
        </div>
      )}

      {/* Grille horaire scrollable */}
      <div ref={scrollRef} className={`flex-1 overflow-y-auto overflow-x-hidden ${GOUTTIERE_STABLE}`}>
        <div className={GABARIT_SEMAINE} style={{ height: weekHours.length * HOUR_HEIGHT_PX }}>
          {/* Colonne heures */}
          <div className="relative">
            {weekHours.map((hour) => (
              <div
                key={hour}
                className="absolute w-full text-right pr-3"
                style={{ top: (hour - weekStartHour) * HOUR_HEIGHT_PX - 8 }}
              >
                <span className="text-xs tabular-nums text-text-muted">
                  {String(hour).padStart(2, '0')}:00
                </span>
              </div>
            ))}
          </div>

          {/* Les sept colonnes de jour en UN SEUL bloc : c'est lui qui porte
              `relative`, donc les lignes d'heure et le repère de l'heure
              s'étendent sur les sept jours et JAMAIS sur la gouttière. */}
          <div className="col-start-2 col-span-7 relative grid grid-cols-7">
            {/* Lignes horizontales des heures. `z-[1]` : le fond opaque
                `bg-surface-2` de la colonne du jour les effacerait sinon. */}
            {weekHours.map((hour) => (
              <div
                key={hour}
                className="absolute left-0 right-0 z-[1] border-t border-border"
                style={{ top: (hour - weekStartHour) * HOUR_HEIGHT_PX }}
              />
            ))}

            {/* Ligne rouge de l'heure actuelle. Ce rouge N'EST PAS un état
                d'erreur : c'est le repère temporel que tous les agendas
                emploient, et le lire comme une alerte serait un contresens.
                Il échappe donc volontairement aux tokens sémantiques, et le
                test des couleurs le nomme comme exception. */}
            {nowLineTop !== null && (
              <div
                role="img"
                aria-label={`Il est ${String(currentHour).padStart(2, '0')}:${String(currentMinute).padStart(2, '0')}`}
                className="absolute left-0 right-0 z-20 pointer-events-none"
                style={{ top: nowLineTop }}
              >
                <div className="relative flex items-center">
                  <div className="w-2 h-2 rounded-full bg-instant -ml-1" />
                  <div className="flex-1 h-px bg-instant" />
                </div>
              </div>
            )}

            {/* Colonnes par jour */}
            {weekDates.map((date, colIndex) => {
              const dateStr = localDateKey(date);
              const isToday = dateStr === todayStr;
              const dayEvents = timedByDate[dateStr] || [];
              const dayLayoutByEventId = layoutByEventId[dateStr] || {};

              return (
                <div
                  key={colIndex}
                  className={`relative border-l border-border ${isToday ? 'bg-surface-2' : ''}`}
                >
                  {dayEvents.map((event) => {
                    const layout = dayLayoutByEventId[event.id];
                    if (!layout) return null;

                    return (
                      <button
                        key={event.id}
                        type="button"
                        onClick={() => onEventClick(event.id)}
                        className={CLASSE_BLOC}
                        style={{
                          top: layout.top,
                          height: Math.max(layout.height, 20),
                          left: `${layout.leftPercent}%`,
                          width: `${layout.widthPercent}%`,
                        }}
                      >
                        <div className="text-sm font-semibold truncate">{event.summary}</div>
                        {/* `truncate` porteur : sans lui « 09:00 à 10:30 · sur
                            place » replierait sur trois lignes dans une colonne
                            de 105 px. Le DOM garde la chaîne entière. */}
                        <div className="text-sm truncate">{horaireDuBloc(event)}</div>
                      </button>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </Carte>
  );
}

// =============================================================================
// DAY VIEW
// =============================================================================

// Fenêtre horaire par défaut de la vue Jour (élargie dynamiquement).
const DAY_START_HOUR = 6;
const DAY_END_HOUR = 22;
const DAY_SLOT_HEIGHT_PX = 80; // 30min = 40px, 1h = 80px

function DayView({
  events,
  selectedDate,
  onEventClick,
}: {
  events: CalendarEvent[];
  selectedDate: Date;
  onEventClick: (eventId: string) => void;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const dateStr = useMemo(() => {
    return localDateKey(selectedDate);
  }, [selectedDate]);

  // Séparer événements journée entière et horaires
  const { allDayEvents, timedEvents } = useMemo(() => {
    const allDayEvents: CalendarEvent[] = [];
    const timedEvents: CalendarEvent[] = [];

    events.forEach((event) => {
      if (!clesDeJoursCouverts(event).includes(dateStr)) return;

      if (event.all_day) {
        allDayEvents.push(event);
      } else {
        timedEvents.push(event);
      }
    });

    return { allDayEvents, timedEvents };
  }, [events, dateStr]);

  // Plage horaire dynamique : élargit la fenêtre par défaut pour englober
  // les événements tôt/tard du jour (sinon ils disparaissent).
  const { startHour: dayStartHour, endHour: dayEndHour } = useMemo(
    () => getVisibleHourRange(timedEvents, DAY_START_HOUR, DAY_END_HOUR),
    [timedEvents]
  );
  const dayHours = useMemo(
    () => Array.from({ length: dayEndHour - dayStartHour }, (_, i) => dayStartHour + i),
    [dayStartHour, dayEndHour]
  );
  const layoutByEventId = useMemo(
    () => getTimedEventLayout(timedEvents, dayStartHour, dayEndHour, DAY_SLOT_HEIGHT_PX),
    [timedEvents, dayStartHour, dayEndHour]
  );

  // Scroll vers l'heure courante au montage (plage dynamique : se réajuste
  // si la grille s'élargit pour un événement tôt/tard).
  useEffect(() => {
    if (scrollRef.current) {
      const hour = new Date().getHours();
      const scrollTo = Math.max(0, (hour - dayStartHour - 1)) * DAY_SLOT_HEIGHT_PX;
      scrollRef.current.scrollTop = scrollTo;
    }
  }, [selectedDate, dayStartHour]);

  const today = new Date();
  const todayStr = localDateKey(today);
  const isToday = dateStr === todayStr;
  const now = new Date();
  const currentHour = now.getHours();
  const currentMinute = now.getMinutes();

  // Position de la ligne rouge
  const nowLineTop =
    isToday && currentHour >= dayStartHour && currentHour < dayEndHour
      ? (currentHour - dayStartHour) * DAY_SLOT_HEIGHT_PX + (currentMinute / 60) * DAY_SLOT_HEIGHT_PX
      : null;

  const dayLabel = selectedDate.toLocaleDateString('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });

  return (
    <Carte
      as="section"
      aria-labelledby="agenda-periode"
      className="flex-1 min-h-0 flex flex-col overflow-hidden"
    >
      {/* En-tête jour. Le `h3#agenda-periode` du panneau porte déjà la date
          civile complète : celui-ci reste le titre de la grille Jour, et c'est
          lui — et lui seul — qui porte le suffixe « (aujourd'hui) ». */}
      <div className="px-6 py-3 border-b border-border shrink-0">
        <h3 className={`text-base font-semibold ${isToday ? 'text-accent' : 'text-text'}`}>
          {dayLabel}
          {isToday && (
            <span className="ml-2 text-xs font-normal text-accent">(aujourd'hui)</span>
          )}
        </h3>
      </div>

      {/* Bannière événements journée entière */}
      {allDayEvents.length > 0 && (
        <div className="px-6 py-2 border-b border-border shrink-0">
          <div className="text-xs text-text-muted mb-1">Toute la journée</div>
          <div className="space-y-1">
            {allDayEvents.map((event) => (
              <button
                key={event.id}
                type="button"
                onClick={() => onEventClick(event.id)}
                className={CLASSE_JETON}
              >
                {event.summary}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Grille horaire scrollable */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="flex relative px-2" style={{ height: dayHours.length * DAY_SLOT_HEIGHT_PX }}>
          {/* Colonne heures : une seule colonne à aligner, le gabarit `flex` et
              la gouttière `w-16` restent ceux d'aujourd'hui. */}
          <div className="w-16 shrink-0 relative">
            {dayHours.map((hour) => (
              <div
                key={hour}
                className="absolute w-full text-right pr-3"
                style={{ top: (hour - dayStartHour) * DAY_SLOT_HEIGHT_PX - 8 }}
              >
                <span className="text-xs tabular-nums text-text-muted">
                  {String(hour).padStart(2, '0')}:00
                </span>
              </div>
            ))}
            {/* Demi-heures */}
            {dayHours.map((hour) => (
              <div
                key={`half-${hour}`}
                className="absolute w-full text-right pr-3"
                style={{ top: (hour - dayStartHour) * DAY_SLOT_HEIGHT_PX + DAY_SLOT_HEIGHT_PX / 2 - 8 }}
              >
                <span className="text-xs tabular-nums text-text-muted">
                  {String(hour).padStart(2, '0')}:30
                </span>
              </div>
            ))}
          </div>

          {/* Zone événements. Aucun fond de colonne ici (la vue entière EST le
              jour), donc rien à faire remonter au-dessus : pas de `z-[1]`. */}
          <div className="flex-1 relative border-l border-border">
            {/* Lignes heures */}
            {dayHours.map((hour) => (
              <div
                key={hour}
                className="absolute left-0 right-0 border-t border-border"
                style={{ top: (hour - dayStartHour) * DAY_SLOT_HEIGHT_PX }}
              />
            ))}
            {/* Lignes demi-heures : repère secondaire, il reste en retrait */}
            {dayHours.map((hour) => (
              <div
                key={`half-line-${hour}`}
                className="absolute left-0 right-0 border-t border-border/10"
                style={{ top: (hour - dayStartHour) * DAY_SLOT_HEIGHT_PX + DAY_SLOT_HEIGHT_PX / 2 }}
              />
            ))}

            {/* Ligne rouge de l'heure actuelle. Ce rouge N'EST PAS un état
                d'erreur : c'est le repère temporel que tous les agendas
                emploient, et le lire comme une alerte serait un contresens.
                Il échappe donc volontairement aux tokens sémantiques, et le
                test des couleurs le nomme comme exception. */}
            {nowLineTop !== null && (
              <div
                className="absolute left-0 right-0 z-20 pointer-events-none"
                style={{ top: nowLineTop }}
              >
                <div className="relative flex items-center">
                  <div className="w-2 h-2 rounded-full bg-instant -ml-1" />
                  <div className="flex-1 h-px bg-instant" />
                  <span className="text-xs font-medium text-instant ml-2">
                    {String(currentHour).padStart(2, '0')}:{String(currentMinute).padStart(2, '0')}
                  </span>
                </div>
              </div>
            )}

            {/* Événements */}
            {timedEvents.map((event) => {
              const layout = layoutByEventId[event.id];
              if (!layout) return null;

              return (
                <button
                  key={event.id}
                  type="button"
                  onClick={() => onEventClick(event.id)}
                  className={CLASSE_BLOC}
                  style={{
                    top: layout.top,
                    height: Math.max(layout.height, 24),
                    left: `${layout.leftPercent}%`,
                    width: `${layout.widthPercent}%`,
                  }}
                >
                  <div className="text-sm font-semibold truncate">{event.summary}</div>
                  {/* Le lieu tient sur la ligne d'horaire, sans garde de
                      hauteur : un bloc court n'a plus à taire où il se passe. */}
                  <div className="text-sm truncate">{horaireDuBloc(event)}</div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </Carte>
  );
}

// =============================================================================
// HELPERS
// =============================================================================

function formatTime(datetime: string): string {
  const date = new Date(datetime);
  return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}

/**
 * Renvoie les 7 dates de la semaine (lundi-dimanche) contenant la date donnée.
 */
function getWeekDates(date: Date): Date[] {
  const d = new Date(date);
  const dayOfWeek = d.getDay(); // 0 = dimanche
  // Décalage pour commencer au lundi (ISO)
  const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
  const monday = new Date(d.getFullYear(), d.getMonth(), d.getDate() + mondayOffset);

  const dates: Date[] = [];
  for (let i = 0; i < 7; i++) {
    dates.push(new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + i));
  }
  return dates;
}


