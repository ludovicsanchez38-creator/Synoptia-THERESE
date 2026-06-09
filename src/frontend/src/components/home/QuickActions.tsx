/**
 * THÉRÈSE v2 - QuickActions : lanceur d'actions rapides depuis le registre unique.
 */
import { MessageSquarePlus, FileText, UserPlus, Receipt } from 'lucide-react';
import { runAction } from '../../lib/actionRegistry';
import { useNavigationStore } from '../../stores/navigationStore';

const ACTIONS: { id: string; label: string; icon: React.ElementType }[] = [
  { id: 'chat.new', label: 'Nouvelle conversation', icon: MessageSquarePlus },
  { id: 'guided.open', label: 'Produire un document', icon: FileText },
  { id: 'contact.new', label: 'Ajouter un contact', icon: UserPlus },
  { id: 'invoices.open', label: 'Factures', icon: Receipt },
];

export function QuickActions() {
  function handle(id: string) {
    runAction(id);
    if (id === 'chat.new') useNavigationStore.getState().setView('chat');
  }
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {ACTIONS.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          type="button"
          onClick={() => handle(id)}
          className="flex items-center gap-2.5 p-3 rounded-xl bg-surface border border-border text-left hover:border-[color-mix(in_srgb,var(--color-accent)_40%,var(--color-border))] transition-colors"
        >
          <span className="w-8 h-8 rounded-lg grid place-items-center bg-accent-tint text-accent shrink-0">
            <Icon className="w-4 h-4" />
          </span>
          <span className="text-[13px] font-medium text-text leading-tight">{label}</span>
        </button>
      ))}
    </div>
  );
}
