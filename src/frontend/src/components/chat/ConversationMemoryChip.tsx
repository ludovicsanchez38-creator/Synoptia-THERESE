/**
 * THÉRÈSE v2 - Pastille de glance (L6, revue produit)
 *
 * Signal de contexte léger, EN LECTURE SEULE, dans le fil de chat :
 * « N contacts liés à cette conversation ». Honore le principe « mémoire
 * visible » sans rouvrir un tiroir concurrent (verdict panel UX/UI L6).
 * Une seule action : cliquer pour ouvrir la vue Mémoire.
 */

import { useEffect, useMemo } from 'react';
import { Users } from 'lucide-react';
import { useContactsStore } from '../../stores/contactsStore';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';

export function ConversationMemoryChip() {
  const conversationId = useChatStore((s) => s.currentConversationId);
  const contacts = useContactsStore((s) => s.contacts);
  const fetchContacts = useContactsStore((s) => s.fetchContacts);
  // B-056 : le store POSE une erreur de lecture, la pastille la jetait. Sans
  // elle, « aucun contact lié » et « contacts non lus » s'affichaient pareil,
  // c'est-à-dire pas du tout.
  const erreurLecture = useContactsStore((s) => s.error);

  // Chargement paresseux : si le store n'a pas encore les contacts (l'utilisateur
  // n'a ouvert ni Mémoire ni CRM), on les charge une fois pour alimenter la pastille.
  useEffect(() => {
    if (contacts.length === 0) {
      fetchContacts().catch(() => undefined);
    }
    // volontairement au montage uniquement
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const linked = useMemo(
    () =>
      conversationId
        ? contacts.filter((c) => c.scope === 'conversation' && c.scope_id === conversationId)
        : [],
    [contacts, conversationId]
  );

  if (!conversationId) return null;

  if (linked.length === 0) {
    if (!erreurLecture) return null;
    // Ne rien dire ici, c'est affirmer qu'aucun contact n'est lié.
    return (
      <div className="px-4 py-1.5">
        <span
          role="alert"
          className="inline-flex items-center gap-1.5 rounded-sm border border-warning/40 bg-warning/10 px-2.5 py-1 text-sm text-warning"
        >
          <Users className="h-3.5 w-3.5" />
          Contacts non lus : le lien avec cette conversation est inconnu.
        </span>
      </div>
    );
  }

  const n = linked.length;
  const label = `${n} contact${n > 1 ? 's' : ''} lié${n > 1 ? 's' : ''} à cette conversation`;

  return (
    <div className="px-4 py-1.5">
      <button
        type="button"
        onClick={() => useNavigationStore.getState().setView('memory')}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-sm text-sm text-text-muted hover:text-accent-cyan-ink bg-surface/40 hover:bg-surface/70 border border-border/40 transition-colors"
        title="Voir dans la Mémoire"
      >
        <Users className="w-3.5 h-3.5" />
        <span>{label}</span>
      </button>
    </div>
  );
}
