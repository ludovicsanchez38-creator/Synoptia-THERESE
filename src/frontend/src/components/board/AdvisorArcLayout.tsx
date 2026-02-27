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
import advisorsBg from '../../assets/board/advisors-bg.png';

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
// Background position X pour chaque strip de l'image (5 bandes verticales)
const BG_POSITIONS = ['0%', '25%', '50%', '75%', '100%'];

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
  if (gb < 8) return 'text-yellow-400';
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
            {' '}<span className="text-yellow-400 ml-2">&#9679;</span> 4-8 Go (16 Go RAM)
            {' '}<span className="text-red-400 ml-2">&#9679;</span> &gt; 8 Go (32 Go+ RAM)
          </p>
          <p className="text-[10px] text-text-muted/70">
            Choisissez des modèles adaptés à votre machine pour éviter les ralentissements
          </p>
        </motion.div>
      )}

      {/* Arc layout for md+ screens */}
      <div className="hidden md:flex justify-center items-end gap-3 min-h-[260px] relative">
        {/* Image de fond atmosphérique */}
        <div
          className="absolute inset-0 rounded-2xl overflow-hidden opacity-[0.07] pointer-events-none"
          style={{
            backgroundImage: `url(${advisorsBg})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center 20%',
            maskImage: 'radial-gradient(ellipse 80% 70% at center, black 30%, transparent 80%)',
            WebkitMaskImage: 'radial-gradient(ellipse 80% 70% at center, black 30%, transparent 80%)',
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
              {/* Avatar avec visage androïde */}
              <div
                className="w-16 h-16 rounded-full mb-2 relative overflow-hidden"
                style={{
                  boxShadow: `0 0 16px ${meta.color}30, inset 0 0 8px ${meta.color}10`,
                  outline: `2px solid ${meta.color}50`,
                  outlineOffset: '2px',
                }}
              >
                {/* Image de fond - strip du conseiller */}
                <div
                  className="absolute inset-0"
                  style={{
                    backgroundImage: `url(${advisorsBg})`,
                    backgroundSize: '500% auto',
                    backgroundPosition: `${BG_POSITIONS[i]} 15%`,
                  }}
                />
                {/* Overlay sombre + teinte couleur */}
                <div
                  className="absolute inset-0"
                  style={{
                    background: `linear-gradient(180deg, ${meta.color}20 0%, ${meta.color}40 100%)`,
                  }}
                />
                {/* Icône en overlay */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <Icon className="w-5 h-5 drop-shadow-lg" style={{ color: '#fff' }} />
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
