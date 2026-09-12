import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import { cn } from '../../lib/utils';
import { jetonDePastille } from './pastilleDeCarte';
import { Button } from '../ui/Button';

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
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.3,
        delay: index * 0.05,
        ease: [0.4, 0, 0.2, 1],
      }}
      className="h-full"
    >
      <Button
        type="button"
        variant="secondary"
        onClick={isPersonnaliser ? undefined : onClick}
        disabled={isPersonnaliser}
        className={cn(
          'group relative h-full w-full flex-col items-start justify-start p-4 text-left',
          isPersonnaliser && 'cursor-default border-dashed opacity-70',
        )}
      >
      {/* Badge Bientôt */}
      {isPersonnaliser && (
        <span className="absolute top-2.5 right-2.5 px-1.5 py-0.5 rounded-sm text-xs font-medium bg-accent-tint text-accent-cyan-ink border border-accent-cyan/20">
          Bientôt
        </span>
      )}

      {/* Pastille duotone : accent catégoriel k1-k4 cerclé d'encre (DA brutaliste) */}
      <div
        className={cn(
          'relative flex items-center justify-center w-10 h-10 rounded-sm mb-3',
          'border-[1.5px] border-[var(--btn-ink)]',
          isPersonnaliser && 'opacity-50'
        )}
        style={{ background: jetonDePastille(index).fond, color: jetonDePastille(index).teinte }}
      >
        <Icon className={cn('w-5 h-5', isPersonnaliser && 'text-text-muted')} />
      </div>

      {/* Title */}
      <h3 className={cn('relative text-sm font-semibold transition-colors duration-200', isPersonnaliser ? 'text-text-muted' : 'text-text group-hover:text-text')}>
        {title}
      </h3>

      {/* Description */}
      <p className="relative mt-1 line-clamp-2 text-sm font-normal text-text-muted">
        {description}
      </p>
      </Button>
    </motion.div>
  );
}
