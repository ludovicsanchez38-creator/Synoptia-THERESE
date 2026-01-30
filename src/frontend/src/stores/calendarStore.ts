/**
 * THÉRÈSE v2 - Calendar Store
 *
 * Zustand store pour la gestion du calendrier.
 * Phase 2 - Calendar
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Calendar, CalendarEvent } from '../services/api';

interface CalendarStore {
  // Calendars
  calendars: Calendar[];
  currentCalendarId: string | null;
  setCalendars: (calendars: Calendar[]) => void;
  setCurrentCalendar: (calendarId: string | null) => void;
  addCalendar: (calendar: Calendar) => void;
  updateCalendar: (calendarId: string, updates: Partial<Calendar>) => void;
  removeCalendar: (calendarId: string) => void;

  // Events
  events: CalendarEvent[];
  currentEventId: string | null;
  setEvents: (events: CalendarEvent[]) => void;
  setCurrentEvent: (eventId: string | null) => void;
  addEvent: (event: CalendarEvent) => void;
  updateEvent: (eventId: string, updates: Partial<CalendarEvent>) => void;
  removeEvent: (eventId: string) => void;

  // UI State
  isCalendarPanelOpen: boolean;
  isEventFormOpen: boolean;
  viewMode: 'month' | 'week' | 'day' | 'list';
  selectedDate: Date;
  toggleCalendarPanel: () => void;
  setIsCalendarPanelOpen: (open: boolean) => void;
  setIsEventFormOpen: (open: boolean) => void;
  setViewMode: (mode: 'month' | 'week' | 'day' | 'list') => void;
  setSelectedDate: (date: Date) => void;

  // Draft Event
  draftEvent: Partial<CalendarEvent>;
  setDraftSummary: (summary: string) => void;
  setDraftDescription: (description: string) => void;
  setDraftLocation: (location: string) => void;
  setDraftStart: (start: string) => void;
  setDraftEnd: (end: string) => void;
  setDraftAllDay: (allDay: boolean) => void;
  setDraftAttendees: (attendees: string[]) => void;
  clearDraft: () => void;

  // Filters
  showCancelled: boolean;
  searchQuery: string;
  setShowCancelled: (show: boolean) => void;
  setSearchQuery: (query: string) => void;

  // Sync
  lastSyncAt: string | null;
  setLastSyncAt: (timestamp: string) => void;
}

export const useCalendarStore = create<CalendarStore>()(
  persist(
    (set) => ({
      // Calendars
      calendars: [],
      currentCalendarId: null,
      setCalendars: (calendars) => set({ calendars }),
      setCurrentCalendar: (calendarId) => set({ currentCalendarId: calendarId }),
      addCalendar: (calendar) =>
        set((state) => ({
          calendars: [...state.calendars, calendar],
        })),
      updateCalendar: (calendarId, updates) =>
        set((state) => ({
          calendars: state.calendars.map((cal) =>
            cal.id === calendarId ? { ...cal, ...updates } : cal
          ),
        })),
      removeCalendar: (calendarId) =>
        set((state) => ({
          calendars: state.calendars.filter((cal) => cal.id !== calendarId),
          currentCalendarId:
            state.currentCalendarId === calendarId ? null : state.currentCalendarId,
        })),

      // Events
      events: [],
      currentEventId: null,
      setEvents: (events) => set({ events }),
      setCurrentEvent: (eventId) => set({ currentEventId: eventId }),
      addEvent: (event) =>
        set((state) => ({
          events: [...state.events, event],
        })),
      updateEvent: (eventId, updates) =>
        set((state) => ({
          events: state.events.map((evt) =>
            evt.id === eventId ? { ...evt, ...updates } : evt
          ),
        })),
      removeEvent: (eventId) =>
        set((state) => ({
          events: state.events.filter((evt) => evt.id !== eventId),
          currentEventId:
            state.currentEventId === eventId ? null : state.currentEventId,
        })),

      // UI State
      isCalendarPanelOpen: false,
      isEventFormOpen: false,
      viewMode: 'month',
      selectedDate: new Date(),
      toggleCalendarPanel: () =>
        set((state) => ({ isCalendarPanelOpen: !state.isCalendarPanelOpen })),
      setIsCalendarPanelOpen: (open) => set({ isCalendarPanelOpen: open }),
      setIsEventFormOpen: (open) => set({ isEventFormOpen: open }),
      setViewMode: (mode) => set({ viewMode: mode }),
      setSelectedDate: (date) => set({ selectedDate: date }),

      // Draft Event
      draftEvent: {},
      setDraftSummary: (summary) =>
        set((state) => ({
          draftEvent: { ...state.draftEvent, summary },
        })),
      setDraftDescription: (description) =>
        set((state) => ({
          draftEvent: { ...state.draftEvent, description },
        })),
      setDraftLocation: (location) =>
        set((state) => ({
          draftEvent: { ...state.draftEvent, location },
        })),
      setDraftStart: (start) =>
        set((state) => ({
          draftEvent: { ...state.draftEvent, start_datetime: start },
        })),
      setDraftEnd: (end) =>
        set((state) => ({
          draftEvent: { ...state.draftEvent, end_datetime: end },
        })),
      setDraftAllDay: (allDay) =>
        set((state) => ({
          draftEvent: { ...state.draftEvent, all_day: allDay },
        })),
      setDraftAttendees: (attendees) =>
        set((state) => ({
          draftEvent: { ...state.draftEvent, attendees },
        })),
      clearDraft: () => set({ draftEvent: {} }),

      // Filters
      showCancelled: false,
      searchQuery: '',
      setShowCancelled: (show) => set({ showCancelled: show }),
      setSearchQuery: (query) => set({ searchQuery: query }),

      // Sync
      lastSyncAt: null,
      setLastSyncAt: (timestamp) => set({ lastSyncAt: timestamp }),
    }),
    {
      name: 'calendar-storage',
      partialize: (state) => ({
        calendars: state.calendars,
        currentCalendarId: state.currentCalendarId,
        events: state.events,
        viewMode: state.viewMode,
        showCancelled: state.showCancelled,
        lastSyncAt: state.lastSyncAt,
      }),
    }
  )
);
