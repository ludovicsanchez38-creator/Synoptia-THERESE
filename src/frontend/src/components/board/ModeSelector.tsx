/**
 * THÉRÈSE v2 - Board Mode Selector
 *
 * Toggle Cloud / Souverain pour le Board de Décision.
 * Mode souverain = Ollama local, séquentiel, pas de recherche web.
 */

import { motion } from 'framer-motion';
import { Cloud, Shield, RefreshCw } from 'lucide-react';
import { cn } from '../../lib/utils';

export type BoardMode = 'cloud' | 'sovereign';

interface ModeSelectorProps {
  mode: BoardMode;
  onChange: (mode: BoardMode) => void;
  ollamaAvailable: boolean;
  onRefreshOllama?: () => void;
}

export function ModeSelector({ mode, onChange, ollamaAvailable, onRefreshOllama }: ModeSelectorProps) {
  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => onChange('cloud')}
        className={cn(
          'relative flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all',
          mode === 'cloud'
            ? 'text-accent-cyan-ink'
            : 'text-text-muted hover:text-text',
        )}
      >
        {/* B-639 / B-640 (Nadia, c4) : l'indicateur partageait un `layoutId`
            entre les deux boutons. Après une bascule de mode, aucune sortie
            d'AnimatePresence au-dessus (changement de vue, fermeture du
            dialogue Décision) ne se terminait plus : le dialogue restait
            monté à opacité 0, cliquable. Un fondu par bouton suffit. */}
        {mode === 'cloud' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 bg-accent-cyan/10 border border-accent-cyan/30 rounded-md"
          />
        )}
        <Cloud className="w-4 h-4 relative z-10" />
        <span className="relative z-10">Cloud</span>
      </button>

      <button
        onClick={() => ollamaAvailable && onChange('sovereign')}
        disabled={!ollamaAvailable}
        title={ollamaAvailable ? 'Mode souverain - Ollama local' : 'Ollama non disponible'}
        className={cn(
          'relative flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all',
          !ollamaAvailable && 'opacity-40 cursor-not-allowed',
          mode === 'sovereign'
            ? 'text-accent-magenta-ink'
            : 'text-text-muted hover:text-text',
        )}
      >
        {mode === 'sovereign' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 bg-accent-magenta/10 border border-accent-magenta/30 rounded-md"
          />
        )}
        <Shield className="w-4 h-4 relative z-10" />
        <span className="relative z-10">Souverain</span>
      </button>

      {!ollamaAvailable && onRefreshOllama && (
        <button
          onClick={onRefreshOllama}
          title="Vérifier Ollama"
          className="p-1.5 rounded-md text-text-muted hover:text-accent-cyan-ink hover:bg-accent-tint transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}
