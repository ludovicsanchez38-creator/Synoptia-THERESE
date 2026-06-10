/**
 * THÉRÈSE v2 - ToolConfirmationCard (US-002)
 *
 * Affiche les actions sensibles (ex. envoi d'email) en attente de validation.
 * Le backend ne les exécute jamais seul : l'utilisateur confirme ici, et
 * l'exécution réelle a lieu via POST /api/chat/confirm-tool.
 */
import { useState } from 'react';
import { Mail, Send, X, Loader2 } from 'lucide-react';
import {
  useToolConfirmationStore,
  type PendingConfirmation,
} from '../../stores/toolConfirmationStore';
import { confirmTool } from '../../services/api/chat';
import { useChatStore } from '../../stores/chatStore';
import { Button } from '../ui/Button';

export function ToolConfirmationCard() {
  const pending = useToolConfirmationStore((s) => s.pending);
  if (pending.length === 0) return null;
  return (
    <div className="space-y-2 px-4 py-2">
      {pending.map((c) => (
        <ConfirmationItem key={c.confirmation_id} confirmation={c} />
      ))}
    </div>
  );
}

function ConfirmationItem({ confirmation }: { confirmation: PendingConfirmation }) {
  const [busy, setBusy] = useState<'send' | 'cancel' | null>(null);
  const remove = useToolConfirmationStore((s) => s.remove);
  const addMessage = useChatStore((s) => s.addMessage);

  const to = String(confirmation.arguments.to ?? '');
  const subject = String(confirmation.arguments.subject ?? '');
  const body = String(confirmation.arguments.body ?? '');

  const handle = async (approved: boolean) => {
    setBusy(approved ? 'send' : 'cancel');
    try {
      const res = await confirmTool(confirmation.confirmation_id, approved);
      if (approved) {
        addMessage({ role: 'assistant', content: res.result || 'Email envoyé.' });
      }
    } catch (e) {
      addMessage({
        role: 'assistant',
        content: `Erreur lors de l'envoi : ${e instanceof Error ? e.message : 'inconnue'}`,
      });
    } finally {
      remove(confirmation.confirmation_id);
      setBusy(null);
    }
  };

  return (
    <div
      className="rounded-lg border border-accent-cyan/30 bg-surface p-3"
      data-testid="tool-confirmation"
    >
      <div className="flex items-center gap-2 mb-2 text-accent-cyan">
        <Mail className="w-4 h-4" />
        <span className="text-sm font-medium text-text">Confirmer l'envoi de l'email</span>
      </div>
      <dl className="text-xs text-text-muted space-y-1 mb-3">
        <div>
          <span className="text-text-muted/70">À : </span>
          <span className="text-text">{to}</span>
        </div>
        <div>
          <span className="text-text-muted/70">Objet : </span>
          <span className="text-text">{subject}</span>
        </div>
        <div className="whitespace-pre-wrap">
          <span className="text-text-muted/70">Message : </span>
          <span className="text-text">{body}</span>
        </div>
      </dl>
      <div className="flex gap-2">
        <Button
          variant="primary"
          size="sm"
          onClick={() => handle(true)}
          disabled={busy !== null}
        >
          {busy === 'send' ? (
            <Loader2 className="w-4 h-4 mr-1 animate-spin" />
          ) : (
            <Send className="w-4 h-4 mr-1" />
          )}
          Envoyer
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => handle(false)}
          disabled={busy !== null}
        >
          <X className="w-4 h-4 mr-1" />
          Annuler
        </Button>
      </div>
    </div>
  );
}
