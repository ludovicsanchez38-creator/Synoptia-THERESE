/**
 * THÉRÈSE V3 - CommandCategoryGroup
 *
 * Groupe de commandes par catégorie avec titre.
 * Style inspiré v0.2.3 : header icon + label uppercase, chips en flex-wrap.
 */

import type { ReactNode } from 'react';
import { Sparkles, Brain, GitBranch, type LucideIcon } from 'lucide-react';
import { CommandCard } from './CommandCard';
import type { CommandDefinition } from '../../types/command';

const CATEGORY_CONFIG: Record<string, { label: string; icon: LucideIcon }> = {
  production: { label: 'Produire', icon: Sparkles },
  analyse: { label: 'Comprendre', icon: Brain },
  organisation: { label: 'Organiser', icon: GitBranch },
};

interface CommandCategoryGroupProps {
  category: string;
  commands: CommandDefinition[];
  onCommandClick: (command: CommandDefinition) => void;
  startIndex: number;
  /** Bouton optionnel rendu inline après les commandes */
  extraButton?: ReactNode;
}

export function CommandCategoryGroup({
  category,
  commands,
  onCommandClick,
  startIndex,
  extraButton,
}: CommandCategoryGroupProps) {
  const config = CATEGORY_CONFIG[category] || { label: category, icon: Sparkles };
  const Icon = config.icon;

  if (commands.length === 0 && !extraButton) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 text-accent-cyan/70" />
        <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest">
          {config.label}
        </h3>
      </div>
      <div className="flex flex-wrap gap-2.5">
        {commands.map((cmd, i) => (
          <CommandCard
            key={cmd.id}
            command={cmd}
            onClick={onCommandClick}
            index={startIndex + i}
          />
        ))}
        {extraButton}
      </div>
    </div>
  );
}
