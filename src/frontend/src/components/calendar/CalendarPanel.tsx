/**
 * THÉRÈSE v2 - Calendar Panel
 *
 * Panel principal pour afficher et gérer le calendrier Google.
 * Phase 2 - Calendar
 */

import { useEffect, useRef, useState } from 'react';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Calendar as CalendarIcon,
  Plus,
  Upload,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  AlertTriangle,
  ExternalLink,
  Download,
} from 'lucide-react';
import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';
import { CalendarView } from './CalendarView';
import { EventForm } from './EventForm';
import { EventDetail } from './EventDetail';
import { classifyCalendarError } from './calendarErrors';
import { Button } from '../ui/Button';
import { Alerte } from '../ui/Alerte';
import { Segments } from '../ui/Segments';
import { Select } from '../ui/Select';
import { Squelette } from '../ui/Squelette';
import * as api from '../../services/api';
import { useStatusStore } from '../../stores/statusStore';
import { Z_LAYER } from '../../styles/z-layers';
import { Spinner } from '../ui/Spinner';

/** Le type de vue, dérivé du store et non recopié : le jour où la liste des
 *  vues change là-bas, elle change ici sans intervention. */
type ModeDeVue = ReturnType<typeof useCalendarStore.getState>['viewMode'];

/** Les quatre vues, dans l'ordre visuel de la maquette ; les identifiants
 *  restent ceux du store — et l'annotation le prouve désormais à la
 *  compilation : sans elle, `VUES` s'inférait en `{ id: string }[]`, une faute
 *  de frappe dans un `id` compilait et cassait `choisirVue` en silence
 *  (revue du diff, point 10). */
const VUES: { id: ModeDeVue; label: string }[] = [
  { id: 'day', label: 'Jour' },
  { id: 'week', label: 'Semaine' },
  { id: 'month', label: 'Mois' },
  { id: 'list', label: 'Liste' },
];

/** Première lettre en capitale, jamais `capitalize` : la classe CSS
 *  capitaliserait chaque mot (« Mercredi 2 Septembre 2026 »). */
function capitaleInitiale(texte: string): string {
  return texte.charAt(0).toUpperCase() + texte.slice(1);
}

/** « 1er » le premier du mois, le nombre décimal sinon. */
function jourDuMois(date: Date): string {
  return date.getDate() === 1 ? '1er' : String(date.getDate());
}

function moisLong(date: Date): string {
  return date.toLocaleDateString('fr-FR', { month: 'long' });
}

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
    lastSyncAt,
  } = useCalendarStore();

  const { accounts, currentAccountId, setAccounts, setCurrentAccount, needsReauth, setNeedsReauth } = useEmailStore();
  const [loading, setLoading] = useState(standalone);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reauthing, setReauthing] = useState(false);
  // B-491 : le sondage de réautorisation meurt avec le panneau et DIT quand
  // il abandonne, au lieu de s'éteindre après cinq minutes sans un mot.
  const sondageReauthRef = useRef<ReturnType<typeof setInterval> | null>(null);
  /** #124 : l'erreur affichée vient des agendas ; le chargement des événements ne l'efface pas. */
  const erreurDesAgendasRef = useRef(false);
  useEffect(() => () => {
    if (sondageReauthRef.current) clearInterval(sondageReauthRef.current);
  }, []);
  const icsInputRef = { current: null as HTMLInputElement | null };

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
  // B-236 : semé depuis le cache, ce drapeau lançait le chargement des
  // événements AVANT la réponse de loadCalendars, avec l'identifiant rehydraté
  // de « calendar-storage » — donc potentiellement celui d'une base morte. La
  // réconciliation (`currentStillExists`, plus bas) existe, mais elle arrivait
  // après : la requête prenait un 400 que le rechargement suivant effaçait
  // aussitôt. On attend désormais la liste du serveur, ou son échec — le `catch`
  // de loadCalendars relève le drapeau quand il reste du cache à afficher.
  const [calendarsReady, setCalendarsReady] = useState(false);
  // B-271 : marqueur discret quand le cache est affiché mais le rafraîchissement a échoué.
  const [staleWarning, setStaleWarning] = useState<string | null>(null);
  // B-359 : en fenêtre, l'agenda se dit modal ; il piège donc le focus.
  const dialogRef = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(dialogRef, { active: !standalone && !!isOpen, onEscape: () => onClose?.() });

  // Load calendars on mount (séquentiel : events se chargent APRÈS)
  useEffect(() => {
    if (effectiveOpen) {
      loadCalendars();
    }
  }, [effectiveOpen, currentAccountId]);

  // Load events APRÈS les calendriers, ou quand le mois/calendrier change
  useEffect(() => {
    if (calendarsReady && currentCalendarId) {
      loadEvents();
    }
  }, [calendarsReady, currentCalendarId, currentAccountId, selectedDate]);

  async function loadCalendars() {
    if (!hasCachedCalendars) setLoading(true);
    setError(null);
    erreurDesAgendasRef.current = false;

    try {
      const cals = await api.listCalendars(currentAccountId || undefined);
      setCalendars(cals);

      // BUG-162 : désarmer la bannière « Connexion Google expirée » quand la
      // situation redevient normale. Elle n'était écrite que dans les `catch`,
      // donc une erreur passagère (jeton rafraîchi entre-temps, réseau, dérive
      // d'horloge) restait affichée jusqu'au redémarrage de l'application, en
      // demandant à l'utilisateur de reconnecter un compte parfaitement valide.
      //
      // Le garde-fou compte : seul un calendrier GOOGLE réellement rendu prouve
      // que le jeton fonctionne. Un succès sur un calendrier local n'apprend
      // rien sur Google et ne doit pas éteindre une vraie expiration.
      if (cals.some((cal) => cal.provider === 'google')) {
        setNeedsReauth(false);
      }

      // Auto-select : calendrier primaire, sinon le PREMIER disponible.
      // BUG-120 : un calendrier local (repli hors Google) n'est pas marqué
      // "primary" ; sans ce fallback, rien n'était sélectionné et la création
      // d'événement restait bloquée sur « Aucun calendrier sélectionné ».
      const primary = cals.find((c) => c.primary) ?? cals[0];
      const currentStillExists = cals.some((c) => c.id === currentCalendarId);
      if (primary && (!currentCalendarId || !currentStillExists)) {
        setCurrentCalendar(primary.id);
      }

      setCalendarsReady(true);
    } catch (err: any) {
      console.error('Failed to load calendars:', err);
      const msg = err?.message || '';
      const action = classifyCalendarError(msg, { fallback: 'Impossible de charger les calendriers' });
      if (action.error !== null) {
        setError(action.error);
        erreurDesAgendasRef.current = true;
      }
      if (action.needsReauth !== undefined) setNeedsReauth(action.needsReauth);
      // Si on a du cache, laisser les events se charger quand même
      if (hasCachedCalendars) setCalendarsReady(true);
    } finally {
      setLoading(false);
    }
  }

  async function loadEvents() {
    if (!currentCalendarId) return;

    // #124 : un succès sur l'agenda local n'efface pas l'explication d'un 403 Google.
    if (!erreurDesAgendasRef.current) setError(null);

    try {
      // Load events for the selected month
      const startOfMonth = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1);
      const endOfMonth = new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 0);

      // L'account_id doit venir du calendrier sélectionné, pas seulement du
      // compte email « courant » qui peut être vide (ouverture de l'agenda à
      // froid) : un calendrier Google sans account_id renvoyait 400 (recette
      // Ludo 16/07). On dérive donc l'account du calendrier lui-même.
      const currentCal = calendars.find((cal) => cal.id === currentCalendarId);
      const effectiveAccountId = currentCal?.account_id || currentAccountId || undefined;

      const evts = await api.listEvents(effectiveAccountId, currentCalendarId, {
        time_min: startOfMonth.toISOString(),
        time_max: endOfMonth.toISOString(),
        max_results: 250,
      });

      setEvents(evts);
      setStaleWarning(null); // B-271 : le rafraîchissement a réussi

      // BUG-162 : même désarmement que dans loadCalendars, sur le chemin le
      // plus fréquent (changer de mois recharge les événements).
      if (currentCal?.provider === 'google') {
        setNeedsReauth(false);
        // Revue Grok 0.70.0 (P2) : un succès DEPUIS GOOGLE rend faux le message
        // posé par loadCalendars (403, expiration) ; il tombe avec le geste.
        if (erreurDesAgendasRef.current) {
          erreurDesAgendasRef.current = false;
          setError(null);
        }
      }
    } catch (err: any) {
      console.error('Failed to load events:', err);
      const msg = err?.message || '';
      const action = classifyCalendarError(msg, {
        fallback: 'Impossible de charger les événements',
        hasCache: hasCachedEvents,
      });
      if (action.error !== null) setError(action.error);
      if (action.staleWarning) setStaleWarning(action.staleWarning);
      if (action.needsReauth !== undefined) setNeedsReauth(action.needsReauth);
    }
  }

  async function handleSync() {
    setSyncing(true);
    setError(null);

    try {
      const result = await api.syncCalendar(currentAccountId || undefined);
      setLastSyncAt(result.synced_at);

      // Reload calendars and events
      await loadCalendars();
      if (currentCalendarId) {
        await loadEvents();
      }
    } catch (err: any) {
      console.error('Failed to sync calendar:', err);
      const msg = err?.message || '';
      const action = classifyCalendarError(msg, { fallback: 'Échec de la synchronisation' });
      if (action.error !== null) setError(action.error);
      if (action.needsReauth !== undefined) setNeedsReauth(action.needsReauth);
    } finally {
      setSyncing(false);
    }
  }

  function handleNewEvent() {
    setCurrentEvent(null);
    setIsEventFormOpen(true);
  }

  async function handleImportICS(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const addNotification = useStatusStore.getState().addNotification;
    try {
      const result = await api.importICSFile(file);
      addNotification({ type: 'success', title: 'Import ICS', message: result.message });
      // Recharger les événements
      await loadCalendars();
      if (currentCalendarId) await loadEvents();
    } catch (err: any) {
      addNotification({ type: 'error', title: 'Erreur import', message: err.message });
    }
    // Reset l'input pour permettre de reimporter le même fichier
    e.target.value = '';
  }

  async function handleExportICS() {
    const addNotification = useStatusStore.getState().addNotification;
    try {
      const blob = await api.exportICSFile(currentCalendarId || undefined);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'therese-calendrier.ics';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      addNotification({ type: 'success', title: 'Export ICS', message: 'Calendrier exporté avec succès' });
    } catch (err: any) {
      addNotification({ type: 'error', title: 'Erreur export', message: err.message });
    }
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

  /** B-238 : choisir une vue est un geste qui RANGE la surface, pas seulement
   *  un changement de `viewMode`. La cascade de rendu donne la priorité à
   *  `currentEventId` (la fiche) : après une création, `EventForm` la pose, et
   *  les quatre boutons ne ramenaient donc jamais la grille — seul l'intitulé
   *  de période changeait. Le formulaire, lui, n'est PAS fermé ici : il porte
   *  une saisie non enregistrée que son propre « Annuler » ne jette qu'après
   *  confirmation. */
  function choisirVue(mode: ModeDeVue) {
    setViewMode(mode);
    setCurrentEvent(null);
  }

  /** Libellé de navigation adapté au mode de vue. La semaine s'écrit en
   *  toutes lettres (« Semaine du 1er au 7 septembre 2026 ») : `month: 'short'`
   *  donnait « 31 août - 6 sept. 2026 », deux abréviations pour une période
   *  qu'on lit à voix haute. Les bornes lundi-dimanche ne changent pas. */
  function getNavLabel(): string {
    if (viewMode === 'day') {
      return capitaleInitiale(
        selectedDate.toLocaleDateString('fr-FR', {
          weekday: 'long',
          day: 'numeric',
          month: 'long',
          year: 'numeric',
        }),
      );
    }
    if (viewMode === 'week') {
      // Calculer lundi et dimanche de la semaine
      const dayOfWeek = selectedDate.getDay();
      const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
      const monday = new Date(selectedDate);
      monday.setDate(selectedDate.getDate() + mondayOffset);
      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);

      const debut = jourDuMois(monday);
      const fin = jourDuMois(sunday);
      if (monday.getFullYear() !== sunday.getFullYear()) {
        return `Semaine du ${debut} ${moisLong(monday)} ${monday.getFullYear()} au ${fin} ${moisLong(sunday)} ${sunday.getFullYear()}`;
      }
      if (monday.getMonth() !== sunday.getMonth()) {
        return `Semaine du ${debut} ${moisLong(monday)} au ${fin} ${moisLong(sunday)} ${sunday.getFullYear()}`;
      }
      return `Semaine du ${debut} au ${fin} ${moisLong(monday)} ${monday.getFullYear()}`;
    }
    // month / list
    return capitaleInitiale(selectedDate.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' }));
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
      if (sondageReauthRef.current) clearInterval(sondageReauthRef.current);
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        if (attempts > 100) {
          clearInterval(poll);
          sondageReauthRef.current = null;
          setReauthing(false);
          setError('La réautorisation Google n’a pas abouti en cinq minutes. Relance-la depuis la bannière.');
          return;
        }
        try {
          const cals = await api.listCalendars(currentAccountId);
          // B-057 : le succès était déduit de l'absence d'exception. Une liste
          // vide, ou qui ne contient que des agendas locaux, éteignait la
          // bannière et arrêtait le sondage sans que Google ait jamais répondu.
          // Même garde qu'aux deux autres sites qui écrivent ce drapeau
          // (BUG-162) : seul un calendrier GOOGLE réellement rendu prouve que le
          // jeton fonctionne.
          if (!cals.some((cal) => cal.provider === 'google')) return;
          clearInterval(poll);
          sondageReauthRef.current = null;
          setNeedsReauth(false);
          setReauthing(false);
          setError(null);
          loadCalendars();
        } catch {
          // Pas encore réautorisé
        }
      }, 3000);
      sondageReauthRef.current = poll;
    } catch (err) {
      console.error('Reauthorize failed:', err);
      setReauthing(false);
    }
  }

  if (!effectiveOpen) return null;

  // Contenu interne partagé entre les deux modes.
  // Une SEULE rangée : les deux barres d'hier (titre et navigation) portaient
  // deux fois la même bordure et coupaient l'écran en trois avant la grille.
  const calendarHeader = (
    <div className="flex flex-wrap items-center gap-3 px-4 pt-4 pb-3 border-b border-border">
      <div className="w-8 h-8 rounded-full bg-accent-tint text-accent flex items-center justify-center shrink-0">
        <CalendarIcon aria-hidden="true" className="w-[18px] h-[18px]" />
      </div>
      <div>
        {/* B-241 : la coque `PrototypeUnifiedViewCanvas` pose déjà le titre de
            la vue, et en fait le nom accessible de la région. Ce libellé reste
            visible mais n'est plus un titre : deux titres de même texte, c'est
            un plan de page qui ment. */}
        <p className="text-lg font-semibold text-text">Agenda</p>
        {currentAccount && (
          <p className="text-sm text-text-muted">{currentAccount.email}</p>
        )}
      </div>

      <div className="flex items-center gap-2">
        <Button variant="secondary" size="icon" onClick={handlePrevious} aria-label="Période précédente" title="Période précédente">
          <ChevronLeft className="w-4 h-4" />
        </Button>
        <Button variant="secondary" size="md" onClick={handleToday}>
          Aujourd'hui
        </Button>
        <Button variant="secondary" size="icon" onClick={handleNext} aria-label="Période suivante" title="Période suivante">
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>

      {/* L'`id` n'est pas décoratif : il nomme les quatre sections de vue par
          `aria-labelledby`, donc le nom suit toujours le libellé affiché. */}
      <h3 id="agenda-periode" className="text-base font-semibold text-text">
        {getNavLabel()}
      </h3>

      {/* BUG-049 : le dropdown passait derrière les autres composants sur Windows/Linux.
          Cause : stacking context bas (body overflow:hidden + conteneur sans z-index).
          Fix : wrapper relative z-[100] force le dropdown au-dessus de toute la pile CSS. */}
      <div className={`relative ${Z_LAYER.ONBOARDING}`}>
        <Select
          aria-label="Agenda affiché"
          value={currentCalendarId || ''}
          onChange={(e) => setCurrentCalendar(e.target.value)}
          options={calendars.map((cal) => ({ value: cal.id, label: cal.summary }))}
        />
      </div>

      {/* L'icône de synchronisation reste rendue dans TOUS les états, y compris
          sous un bandeau qui porte « Réessayer » : c'est le geste permanent de
          la barre d'outils, l'autre est la reprise contextuelle d'un échec. */}
      <Button variant="ghost" size="icon" onClick={handleSync} disabled={syncing} aria-label="Synchroniser l'agenda" title="Synchroniser l'agenda">
        <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
      </Button>

      <Button variant="ghost" size="icon" onClick={() => icsInputRef.current?.click()} aria-label="Importer un fichier .ics" title="Importer un fichier .ics">
        <Upload className="w-4 h-4" />
      </Button>
      <input
        ref={(el) => { icsInputRef.current = el; }}
        type="file"
        accept=".ics"
        className="hidden"
        onChange={handleImportICS}
      />

      <Button variant="ghost" size="icon" onClick={handleExportICS} aria-label="Exporter en .ics" title="Exporter en .ics">
        <Download className="w-4 h-4" />
      </Button>

      {/* `ml-auto` : sans lui le groupe reste collé au sélecteur, pas à droite.
          Sous 840 px il prend une ligne entière sous le titre. */}
      <div className="ml-auto flex flex-wrap gap-2 max-[840px]:basis-full">
        <Segments
          label="Vue de l'agenda"
          options={VUES}
          valeur={viewMode}
          /* `Segments` rend un `id: string` : la table le retraduit en mode de
             vue au lieu d'un cast, qui aurait rendu la garde de typage inerte. */
          onChange={(id) => {
            const vue = VUES.find((v) => v.id === id);
            if (vue) choisirVue(vue.id);
          }}
        />
        <Button variant="primary" size="lg" onClick={handleNewEvent}>
          <Plus aria-hidden="true" className="w-[18px] h-[18px] mr-2" />
          Nouveau rendez-vous
        </Button>
      </div>

      {!standalone && (
        <Button variant="ghost" size="icon" onClick={onClose} aria-label="Fermer l'agenda">
          <X className="w-4 h-4" />
        </Button>
      )}
    </div>
  );

  const reauthBanner = needsReauth ? (
    // Un état dit en deux couleurs se lit comme deux états : tout passe par les
    // jetons d'attention, plus rien par l'ambre d'agent.
    <div className="px-4 py-3 border-b border-border bg-warning-tint flex items-center gap-3">
      <AlertTriangle className="w-4 h-4 text-warning shrink-0" />
      <p className="text-sm text-warning flex-1">
        Connexion Google expirée. Reconnecte-toi pour synchroniser le calendrier.
      </p>
      <Button
        variant="ghost"
        size="md"
        onClick={handleReauthorize}
        disabled={reauthing}
        className="shrink-0"
      >
        {reauthing ? (
          <>
            <Spinner taille="ligne" className="mr-2" />
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

  // Les deux états ne s'excluent pas tout seuls : `loadCalendars` peut laisser
  // une erreur d'agendas (403) et relever `calendarsReady`, pendant que
  // `loadEvents` pose `staleWarning` sans effacer cette erreur. Quand les deux
  // coexistent, un SEUL bandeau les dit tous les deux : ni deux « Réessayer »,
  // ni une péremption tue parce qu'une erreur est plus grave.
  const horodatageDeSync = lastSyncAt
    ? ` (synchronisées le ${new Date(lastSyncAt).toLocaleString('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })})`
    : '';
  const erreurTotale = error && !needsReauth ? error : null;
  const reprise = (variante: 'ghost' | 'secondary') => (
    <Button variant={variante} size="md" onClick={handleSync} disabled={syncing}>
      Réessayer
    </Button>
  );

  let bandeau: React.ReactNode = null;
  if (erreurTotale && staleWarning) {
    bandeau = (
      <div className="px-4 pt-3">
        <Alerte
          data-testid="calendar-stale-warning"
          titre={erreurTotale}
          icone={<AlertTriangle className="w-[18px] h-[18px]" />}
          action={reprise('secondary')}
        >
          {`Données conservées${horodatageDeSync}.`}
        </Alerte>
      </div>
    );
  } else if (staleWarning) {
    bandeau = (
      <div className="px-4 pt-3">
        <Alerte
          data-testid="calendar-stale-warning"
          titre="L'agenda est affiché tel qu'il était."
          icone={<AlertTriangle className="w-[18px] h-[18px]" />}
          action={reprise('ghost')}
        >
          {`Dernier rafraîchissement échoué : données conservées${horodatageDeSync}.`}
        </Alerte>
      </div>
    );
  } else if (erreurTotale) {
    bandeau = (
      <div className="px-4 pt-3">
        <Alerte
          icone={<AlertCircle className="w-[18px] h-[18px]" />}
          action={reprise('secondary')}
        >
          {erreurTotale}
        </Alerte>
      </div>
    );
  }

  // Le pied ne se rend QUE sur la grille, et seulement s'il existe un agenda
  // courant : sur une liste vide (premier lancement, BUG-143), annoncer
  // « aucun agenda en ligne branché » nommerait une absence là où il n'y a
  // aucun agenda du tout.
  const agendaCourant = calendars.find((cal) => cal.id === currentCalendarId);
  const aucunAgendaEnLigne =
    calendars.length > 0 && !calendars.some((cal) => cal.provider !== 'local');
  const piedDeGrille = agendaCourant ? (
    <p className="shrink-0 text-xs font-medium text-text-muted">
      {agendaCourant.provider === 'local'
        ? `Agenda local « ${agendaCourant.summary} »`
        : agendaCourant.summary}
      {aucunAgendaEnLigne ? ' · aucun agenda en ligne branché' : ''}
    </p>
  ) : null;

  const calendarContent = (
    <>
      {bandeau}

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {loading ? (
          <div className="h-full p-4 space-y-2">
            {[0, 1, 2].map((rangee) => (
              <div key={rangee} className="flex items-center gap-2">
                <Squelette classeBarre="h-8 rounded-sm" largeur="w-8" />
                {/* `flex-1` porteur : la racine de `Squelette` n'a pas de
                    largeur propre, et un `w-[60%]` contre une largeur de
                    contenu se résout à zéro pixel. */}
                <Squelette className="flex-1" classeBarre="h-8 rounded-sm" largeur="w-[60%]" />
              </div>
            ))}
            <p role="status" className="text-sm text-text-muted">Chargement de l'agenda…</p>
          </div>
        ) : isEventFormOpen ? (
          <EventForm />
        ) : currentEventId ? (
          <EventDetail />
        ) : (
          // Conteneur PROPRE à la branche « grille » : le formulaire, la fiche
          // et le chargement gardent leurs paddings et n'en héritent pas un second.
          <div className="h-full flex flex-col gap-2 p-4">
            <CalendarView />
            {piedDeGrille}
          </div>
        )}
      </div>
    </>
  );

  // Mode standalone : pleine page
  if (standalone) {
    // flex-1 min-h-0, pas h-full : la back-bar « Chat » du conteneur de vue
    // ferait déborder le panneau de sa hauteur (cf. bug EmailPanel 11/06).
    return (
      <div data-testid="calendar-panel" className="flex-1 min-h-0 flex flex-col bg-bg">
        {calendarHeader}
        {reauthBanner}
        {calendarContent}
      </div>
    );
  }

  // Mode modal
  return (
    <AnimatePresence>
      <div data-testid="calendar-panel" className={`fixed inset-0 ${Z_LAYER.MODAL} flex items-center justify-center`}>
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-bg/80 backdrop-blur-md"
          onClick={onClose}
        />

        {/* Panel */}
        <motion.div
          ref={dialogRef}
          role="dialog"
          aria-modal="true"
          aria-label="Agenda"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="relative w-full h-full max-w-7xl max-h-[90vh] mx-4 bg-surface/95 backdrop-blur-xl border border-border/50 rounded-md shadow-2xl overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {calendarHeader}
          {reauthBanner}
          {calendarContent}
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
