/**
 * THÉRÈSE v2 - Event Detail
 *
 * Vue détaillée d'un événement calendrier.
 * Phase 2 - Calendar
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ChevronLeft,
  Edit,
  Trash2,
  MapPin,
  Clock,
  Users,
  Repeat,
  Loader2,
} from 'lucide-react';
import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';
import { Button } from '../ui/Button';
import * as api from '../../services/api';

export function EventDetail() {
  const { events, currentEventId, setCurrentEvent, setIsEventFormOpen, removeEvent } =
    useCalendarStore();
  const { currentAccountId } = useEmailStore();

  const [deleting, setDeleting] = useState(false);

  const event = events.find((evt) => evt.id === currentEventId);

  async function handleDelete() {
    if (!event || !currentAccountId || !confirm('Supprimer cet événement ?')) return;

    setDeleting(true);

    try {
      await api.deleteEvent(event.id, event.calendar_id, currentAccountId);
      removeEvent(event.id);
      setCurrentEvent(null);
    } catch (err) {
      console.error('Failed to delete event:', err);
      alert('Échec de la suppression');
    } finally {
      setDeleting(false);
    }
  }

  function handleEdit() {
    setIsEventFormOpen(true);
  }

  if (!event) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-text-muted">Événement introuvable</p>
      </div>
    );
  }

  const startDate = event.all_day
    ? new Date(event.start_date!)
    : new Date(event.start_datetime!);
  const endDate = event.all_day ? new Date(event.end_date!) : new Date(event.end_datetime!);

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="h-full flex flex-col"
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-border/30">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => setCurrentEvent(null)}
            className="p-2 hover:bg-border/30 rounded-lg transition-colors"
          >
            <ChevronLeft className="w-5 h-5 text-text-muted" />
          </button>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={handleEdit}>
              <Edit className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={handleDelete} disabled={deleting}>
              {deleting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>

        <h3 className="text-xl font-semibold text-text mb-2">{event.summary}</h3>

        {/* Status */}
        {event.status !== 'confirmed' && (
          <span
            className={`inline-block px-2 py-1 text-xs rounded ${
              event.status === 'tentative'
                ? 'bg-yellow-500/10 text-yellow-400'
                : 'bg-red-500/10 text-red-400'
            }`}
          >
            {event.status === 'tentative' ? 'Provisoire' : 'Annulé'}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {/* Date & Time */}
        <div className="flex items-start gap-3">
          <Clock className="w-5 h-5 text-accent-cyan mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-text">
              {startDate.toLocaleDateString('fr-FR', {
                weekday: 'long',
                day: 'numeric',
                month: 'long',
                year: 'numeric',
              })}
            </p>
            {!event.all_day && (
              <p className="text-sm text-text-muted mt-1">
                {startDate.toLocaleTimeString('fr-FR', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}{' '}
                -{' '}
                {endDate.toLocaleTimeString('fr-FR', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
            )}
            {event.all_day && <p className="text-sm text-text-muted mt-1">Toute la journée</p>}
          </div>
        </div>

        {/* Location */}
        {event.location && (
          <div className="flex items-start gap-3">
            <MapPin className="w-5 h-5 text-accent-cyan mt-0.5 shrink-0" />
            <p className="text-sm text-text">{event.location}</p>
          </div>
        )}

        {/* Attendees */}
        {event.attendees && event.attendees.length > 0 && (
          <div className="flex items-start gap-3">
            <Users className="w-5 h-5 text-accent-cyan mt-0.5 shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-text mb-2">
                {event.attendees.length} participant{event.attendees.length > 1 ? 's' : ''}
              </p>
              <div className="space-y-1">
                {event.attendees.map((email) => (
                  <p key={email} className="text-sm text-text-muted">
                    {email}
                  </p>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Recurrence */}
        {event.recurrence && event.recurrence.length > 0 && (
          <div className="flex items-start gap-3">
            <Repeat className="w-5 h-5 text-accent-cyan mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-medium text-text mb-1">Événement récurrent</p>
              {event.recurrence.map((rule, i) => (
                <p key={i} className="text-xs text-text-muted font-mono">
                  {rule}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Description */}
        {event.description && (
          <div>
            <h4 className="text-sm font-medium text-text mb-2">Description</h4>
            <p className="text-sm text-text-muted whitespace-pre-wrap">{event.description}</p>
          </div>
        )}
      </div>
    </motion.div>
  );
}
