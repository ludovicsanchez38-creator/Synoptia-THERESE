/**
 * THÉRÈSE V3 - CommandCard
 *
 * Chip cliquable représentant une commande sur la page d'accueil.
 * Style v0.2.3 : pill arrondi, bordure subtile, icône cyan.
 */

import { motion } from 'framer-motion';
import {
  Mail, Linkedin, FileText, Presentation, FileSpreadsheet,
  Globe, TrendingUp, Bot, Lightbulb, CheckCircle,
  Calendar, FolderKanban, CalendarDays, Target, Workflow,
  ImagePlus, Zap, Plus, Sparkles, Brain, GitBranch,
  UserPlus, FolderPlus, Search, ListTodo, Mic,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import type { CommandDefinition } from '../../types/command';

/** Mapping nom d'icône Lucide -> composant */
const ICON_MAP: Record<string, LucideIcon> = {
  Mail, Linkedin, FileText, Presentation, FileSpreadsheet,
  Globe, TrendingUp, Bot, Lightbulb, CheckCircle,
  Calendar, FolderKanban, CalendarDays, Target, Workflow,
  ImagePlus, Zap, Plus, Sparkles, Brain, GitBranch,
  UserPlus, FolderPlus, Search, ListTodo, Mic,
};

interface CommandCardProps {
  command: CommandDefinition;
  onClick: (command: CommandDefinition) => void;
  index: number;
}

export function CommandCard({ command, onClick, index }: CommandCardProps) {
  // Résoudre l'icône : emoji direct ou composant Lucide
  const isEmoji = command.icon && !ICON_MAP[command.icon];
  const IconComponent = !isEmoji ? ICON_MAP[command.icon] || Zap : null;

  return (
    <motion.button
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.15, delay: index * 0.02 }}
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.97 }}
      onClick={() => onClick(command)}
      className={cn(
        'flex items-center gap-2 px-4 py-2 rounded-full',
        'bg-surface-elevated/50 hover:bg-surface-elevated',
        'border border-border/60 hover:border-accent-cyan/40',
        'text-left transition-colors duration-150',
        'hover:shadow-[0_0_12px_rgba(34,211,238,0.08)]',
        command.source === 'user' && 'border-accent-magenta/30 hover:border-accent-magenta/50',
      )}
      title={command.description}
    >
      <span className="flex-shrink-0 text-accent-cyan">
        {isEmoji ? (
          <span className="text-base">{command.icon}</span>
        ) : IconComponent ? (
          <IconComponent className="w-4 h-4" />
        ) : null}
      </span>
      <span className="text-sm text-text whitespace-nowrap">{command.name}</span>
    </motion.button>
  );
}
