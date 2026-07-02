/**
 * THÉRÈSE v2 - Calendar View
 *
 * Vue calendrier (mois/semaine/jour/liste).
 * Phase 2 - Calendar
 */

import { useMemo, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { useCalendarStore } from '../../stores/calendarStore';
import type { CalendarEvent } from '../../services/api';
import { getVisibleHourRange } from './calendarHours';
import { getTimedEventLayout } from './calendarEventLayout';

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
      const dateKey = event.start_date || event.start_datetime?.split('T')[0] || 'unknown';
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(event);
    });

    // Sort by date descending
    return Object.entries(groups).sort(([a], [b]) => b.localeCompare(a));
  }, [events]);

  return (
    <div className="h-full overflow-y-auto px-6 py-4">
      {groupedEvents.length === 0 ? (
        <div className="flex items-center justify-center h-full">
          <p className="text-text-muted">Aucun événement</p>
        </div>
      ) : (
        <div className="space-y-6">
          {groupedEvents.map(([date, evts]) => (
            <div key={date}>
              <h3 className="text-sm font-medium text-accent-cyan mb-3">
                {new Date(date).toLocaleDateString('fr-FR', {
                  weekday: 'long',
                  day: 'numeric',
                  month: 'long',
                })}
              </h3>
              <div className="space-y-2">
                {evts.map((event) => (
                  <motion.button
                    key={event.id}
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                    onClick={() => onEventClick(event.id)}
                    className="w-full text-left p-4 bg-surface-elevated/60 hover:bg-surface-elevated rounded-lg border border-border/30 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-text truncate">
                          {event.summary}
                        </h4>
                        {event.location && (
                          <p className="text-xs text-text-muted mt-1">{event.location}</p>
                        )}
                      </div>
                      <div className="text-xs text-text-muted shrink-0">
                        {event.all_day
                          ? 'Toute la journée'
                          : formatTime(event.start_datetime!)}
                      </div>
                    </div>
                  </motion.button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
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
    const startDay = monthStart.getDay(); // 0 = Sunday
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
      const dateKey = event.start_date || event.start_datetime?.split('T')[0] || '';
      if (dateKey) {
        if (!map[dateKey]) {
          map[dateKey] = [];
        }
        map[dateKey].push(event);
      }
    });

    return map;
  }, [events]);

  const weekDays = ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'];
  const currentMonth = monthStart.getMonth();
  const today = new Date();
  const todayStr = today.toISOString().split('T')[0];

  return (
    <div className="h-full flex flex-col p-6">
      {/* Week days header */}
      <div className="grid grid-cols-7 gap-2 mb-2">
        {weekDays.map((day) => (
          <div key={day} className="text-center text-sm font-medium text-text-muted py-2">
            {day}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="flex-1 grid grid-cols-7 gap-2 overflow-hidden">
        {days.map((day, index) => {
          const dateKey = day.toISOString().split('T')[0];
          const dayEvents = eventsByDate[dateKey] || [];
          const isCurrentMonth = day.getMonth() === currentMonth;
          const isToday = dateKey === todayStr;

          return (
            <div
              key={index}
              className={`border border-border/30 rounded-lg p-2 overflow-hidden ${
                isCurrentMonth ? 'bg-surface-elevated/40' : 'bg-background/20 opacity-50'
              } ${isToday ? 'ring-2 ring-accent-cyan' : ''}`}
            >
              <div className="text-sm font-medium text-text mb-1">{day.getDate()}</div>
              <div className="space-y-1">
                {dayEvents.slice(0, 3).map((event) => (
                  <button
                    key={event.id}
                    onClick={() => onEventClick(event.id)}
                    className="w-full text-left px-2 py-1 bg-accent-cyan/10 hover:bg-accent-cyan/20 rounded text-xs text-text truncate transition-colors"
                  >
                    {event.summary}
                  </button>
                ))}
                {dayEvents.length > 3 && (
                  <div className="text-xs text-text-muted px-2">
                    +{dayEvents.length - 3} autre{dayEvents.length - 3 > 1 ? 's' : ''}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
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

    events.forEach((event) => {
      const dateKey = event.start_date || event.start_datetime?.split('T')[0] || '';
      if (!dateKey) return;

      // Vérifier si l'événement est dans la semaine visible
      const eventDate = new Date(dateKey);
      const weekStart = weekDates[0];
      const weekEnd = weekDates[6];
      if (eventDate < new Date(weekStart.getFullYear(), weekStart.getMonth(), weekStart.getDate()) ||
          eventDate > new Date(weekEnd.getFullYear(), weekEnd.getMonth(), weekEnd.getDate())) {
        return;
      }

      if (event.all_day) {
        if (!allDayByDate[dateKey]) allDayByDate[dateKey] = [];
        allDayByDate[dateKey].push(event);
      } else {
        if (!timedByDate[dateKey]) timedByDate[dateKey] = [];
        timedByDate[dateKey].push(event);
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
  const todayStr = today.toISOString().split('T')[0];
  const now = new Date();
  const currentHour = now.getHours();
  const currentMinute = now.getMinutes();

  // La semaine contient-elle aujourd'hui ?
  const weekContainsToday = weekDates.some(
    (d) => d.toISOString().split('T')[0] === todayStr
  );

  // Position de la ligne rouge (en px depuis le haut de la grille)
  const nowLineTop =
    weekContainsToday && currentHour >= weekStartHour && currentHour < weekEndHour
      ? (currentHour - weekStartHour) * HOUR_HEIGHT_PX + (currentMinute / 60) * HOUR_HEIGHT_PX
      : null;

  const hasAnyAllDay = Object.keys(allDayByDate).length > 0;

  const weekDayLabels = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];

  return (
    <motion.div
      className="h-full flex flex-col"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
    >
      {/* En-tête colonnes */}
      <div className="flex border-b border-border/30 shrink-0">
        {/* Colonne heures (gutter) */}
        <div className="w-16 shrink-0" />
        {/* Colonnes jours */}
        {weekDates.map((date, i) => {
          const dateStr = date.toISOString().split('T')[0];
          const isToday = dateStr === todayStr;
          return (
            <div
              key={i}
              className={`flex-1 text-center py-3 border-l border-border/20 ${
                isToday ? 'bg-accent-cyan/5' : ''
              }`}
            >
              <div className="text-xs text-text-muted">{weekDayLabels[i]}</div>
              <div
                className={`text-lg font-semibold mt-0.5 ${
                  isToday ? 'text-accent-cyan' : 'text-text'
                }`}
              >
                {date.getDate()}
              </div>
            </div>
          );
        })}
      </div>

      {/* Bannière événements journée entière */}
      {hasAnyAllDay && (
        <div className="flex border-b border-border/30 shrink-0">
          <div className="w-16 shrink-0 flex items-center justify-center">
            <span className="text-xs text-text-muted">Journée</span>
          </div>
          {weekDates.map((date, i) => {
            const dateStr = date.toISOString().split('T')[0];
            const dayAllDay = allDayByDate[dateStr] || [];
            return (
              <div
                key={i}
                className="flex-1 border-l border-border/20 p-1 min-h-[32px]"
              >
                {dayAllDay.map((event) => (
                  <button
                    key={event.id}
                    onClick={() => onEventClick(event.id)}
                    className="w-full text-left px-2 py-0.5 bg-accent-magenta/20 hover:bg-accent-magenta/30 rounded text-xs text-text truncate transition-colors mb-0.5"
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
      <div ref={scrollRef} className="flex-1 overflow-y-auto overflow-x-hidden">
        <div className="flex relative" style={{ height: weekHours.length * HOUR_HEIGHT_PX }}>
          {/* Colonne heures */}
          <div className="w-16 shrink-0 relative">
            {weekHours.map((hour) => (
              <div
                key={hour}
                className="absolute w-full text-right pr-3"
                style={{ top: (hour - weekStartHour) * HOUR_HEIGHT_PX - 8 }}
              >
                <span className="text-xs text-text-muted">
                  {String(hour).padStart(2, '0')}:00
                </span>
              </div>
            ))}
          </div>

          {/* Colonnes jours */}
          <div className="flex-1 flex relative">
            {/* Lignes horizontales des heures */}
            {weekHours.map((hour) => (
              <div
                key={hour}
                className="absolute left-0 right-0 border-t border-border/15"
                style={{ top: (hour - weekStartHour) * HOUR_HEIGHT_PX }}
              />
            ))}

            {/* Ligne rouge heure actuelle */}
            {nowLineTop !== null && (
              <div
                className="absolute left-0 right-0 z-20 pointer-events-none"
                style={{ top: nowLineTop }}
              >
                <div className="relative flex items-center">
                  <div className="w-2 h-2 rounded-full bg-red-500 -ml-1" />
                  <div className="flex-1 h-px bg-red-500" />
                </div>
              </div>
            )}

            {/* Colonnes par jour */}
            {weekDates.map((date, colIndex) => {
              const dateStr = date.toISOString().split('T')[0];
              const isToday = dateStr === todayStr;
              const dayEvents = timedByDate[dateStr] || [];
              const dayLayoutByEventId = layoutByEventId[dateStr] || {};

              return (
                <div
                  key={colIndex}
                  className={`flex-1 relative border-l border-border/20 ${
                    isToday ? 'bg-accent-cyan/5' : ''
                  }`}
                >
                  {dayEvents.map((event) => {
                    const layout = dayLayoutByEventId[event.id];
                    if (!layout) return null;

                    return (
                      <motion.button
                        key={event.id}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        onClick={() => onEventClick(event.id)}
                        className="absolute bg-accent-cyan/20 hover:bg-accent-cyan/30 border-l-2 border-accent-cyan rounded-r px-2 py-1 text-left overflow-hidden transition-colors z-10"
                        style={{
                          top: layout.top,
                          height: Math.max(layout.height, 20),
                          left: `${layout.leftPercent}%`,
                          width: `${layout.widthPercent}%`,
                        }}
                      >
                        <div className="text-xs font-medium text-text truncate">
                          {event.summary}
                        </div>
                        <div className="text-xs text-text-muted truncate">
                          {formatTime(event.start_datetime!)} - {formatTime(event.end_datetime!)}
                        </div>
                      </motion.button>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </motion.div>
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
    return selectedDate.toISOString().split('T')[0];
  }, [selectedDate]);

  // Séparer événements journée entière et horaires
  const { allDayEvents, timedEvents } = useMemo(() => {
    const allDayEvents: CalendarEvent[] = [];
    const timedEvents: CalendarEvent[] = [];

    events.forEach((event) => {
      const eventDate = event.start_date || event.start_datetime?.split('T')[0] || '';
      if (eventDate !== dateStr) return;

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
  const todayStr = today.toISOString().split('T')[0];
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
    <motion.div
      className="h-full flex flex-col"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
    >
      {/* En-tête jour */}
      <div className="px-6 py-3 border-b border-border/30 shrink-0">
        <h3 className={`text-base font-semibold capitalize ${isToday ? 'text-accent-cyan' : 'text-text'}`}>
          {dayLabel}
          {isToday && (
            <span className="ml-2 text-xs font-normal text-accent-cyan/70">(aujourd'hui)</span>
          )}
        </h3>
      </div>

      {/* Bannière événements journée entière */}
      {allDayEvents.length > 0 && (
        <div className="px-6 py-2 border-b border-border/30 shrink-0">
          <div className="text-xs text-text-muted mb-1">Toute la journée</div>
          <div className="space-y-1">
            {allDayEvents.map((event) => (
              <button
                key={event.id}
                onClick={() => onEventClick(event.id)}
                className="w-full text-left px-3 py-1.5 bg-accent-magenta/20 hover:bg-accent-magenta/30 rounded text-sm text-text transition-colors"
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
          {/* Colonne heures */}
          <div className="w-16 shrink-0 relative">
            {dayHours.map((hour) => (
              <div
                key={hour}
                className="absolute w-full text-right pr-3"
                style={{ top: (hour - dayStartHour) * DAY_SLOT_HEIGHT_PX - 8 }}
              >
                <span className="text-xs text-text-muted">
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
                <span className="text-xs text-text-muted/50">
                  {String(hour).padStart(2, '0')}:30
                </span>
              </div>
            ))}
          </div>

          {/* Zone événements */}
          <div className="flex-1 relative">
            {/* Lignes heures */}
            {dayHours.map((hour) => (
              <div
                key={hour}
                className="absolute left-0 right-0 border-t border-border/20"
                style={{ top: (hour - dayStartHour) * DAY_SLOT_HEIGHT_PX }}
              />
            ))}
            {/* Lignes demi-heures */}
            {dayHours.map((hour) => (
              <div
                key={`half-line-${hour}`}
                className="absolute left-0 right-0 border-t border-border/10"
                style={{ top: (hour - dayStartHour) * DAY_SLOT_HEIGHT_PX + DAY_SLOT_HEIGHT_PX / 2 }}
              />
            ))}

            {/* Ligne rouge heure actuelle */}
            {nowLineTop !== null && (
              <div
                className="absolute left-0 right-0 z-20 pointer-events-none"
                style={{ top: nowLineTop }}
              >
                <div className="relative flex items-center">
                  <div className="w-2 h-2 rounded-full bg-red-500 -ml-1" />
                  <div className="flex-1 h-px bg-red-500" />
                  <span className="text-xs font-medium text-red-400 ml-2">
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
                <motion.button
                  key={event.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  onClick={() => onEventClick(event.id)}
                  className="absolute bg-accent-cyan/20 hover:bg-accent-cyan/30 border-l-2 border-accent-cyan rounded-r px-3 py-2 text-left overflow-hidden transition-colors z-10"
                  style={{
                    top: layout.top,
                    height: Math.max(layout.height, 24),
                    left: `${layout.leftPercent}%`,
                    width: `${layout.widthPercent}%`,
                  }}
                >
                  <div className="text-sm font-medium text-text truncate">
                    {event.summary}
                  </div>
                  <div className="text-xs text-text-muted">
                    {formatTime(event.start_datetime!)} - {formatTime(event.end_datetime!)}
                  </div>
                  {event.location && layout.height > 50 && (
                    <div className="text-xs text-text-muted/70 mt-0.5 truncate">
                      {event.location}
                    </div>
                  )}
                </motion.button>
              );
            })}
          </div>
        </div>
      </div>
    </motion.div>
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


