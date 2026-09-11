/**
 * THÉRÈSE v2 - Event Form
 *
 * Formulaire pour créer ou éditer un événement.
 * Phase 2 - Calendar
 */

import { useState, useEffect } from 'react';
import { ChevronLeft, Save } from 'lucide-react';
import { localDateKey } from '../../lib/civilDate';
import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';
import { useGuardedAction } from '../../hooks/useGuardedAction';
import { Alerte } from '../ui/Alerte';
import { Button } from '../ui/Button';
import { FormField } from '../ui/FormField';
import { Input } from '../ui/Input';
import { Textarea } from '../ui/Textarea';
import { useExternalActionConfirmation } from '../app/useExternalActionConfirmation';
import * as api from '../../services/api';
import { Spinner } from '../ui/Spinner';

export function EventForm() {
  const requestExternalAction = useExternalActionConfirmation();
  const {
    calendars,
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
  const [formError, setFormError] = useState<string | null>(null);

  const { execute, error: guardError, loading: guardLoading, clearError } = useGuardedAction([
    { check: currentCalendarId, message: 'Aucun calendrier sélectionné. Choisis un calendrier dans le menu déroulant.' },
  ]);

  const error = formError || guardError;
  const saving = guardLoading;

  const isEditing = !!currentEventId;
  const event = events.find((evt) => evt.id === currentEventId);
  const selectedCalendar = calendars.find((calendar) => calendar.id === currentCalendarId);

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
      const fin = new Date(now.getTime() + 60 * 60 * 1000);
      // La date de FIN se déduit de l'instant de fin, pas de la date du jour :
      // à 23 h 30, début + 1 h tombe le LENDEMAIN. Figer la date de fin sur
      // aujourd'hui rendait la fin antérieure au début, et la validation
      // refusait toute création entre 23 h et minuit.
      //
      // `localDateKey` plutôt que `toISOString()` : ce dernier rend la date
      // UTC alors que l'heure affichée est locale — un décalage d'un jour en
      // UTC+ (dates civiles, BUG-144).
      setStartDate(localDateKey(now));
      setStartTime(now.toTimeString().slice(0, 5));
      setEndDate(localDateKey(fin));
      setEndTime(fin.toTimeString().slice(0, 5));
    }
  }, [isEditing, event]);

  async function handleSave() {
    // Validation formulaire (avant les guards)
    if (!summary.trim()) {
      setFormError('Ajoute un titre');
      return;
    }

    if (!startDate || (!allDay && !startTime)) {
      setFormError('Définis la date et heure de début');
      return;
    }

    if (!endDate || (!allDay && !endTime)) {
      setFormError('Définis la date et heure de fin');
      return;
    }

    // Validation : la fin ne peut pas précéder le début (message explicite, BUG capov 0.20).
    // Comparaison sur l'heure MURALE (chaînes ISO triables à champs fixes) plutôt que sur
    // des timestamps locaux : juste même autour des changements d'heure (DST) — revue F3.
    const startKey = allDay ? startDate : `${startDate}T${startTime}`;
    const endKey = allDay ? endDate : `${endDate}T${endTime}`;
    // BUG-144 : en « toute la journée », début = fin est un événement d'un
    // seul jour, valide (la fin est INCLUSIVE dans l'app). La règle reste
    // stricte pour les événements horaires.
    const endInvalid = allDay ? endKey < startKey : endKey <= startKey;
    if (endInvalid) {
      setFormError(
        allDay
          ? 'La date de fin ne peut pas précéder la date de début.'
          : "La date et l'heure de fin doivent être postérieures au début."
      );
      return;
    }

    setFormError(null);
    clearError();

    if (!currentCalendarId) {
      await execute(async () => undefined);
      return;
    }

    const attendees = attendeesInput
      .split(',')
      .map((e) => e.trim())
      .filter((e) => e);

    requestExternalAction({
      title: isEditing ? 'Confirmer la modification de l’événement' : 'Confirmer la création de l’événement',
      // B-573 : un agenda local enregistre les participants sans pouvoir
      // les inviter ; promettre des invitations serait faux.
      description: attendees.length === 0
        ? 'Vérifie les horaires et la destination avant d’enregistrer cet événement.'
        : !selectedCalendar || selectedCalendar.provider === 'local'
          ? 'Vérifie les horaires et les participants. Cet agenda local les enregistre mais ne peut pas leur envoyer d’invitation : préviens-les toi-même.'
          : 'Vérifie les horaires et les participants. Les invitations ne partiront qu’après ta confirmation.',
      confirmLabel: isEditing ? 'Confirmer la modification' : 'Confirmer la création',
      details: [
        { label: 'Titre', value: summary },
        { label: 'Début', value: allDay ? startDate : `${startDate} ${startTime}` },
        { label: 'Fin', value: allDay ? endDate : `${endDate} ${endTime}` },
        { label: 'Calendrier', value: selectedCalendar?.summary || currentCalendarId },
        { label: 'Fournisseur', value: selectedCalendar?.provider || 'Destination locale' },
        { label: 'Compte', value: currentAccountId || 'Compte local' },
        { label: 'Participants', value: attendees.join(', ') },
        { label: 'Lieu', value: location },
        { label: 'Description', value: description },
      ],
    }, async () => {
      await execute(async () => {
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
            // Fuseau réel du poste : sans lui, le backend retombe sur Europe/Paris
            // et l'heure se décale (ex: 9h30 à Toronto affichée à 3h30).
            request.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
          }

          const updated = await api.updateEvent(
            event.id,
            request,
            currentCalendarId,
            currentAccountId || undefined
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
            // Fuseau réel du poste : sans lui, le backend retombe sur Europe/Paris
            // et l'heure se décale (ex: 9h30 à Toronto affichée à 3h30).
            request.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
          }

          const created = await api.createEvent(request, currentAccountId || undefined);
          addEvent(created);
          setCurrentEvent(created.id);
        }

        clearDraft();
        setIsEventFormOpen(false);
      });
    });
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
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={handleCancel} aria-label="Retour">
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <h3 className="text-lg font-semibold text-text">
            {isEditing ? "Modifier l'événement" : 'Nouveau rendez-vous'}
          </h3>
        </div>

        <Button variant="primary" size="md" onClick={handleSave} disabled={saving}>
          {saving ? (
            <>
              <Spinner taille="bouton" className="mr-2" />
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
        {/* Un seul bandeau pour les deux sources : `formError` (saisie) et
            `guardError` (aucun agenda sélectionné). `FormField error` en
            rendrait un second, avec son propre `role="alert"`. */}
        {error && (
          <Alerte>{error}</Alerte>
        )}

        {/* Summary. L'astérisque de `FormField` est `aria-hidden` : c'est
            l'attribut `required` de l'`Input` qui porte l'obligation jusqu'au
            lecteur d'écran. Aucune validation native n'entre par là, il n'y a
            pas de `<form>` et l'enregistrement passe par `onClick`. */}
        <FormField label="Titre" htmlFor="eventform-titre" required>
          <Input
            id="eventform-titre"
            type="text"
            required
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="Titre de l'événement"
          />
        </FormField>

        {/* All Day Toggle : hors `FormField`, dont le label est un bloc
            au-dessus du champ. Le libellé d'une case va à côté. */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="all-day"
            checked={allDay}
            onChange={(e) => setAllDay(e.target.checked)}
            className="w-4 h-4 rounded-sm border-border/50 bg-background/60 text-accent focus:ring-2 focus:ring-ring/50"
          />
          <label htmlFor="all-day" className="text-sm text-text cursor-pointer">
            Événement sur toute la journée
          </label>
        </div>

        {/* Start Date/Time */}
        <div className="grid grid-cols-2 max-[1023px]:grid-cols-1 gap-4">
          <FormField label="Date de début" htmlFor="eventform-date-de-debut" required>
            <Input
              id="eventform-date-de-debut"
              type="date"
              required
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </FormField>
          {!allDay && (
            <FormField label="Heure de début" htmlFor="eventform-heure-de-debut" required>
              <Input
                id="eventform-heure-de-debut"
                type="time"
                required
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
              />
            </FormField>
          )}
        </div>

        {/* End Date/Time */}
        <div className="grid grid-cols-2 max-[1023px]:grid-cols-1 gap-4">
          <FormField label="Date de fin" htmlFor="eventform-date-de-fin" required>
            <Input
              id="eventform-date-de-fin"
              type="date"
              required
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </FormField>
          {!allDay && (
            <FormField label="Heure de fin" htmlFor="eventform-heure-de-fin" required>
              <Input
                id="eventform-heure-de-fin"
                type="time"
                required
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
              />
            </FormField>
          )}
        </div>

        {/* Location */}
        <FormField label="Lieu ou visio" htmlFor="eventform-lieu">
          <Input
            id="eventform-lieu"
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Atelier, adresse ou lien"
          />
        </FormField>

        {/* Description */}
        <FormField label="Description" htmlFor="eventform-description">
          {/* `resize-none` : sans `autoResize`, la primitive rend `resize-y`
              (`Textarea.tsx:66`) et ferait apparaître une poignée que `main`
              n'avait pas et que le design ne demande pas (revue du diff,
              point 8). */}
          <Textarea
            id="eventform-description"
            className="resize-none"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description de l'événement"
            rows={4}
          />
        </FormField>

        {/* Attendees */}
        <FormField
          label="Participants"
          htmlFor="eventform-participants"
          description="Séparez les emails par des virgules"
        >
          <Input
            id="eventform-participants"
            type="text"
            value={attendeesInput}
            onChange={(e) => setAttendeesInput(e.target.value)}
            placeholder="email1@example.com, email2@example.com"
          />
        </FormField>

        {/* Agenda : la destination de l'enregistrement, jusqu'ici visible dans
            la seule confirmation externe. Lecture seule et non `disabled` : un
            champ désactivé sort de la tabulation et sa valeur ne se copie pas.
            Le `?? ''` garde l'`Input` contrôlé quand aucun agenda n'est choisi. */}
        <FormField label="Agenda" htmlFor="eventform-agenda">
          <Input
            id="eventform-agenda"
            type="text"
            readOnly
            aria-readonly="true"
            value={selectedCalendar?.summary ?? ''}
          />
        </FormField>
      </div>
    </div>
  );
}
