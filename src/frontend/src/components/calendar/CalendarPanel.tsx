/**
 * THÉRÈSE v2 - Calendar Panel
 *
 * Panel principal pour afficher et gérer le calendrier Google.
 * Phase 2 - Calendar
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Calendar as CalendarIcon,
  Plus,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  ExternalLink,
  Loader2,
} from 'lucide-react';
import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';
import { CalendarView } from './CalendarView';
import { EventForm } from './EventForm';
import { EventDetail } from './EventDetail';
import { Button } from '../ui/Button';
import * as api from '../../services/api';

interface CalendarPanelProps {
  isOpen?: boolean;
  onClose?: () => void;
  standalone?: boolean;
}

export function CalendarPanel({ isOpen, onClose, standalone = false }: CalendarPanelProps) {
  const {
    calendars,
    currentCalendarId,
    events,
    currentEventId,
    viewMode,
    selectedDate,
    isEventFormOpen,
    setCalendars,
    setCurrentCalendar,
    setEvents,
    setCurrentEvent,
    setIsEventFormOpen,
    setViewMode,
    setSelectedDate,
    setLastSyncAt,
  } = useCalendarStore();

  const { accounts, currentAccountId, setAccounts, setCurrentAccount, needsReauth, setNeedsReauth } = useEmailStore();
  const [loading, setLoading] = useState(standalone);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reauthing, setReauthing] = useState(false);

  const currentAccount = accounts.find((acc) => acc.id === currentAccountId);

  const effectiveOpen = standalone || isOpen;

  // En standalone, charger les comptes email si pas encore disponibles
  useEffect(() => {
    if (standalone && !currentAccountId) {
      api.getEmailAuthStatus().then((status) => {
        setAccounts(status.accounts);
        if (status.accounts.length > 0) {
          setCurrentAccount(status.accounts[0].id);
        } else {
          setLoading(false);
          setError('Aucun compte email configuré');
        }
      }).catch((err) => {
        console.error('Failed to load email accounts for calendar:', err);
        setLoading(false);
        setError('Impossible de charger les comptes email');
      });
    }
  }, [standalone, currentAccountId]);

  const hasCachedCalendars = calendars.length > 0;
  const hasCachedEvents = events.length > 0;
  const [calendarsReady, setCalendarsReady] = useState(hasCachedCalendars);

  // Load calendars on mount (séquentiel : events se chargent APRÈS)
  useEffect(() => {
    if (effectiveOpen && currentAccountId) {
      loadCalendars();
    }
  }, [effectiveOpen, currentAccountId]);

  // Load events APRÈS les calendriers, ou quand le mois/calendrier change
  useEffect(() => {
    if (calendarsReady && currentCalendarId && currentAccountId) {
      loadEvents();
    }
  }, [calendarsReady, currentCalendarId, currentAccountId, selectedDate]);

  async function loadCalendars() {
    if (!currentAccountId) return;

    if (!hasCachedCalendars) setLoading(true);
    setError(null);

    try {
      const cals = await api.listCalendars(currentAccountId);
      setCalendars(cals);

      // Auto-select primary calendar
      const primary = cals.find((c) => c.primary);
      if (primary && !currentCalendarId) {
        setCurrentCalendar(primary.id);
      }

      setCalendarsReady(true);
    } catch (err: any) {
      console.error('Failed to load calendars:', err);
      const msg = err?.message || '';
      if (msg.includes('expired') || msg.includes('revoked') || msg.includes('401') || msg.includes('reconnect')) {
        setError('Connexion Google expirée.');
        setNeedsReauth(true);
      } else {
        setError('Impossible de charger les calendriers');
      }
      // Si on a du cache, laisser les events se charger quand même
      if (hasCachedCalendars) setCalendarsReady(true);
    } finally {
      setLoading(false);
    }
  }

  async function loadEvents() {
    if (!currentAccountId || !currentCalendarId) return;

    setError(null);

    try {
      // Load events for the selected month
      const startOfMonth = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1);
      const endOfMonth = new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 0);

      const evts = await api.listEvents(currentAccountId, currentCalendarId, {
        time_min: startOfMonth.toISOString(),
        time_max: endOfMonth.toISOString(),
        max_results: 250,
      });

      setEvents(evts);
    } catch (err: any) {
      console.error('Failed to load events:', err);
      const msg = err?.message || '';
      if (msg.includes('expired') || msg.includes('revoked') || msg.includes('401') || msg.includes('reconnect')) {
        setError('Connexion Google expirée.');
        setNeedsReauth(true);
      } else if (!hasCachedEvents) {
        // Afficher l'erreur uniquement si pas de cache
        setError('Impossible de charger les événements');
      }
    }
  }

  async function handleSync() {
    if (!currentAccountId) return;

    setSyncing(true);
    setError(null);

    try {
      const result = await api.syncCalendar(currentAccountId);
      setLastSyncAt(result.synced_at);

      // Reload calendars and events
      await loadCalendars();
      if (currentCalendarId) {
        await loadEvents();
      }
    } catch (err: any) {
      console.error('Failed to sync calendar:', err);
      const msg = err?.message || '';
      if (msg.includes('expired') || msg.includes('revoked') || msg.includes('401') || msg.includes('reconnect')) {
        setError('Connexion Google expirée.');
        setNeedsReauth(true);
      } else {
        setError('Échec de la synchronisation');
      }
    } finally {
      setSyncing(false);
    }
  }

  function handleNewEvent() {
    setCurrentEvent(null);
    setIsEventFormOpen(true);
  }

  function handlePrevious() {
    const newDate = new Date(selectedDate);
    if (viewMode === 'day') {
      newDate.setDate(newDate.getDate() - 1);
    } else if (viewMode === 'week') {
      newDate.setDate(newDate.getDate() - 7);
    } else {
      newDate.setMonth(newDate.getMonth() - 1);
    }
    setSelectedDate(newDate);
  }

  function handleNext() {
    const newDate = new Date(selectedDate);
    if (viewMode === 'day') {
      newDate.setDate(newDate.getDate() + 1);
    } else if (viewMode === 'week') {
      newDate.setDate(newDate.getDate() + 7);
    } else {
      newDate.setMonth(newDate.getMonth() + 1);
    }
    setSelectedDate(newDate);
  }

  function handleToday() {
    setSelectedDate(new Date());
  }

  /** Libellé de navigation adapté au mode de vue */
  function getNavLabel(): string {
    if (viewMode === 'day') {
      return selectedDate.toLocaleDateString('fr-FR', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      });
    }
    if (viewMode === 'week') {
      // Calculer lundi et dimanche de la semaine
      const dayOfWeek = selectedDate.getDay();
      const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
      const monday = new Date(selectedDate);
      monday.setDate(selectedDate.getDate() + mondayOffset);
      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);

      const fmtStart = monday.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
      const fmtEnd = sunday.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' });
      return `${fmtStart} - ${fmtEnd}`;
    }
    // month / list
    return selectedDate.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });
  }

  async function handleReauthorize() {
    if (!currentAccountId || reauthing) return;
    setReauthing(true);

    try {
      const flow = await api.reauthorizeEmail(currentAccountId);
      const { open } = await import('@tauri-apps/plugin-shell');
      try {
        await open(flow.auth_url);
      } catch {
        window.open(flow.auth_url, '_blank');
      }

      // Poller le status pour détecter quand le token est renouvelé
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        if (attempts > 100) {
          clearInterval(poll);
          setReauthing(false);
          return;
        }
        try {
          await api.listCalendars(currentAccountId);
          clearInterval(poll);
          setNeedsReauth(false);
          setReauthing(false);
          setError(null);
          loadCalendars();
        } catch {
          // Pas encore réautorisé
        }
      }, 3000);
    } catch (err) {
      console.error('Reauthorize failed:', err);
      setReauthing(false);
    }
  }

  if (!effectiveOpen) return null;

  // Contenu interne partagé entre les deux modes
  const calendarHeader = (
    <div className="px-6 py-4 border-b border-border/30 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
          <CalendarIcon className="w-5 h-5 text-accent-cyan" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-text">Calendrier</h2>
          {currentAccount && (
            <p className="text-sm text-text-muted">{currentAccount.email}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* View Mode */}
        <div className="flex items-center gap-1 bg-background/60 rounded-lg p-1">
          {(['month', 'week', 'day', 'list'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`px-3 py-1 text-sm rounded transition-colors ${
                viewMode === mode
                  ? 'bg-accent-cyan/20 text-accent-cyan'
                  : 'text-text-muted hover:text-text'
              }`}
            >
              {mode === 'month' && 'Mois'}
              {mode === 'week' && 'Semaine'}
              {mode === 'day' && 'Jour'}
              {mode === 'list' && 'Liste'}
            </button>
          ))}
        </div>

        <Button variant="ghost" size="sm" onClick={handleSync} disabled={syncing}>
          <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
        </Button>

        <Button variant="primary" size="sm" onClick={handleNewEvent}>
          <Plus className="w-4 h-4 mr-2" />
          Nouvel événement
        </Button>

        {!standalone && (
          <button
            onClick={onClose}
            className="p-2 hover:bg-border/30 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-text-muted" />
          </button>
        )}
      </div>
    </div>
  );

  const calendarNav = (
    <div className="px-6 py-3 border-b border-border/30 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={handlePrevious}>
          <ChevronLeft className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={handleNext}>
          <ChevronRight className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={handleToday}>
          Aujourd'hui
        </Button>
      </div>

      <h3 className="text-lg font-semibold text-text capitalize">
        {getNavLabel()}
      </h3>

      {/* Calendar Selector */}
      <select
        value={currentCalendarId || ''}
        onChange={(e) => setCurrentCalendar(e.target.value)}
        className="px-3 py-1.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
      >
        {calendars.map((cal) => (
          <option key={cal.id} value={cal.id}>
            {cal.summary}
          </option>
        ))}
      </select>
    </div>
  );

  const reauthBanner = needsReauth ? (
    <div className="px-4 py-2 bg-yellow-500/10 border-b border-yellow-500/20 flex items-center gap-3">
      <AlertTriangle className="w-4 h-4 text-yellow-400 shrink-0" />
      <p className="text-sm text-yellow-200 flex-1">
        Connexion Google expirée. Reconnecte-toi pour synchroniser le calendrier.
      </p>
      <Button
        variant="ghost"
        size="sm"
        onClick={handleReauthorize}
        disabled={reauthing}
        className="text-yellow-300 hover:text-yellow-100 shrink-0"
      >
        {reauthing ? (
          <>
            <Loader2 className="w-3 h-3 animate-spin mr-2" />
            En attente...
          </>
        ) : (
          <>
            <ExternalLink className="w-3 h-3 mr-2" />
            Reconnecter
          </>
        )}
      </Button>
    </div>
  ) : null;

  const calendarContent = (
    <>
      {/* Error */}
      {error && !needsReauth && (
        <div className="mx-6 mt-4 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <RefreshCw className="w-8 h-8 animate-spin text-accent-cyan" />
          </div>
        ) : isEventFormOpen ? (
          <EventForm />
        ) : currentEventId ? (
          <EventDetail />
        ) : (
          <CalendarView />
        )}
      </div>
    </>
  );

  // Mode standalone : pleine page
  if (standalone) {
    return (
      <div className="h-full flex flex-col bg-bg">
        {calendarHeader}
        {reauthBanner}
        {calendarNav}
        {calendarContent}
      </div>
    );
  }

  // Mode modal
  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/60 backdrop-blur-md"
          onClick={onClose}
        />

        {/* Panel */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="relative w-full h-full max-w-7xl max-h-[90vh] mx-4 bg-surface/95 backdrop-blur-xl border border-border/50 rounded-xl shadow-2xl overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {calendarHeader}
          {reauthBanner}
          {calendarNav}
          {calendarContent}
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
