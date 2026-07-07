/**
 * THÉRÈSE v2 - QuickActions : lanceur d'actions rapides depuis le registre unique.
 *
 * « Rédiger un document » (D4) déclenche `documents.new` (atelier
 * documentaire : trame + sections, D2-D3) - à distinguer de « Produire un
 * document » (`guided.open`, Skills Office DOCX/PPTX/XLSX). Icône `FileStack`
 * pour cohérence avec le bouton Documents de l'en-tête et la palette ⌘K.
 */
import { MessageSquarePlus, FileText, FileStack, UserPlus, Receipt } from 'lucide-react';
import { runAction } from '../../lib/actionRegistry';
import { useNavigationStore } from '../../stores/navigationStore';

const ACTIONS: { id: string; label: string; icon: React.ElementType }[] = [
  { id: 'chat.new', label: 'Nouvelle conversation', icon: MessageSquarePlus },
  { id: 'guided.open', label: 'Produire un document', icon: FileText },
  { id: 'documents.new', label: 'Rédiger un document', icon: FileStack },
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
      {ACTIONS.map(({ id, label, icon: Icon }, i) => (
        <button
          key={id}
          type="button"
          onClick={() => handle(id)}
          className="card-brutal flex items-center gap-2.5 p-3 rounded-[9px] bg-surface border-[1.5px] border-border text-left"
        >
          {/* Pastille duotone : accent catégoriel k1-k4, cerclée d'encre */}
          <span
            className="w-8 h-8 rounded-[6px] grid place-items-center shrink-0 border-[1.5px] border-[var(--btn-ink)]"
            style={{ background: `var(--k${(i % 4) + 1}bg)`, color: `var(--k${(i % 4) + 1})` }}
          >
            <Icon className="w-4 h-4" />
          </span>
          <span className="text-[13px] font-medium text-text leading-tight">{label}</span>
        </button>
      ))}
    </div>
  );
}
