import { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAccessibilityStore } from '../../stores/accessibilityStore';
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
  PanelLeft,
  PanelRight,
  Gavel,
  Mail,
  Calendar,
  ListTodo,
  Receipt,
  BarChart3,
  Search as SearchIcon,
  Sparkles,
  BookOpen,
  Play,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useUXMode } from '../../hooks/useUXMode';
import { getActions, runAction } from '../../lib/actionRegistry';
import { Z_LAYER } from '../../styles/z-layers';

export interface Command {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  shortcut?: string;
  action: () => void;
  category: 'chat' | 'memory' | 'panels' | 'settings';
  contributeurOnly?: boolean;
  keywords?: string[];
}

// L8 : la palette ⌘K affiche le registre d'actions. Le registre est sans JSX
// (invocable hors React) ; la palette mappe id -> icône ici.
const ACTION_ICONS: Record<string, React.ReactNode> = {
  'chat.new': <MessageSquarePlus className="w-4 h-4" />,
  'chat.clear': <Trash2 className="w-4 h-4" />,
  'conversations.toggle': <PanelLeft className="w-4 h-4" />,
  'guided.open': <Sparkles className="w-4 h-4" />,
  'prompt-library.open': <BookOpen className="w-4 h-4" />,
  'memory.open': <PanelRight className="w-4 h-4" />,
  'memory.search': <SearchIcon className="w-4 h-4" />,
  'contact.new': <UserPlus className="w-4 h-4" />,
  'project.new': <FolderPlus className="w-4 h-4" />,
  'crm.open': <BarChart3 className="w-4 h-4" />,
  'email.open': <Mail className="w-4 h-4" />,
  'calendar.open': <Calendar className="w-4 h-4" />,
  'tasks.open': <ListTodo className="w-4 h-4" />,
  'invoices.open': <Receipt className="w-4 h-4" />,
  'board.open': <Gavel className="w-4 h-4" />,
  'actions.open': <Play className="w-4 h-4 text-cyan-400" />,
  'data.export': <Download className="w-4 h-4" />,
  'settings.open': <Settings className="w-4 h-4" />,
  'shortcuts.open': <Keyboard className="w-4 h-4" />,
};

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const reduceMotion = useAccessibilityStore((s) => s.reduceMotion);
  const { isContributeur } = useUXMode();

  // Détection plateforme pour affichage raccourcis (⌘ sur Mac, Ctrl sur Windows/Linux)
  const mod = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform) ? '⌘' : 'Ctrl+';

  const commands = useMemo<Command[]>(
    () =>
      getActions().map((a) => ({
        id: a.id,
        name: a.label,
        description: a.description ?? '',
        icon: ACTION_ICONS[a.id] ?? <Sparkles className="w-4 h-4" />,
        shortcut: a.shortcut ? `${mod}${a.shortcut}` : undefined,
        category: 'panels' as const,
        keywords: a.keywords,
        action: () => {
          onClose();
          runAction(a.id);
        },
      })),
    [mod, onClose]
  );

  const filteredCommands = useMemo(() => {
    // Filtrer les commandes reservees au mode Contributeur
    const available = isContributeur
      ? commands
      : commands.filter((cmd) => !cmd.contributeurOnly);

    if (!query.trim()) return available;
    const q = query.toLowerCase();
    return available.filter(
      (cmd) =>
        cmd.name.toLowerCase().includes(q) ||
        cmd.description.toLowerCase().includes(q) ||
        (cmd.keywords ?? []).some((k) => k.toLowerCase().includes(q))
    );
  }, [commands, query, isContributeur]);

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
        // Échap : géré par la pile unifiée (resolveEscape, L7), pas localement.
        // Sinon course : la palette (onKeyDown élément, tire avant le handler
        // global window) se fermerait, et resolveEscape ferait un retour de vue.
      }
    },
    [filteredCommands, selectedIndex]
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
          className={`fixed inset-0 ${Z_LAYER.COMMAND_PALETTE} flex items-start justify-center pt-[15vh]`}
          onClick={onClose}
        >
          {/* Backdrop with fade animation */}
          <motion.div
            initial={reduceMotion ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: reduceMotion ? 0 : 0.15 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-md"
          />

          {/* Palette with scale and fade animation */}
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-label="Palette de commandes"
            initial={reduceMotion ? false : { opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={reduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: reduceMotion ? 0 : 0.2, ease: [0.23, 1, 0.32, 1] }}
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
                initial={reduceMotion ? false : { opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={reduceMotion ? { duration: 0 } : { delay: index * 0.03 }}
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
