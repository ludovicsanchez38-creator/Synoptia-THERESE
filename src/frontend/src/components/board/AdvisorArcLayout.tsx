/**
 * THÉRÈSE v2 - Advisor Arc Layout
 *
 * Affiche les 5 conseillers en arc de cercle.
 * En mode souverain, affiche un mini-select modèle Ollama sur chaque carte.
 * Responsive : fallback grille 3+2 sur petits écrans.
 */

import { motion } from 'framer-motion';
import {
  BarChart3,
  Target,
  Flame,
  Wrench,
  Rocket,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import type { AdvisorRole } from '../../services/api';
import type { BoardMode } from './ModeSelector';

const ADVISOR_ICONS: Record<AdvisorRole, LucideIcon> = {
  analyst: BarChart3,
  strategist: Target,
  devil: Flame,
  pragmatic: Wrench,
  visionary: Rocket,
};

const ADVISOR_META: Record<AdvisorRole, { name: string; color: string; personality: string }> = {
  analyst: { name: "L'Analyste", color: '#22D3EE', personality: 'Données & Chiffres' },
  strategist: { name: 'Le Stratège', color: '#A855F7', personality: 'Vision long terme' },
  devil: { name: "L'Avocat du Diable", color: '#EF4444', personality: 'Contre-arguments' },
  pragmatic: { name: 'Le Pragmatique', color: '#F59E0B', personality: 'Faisabilité' },
  visionary: { name: 'Le Visionnaire', color: '#E11D8D', personality: 'Innovation' },
};

const ROLES: AdvisorRole[] = ['analyst', 'strategist', 'devil', 'pragmatic', 'visionary'];
const ARC_ANGLES = [-50, -25, 0, 25, 50]; // Degrees for 5 cards

interface AdvisorArcLayoutProps {
  mode: BoardMode;
  ollamaModels: string[];
  selectedModels: Record<string, string>;
  onModelChange: (role: string, model: string) => void;
}

export function AdvisorArcLayout({
  mode,
  ollamaModels,
  selectedModels,
  onModelChange,
}: AdvisorArcLayoutProps) {
  return (
    <div className="relative py-4">
      {/* Arc layout for md+ screens */}
      <div className="hidden md:flex justify-center items-end gap-3 min-h-[220px]">
        {ROLES.map((role, i) => {
          const meta = ADVISOR_META[role];
          const Icon = ADVISOR_ICONS[role];
          const angle = ARC_ANGLES[i];
          const yOffset = Math.abs(angle) * 0.6; // Parabolic curve

          return (
            <motion.div
              key={role}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
              className="w-36 flex flex-col items-center"
              style={{
                transform: `translateY(${yOffset}px) rotate(${angle * 0.1}deg)`,
              }}
            >
              {/* Avatar */}
              <div
                className="w-14 h-14 rounded-full flex items-center justify-center mb-2"
                style={{
                  backgroundColor: `${meta.color}15`,
                  boxShadow: `0 0 12px ${meta.color}25`,
                  outline: `2px solid ${meta.color}40`,
                  outlineOffset: '2px',
                }}
              >
                <Icon className="w-6 h-6" style={{ color: meta.color }} />
              </div>

              {/* Name */}
              <span
                className="text-xs font-semibold text-center leading-tight"
                style={{ color: meta.color }}
              >
                {meta.name}
              </span>
              <span className="text-[10px] text-text-muted text-center">
                {meta.personality}
              </span>

              {/* Ollama model selector (sovereign mode) */}
              {mode === 'sovereign' && ollamaModels.length > 0 && (
                <select
                  value={selectedModels[role] || ollamaModels[0] || 'mistral-nemo'}
                  onChange={(e) => onModelChange(role, e.target.value)}
                  className="mt-1.5 w-full text-[10px] px-1.5 py-1 bg-surface border border-border/50 rounded text-text-muted focus:outline-none focus:ring-1 focus:ring-accent-magenta/50"
                >
                  {ollamaModels.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Grid fallback for small screens */}
      <div className="md:hidden grid grid-cols-3 gap-3">
        {ROLES.map((role, i) => {
          const meta = ADVISOR_META[role];
          const Icon = ADVISOR_ICONS[role];

          return (
            <motion.div
              key={role}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.06 }}
              className={cn(
                'flex flex-col items-center p-2 rounded-lg bg-surface-elevated/50 border border-border/30',
                i >= 3 && 'col-span-1',
              )}
            >
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center mb-1"
                style={{ backgroundColor: `${meta.color}15` }}
              >
                <Icon className="w-4 h-4" style={{ color: meta.color }} />
              </div>
              <span className="text-[10px] font-medium text-center" style={{ color: meta.color }}>
                {meta.name}
              </span>

              {mode === 'sovereign' && ollamaModels.length > 0 && (
                <select
                  value={selectedModels[role] || ollamaModels[0] || 'mistral-nemo'}
                  onChange={(e) => onModelChange(role, e.target.value)}
                  className="mt-1 w-full text-[9px] px-1 py-0.5 bg-surface border border-border/50 rounded text-text-muted"
                >
                  {ollamaModels.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
