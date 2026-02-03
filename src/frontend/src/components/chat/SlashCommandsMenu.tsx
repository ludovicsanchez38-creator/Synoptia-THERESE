import { useEffect, useRef, useCallback, useMemo } from 'react';
import {
  UserPlus,
  FolderPlus,
  Search,
  FileText,
  Sparkles,
  ListTodo,
  Mail,
  Calendar,
} from 'lucide-react';
import { cn } from '../../lib/utils';

export interface SlashCommand {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  prefix: string;
}

const SLASH_COMMANDS: SlashCommand[] = [
  {
    id: 'contact',
    name: 'contact',
    description: 'Mentionner ou créer un contact',
    icon: <UserPlus className="w-4 h-4" />,
    prefix: '/contact ',
  },
  {
    id: 'projet',
    name: 'projet',
    description: 'Mentionner ou créer un projet',
    icon: <FolderPlus className="w-4 h-4" />,
    prefix: '/projet ',
  },
  {
    id: 'recherche',
    name: 'recherche',
    description: 'Rechercher dans la mémoire',
    icon: <Search className="w-4 h-4" />,
    prefix: '/recherche ',
  },
  {
    id: 'fichier',
    name: 'fichier',
    description: 'Analyser un fichier local',
    icon: <FileText className="w-4 h-4" />,
    prefix: '/fichier ',
  },
  {
    id: 'resume',
    name: 'résumé',
    description: 'Résumer la conversation',
    icon: <Sparkles className="w-4 h-4" />,
    prefix: '/résumé',
  },
  {
    id: 'taches',
    name: 'tâches',
    description: 'Extraire les tâches de la conversation',
    icon: <ListTodo className="w-4 h-4" />,
    prefix: '/tâches',
  },
  {
    id: 'email',
    name: 'email',
    description: 'Rédiger un email',
    icon: <Mail className="w-4 h-4" />,
    prefix: '/email ',
  },
  {
    id: 'rdv',
    name: 'rdv',
    description: 'Préparer un rendez-vous',
    icon: <Calendar className="w-4 h-4" />,
    prefix: '/rdv ',
  },
];

interface SlashCommandsMenuProps {
  isOpen: boolean;
  query: string;
  selectedIndex: number;
  onSelect: (command: SlashCommand) => void;
  onClose: () => void;
  onIndexChange: (index: number) => void;
  inputRect?: DOMRect | null;
  userCommands?: SlashCommand[];
}

export function SlashCommandsMenu({
  isOpen,
  query,
  selectedIndex,
  onSelect,
  onClose,
  onIndexChange,
  inputRect,
  userCommands,
}: SlashCommandsMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  // Merge built-in and user commands
  const allCommands = useMemo(() => {
    if (!userCommands || userCommands.length === 0) return SLASH_COMMANDS;
    return [...SLASH_COMMANDS, ...userCommands];
  }, [userCommands]);

  // Filter commands based on query
  const filteredCommands = useMemo(() => {
    // Remove the leading slash from query
    const searchTerm = query.startsWith('/') ? query.slice(1).toLowerCase() : '';
    if (!searchTerm) return allCommands;
    return allCommands.filter(
      (cmd) =>
        cmd.name.toLowerCase().startsWith(searchTerm) ||
        cmd.description.toLowerCase().includes(searchTerm)
    );
  }, [query, allCommands]);

  // Clamp selected index
  useEffect(() => {
    if (selectedIndex >= filteredCommands.length) {
      onIndexChange(Math.max(0, filteredCommands.length - 1));
    }
  }, [filteredCommands.length, selectedIndex, onIndexChange]);

  // Scroll selected item into view
  useEffect(() => {
    const menu = menuRef.current;
    const selected = menu?.children[selectedIndex] as HTMLElement | undefined;
    selected?.scrollIntoView({ block: 'nearest' });
  }, [selectedIndex]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!isOpen) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          onIndexChange(Math.min(selectedIndex + 1, filteredCommands.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          onIndexChange(Math.max(selectedIndex - 1, 0));
          break;
        case 'Tab':
        case 'Enter':
          e.preventDefault();
          if (filteredCommands[selectedIndex]) {
            onSelect(filteredCommands[selectedIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    },
    [isOpen, selectedIndex, filteredCommands, onIndexChange, onSelect, onClose]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  if (!isOpen || filteredCommands.length === 0) return null;

  // Position menu above the input
  const menuStyle: React.CSSProperties = inputRect
    ? {
        position: 'fixed',
        bottom: window.innerHeight - inputRect.top + 8,
        left: inputRect.left,
        maxWidth: inputRect.width,
      }
    : {};

  return (
    <div
      style={menuStyle}
      className={cn(
        'z-50 w-full max-w-md',
        'bg-surface border border-border rounded-lg shadow-xl',
        'overflow-hidden'
      )}
    >
      {/* Header */}
      <div className="px-3 py-2 border-b border-border">
        <span className="text-xs font-medium text-text-muted">
          Commandes disponibles
        </span>
      </div>

      {/* Commands list */}
      <div ref={menuRef} className="max-h-60 overflow-y-auto py-1">
        {filteredCommands.map((cmd, index) => (
          <button
            key={cmd.id}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2',
              'text-left transition-colors',
              index === selectedIndex
                ? 'bg-accent-cyan/10 text-accent-cyan'
                : 'hover:bg-surface-elevated text-text'
            )}
            onClick={() => onSelect(cmd)}
            onMouseEnter={() => onIndexChange(index)}
          >
            <span
              className={cn(
                'flex-shrink-0',
                index === selectedIndex ? 'text-accent-cyan' : 'text-text-muted'
              )}
            >
              {cmd.icon}
            </span>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium">/{cmd.name}</div>
              <div className="text-xs text-text-muted truncate">
                {cmd.description}
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Footer hint */}
      <div className="px-3 py-1.5 border-t border-border bg-bg/50">
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <span className="flex items-center gap-1">
            <kbd className="px-1 rounded bg-surface-elevated">↑↓</kbd>
            naviguer
          </span>
          <span className="flex items-center gap-1">
            <kbd className="px-1 rounded bg-surface-elevated">Tab</kbd>
            compléter
          </span>
        </div>
      </div>
    </div>
  );
}

// Helper to detect if input starts with a slash command
export function detectSlashCommand(input: string): boolean {
  return input.startsWith('/') && !input.includes(' ');
}
