/** Confirmation humaine des mutations préparées par le chat. */
import { useState, type ReactNode } from 'react';
import { Calendar, Check, Loader2, Mail, Send, X } from 'lucide-react';
import {
  useToolConfirmationStore,
  type PendingConfirmation,
} from '../../stores/toolConfirmationStore';
import { confirmTool } from '../../services/api/chat';
import { useChatStore } from '../../stores/chatStore';
import { Button } from '../ui/Button';

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
      <Detail label="Fournisseur">{provider === 'google' ? 'Google Calendar' : provider === 'caldav' ? 'CalDAV' : 'Local'}</Detail>
      {account && <Detail label="Compte">{account}</Detail>}
      {attendees && <Detail label="Participants">{attendees}</Detail>}
      {value(args, 'location') && <Detail label="Lieu">{value(args, 'location')}</Detail>}
      {value(args, 'description') && <Detail label="Description">{value(args, 'description')}</Detail>}
      {willCreateCalendar && <div className="mt-2 rounded-md border border-amber-400/30 bg-amber-400/10 p-2 text-amber-200">Aucun calendrier local n’existe encore. La confirmation créera aussi « Mon calendrier ».</div>}
    </dl>
  );
}

function EmailDetails({ confirmation }: { confirmation: PendingConfirmation }) {
  const args = confirmation.arguments;
  return (
    <dl className="mb-3 space-y-1 text-xs text-text-muted">
      <Detail label="À">{value(args, 'to')}</Detail>
      <Detail label="Objet">{value(args, 'subject')}</Detail>
      <Detail label="Message">{value(args, 'body')}</Detail>
    </dl>
  );
}

function ConfirmationItem({ confirmation }: { confirmation: PendingConfirmation }) {
  const [busy, setBusy] = useState<'approve' | 'cancel' | null>(null);
  const remove = useToolConfirmationStore((state) => state.remove);
  const addMessage = useChatStore((state) => state.addMessage);
  const toolName = baseToolName(confirmation.tool_name);
  const isCalendar = toolName === 'create_calendar_event';
  const title = isCalendar ? 'Confirmer la création du rendez-vous' : 'Confirmer l’envoi de l’email';

  async function handle(approved: boolean) {
    setBusy(approved ? 'approve' : 'cancel');
    try {
      const response = await confirmTool(confirmation.confirmation_id, approved);
      if (approved) {
        addMessage({
          role: 'assistant',
          content: response.result || (isCalendar ? 'Rendez-vous créé.' : 'Email envoyé.'),
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
    <div className="rounded-lg border border-accent-cyan/30 bg-surface p-3" data-testid="tool-confirmation">
      <div className="mb-2 flex items-center gap-2 text-accent-cyan">
        {isCalendar ? <Calendar className="h-4 w-4" /> : <Mail className="h-4 w-4" />}
        <span className="text-sm font-medium text-text">{title}</span>
      </div>
      {isCalendar ? <CalendarDetails confirmation={confirmation} /> : <EmailDetails confirmation={confirmation} />}
      <div className="flex gap-2">
        <Button variant="primary" size="sm" onClick={() => void handle(true)} disabled={busy !== null}>
          {busy === 'approve' ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : isCalendar ? <Check className="mr-1 h-4 w-4" /> : <Send className="mr-1 h-4 w-4" />}
          {isCalendar ? 'Créer' : 'Envoyer'}
        </Button>
        <Button variant="ghost" size="sm" onClick={() => void handle(false)} disabled={busy !== null}>
          <X className="mr-1 h-4 w-4" />
          Annuler
        </Button>
      </div>
    </div>
  );
}
