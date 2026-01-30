import { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  MessageSquarePlus,
  Trash2,
  Settings,
  Download,
  UserPlus,
  FolderPlus,
  Keyboard,
  X,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useChatStore } from '../../stores/chatStore';

export interface Command {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  shortcut?: string;
  action: () => void;
  category: 'chat' | 'memory' | 'settings';
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onShowShortcuts: () => void;
}

export function CommandPalette({ isOpen, onClose, onShowShortcuts }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const { createConversation, clearCurrentConversation } = useChatStore();

  const commands = useMemo<Command[]>(
    () => [
      {
        id: 'new-conversation',
        name: 'Nouvelle conversation',
        description: 'Démarrer une nouvelle conversation',
        icon: <MessageSquarePlus className="w-4 h-4" />,
        shortcut: '⌘N',
        action: () => {
          createConversation();
          onClose();
        },
        category: 'chat',
      },
      {
        id: 'clear-conversation',
        name: 'Effacer conversation',
        description: 'Supprimer tous les messages',
        icon: <Trash2 className="w-4 h-4" />,
        action: () => {
          clearCurrentConversation();
          onClose();
        },
        category: 'chat',
      },
      {
        id: 'add-contact',
        name: 'Ajouter un contact',
        description: 'Créer un nouveau contact en mémoire',
        icon: <UserPlus className="w-4 h-4" />,
        action: () => {
          // TODO: Open contact modal
          onClose();
        },
        category: 'memory',
      },
      {
        id: 'add-project',
        name: 'Ajouter un projet',
        description: 'Créer un nouveau projet en mémoire',
        icon: <FolderPlus className="w-4 h-4" />,
        action: () => {
          // TODO: Open project modal
          onClose();
        },
        category: 'memory',
      },
      {
        id: 'export-data',
        name: 'Exporter les données',
        description: 'Télécharger un backup de ta mémoire',
        icon: <Download className="w-4 h-4" />,
        action: () => {
          // TODO: Trigger export
          onClose();
        },
        category: 'settings',
      },
      {
        id: 'settings',
        name: 'Paramètres',
        description: 'Configurer THÉRÈSE',
        icon: <Settings className="w-4 h-4" />,
        action: () => {
          // TODO: Open settings
          onClose();
        },
        category: 'settings',
      },
      {
        id: 'shortcuts',
        name: 'Raccourcis clavier',
        description: 'Voir tous les raccourcis',
        icon: <Keyboard className="w-4 h-4" />,
        shortcut: '⌘/',
        action: () => {
          onClose();
          onShowShortcuts();
        },
        category: 'settings',
      },
    ],
    [createConversation, clearCurrentConversation, onClose, onShowShortcuts]
  );

  const filteredCommands = useMemo(() => {
    if (!query.trim()) return commands;
    const q = query.toLowerCase();
    return commands.filter(
      (cmd) =>
        cmd.name.toLowerCase().includes(q) ||
        cmd.description.toLowerCase().includes(q)
    );
  }, [commands, query]);

  // Reset selection when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((i) => Math.min(i + 1, filteredCommands.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((i) => Math.max(i - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredCommands[selectedIndex]) {
            filteredCommands[selectedIndex].action();
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    },
    [filteredCommands, selectedIndex, onClose]
  );

  // Scroll selected item into view
  useEffect(() => {
    const list = listRef.current;
    const selected = list?.children[selectedIndex] as HTMLElement | undefined;
    selected?.scrollIntoView({ block: 'nearest' });
  }, [selectedIndex]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]"
          onClick={onClose}
        >
          {/* Backdrop with fade animation */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-md"
          />

          {/* Palette with scale and fade animation */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
            className={cn(
              'relative w-full max-w-lg',
              'bg-surface/95 backdrop-blur-xl border border-border/50 rounded-xl',
              'shadow-[0_25px_50px_-12px_rgba(0,0,0,0.5),0_0_40px_rgba(34,211,238,0.1)]',
              'overflow-hidden'
            )}
            onClick={(e) => e.stopPropagation()}
          >
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <Search className="w-5 h-5 text-text-muted flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Rechercher une commande..."
            className={cn(
              'flex-1 bg-transparent text-text placeholder:text-text-muted',
              'focus:outline-none text-sm'
            )}
          />
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-surface-elevated transition-colors"
          >
            <X className="w-4 h-4 text-text-muted" />
          </button>
        </div>

        {/* Commands list */}
        <div ref={listRef} className="max-h-80 overflow-y-auto py-2">
          {filteredCommands.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="px-4 py-8 text-center text-text-muted text-sm"
            >
              Aucune commande trouvée
            </motion.div>
          ) : (
            filteredCommands.map((cmd, index) => (
              <motion.button
                key={cmd.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.03 }}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-2.5',
                  'text-left transition-all duration-150',
                  index === selectedIndex
                    ? 'bg-accent-cyan/10 text-accent-cyan shadow-[inset_0_0_20px_rgba(34,211,238,0.05)]'
                    : 'hover:bg-surface-elevated/50 text-text'
                )}
                onClick={() => cmd.action()}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                <span
                  className={cn(
                    'flex-shrink-0 transition-colors',
                    index === selectedIndex ? 'text-accent-cyan' : 'text-text-muted'
                  )}
                >
                  {cmd.icon}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{cmd.name}</div>
                  <div className="text-xs text-text-muted truncate">
                    {cmd.description}
                  </div>
                </div>
                {cmd.shortcut && (
                  <kbd
                    className={cn(
                      'flex-shrink-0 px-1.5 py-0.5 rounded text-xs',
                      'bg-bg border border-border/50 font-mono',
                      index === selectedIndex && 'border-accent-cyan/30'
                    )}
                  >
                    {cmd.shortcut}
                  </kbd>
                )}
              </motion.button>
            ))
          )}
        </div>

          {/* Footer */}
          <div className="px-4 py-2 border-t border-border/50 bg-bg/30">
            <div className="flex items-center justify-between text-xs text-text-muted">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1">
                  <kbd className="px-1 rounded bg-surface-elevated">↑↓</kbd>
                  naviguer
                </span>
                <span className="flex items-center gap-1">
                  <kbd className="px-1 rounded bg-surface-elevated">↵</kbd>
                  sélectionner
                </span>
              </div>
              <span className="flex items-center gap-1">
                <kbd className="px-1 rounded bg-surface-elevated">esc</kbd>
                fermer
              </span>
            </div>
          </div>
        </motion.div>
      </div>
    )}
    </AnimatePresence>
  );
}
