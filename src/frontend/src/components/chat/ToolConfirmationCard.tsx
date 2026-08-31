/** Confirmation humaine des mutations préparées par le chat. */
import { useState, type ReactNode } from 'react';
import { Calendar, Check, Mail, Send, Shield, X } from 'lucide-react';
import {
  useToolConfirmationStore,
  type PendingConfirmation,
} from '../../stores/toolConfirmationStore';
import { confirmTool } from '../../services/api/chat';
import { useChatStore } from '../../stores/chatStore';
import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';

export function ToolConfirmationCard() {
  const pending = useToolConfirmationStore((state) => state.pending);
  if (pending.length === 0) return null;
  return <div className="space-y-2 px-4 py-2">{pending.map((confirmation) => <ConfirmationItem key={confirmation.confirmation_id} confirmation={confirmation} />)}</div>;
}

function baseToolName(toolName: string): string {
  return toolName.includes('__') ? toolName.split('__', 2)[1] : toolName;
}

function value(argumentsValue: Record<string, unknown>, key: string): string {
  return String(argumentsValue[key] ?? '');
}

function Detail({ label, children }: { label: string; children: ReactNode }) {
  if (!children) return null;
  return <div><dt className="inline text-text-muted/70">{label} : </dt><dd className="inline whitespace-pre-wrap text-text">{children}</dd></div>;
}

function CalendarDetails({ confirmation }: { confirmation: PendingConfirmation }) {
  const args = confirmation.arguments;
  const destination = (args._confirmation_destination || {}) as Record<string, unknown>;
  const attendees = value(args, 'attendees');
  const provider = value(destination, 'provider');
  const account = value(destination, 'account');
  const willCreateCalendar = Boolean(destination.will_create_calendar);
  return (
    <dl className="mb-3 space-y-1 text-xs text-text-muted">
      <Detail label="Événement">{value(args, 'summary')}</Detail>
      <Detail label="Début">{value(args, 'start')}</Detail>
      <Detail label="Fin">{value(args, 'end')}</Detail>
      <Detail label="Fuseau">{value(args, 'timezone') || 'Europe/Paris'}</Detail>
      <Detail label="Calendrier">{value(destination, 'calendar_name') || 'Destination à vérifier'}</Detail>
      {/* Campagne cinq personas : Inès a validé « Séance Martin » en lisant
          « Mon calendrier », sans qu'on lui dise que la ligne serait visible
          depuis le dossier d'un autre patient. Le leak était CONSENTI, donc
          pire : elle avait lu, et ce qu'on lui montrait était incomplet.
          Avouer avant de réparer — le cloisonnement de l'agenda vient après. */}
      <p className="pt-1 text-xs leading-4 text-warning">
        Cet agenda est commun à tous tes dossiers : l’événement sera visible
        depuis n’importe quelle conversation.
      </p>
      <Detail label="Fournisseur">{provider === 'google' ? 'Google Calendar' : provider === 'caldav' ? 'CalDAV' : 'Local'}</Detail>
      {account && <Detail label="Compte">{account}</Detail>}
      {attendees && <Detail label="Participants">{attendees}</Detail>}
      {value(args, 'location') && <Detail label="Lieu">{value(args, 'location')}</Detail>}
      {value(args, 'description') && <Detail label="Description">{value(args, 'description')}</Detail>}
      {willCreateCalendar && <div className="mt-2 rounded-md border border-agent-amber/30 bg-agent-amber/10 p-2 text-agent-amber">Aucun calendrier local n’existe encore. La confirmation créera aussi « Mon calendrier ».</div>}
    </dl>
  );
}

function EmailDetails({ confirmation }: { confirmation: PendingConfirmation }) {
  const args = confirmation.arguments;
  const destination = (args._confirmation_destination || {}) as Record<string, unknown>;
  const expediteur = value(destination, 'account');
  const erreurDestination = value(destination, 'error');
  return (
    <dl className="mb-3 space-y-1 text-xs text-text-muted">
      {/* Finding 1 (30/08) : sans l'expéditeur, on confirmait un envoi
          dont on ne savait pas DE QUEL compte il partait. */}
      {expediteur && <Detail label="De">{expediteur}</Detail>}
      {erreurDestination && (
        <div className="mt-1 rounded-md border border-error/30 bg-error/10 p-2 text-error">{erreurDestination}</div>
      )}
      <Detail label="À">{value(args, 'to')}</Detail>
      <Detail label="Objet">{value(args, 'subject')}</Detail>
      <Detail label="Message">{value(args, 'body')}</Detail>
    </dl>
  );
}

function GenericDetails({ confirmation }: { confirmation: PendingConfirmation }) {
  // Passe 4 : hors e-mail et agenda, la carte empruntait le titre « envoi
  // de l'email » et des champs vides. Confirmer à l'aveugle. On montre le
  // nom réel et les arguments, sans les clés internes (_confirmation_*).
  const entries = Object.entries(confirmation.arguments).filter(
    ([key]) => !key.startsWith('_'),
  );
  return (
    <dl className="mb-3 space-y-1 text-xs text-text-muted">
      <Detail label="Outil">{confirmation.tool_name}</Detail>
      {entries.map(([key, raw]) => (
        <Detail key={key} label={key}>
          {raw == null ? '' : typeof raw === 'string' ? raw : JSON.stringify(raw)}
        </Detail>
      ))}
    </dl>
  );
}

function ConfirmationItem({ confirmation }: { confirmation: PendingConfirmation }) {
  const [busy, setBusy] = useState<'approve' | 'cancel' | null>(null);
  const remove = useToolConfirmationStore((state) => state.remove);
  const addMessage = useChatStore((state) => state.addMessage);
  const toolName = baseToolName(confirmation.tool_name);
  const isCalendar = toolName === 'create_calendar_event';
  const isEmail = toolName === 'send_email';
  const title = isCalendar
    ? 'Confirmer la création du rendez-vous'
    : isEmail
      ? 'Confirmer l’envoi de l’email'
      : `Confirmer l’action ${confirmation.tool_name}`;

  async function handle(approved: boolean) {
    setBusy(approved ? 'approve' : 'cancel');
    try {
      const response = await confirmTool(confirmation.confirmation_id, approved);
      if (approved) {
        const fichiers = response.skill_files ?? [];
        addMessage({
          role: 'assistant',
          content: response.result || (isCalendar ? 'Rendez-vous créé.' : isEmail ? 'Email envoyé.' : 'Action exécutée.'),
          skillFile: fichiers[0],
          skillFiles: fichiers.length > 0 ? fichiers : undefined,
        });
      }
    } catch (error) {
      addMessage({
        role: 'assistant',
        content: `Erreur lors de l’action : ${error instanceof Error ? error.message : 'inconnue'}`,
      });
    } finally {
      remove(confirmation.confirmation_id);
      setBusy(null);
    }
  }

  return (
    <div className="rounded-md border border-accent-cyan/30 bg-surface p-3" data-testid="tool-confirmation">
      <div className="mb-2 flex items-center gap-2 text-accent-cyan-ink">
        {isCalendar ? <Calendar className="h-4 w-4" /> : isEmail ? <Mail className="h-4 w-4" /> : <Shield className="h-4 w-4" />}
        <span className="text-sm font-medium text-text">{title}</span>
      </div>
      {isCalendar ? <CalendarDetails confirmation={confirmation} /> : isEmail ? <EmailDetails confirmation={confirmation} /> : <GenericDetails confirmation={confirmation} />}
      <div className="flex gap-2">
        <Button variant="primary" size="sm" onClick={() => void handle(true)} disabled={busy !== null}>
          {busy === 'approve' ? <Spinner taille="bouton" className="mr-1" /> : isCalendar ? <Check className="mr-1 h-4 w-4" /> : isEmail ? <Send className="mr-1 h-4 w-4" /> : <Check className="mr-1 h-4 w-4" />}
          {isCalendar ? 'Créer' : isEmail ? 'Envoyer' : 'Confirmer'}
        </Button>
        <Button variant="ghost" size="sm" onClick={() => void handle(false)} disabled={busy !== null}>
          <X className="mr-1 h-4 w-4" />
          Annuler
        </Button>
      </div>
    </div>
  );
}
