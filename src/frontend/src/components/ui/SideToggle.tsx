/**
 * THÉRÈSE v2 - Side Toggle Component
 *
 * Rail latéral pour ouvrir/fermer les panels (Conversations, Mémoire)
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen } from 'lucide-react';

interface SideToggleProps {
  side: 'left' | 'right';
  isOpen: boolean;
  onClick: () => void;
  label: string;
  shortcut: string;
}

export function SideToggle({ side, isOpen, onClick, label, shortcut }: SideToggleProps) {
  const [isHovered, setIsHovered] = useState(false);
  const isLeft = side === 'left';

  // Sélection des icônes selon le côté et l'état
  const Icon = isLeft
    ? isOpen
      ? PanelLeftClose
      : PanelLeftOpen
    : isOpen
      ? PanelRightClose
      : PanelRightOpen;

  return (
    <motion.button
      className={`
        fixed z-30 overflow-hidden
        cursor-pointer
        ${isLeft ? 'left-0 rounded-r-lg' : 'right-0 rounded-l-lg'}
      `}
      style={{
        top: '56px',
        bottom: '0',
      }}
      initial={{ width: 8 }}
      animate={{ width: isHovered ? 32 : 8 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
      title={`${label} (${shortcut})`}
      aria-label={`${isOpen ? 'Fermer' : 'Ouvrir'} ${label}`}
    >
      {/* Rail de fond avec gradient */}
      <div
        className={`
          absolute inset-0
          bg-gradient-to-b from-surface/40 via-surface/80 to-surface/40
          backdrop-blur-sm
          ${isLeft ? 'border-r' : 'border-l'} border-white/5
          transition-colors duration-300
          ${isOpen ? 'bg-accent-cyan/10' : ''}
        `}
      />

      {/* Indicateur vertical - centré */}
      <div
        className={`
          absolute ${isLeft ? 'right-1' : 'left-1'}
          top-1/2 -translate-y-1/2
          w-0.5 rounded-full
          transition-all duration-300
          ${isOpen
            ? 'h-16 bg-accent-cyan shadow-[0_0_12px_rgba(34,211,238,0.5)]'
            : 'h-10 bg-accent-cyan/40'
          }
          ${isHovered ? 'bg-accent-cyan/70' : ''}
        `}
      />

      {/* Icône (visible au hover) - centrée */}
      <AnimatePresence>
        {isHovered && (
          <motion.div
            className={`
              absolute top-1/2 -translate-y-1/2
              ${isLeft ? 'left-1.5' : 'right-1.5'}
              text-accent-cyan
            `}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.5 }}
            transition={{ duration: 0.15 }}
          >
            <Icon size={16} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Glow effect au hover */}
      <motion.div
        className={`
          absolute inset-0 pointer-events-none
          ${isLeft
            ? 'bg-gradient-to-r from-transparent to-accent-cyan/10'
            : 'bg-gradient-to-l from-transparent to-accent-cyan/10'
          }
        `}
        initial={{ opacity: 0 }}
        animate={{ opacity: isHovered ? 1 : 0 }}
        transition={{ duration: 0.2 }}
      />
    </motion.button>
  );
}

export default SideToggle;
