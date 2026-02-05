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
      whileHover={isPersonnaliser ? {} : { scale: 1.02, y: -2 }}
      whileTap={isPersonnaliser ? {} : { scale: 0.98 }}
      onClick={isPersonnaliser ? undefined : onClick}
      disabled={isPersonnaliser}
      className={cn(
        'group relative flex flex-col items-start p-4 rounded-xl',
        'bg-surface-elevated/60 backdrop-blur-sm',
        'transition-all duration-200 text-left',
        'focus:outline-none focus:ring-2 focus:ring-accent-cyan/30',
        isPersonnaliser
          ? 'border-2 border-dashed border-border/40 cursor-default opacity-70'
          : 'border border-border hover:border-accent-cyan/50 hover:shadow-[0_0_20px_rgba(34,211,238,0.15)]'
      )}
    >
      {/* Gradient glow on hover */}
      <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-accent-cyan/5 to-accent-magenta/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      {/* Badge Bientôt */}
      {isPersonnaliser && (
        <span className="absolute top-2.5 right-2.5 px-1.5 py-0.5 rounded text-[9px] font-medium bg-accent-cyan/10 text-accent-cyan/60 border border-accent-cyan/20">
          Bientôt
        </span>
      )}

      {/* Icon container */}
      <div className={cn(
        'relative flex items-center justify-center w-10 h-10 rounded-lg mb-3',
        'bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20',
        isPersonnaliser ? 'opacity-50' : 'group-hover:from-accent-cyan/30 group-hover:to-accent-magenta/30',
        'transition-all duration-200'
      )}>
        <Icon className={cn('w-5 h-5 transition-colors duration-200', isPersonnaliser ? 'text-text-muted' : 'text-accent-cyan group-hover:text-white')} />
      </div>

      {/* Title */}
      <h3 className={cn('relative text-sm font-semibold transition-colors duration-200', isPersonnaliser ? 'text-text-muted' : 'text-text group-hover:text-white')}>
        {title}
      </h3>

      {/* Description */}
      <p className={cn('relative text-xs mt-1 line-clamp-2', isPersonnaliser ? 'text-text-muted/60' : 'text-text-muted')}>
        {description}
      </p>
    </motion.button>
  );
}
