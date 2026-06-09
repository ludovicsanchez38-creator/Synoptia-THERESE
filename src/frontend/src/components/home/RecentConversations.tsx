/**
 * THERESE v2 - RecentConversations : reprendre une conversation recente.
 */
import { MessageSquare } from 'lucide-react';
import { useChatStore, type Conversation } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';

/** Pure : conversations non vides, non ephemeres, triees recentes d'abord, top N. */
export function selectRecentConversations(conversations: Conversation[], limit: number): Conversation[] {
  return [...conversations]
    .filter((c) => !c.ephemeral && c.messages.length > 0)
    .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
    .slice(0, limit);
}

export function RecentConversations() {
  const conversations = useChatStore((s) => s.conversations);
  const loadConversation = useChatStore((s) => s.loadConversation);
  const recent = selectRecentConversations(conversations, 5);

  function open(id: string) {
    loadConversation(id);
    useNavigationStore.getState().setView('chat');
  }

  return (
    <section className="bg-surface border border-border rounded-xl p-5 shadow-[var(--shadow-sm)]">
      <h2 className="text-base font-bold text-text mb-4">Reprendre une conversation</h2>
      {recent.length === 0 ? (
        <p className="text-sm text-text-muted py-2">Aucune conversation pour l'instant.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {recent.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                onClick={() => open(c.id)}
                className="w-full flex items-center gap-3 p-2.5 rounded-lg border border-border bg-surface-2 hover:border-[color-mix(in_srgb,var(--color-accent)_40%,var(--color-border))] transition-colors text-left"
              >
                <MessageSquare className="w-4 h-4 text-accent shrink-0" />
                <span className="text-sm text-text truncate flex-1">{c.title || 'Sans titre'}</span>
                <span className="text-xs text-text-muted shrink-0">
                  {new Date(c.updatedAt).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
