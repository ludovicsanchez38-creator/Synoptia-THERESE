import { useMemo, useState } from 'react';
import { FileDown, History, MessageSquare, MoreHorizontal, Pencil, Plus, Search, Trash2, X } from 'lucide-react';
import { motion } from 'framer-motion';
import { useChatStore, type Conversation } from '../../stores/chatStore';
import {
  deleteConversation as deleteConversationRemote,
  exportConversation,
  renameConversation as renameConversationRemote,
} from '../../services/api/chat';

interface PrototypeConversationDrawerProps {
  onClose: () => void;
  onOpenChat: () => void;
  navigationLocked?: boolean;
}

function dateLabel(date: Date): string {
  const value = new Date(date);
  if (Number.isNaN(value.getTime())) return 'Date inconnue';

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const day = new Date(value.getFullYear(), value.getMonth(), value.getDate());
  const distance = Math.round((today.getTime() - day.getTime()) / 86_400_000);

  if (distance === 0) return 'Aujourd’hui';
  if (distance === 1) return 'Hier';
  if (distance > 1 && distance < 7) return 'Cette semaine';
  return value.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });
}

function updatedLabel(date: Date): string {
  const value = new Date(date);
  if (Number.isNaN(value.getTime())) return 'Date inconnue';
  return value.toLocaleString('fr-FR', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function groupConversations(conversations: Conversation[]): Array<[string, Conversation[]]> {
  const groups = new Map<string, Conversation[]>();
  conversations.forEach((conversation) => {
    const label = dateLabel(conversation.updatedAt);
    groups.set(label, [...(groups.get(label) ?? []), conversation]);
  });
  return [...groups.entries()];
}

export function PrototypeConversationDrawer({
  onClose,
  onOpenChat,
  navigationLocked = false,
}: PrototypeConversationDrawerProps) {
  const [query, setQuery] = useState('');
  const [menuId, setMenuId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [deleteConfirmationId, setDeleteConfirmationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const conversations = useChatStore((state) => state.conversations);
  const currentConversationId = useChatStore((state) => state.currentConversationId);
  const createConversation = useChatStore((state) => state.createConversation);
  const loadConversation = useChatStore((state) => state.loadConversation);
  const renameConversation = useChatStore((state) => state.renameConversation);
  const deleteConversation = useChatStore((state) => state.deleteConversation);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase('fr-FR');
    return [...conversations]
      .filter((conversation) => !normalized || conversation.title.toLocaleLowerCase('fr-FR').includes(normalized))
      .sort((left, right) => new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime());
  }, [conversations, query]);
  const grouped = useMemo(() => groupConversations(filtered), [filtered]);

  const rejectLockedNavigation = () => {
    if (!navigationLocked) return false;
    setError('Arrête la réponse en cours avant de changer de conversation.');
    return true;
  };

  const startConversation = () => {
    if (rejectLockedNavigation()) return;
    createConversation();
    onClose();
    onOpenChat();
  };

  const openConversation = (id: string) => {
    if (rejectLockedNavigation()) return;
    loadConversation(id);
    onClose();
    onOpenChat();
  };

  const saveTitle = async (conversation: Conversation) => {
    const title = editingTitle.trim();
    setEditingId(null);
    if (!title || title === conversation.title) return;
    const previous = conversation.title;
    renameConversation(conversation.id, title);
    try {
      await renameConversationRemote(conversation.id, title);
    } catch {
      renameConversation(conversation.id, previous);
      setError('Le renommage n’a pas pu être enregistré.');
    }
  };

  const confirmDelete = async (conversation: Conversation) => {
    try {
      if (conversation.synced) await deleteConversationRemote(conversation.id);
      deleteConversation(conversation.id);
      setDeleteConfirmationId(null);
      setMenuId(null);
    } catch {
      setError('La conversation n’a pas pu être supprimée.');
    }
  };

  return (
    <motion.aside
      initial={{ x: -24, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: -24, opacity: 0 }}
      transition={{ duration: 0.18 }}
      className="absolute inset-y-0 left-16 z-30 flex w-[306px] flex-col border-r border-border bg-surface shadow-[12px_0_40px_rgba(16,28,54,0.10)]"
      data-testid="prototype-conversation-drawer"
    >
      <div className="flex h-14 shrink-0 items-center justify-between border-b border-border px-4">
        <span className="text-sm font-semibold text-text">Conversations</span>
        <button type="button" onClick={onClose} aria-label="Fermer les conversations" className="grid h-8 w-8 place-items-center rounded-[9px] text-text-muted hover:bg-bg hover:text-text">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="shrink-0 p-3">
        <button
          type="button"
          onClick={startConversation}
          className="mb-3 flex w-full items-center justify-center gap-2 rounded-[10px] border border-text bg-text px-3 py-2.5 text-sm font-semibold text-white shadow-[2px_2px_0_#22D3EE]"
        >
          <Plus className="h-4 w-4" />
          Nouvelle conversation
        </button>
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-text-muted" />
          <input
            aria-label="Rechercher une conversation"
            placeholder="Rechercher…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="w-full rounded-[10px] border border-border bg-surface-2 py-2 pl-9 pr-3 text-sm text-text outline-none focus:border-[#22D3EE]"
          />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-3 pb-3" data-testid="prototype-conversation-list">
        {error && <div role="alert" className="mb-2 rounded-[8px] border border-error/40 bg-[var(--color-error-tint)] px-3 py-2 text-xs text-error">{error}</div>}
        {filtered.length === 0 ? (
          <div className="flex min-h-40 flex-col items-center justify-center px-5 text-center text-text-muted">
            <MessageSquare className="mb-2 h-7 w-7 opacity-50" />
            <p className="text-sm font-medium">{query ? 'Aucune conversation trouvée' : 'Aucune conversation enregistrée'}</p>
            {!query && <p className="mt-1 text-xs leading-5">Commence une conversation pour la retrouver ici.</p>}
          </div>
        ) : grouped.map(([label, items]) => (
          <section key={label} className="mb-4">
            <div className="mb-1 flex items-center gap-1.5 px-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-text-muted">
              <History className="h-3 w-3" />
              {label}
            </div>
            {items.map((conversation) => (
              <div key={conversation.id} className="relative mb-1">
                {editingId === conversation.id ? (
                  <div className="rounded-[9px] border border-[#22D3EE] bg-surface p-2">
                    <input autoFocus aria-label="Nouveau titre" value={editingTitle} maxLength={120} onChange={(event) => setEditingTitle(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') void saveTitle(conversation); if (event.key === 'Escape') setEditingId(null); }} className="w-full rounded-[7px] border border-border px-2 py-1.5 text-sm text-text outline-none" />
                    <div className="mt-2 flex justify-end gap-2"><button type="button" onClick={() => setEditingId(null)} className="text-[10px] font-semibold text-text-muted">Annuler</button><button type="button" onClick={() => void saveTitle(conversation)} className="rounded-[6px] bg-text px-2 py-1 text-[10px] font-semibold text-white">Enregistrer</button></div>
                  </div>
                ) : deleteConfirmationId === conversation.id ? (
                  <div className="rounded-[9px] border border-error/40 bg-[var(--color-error-tint)] p-3 text-xs text-error" data-testid="conversation-delete-confirmation"><strong>Supprimer définitivement cette conversation ?</strong><div className="mt-2 flex justify-end gap-2"><button type="button" onClick={() => setDeleteConfirmationId(null)} className="rounded-[6px] bg-surface px-2 py-1 font-semibold">Annuler</button><button type="button" onClick={() => void confirmDelete(conversation)} className="rounded-[6px] bg-[#A61B1B] px-2 py-1 font-semibold text-white">Confirmer la suppression</button></div></div>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={() => openConversation(conversation.id)}
                      className={`w-full rounded-[9px] border px-3 py-2.5 pr-10 text-left transition-colors ${
                        currentConversationId === conversation.id
                          ? 'border-[#BDE8EF] bg-accent-tint'
                          : 'border-transparent hover:border-border hover:bg-surface-2'
                      }`}
                    >
                      <span className="block truncate text-sm font-semibold text-text">{conversation.title || 'Nouvelle conversation'}</span>
                      <span className="mt-0.5 flex items-center justify-between gap-2 text-[10px] text-text-muted">
                        <span>{updatedLabel(conversation.updatedAt)}</span>
                        <span>{conversation.messages.length || conversation.messageCount || 0} message{(conversation.messages.length || conversation.messageCount || 0) > 1 ? 's' : ''}</span>
                      </span>
                    </button>
                    <button type="button" aria-label={`Actions pour ${conversation.title}`} onClick={() => setMenuId(menuId === conversation.id ? null : conversation.id)} className="absolute right-2 top-2 grid h-7 w-7 place-items-center rounded-[7px] text-text-muted hover:bg-surface"><MoreHorizontal className="h-4 w-4" /></button>
                    {menuId === conversation.id && <div className="absolute right-2 top-9 z-10 w-44 rounded-[9px] border border-border bg-surface py-1 shadow-xl" data-testid="conversation-actions-menu"><button type="button" onClick={() => { setEditingId(conversation.id); setEditingTitle(conversation.title); setMenuId(null); }} className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-text hover:bg-surface-2"><Pencil className="h-3.5 w-3.5" />Renommer</button><button type="button" onClick={() => void exportConversation(conversation.id, 'md').catch(() => setError('L’export Markdown a échoué.'))} className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-text hover:bg-surface-2"><FileDown className="h-3.5 w-3.5" />Exporter en Markdown</button><button type="button" onClick={() => void exportConversation(conversation.id, 'docx').catch(() => setError('L’export Word a échoué.'))} className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-text hover:bg-surface-2"><FileDown className="h-3.5 w-3.5" />Exporter en Word</button><button type="button" onClick={() => { setDeleteConfirmationId(conversation.id); setMenuId(null); }} className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-error hover:bg-[var(--color-error-tint)]"><Trash2 className="h-3.5 w-3.5" />Supprimer</button></div>}
                  </>
                )}
              </div>
            ))}
          </section>
        ))}
      </div>
    </motion.aside>
  );
}
