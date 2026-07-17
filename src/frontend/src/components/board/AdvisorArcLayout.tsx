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
// Harmonisation 17/07 : mêmes portraits que la nouvelle interface
// (BoardConversationCard) - un seul visage par conseiller dans toute l'app.
import { CharacterPortrait } from '../prototype/DecisionMissionPrototype';

const ADVISOR_PORTRAITS: Record<AdvisorRole, number> = {
  analyst: 1, strategist: 2, devil: 3, pragmatic: 4, visionary: 5,
};

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

export interface OllamaModelInfo {
  name: string;
  size: number; // bytes
  paramSize?: string; // e.g. "7B", "14B"
}

function formatSize(bytes: number): string {
  if (bytes === 0) return '';
  const gb = bytes / 1_073_741_824;
  return gb >= 1 ? `${gb.toFixed(1)} Go` : `${(bytes / 1_048_576).toFixed(0)} Mo`;
}

function sizeColor(bytes: number): string {
  const gb = bytes / 1_073_741_824;
  if (gb < 4) return 'text-green-400';
  if (gb < 8) return 'text-warning';
  return 'text-red-400';
}

interface AdvisorArcLayoutProps {
  mode: BoardMode;
  ollamaModels: OllamaModelInfo[];
  selectedModels: Record<string, string>;
  onModelChange: (role: string, model: string) => void;
}

export function AdvisorArcLayout({
  mode,
  ollamaModels,
  selectedModels,
  onModelChange,
}: AdvisorArcLayoutProps) {
  const defaultModel = ollamaModels[0]?.name || 'mistral-nemo';

  return (
    <div className="relative py-4">
      {/* Hardware recommendation (sovereign mode) */}
      {mode === 'sovereign' && ollamaModels.length > 0 && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mb-4 px-4 py-2.5 rounded-lg bg-surface-elevated/60 border border-border/40 text-center space-y-1"
        >
          <p className="text-xs text-text-muted">
            <span className="text-green-400">&#9679;</span> &lt; 4 Go (8 Go RAM)
            {' '}<span className="text-warning ml-2">&#9679;</span> 4-8 Go (16 Go RAM)
            {' '}<span className="text-red-400 ml-2">&#9679;</span> &gt; 8 Go (32 Go+ RAM)
          </p>
          <p className="text-[10px] text-text-muted/70">
            Choisis des modèles adaptés à ta machine pour éviter les ralentissements
          </p>
        </motion.div>
      )}

      {/* Arc layout for md+ screens */}
      <div className="hidden md:flex justify-center items-end gap-3 min-h-[260px] relative">
        {/* Halo atmosphérique neutre (les anciens visages androïdes en
            filigrane sont partis avec le strip - remarque Ludo 17/07) */}
        <div
          className="pointer-events-none absolute inset-0 overflow-hidden rounded-2xl"
          style={{
            background:
              'radial-gradient(ellipse 70% 60% at center 30%, var(--color-accent-tint) 0%, transparent 75%)',
          }}
        />

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
              className="w-36 flex flex-col items-center relative z-10"
              style={{
                transform: `translateY(${yOffset}px) rotate(${angle * 0.1}deg)`,
              }}
            >
              {/* Portrait partagé avec la nouvelle interface, anneau couleur conservé */}
              <div
                className="w-16 h-16 rounded-[14px] mb-2 relative overflow-hidden"
                style={{
                  boxShadow: `0 0 16px ${meta.color}30`,
                  outline: `2px solid ${meta.color}50`,
                  outlineOffset: '2px',
                }}
              >
                <CharacterPortrait index={ADVISOR_PORTRAITS[role]} className="h-full w-full" />
                <div
                  className="absolute bottom-0 right-0 flex h-5 w-5 items-center justify-center rounded-tl-[8px]"
                  style={{ backgroundColor: meta.color }}
                >
                  <Icon className="h-3 w-3 text-white" />
                </div>
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
                  value={selectedModels[role] || defaultModel}
                  onChange={(e) => onModelChange(role, e.target.value)}
                  className="mt-1.5 w-full text-[10px] px-1.5 py-1 bg-surface border border-border/50 rounded text-text-muted focus:outline-none focus:ring-1 focus:ring-accent-magenta/50"
                >
                  {ollamaModels.map((m) => (
                    <option key={m.name} value={m.name} className={sizeColor(m.size)}>
                      {m.name} {m.size > 0 ? `(${formatSize(m.size)})` : ''}
                    </option>
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
                className="relative mb-1 h-10 w-10 overflow-hidden rounded-[10px]"
                style={{ outline: `2px solid ${meta.color}50` }}
              >
                <CharacterPortrait index={ADVISOR_PORTRAITS[role]} className="h-full w-full" />
                <div
                  className="absolute bottom-0 right-0 flex h-4 w-4 items-center justify-center rounded-tl-[6px]"
                  style={{ backgroundColor: meta.color }}
                >
                  <Icon className="h-2.5 w-2.5 text-white" />
                </div>
              </div>
              <span className="text-[10px] font-medium text-center" style={{ color: meta.color }}>
                {meta.name}
              </span>

              {mode === 'sovereign' && ollamaModels.length > 0 && (
                <select
                  value={selectedModels[role] || defaultModel}
                  onChange={(e) => onModelChange(role, e.target.value)}
                  className="mt-1 w-full text-[9px] px-1 py-0.5 bg-surface border border-border/50 rounded text-text-muted"
                >
                  {ollamaModels.map((m) => (
                    <option key={m.name} value={m.name}>
                      {m.name} {m.size > 0 ? `(${formatSize(m.size)})` : ''}
                    </option>
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
