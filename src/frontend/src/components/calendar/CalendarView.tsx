/**
 * THÉRÈSE v2 - Calendar View
 *
 * Vue calendrier (mois/semaine/jour/liste).
 * Phase 2 - Calendar
 */

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useCalendarStore } from '../../stores/calendarStore';
import type { CalendarEvent } from '../../services/api';

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
// HELPERS
// =============================================================================

function formatTime(datetime: string): string {
  const date = new Date(datetime);
  return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}
