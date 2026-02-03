import { useState, useEffect, useCallback } from 'react';
import {
  MessageSquare,
  Plus,
  Trash2,
  ChevronLeft,
  Search,
  MoreHorizontal,
  Calendar,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { useChatStore, Conversation } from '../../stores/chatStore';
import { staggerContainer, staggerItem, sidebarLeftVariants, overlayVariants } from '../../lib/animations';
import * as api from '../../services/api';
import { useDemoMask } from '../../hooks';

interface ConversationSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ConversationSidebar({ isOpen, onClose }: ConversationSidebarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [contextMenuId, setContextMenuId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  const {
    conversations,
    currentConversationId,
    loadConversation,
    createConversation,
    deleteConversation,
  } = useChatStore();
  const { maskText } = useDemoMask();

  // Filter conversations
  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Group by date
  const grouped = groupConversationsByDate(filteredConversations);

  // Handle new conversation - create on backend first
  const handleNewConversation = useCallback(async () => {
    try {
      // Create on backend first to get the real ID
      const backendConv = await api.createConversation('Nouvelle conversation');
      // Create locally with the backend ID
      const localId = createConversation();
      // Update local ID to match backend ID
      useChatStore.getState().updateConversationId(localId, backendConv.id);
    } catch (error) {
      console.error('Failed to create conversation on backend:', error);
      // Still create locally as fallback
      createConversation();
    }
    onClose();
  }, [createConversation, onClose]);

  // Handle select conversation - load messages from backend
  const handleSelectConversation = useCallback(
    async (id: string) => {
      // Set as current conversation immediately
      loadConversation(id);
      onClose();

      // Load messages from backend
      try {
        const messages = await api.getConversationMessages(id);
        const formattedMessages = messages.map((msg: api.MessageResponse) => ({
          id: msg.id,
          role: msg.role as 'user' | 'assistant' | 'system',
          content: msg.content,
          timestamp: new Date(msg.created_at),
        }));
        // This will now create the conversation if it doesn't exist
        useChatStore.getState().setConversationMessages(id, formattedMessages);
      } catch (error) {
        console.error('Failed to load conversation messages:', error);
        // If backend fails, check if conversation exists locally with messages
        const localConv = useChatStore.getState().conversations.find((c) => c.id === id);
        if (!localConv || localConv.messages.length === 0) {
          console.warn('Conversation has no messages locally or on backend');
        }
      }
    },
    [loadConversation, onClose]
  );

  // Handle delete
  const handleDelete = useCallback(
    async (id: string) => {
      setDeleting(id);
      try {
        // Delete from backend
        await api.deleteConversation(id).catch(() => {
          // Ignore backend errors (conversation might not be synced)
        });
        // Delete from local store
        deleteConversation(id);
      } finally {
        setDeleting(null);
        setContextMenuId(null);
      }
    },
    [deleteConversation]
  );

  // Close context menu on click outside
  useEffect(() => {
    function handleClickOutside() {
      setContextMenuId(null);
    }
    if (contextMenuId) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [contextMenuId]);

  // Keyboard shortcut to toggle
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            variants={overlayVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          {/* Sidebar */}
          <motion.div
            variants={sidebarLeftVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="fixed left-0 top-0 bottom-0 w-[320px] bg-surface border-r border-border z-50 flex flex-col shadow-2xl"
          >
            {/* Header */}
            <div className="h-14 flex items-center justify-between px-4 border-b border-border/50">
              <h2 className="text-lg font-semibold text-text">Conversations</h2>
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="icon" onClick={handleNewConversation} title="Nouvelle conversation">
                  <Plus className="w-5 h-5" />
                </Button>
                <Button variant="ghost" size="icon" onClick={onClose}>
                  <ChevronLeft className="w-5 h-5" />
                </Button>
              </div>
            </div>

            {/* Search */}
            <div className="p-3 border-b border-border/30">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  type="text"
                  placeholder="Rechercher..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent-cyan/50 transition-colors"
                />
              </div>
            </div>

            {/* Conversations list */}
            <div className="flex-1 overflow-y-auto">
              {filteredConversations.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-32 text-text-muted">
                  <MessageSquare className="w-8 h-8 mb-2 opacity-50" />
                  <p className="text-sm">
                    {searchQuery ? 'Aucun résultat' : 'Aucune conversation'}
                  </p>
                  {!searchQuery && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mt-2"
                      onClick={handleNewConversation}
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      Nouvelle conversation
                    </Button>
                  )}
                </div>
              ) : (
                <motion.div
                  variants={staggerContainer}
                  initial="initial"
                  animate="animate"
                  className="py-2"
                >
                  {Object.entries(grouped).map(([label, convos]) => (
                    <div key={label} className="mb-2">
                      {/* Date label */}
                      <motion.div
                        variants={staggerItem}
                        className="px-4 py-1.5 flex items-center gap-2 text-xs text-text-muted/70"
                      >
                        <Calendar className="w-3 h-3" />
                        {label}
                      </motion.div>

                      {/* Conversations */}
                      {convos.map((conversation) => (
                        <motion.div key={conversation.id} variants={staggerItem}>
                          <ConversationItem
                            conversation={conversation}
                            isActive={conversation.id === currentConversationId}
                            isDeleting={deleting === conversation.id}
                            showContextMenu={contextMenuId === conversation.id}
                            onSelect={() => handleSelectConversation(conversation.id)}
                            onContextMenu={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              setContextMenuId(conversation.id);
                            }}
                            onDelete={() => handleDelete(conversation.id)}
                            onCloseContextMenu={() => setContextMenuId(null)}
                            maskTextFn={maskText}
                          />
                        </motion.div>
                      ))}
                    </div>
                  ))}
                </motion.div>
              )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-border/50">
              <Button
                variant="primary"
                className="w-full"
                onClick={handleNewConversation}
              >
                <Plus className="w-4 h-4 mr-2" />
                Nouvelle conversation
              </Button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// Individual conversation item
interface ConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  isDeleting: boolean;
  showContextMenu: boolean;
  onSelect: () => void;
  onContextMenu: (e: React.MouseEvent) => void;
  onDelete: () => void;
  onCloseContextMenu: () => void;
  maskTextFn?: (text: string) => string;
}

function ConversationItem({
  conversation,
  isActive,
  isDeleting,
  showContextMenu,
  onSelect,
  onContextMenu,
  onDelete,
  onCloseContextMenu: _onCloseContextMenu,
  maskTextFn,
}: ConversationItemProps) {
  const messageCount = conversation.messages?.length || conversation.messageCount || 0;
  const lastMessage = conversation.messages?.[conversation.messages.length - 1];
  const rawPreview = lastMessage?.content?.slice(0, 60) || 'Pas de messages';
  const displayTitle = maskTextFn ? maskTextFn(conversation.title) : conversation.title;
  const preview = maskTextFn ? maskTextFn(rawPreview) : rawPreview;

  return (
    <div className="relative px-2">
      <button
        onClick={onSelect}
        onContextMenu={onContextMenu}
        disabled={isDeleting}
        className={`w-full flex items-start gap-3 p-3 rounded-lg transition-colors text-left group ${
          isActive
            ? 'bg-accent-cyan/10 border border-accent-cyan/30'
            : 'hover:bg-background/40 border border-transparent'
        } ${isDeleting ? 'opacity-50' : ''}`}
      >
        {/* Icon */}
        <div
          className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
            isActive
              ? 'bg-accent-cyan/20'
              : 'bg-gradient-to-br from-accent-cyan/10 to-accent-magenta/10'
          }`}
        >
          <MessageSquare
            className={`w-4 h-4 ${isActive ? 'text-accent-cyan' : 'text-text-muted'}`}
          />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-text truncate">{displayTitle}</p>
          <p className="text-xs text-text-muted truncate mt-0.5">{preview}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-text-muted/60">
              {messageCount} message{messageCount !== 1 ? 's' : ''}
            </span>
            <span className="text-xs text-text-muted/40">•</span>
            <span className="text-xs text-text-muted/60">
              {formatRelativeTime(conversation.updatedAt)}
            </span>
          </div>
        </div>

        {/* Menu button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onContextMenu(e);
          }}
          className="opacity-0 group-hover:opacity-100 p-1 hover:bg-background/60 rounded transition-all"
        >
          <MoreHorizontal className="w-4 h-4 text-text-muted" />
        </button>
      </button>

      {/* Context menu */}
      <AnimatePresence>
        {showContextMenu && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -5 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -5 }}
            transition={{ type: 'spring', stiffness: 500, damping: 30 }}
            className="absolute right-4 top-12 z-10 w-40 bg-surface border border-border rounded-lg shadow-xl py-1"
            onClick={(e) => e.stopPropagation()}
          >
            <motion.button
              onClick={onDelete}
              whileHover={{ x: 2 }}
              whileTap={{ scale: 0.98 }}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              Supprimer
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Group conversations by date
function groupConversationsByDate(conversations: Conversation[]): Record<string, Conversation[]> {
  const groups: Record<string, Conversation[]> = {};
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 86400000);
  const lastWeek = new Date(today.getTime() - 7 * 86400000);
  const lastMonth = new Date(today.getTime() - 30 * 86400000);

  for (const conv of conversations) {
    const date = new Date(conv.updatedAt);
    let label: string;

    if (date >= today) {
      label = "Aujourd'hui";
    } else if (date >= yesterday) {
      label = 'Hier';
    } else if (date >= lastWeek) {
      label = 'Cette semaine';
    } else if (date >= lastMonth) {
      label = 'Ce mois';
    } else {
      label = 'Plus ancien';
    }

    if (!groups[label]) {
      groups[label] = [];
    }
    groups[label].push(conv);
  }

  return groups;
}

// Format relative time
function formatRelativeTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "À l'instant";
  if (diffMins < 60) return `${diffMins}min`;
  if (diffHours < 24) return `${diffHours}h`;
  if (diffDays < 7) return `${diffDays}j`;

  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
}
