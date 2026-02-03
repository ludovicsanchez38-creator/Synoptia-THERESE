import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ActionCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  onClick: () => void;
  index: number;
  variant?: 'default' | 'personnaliser';
}

export function ActionCard({ icon: Icon, title, description, onClick, index, variant = 'default' }: ActionCardProps) {
  const isPersonnaliser = variant === 'personnaliser';

  return (
    <motion.button
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.3,
        delay: index * 0.05,
        ease: [0.4, 0, 0.2, 1],
      }}
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        'group relative flex flex-col items-start p-4 rounded-xl',
        'bg-surface-elevated/60 backdrop-blur-sm',
        'transition-all duration-200 text-left',
        'focus:outline-none focus:ring-2 focus:ring-accent-cyan/30',
        isPersonnaliser
          ? 'border-2 border-dashed border-accent-cyan/30 hover:border-accent-cyan/60 hover:shadow-[0_0_20px_rgba(34,211,238,0.2)]'
          : 'border border-border hover:border-accent-cyan/50 hover:shadow-[0_0_20px_rgba(34,211,238,0.15)]'
      )}
    >
      {/* Gradient glow on hover */}
      <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-accent-cyan/5 to-accent-magenta/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      {/* Icon container */}
      <div className={cn(
        'relative flex items-center justify-center w-10 h-10 rounded-lg mb-3',
        'bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20',
        'group-hover:from-accent-cyan/30 group-hover:to-accent-magenta/30',
        'transition-all duration-200'
      )}>
        <Icon className="w-5 h-5 text-accent-cyan group-hover:text-white transition-colors duration-200" />
      </div>

      {/* Title */}
      <h3 className="relative text-sm font-semibold text-text group-hover:text-white transition-colors duration-200">
        {title}
      </h3>

      {/* Description */}
      <p className="relative text-xs text-text-muted mt-1 line-clamp-2">
        {description}
      </p>
    </motion.button>
  );
}
