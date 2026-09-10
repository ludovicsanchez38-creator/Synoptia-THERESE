import { useEffect, useMemo, useRef, useState } from 'react';
import { FileDown, MoreHorizontal, Pencil, Plus, Search, Trash2, X } from 'lucide-react';
import { motion, useIsPresent } from 'framer-motion';
import { useChatStore, type Conversation } from '../../stores/chatStore';
import { aUnBrouillonLocal } from '../../hooks/useAutosave';
import { Alerte } from '../ui/Alerte';
import { Button } from '../ui/Button';
import { EtatVide } from '../ui/EtatVide';
import { Input } from '../ui/Input';
import { cn } from '../../lib/utils';

/** Revue COCO 0.69.0 (finding 2) : une conversation listée sans message l'est pour son brouillon, autant le dire. */
function compteMessages(conversation: { messages: unknown[]; messageCount?: number }): string {
  const nombre = conversation.messages.length || conversation.messageCount || 0;
  if (nombre === 0) return 'Brouillon en attente';
  return `${nombre} message${nombre > 1 ? 's' : ''}`;
}
import {
  deleteConversation as deleteConversationRemote,
  exportConversation,
  renameConversation as renameConversationRemote,
} from '../../services/api/chat';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { usePanneauCouvrant } from '../../hooks/usePanneauCouvrant';
import { pushEscapeHandler } from '../../lib/escapeStack';

interface PrototypeConversationDrawerProps {
  onClose: () => void;
  onOpenChat: () => void;
  navigationLocked?: boolean;
  surface?: PrototypeConversationDrawerSurface;
}

export type PrototypeConversationDrawerSurface = 'new' | 'search' | 'history';

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

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const day = new Date(value.getFullYear(), value.getMonth(), value.getDate());
  const distance = Math.round((today.getTime() - day.getTime()) / 86_400_000);

  if (distance === 0 || distance === 1) {
    return value.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  }
  if (distance > 1 && distance < 7) {
    return value.toLocaleDateString('fr-FR', { weekday: 'short' });
  }
  return value.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
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
  surface = 'history',
}: PrototypeConversationDrawerProps) {
  const [query, setQuery] = useState('');
  const [menuId, setMenuId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [deleteConfirmationId, setDeleteConfirmationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const drawerRef = useRef<HTMLElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuTriggerRef = useRef<HTMLButtonElement>(null);
  const newConversationRef = useRef<HTMLButtonElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const historyRef = useRef<HTMLDivElement>(null);
  const conversations = useChatStore((state) => state.conversations);
  const currentConversationId = useChatStore((state) => state.currentConversationId);
  const createConversation = useChatStore((state) => state.createConversation);
  const loadConversation = useChatStore((state) => state.loadConversation);
  const renameConversation = useChatStore((state) => state.renameConversation);
  const deleteConversation = useChatStore((state) => state.deleteConversation);
  const isPresent = useIsPresent();
  // B-204 : ce tiroir isolait la colonne principale À TOUTE LARGEUR et se
  // déclarait modal, alors que la règle de l'application dit « côte à côte,
  // ne pas recouvrir » au-dessus du seuil xl. Il avait échappé aux deux gardes
  // du hotfix 0.48.1 parce qu'elles énumèrent des fichiers `*Canvas.tsx` PAR
  // NOM. Aligné sur ses six frères : isolation seulement quand il recouvre,
  // aucun piège clavier (le rail et l'en-tête restent joignables).
  // B-277 : l'alignement n'avait porté que sur cette moitié-ci. Le VOILE, la
  // seconde moitié du contrat 0.48.1, se décide dans la coque à partir d'une
  // autre liste par nom (`panneauLateralOuvert`), où le tiroir manquait aussi.
  const estCouvrant = usePanneauCouvrant();
  useDialogFocusTrap(drawerRef, {
    active: isPresent,
    isolateBackground: estCouvrant,
    piegeClavier: false,
  });

  // `piegeClavier: false` retire aussi Échap au piège (S1-3 : un panneau ne
  // s'inscrit jamais dans la pile des pièges, sinon il vole Échap à une modale
  // ouverte par-dessus). Il faut donc replacer la cascade AILLEURS, et au bon
  // rang - ce qui se joue en deux temps.
  //
  // 1. Les overlays INTERNES du tiroir (renommage, confirmation de
  //    suppression, menu contextuel) passent par `escapeStack`, exactement ce
  //    pour quoi elle a été écrite. Elle n'est peuplée que TANT QU'UN de ces
  //    overlays est ouvert : y laisser un handler en permanence ferait fermer
  //    le tiroir au lieu des Réglages ouverts par-dessus - la faute que S1-3
  //    décrit, mesurée par « une modale ouverte PAR-DESSUS garde Échap ».
  // 2. La fermeture du tiroir lui-même reste à la coque, qui la traite APRÈS
  //    les modales dans sa cascade (`else if (drawerOpen)`), c'est-à-dire au
  //    rang qui était déjà le sien.
  const overlayInterne = editingId ?? deleteConfirmationId ?? menuId;
  const fermerOverlayInterneRef = useRef<() => void>(() => {});
  fermerOverlayInterneRef.current = () => {
    if (editingId) setEditingId(null);
    else if (deleteConfirmationId) setDeleteConfirmationId(null);
    else if (menuId) {
      menuTriggerRef.current?.focus();
      setMenuId(null);
    }
  };
  useEffect(() => {
    if (!overlayInterne) return;
    return pushEscapeHandler(() => fermerOverlayInterneRef.current());
  }, [overlayInterne]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase('fr-FR');
    return [...conversations]
      // P-054 (Nadia, c4) : une conversation sans aucun message (⌘N sans
      // rien écrire) n'a rien où revenir ; la lister faisait un fantôme
      // « Nouvelle conversation · 0 message ». Elle apparaît au premier message.
      // Revue COCO 0.69.0 (finding 2) : sauf si un brouillon local l'attend,
      // sinon ce brouillon devient injoignable.
      .filter((conversation) =>
        (conversation.messages.length || conversation.messageCount || 0) > 0 || aUnBrouillonLocal(conversation.id))
      .filter((conversation) => !normalized || conversation.title.toLocaleLowerCase('fr-FR').includes(normalized))
      .sort((left, right) => new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime());
  }, [conversations, query]);
  const grouped = useMemo(() => groupConversations(filtered), [filtered]);

  useEffect(() => {
    if (surface !== 'search') setQuery('');

    if (surface === 'new') newConversationRef.current?.focus();
    else if (surface === 'search') searchRef.current?.focus();
    else historyRef.current?.focus();
  }, [surface]);

  useEffect(() => {
    if (!menuId) return;
    menuRef.current?.querySelector<HTMLElement>('[role="menuitem"]')?.focus();
  }, [menuId]);

  const handleMenuKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp' && event.key !== 'Home' && event.key !== 'End') return;
    const items = Array.from(menuRef.current?.querySelectorAll<HTMLButtonElement>('[role="menuitem"]') ?? []);
    if (items.length === 0) return;
    event.preventDefault();
    const current = Math.max(0, items.indexOf(document.activeElement as HTMLButtonElement));
    const next = event.key === 'Home'
      ? 0
      : event.key === 'End'
        ? items.length - 1
        : event.key === 'ArrowDown'
          ? (current + 1) % items.length
          : (current - 1 + items.length) % items.length;
    items[next].focus();
  };

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
      ref={drawerRef}
      // B-204 : `role="dialog"` + `aria-modal` promettaient un focus contenu et
      // une page neutralisée que ce panneau ne tient pas - le rail et l'en-tête
      // restent volontairement actifs. Forme des six frères : une région nommée.
      role="region"
      aria-labelledby="prototype-conversation-drawer-title"
      tabIndex={-1}
      initial={{ x: -24, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: -24, opacity: 0 }}
      transition={{ duration: 0.18 }}
      // Au-dessus du seuil xl il devient un vrai voisin de la colonne (comme les
      // six panneaux : `xl:relative`), sinon retirer l'isolation laisserait des
      // contrôles tabulables SOUS un panneau opaque - le finding S1-2 du hotfix.
      // `xl:left-0` annule le décalage du rail, qui n'a plus lieu d'être une fois
      // le tiroir placé dans le flux.
      className="absolute inset-y-0 left-16 z-30 flex w-[22rem] flex-col border-r border-border bg-surface shadow-lg xl:relative xl:left-0 xl:shrink-0 xl:shadow-none"
      data-testid="prototype-conversation-drawer"
    >
      <div className="flex h-14 shrink-0 items-center justify-between border-b border-border px-4">
        <h2 id="prototype-conversation-drawer-title" className="text-base">Conversations</h2>
        <Button variant="ghost" size="icon" onClick={onClose} aria-label="Fermer les conversations">
          <X className="h-[18px] w-[18px]" />
        </Button>
      </div>

      <div className="shrink-0 px-4 py-2">
        <Input
          ref={searchRef}
          type="search"
          icon={<Search className="h-[18px] w-[18px]" />}
          aria-label="Rechercher une conversation"
          placeholder="Rechercher dans les conversations"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="bg-surface-2"
        />
      </div>

      <div
        ref={historyRef}
        tabIndex={-1}
        aria-label="Historique des conversations"
        className="min-h-0 flex-1 overflow-y-auto px-3 pb-3 outline-none"
        data-testid="prototype-conversation-list"
      >
        {error && <Alerte className="mb-2">{error}</Alerte>}
        {filtered.length === 0 ? (
          <EtatVide titre={query ? 'Aucune conversation trouvée' : 'Aucune conversation'}>
            {query ? null : 'Ta première demande à Thérèse apparaîtra ici, avec ce qu’elle a produit.'}
          </EtatVide>
        ) : grouped.map(([label, items]) => (
          <section key={label} className="mb-4">
            <div className="px-2 py-1.5 text-xs font-semibold uppercase tracking-wider text-text-muted">
              {label}
            </div>
            {items.map((conversation) => (
              <div key={conversation.id} className="relative mb-1">
                {editingId === conversation.id ? (
                  <div className="rounded-md border border-accent bg-surface p-2">
                    <Input
                      autoFocus
                      aria-label="Nouveau titre"
                      value={editingTitle}
                      maxLength={120}
                      onChange={(event) => setEditingTitle(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter') void saveTitle(conversation);
                        if (event.key === 'Escape') setEditingId(null);
                      }}
                    />
                    <div className="mt-2 flex justify-end gap-2">
                      <Button variant="ghost" size="md" type="button" onClick={() => setEditingId(null)}>Annuler</Button>
                      <Button variant="primary" size="md" type="button" onClick={() => void saveTitle(conversation)}>Enregistrer</Button>
                    </div>
                  </div>
                ) : deleteConfirmationId === conversation.id ? (
                  <div className="rounded-md border border-border bg-surface p-3" data-testid="conversation-delete-confirmation">
                    <p className="text-sm font-semibold">Supprimer définitivement cette conversation ?</p>
                    <div className="mt-2 flex justify-end gap-2">
                      <Button variant="secondary" size="md" type="button" onClick={() => setDeleteConfirmationId(null)}>Annuler</Button>
                      <Button variant="danger" size="md" type="button" onClick={() => void confirmDelete(conversation)}>Confirmer la suppression</Button>
                    </div>
                  </div>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={() => openConversation(conversation.id)}
                      aria-current={currentConversationId === conversation.id ? 'page' : undefined}
                      className={cn(
                        'grid w-full grid-cols-[1fr_auto] gap-x-2 gap-y-0.5 rounded-sm px-3 py-2.5 pr-11 text-left',
                        'focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-[-3px] focus-visible:outline-ring',
                        currentConversationId === conversation.id ? 'bg-accent-tint' : 'hover:bg-surface-2',
                      )}
                    >
                      <b className="truncate text-sm font-semibold">{conversation.title || 'Nouvelle conversation'}</b>
                      <span className="text-sm tabular-nums text-text-muted">{updatedLabel(conversation.updatedAt)}</span>
                      <span className="col-span-2 truncate text-sm text-text-muted">
                        {compteMessages(conversation)}{conversation.synced ? '' : ' · non enregistrée'}
                      </span>
                    </button>
                    <Button
                      ref={menuId === conversation.id ? menuTriggerRef : undefined}
                      variant="ghost"
                      size="icon"
                      type="button"
                      aria-label={`Actions pour ${conversation.title}`}
                      aria-haspopup="menu"
                      aria-expanded={menuId === conversation.id}
                      aria-controls={`conversation-menu-${conversation.id}`}
                      onClick={(event) => {
                        menuTriggerRef.current = event.currentTarget;
                        setMenuId(menuId === conversation.id ? null : conversation.id);
                      }}
                      className="absolute right-2 top-2 text-text-muted"
                    >
                      <MoreHorizontal className="h-[18px] w-[18px]" />
                    </Button>
                    {menuId === conversation.id && <div ref={menuRef} id={`conversation-menu-${conversation.id}`} role="menu" aria-label={`Actions pour ${conversation.title}`} onKeyDown={handleMenuKeyDown} className="absolute right-2 top-11 z-10 w-44 rounded-md border border-border bg-surface py-1 shadow-xl" data-testid="conversation-actions-menu"><button role="menuitem" tabIndex={-1} type="button" onClick={() => { setEditingId(conversation.id); setEditingTitle(conversation.title); setMenuId(null); }} className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-text hover:bg-surface-2"><Pencil className="h-3.5 w-3.5" />Renommer</button><button role="menuitem" tabIndex={-1} type="button" onClick={() => void exportConversation(conversation.id, 'md').catch(() => setError('L’export Markdown a échoué.'))} className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-text hover:bg-surface-2"><FileDown className="h-3.5 w-3.5" />Exporter en Markdown</button><button role="menuitem" tabIndex={-1} type="button" onClick={() => void exportConversation(conversation.id, 'docx').catch(() => setError('L’export Word a échoué.'))} className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-text hover:bg-surface-2"><FileDown className="h-3.5 w-3.5" />Exporter en Word</button><button role="menuitem" tabIndex={-1} type="button" onClick={() => { setDeleteConfirmationId(conversation.id); setMenuId(null); }} className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-error hover:bg-[var(--color-error-tint)]"><Trash2 className="h-3.5 w-3.5" />Supprimer</button></div>}
                  </>
                )}
              </div>
            ))}
          </section>
        ))}
      </div>
      <div className="border-t border-border px-4 py-2.5">
        <Button
          ref={newConversationRef}
          variant="primary"
          size="md"
          type="button"
          onClick={startConversation}
          className="w-full gap-2"
        >
          <Plus className="h-[18px] w-[18px]" />
          Nouvelle conversation
        </Button>
      </div>
    </motion.aside>
  );
}
