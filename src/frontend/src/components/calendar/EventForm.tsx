/**
 * THÉRÈSE v2 - Event Form
 *
 * Formulaire pour créer ou éditer un événement.
 * Phase 2 - Calendar
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, Save, Loader2 } from 'lucide-react';
import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';
import { Button } from '../ui/Button';
import * as api from '../../services/api';

export function EventForm() {
  const {
    events,
    currentCalendarId,
    currentEventId,
    setIsEventFormOpen,
    setCurrentEvent,
    addEvent,
    updateEvent: updateEventInStore,
    clearDraft,
  } = useCalendarStore();

  const { currentAccountId } = useEmailStore();

  const [summary, setSummary] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [startDate, setStartDate] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endDate, setEndDate] = useState('');
  const [endTime, setEndTime] = useState('');
  const [allDay, setAllDay] = useState(false);
  const [attendeesInput, setAttendeesInput] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isEditing = !!currentEventId;
  const event = events.find((evt) => evt.id === currentEventId);

  // Load event data for editing
  useEffect(() => {
    if (isEditing && event) {
      setSummary(event.summary || '');
      setDescription(event.description || '');
      setLocation(event.location || '');
      setAllDay(event.all_day);

      if (event.all_day) {
        setStartDate(event.start_date || '');
        setEndDate(event.end_date || '');
      } else {
        const start = new Date(event.start_datetime!);
        const end = new Date(event.end_datetime!);
        setStartDate(start.toISOString().split('T')[0]);
        setStartTime(start.toTimeString().slice(0, 5));
        setEndDate(end.toISOString().split('T')[0]);
        setEndTime(end.toTimeString().slice(0, 5));
      }

      if (event.attendees && event.attendees.length > 0) {
        setAttendeesInput(event.attendees.join(', '));
      }
    } else {
      // New event: default to today
      const now = new Date();
      const todayStr = now.toISOString().split('T')[0];
      const timeStr = now.toTimeString().slice(0, 5);
      setStartDate(todayStr);
      setStartTime(timeStr);
      setEndDate(todayStr);
      const endTime = new Date(now.getTime() + 60 * 60 * 1000);
      setEndTime(endTime.toTimeString().slice(0, 5));
    }
  }, [isEditing, event]);

  async function handleSave() {
    if (!currentAccountId || !currentCalendarId) return;

    if (!summary.trim()) {
      setError('Veuillez ajouter un titre');
      return;
    }

    if (!startDate || (!allDay && !startTime)) {
      setError('Veuillez définir la date et heure de début');
      return;
    }

    if (!endDate || (!allDay && !endTime)) {
      setError('Veuillez définir la date et heure de fin');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const attendees = attendeesInput
        .split(',')
        .map((e) => e.trim())
        .filter((e) => e);

      if (isEditing && event) {
        // Update existing event
        const request: api.UpdateEventRequest = {
          summary,
          description: description || undefined,
          location: location || undefined,
          attendees: attendees.length > 0 ? attendees : undefined,
        };

        if (allDay) {
          request.start_date = startDate;
          request.end_date = endDate;
        } else {
          request.start_datetime = `${startDate}T${startTime}:00`;
          request.end_datetime = `${endDate}T${endTime}:00`;
        }

        const updated = await api.updateEvent(
          event.id,
          request,
          currentCalendarId,
          currentAccountId
        );
        updateEventInStore(event.id, updated);
        setCurrentEvent(event.id);
      } else {
        // Create new event
        const request: api.CreateEventRequest = {
          calendar_id: currentCalendarId,
          summary,
          description: description || undefined,
          location: location || undefined,
          attendees: attendees.length > 0 ? attendees : undefined,
        };

        if (allDay) {
          request.start_date = startDate;
          request.end_date = endDate;
        } else {
          request.start_datetime = `${startDate}T${startTime}:00`;
          request.end_datetime = `${endDate}T${endTime}:00`;
        }

        const created = await api.createEvent(request, currentAccountId);
        addEvent(created);
        setCurrentEvent(created.id);
      }

      clearDraft();
      setIsEventFormOpen(false);
    } catch (err) {
      console.error('Failed to save event:', err);
      setError(err instanceof Error ? err.message : 'Échec de la sauvegarde');
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    if (confirm('Abandonner les modifications ?')) {
      clearDraft();
      setIsEventFormOpen(false);
      if (isEditing) {
        setCurrentEvent(currentEventId);
      } else {
        setCurrentEvent(null);
      }
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="h-full flex flex-col"
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-border/30 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={handleCancel}
            className="p-2 hover:bg-border/30 rounded-lg transition-colors"
          >
            <ChevronLeft className="w-5 h-5 text-text-muted" />
          </button>
          <h3 className="text-lg font-semibold text-text">
            {isEditing ? "Modifier l'événement" : "Nouvel événement"}
          </h3>
        </div>

        <Button variant="primary" size="sm" onClick={handleSave} disabled={saving}>
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Enregistrement...
            </>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Enregistrer
            </>
          )}
        </Button>
      </div>

      {/* Form */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {error && (
          <div className="px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Summary */}
        <div>
          <label className="text-sm text-text-muted mb-2 block">Titre *</label>
          <input
            type="text"
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="Titre de l'événement"
            className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
        </div>

        {/* All Day Toggle */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="all-day"
            checked={allDay}
            onChange={(e) => setAllDay(e.target.checked)}
            className="w-4 h-4 rounded border-border/50 bg-background/60 text-accent-cyan focus:ring-2 focus:ring-accent-cyan/50"
          />
          <label htmlFor="all-day" className="text-sm text-text cursor-pointer">
            Événement sur toute la journée
          </label>
        </div>

        {/* Start Date/Time */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-text-muted mb-2 block">Date de début *</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
            />
          </div>
          {!allDay && (
            <div>
              <label className="text-sm text-text-muted mb-2 block">Heure de début *</label>
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
              />
            </div>
          )}
        </div>

        {/* End Date/Time */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-text-muted mb-2 block">Date de fin *</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
            />
          </div>
          {!allDay && (
            <div>
              <label className="text-sm text-text-muted mb-2 block">Heure de fin *</label>
              <input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
              />
            </div>
          )}
        </div>

        {/* Location */}
        <div>
          <label className="text-sm text-text-muted mb-2 block">Lieu</label>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Lieu de l'événement"
            className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
        </div>

        {/* Description */}
        <div>
          <label className="text-sm text-text-muted mb-2 block">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description de l'événement"
            rows={4}
            className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 resize-none focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
        </div>

        {/* Attendees */}
        <div>
          <label className="text-sm text-text-muted mb-2 block">Participants</label>
          <input
            type="text"
            value={attendeesInput}
            onChange={(e) => setAttendeesInput(e.target.value)}
            placeholder="email1@example.com, email2@example.com"
            className="w-full px-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
          />
          <p className="text-xs text-text-muted mt-1">
            Séparez les emails par des virgules
          </p>
        </div>
      </div>
    </motion.div>
  );
}
