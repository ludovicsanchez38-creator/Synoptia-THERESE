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
  Image,
  Palette,
  Wand2,
  Presentation,
  FileSpreadsheet,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useCommandsStore } from '../../stores/commandsStore';
import { pushEscapeHandler } from '../../lib/escapeStack';
import { Z_LAYER } from '../../styles/z-layers';

/** Map icon name (string from backend) to Lucide component */
const ICON_MAP: Record<string, LucideIcon> = {
  UserPlus, FolderPlus, Search, FileText, Sparkles, ListTodo, Mail, Calendar,
  Image, Palette, Wand2, Presentation, FileSpreadsheet,
};

export interface SlashCommand {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  prefix: string;
}

const SLASH_COMMANDS: SlashCommand[] = [
  // Actions déterministes (tranche 1a) : insèrent un message-action pur,
  // exécuté localement par le backend sans passer par le LLM.
  {
    id: 'ouvrir-email',
    name: 'ouvrir email',
    description: 'Ouvrir la boîte email (action locale, sans IA)',
    icon: <Mail className="w-4 h-4" />,
    prefix: '{action: ouvrir email}',
  },
  {
    id: 'ouvrir-crm',
    name: 'ouvrir crm',
    description: 'Ouvrir le pipeline CRM (action locale, sans IA)',
    icon: <UserPlus className="w-4 h-4" />,
    prefix: '{action: ouvrir crm}',
  },
  {
    id: 'ouvrir-memoire',
    name: 'ouvrir mémoire',
    description: 'Ouvrir la Mémoire (action locale, sans IA)',
    icon: <Search className="w-4 h-4" />,
    prefix: '{action: ouvrir mémoire}',
  },
  {
    id: 'ouvrir-calendrier',
    name: 'ouvrir calendrier',
    description: 'Ouvrir le Calendrier (action locale, sans IA)',
    icon: <Calendar className="w-4 h-4" />,
    prefix: '{action: ouvrir calendrier}',
  },
  {
    id: 'ouvrir-taches',
    name: 'ouvrir tâches',
    description: 'Ouvrir les Tâches (action locale, sans IA)',
    icon: <ListTodo className="w-4 h-4" />,
    prefix: '{action: ouvrir tâches}',
  },
  {
    id: 'ouvrir-documents',
    name: 'ouvrir documents',
    description: "Ouvrir l'Atelier documentaire (action locale, sans IA)",
    icon: <FileText className="w-4 h-4" />,
    prefix: '{action: ouvrir documents}',
  },
  {
    id: 'ouvrir-facturation',
    name: 'ouvrir facturation',
    description: 'Ouvrir les Factures (action locale, sans IA)',
    icon: <FileSpreadsheet className="w-4 h-4" />,
    prefix: '{action: ouvrir facturation}',
  },
  {
    id: 'produire-docx',
    name: 'produire docx',
    description: 'Générer un document Word (le fichier est créé localement)',
    icon: <FileText className="w-4 h-4" />,
    prefix: '{action: produire docx "sujet du document"}',
  },
  {
    id: 'produire-xlsx',
    name: 'produire xlsx',
    description: 'Générer un tableur Excel (le fichier est créé localement)',
    icon: <FileSpreadsheet className="w-4 h-4" />,
    prefix: '{action: produire xlsx "sujet du tableur"}',
  },
  {
    id: 'produire-pptx',
    name: 'produire pptx',
    description: 'Générer une présentation PowerPoint (le fichier est créé localement)',
    icon: <Presentation className="w-4 h-4" />,
    prefix: '{action: produire pptx "sujet de la présentation"}',
  },
  {
    id: 'contact',
    name: 'contact',
    description: 'Créer un contact : Prénom Nom (email=… tel=…)',
    icon: <UserPlus className="w-4 h-4" />,
    prefix: '/contact ',
  },
  {
    id: 'projet',
    name: 'projet',
    description: 'Créer un projet : Nom (budget=… statut=…)',
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
    description: 'Créer un rendez-vous : Titre (date=2026-06-03T14:00)',
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
  const storeCommands = useCommandsStore((s) => s.commands);

  // Merge built-in static commands with dynamic commands from the store
  const allCommands = useMemo(() => {
    // Convert store slash commands to SlashCommand format
    const storeSlash = storeCommands
      .filter((c) => c.show_in_slash)
      .filter((c) => !SLASH_COMMANDS.some((s) => s.id === c.id)) // pas de doublons
      .map((c): SlashCommand => {
        const IconComp = typeof c.icon === 'string' ? ICON_MAP[c.icon] : null;
        // Pour les commandes utilisateur avec template, injecter le template
        const prefix = c.source === 'user' && c.prompt_template
          ? c.prompt_template
          : `/${c.name} `;
        return {
          id: c.id,
          name: c.name,
          description: c.description,
          icon: IconComp ? <IconComp className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />,
          prefix,
        };
      });

    const base = [...SLASH_COMMANDS, ...storeSlash];
    // Ajouter aussi les userCommands props (ancien système, fallback)
    if (userCommands && userCommands.length > 0) {
      const ids = new Set(base.map((c) => c.id));
      for (const uc of userCommands) {
        if (!ids.has(uc.id)) base.push(uc);
      }
    }
    return base;
  }, [storeCommands, userCommands]);

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
        // Échap : géré par la pile unifiée (resolveEscape via escapeStack, correctif
        // KO Syn 1.3) ; ne plus le traiter ici sinon il ferme aussi la sidebar.
      }
    },
    [isOpen, selectedIndex, filteredCommands, onIndexChange, onSelect]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Le menu slash s'inscrit sur la pile d'Échap : Échap le ferme via resolveEscape
  // sans effet de bord (sidebar) — correctif KO Syn 1.3.
  useEffect(() => {
    if (!isOpen) return;
    return pushEscapeHandler(onClose);
  }, [isOpen, onClose]);

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
        Z_LAYER.MODAL, 'w-full max-w-md',
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
