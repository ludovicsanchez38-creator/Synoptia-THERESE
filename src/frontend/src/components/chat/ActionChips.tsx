/**
 * THÉRÈSE v2 - Puces d'actions déterministes (tranche 1c, 10/07/2026).
 *
 * Affichées au-dessus de l'input quand la conversation est vide : un clic
 * insère la syntaxe {action: ...} dans le champ - l'utilisateur voit ce qui
 * part, peut compléter le sujet, puis envoie. L'exécution est locale
 * (allowlist backend), le LLM n'est sollicité que pour rédiger le contenu
 * des documents produits.
 */
import { Mail, Users, FileText, FileSpreadsheet } from 'lucide-react';

const CHIPS = [
  { label: "Ouvrir l'email", insert: '{action: ouvrir email}', Icon: Mail },
  { label: 'Ouvrir le CRM', insert: '{action: ouvrir crm}', Icon: Users },
  {
    label: 'Document Word',
    insert: '{action: produire docx "sujet du document"}',
    Icon: FileText,
  },
  {
    label: 'Tableur Excel',
    insert: '{action: produire xlsx "sujet du tableur"}',
    Icon: FileSpreadsheet,
  },
] as const;

export function ActionChips({ onInsert }: { onInsert: (text: string) => void }) {
  return (
    <div className="flex flex-wrap gap-1.5 px-1 pb-2" aria-label="Actions rapides">
      {CHIPS.map(({ label, insert, Icon }) => (
        <button
          key={label}
          type="button"
          onClick={() => onInsert(insert)}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs text-text-muted bg-surface-2 border border-border hover:border-accent-cyan/50 hover:text-text transition-all"
        >
          <Icon className="w-3 h-3 shrink-0" />
          {label}
        </button>
      ))}
    </div>
  );
}
