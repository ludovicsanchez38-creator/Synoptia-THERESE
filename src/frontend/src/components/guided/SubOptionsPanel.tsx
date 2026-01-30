import { motion } from 'framer-motion';
import { ChevronLeft, FileText, Presentation, Table } from 'lucide-react';
import type { SubOption, GuidedAction, FileFormat } from './actionData';
import { cn } from '../../lib/utils';

// Mapping format -> icône et couleur
const formatConfig: Record<FileFormat, { icon: typeof FileText; color: string; label: string }> = {
  docx: { icon: FileText, color: 'text-blue-400 bg-blue-400/20', label: 'DOCX' },
  pptx: { icon: Presentation, color: 'text-orange-400 bg-orange-400/20', label: 'PPTX' },
  xlsx: { icon: Table, color: 'text-green-400 bg-green-400/20', label: 'XLSX' },
  pdf: { icon: FileText, color: 'text-red-400 bg-red-400/20', label: 'PDF' },
};

interface SubOptionsPanelProps {
  action: GuidedAction;
  onSelect: (option: SubOption) => void;
  onBack: () => void;
}

export function SubOptionsPanel({ action, onSelect, onBack }: SubOptionsPanelProps) {
  const Icon = action.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
      className="w-full max-w-lg"
    >
      {/* Back button */}
      <motion.button
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.1 }}
        onClick={onBack}
        className={cn(
          'flex items-center gap-2 text-sm text-text-muted hover:text-text',
          'transition-colors duration-150 mb-4',
          'focus:outline-none focus:text-accent-cyan'
        )}
      >
        <ChevronLeft className="w-4 h-4" />
        <span>Retour</span>
      </motion.button>

      {/* Header with icon and question */}
      <div className="flex items-center gap-3 mb-6">
        <div className={cn(
          'flex items-center justify-center w-12 h-12 rounded-xl',
          'bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20'
        )}>
          <Icon className="w-6 h-6 text-accent-cyan" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-text">{action.title}</h3>
          <p className="text-sm text-text-muted">{action.question}</p>
        </div>
      </div>

      {/* Options as pills */}
      <div className="flex flex-wrap gap-3">
        {action.options.map((option, index) => (
          <motion.button
            key={option.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.2,
              delay: 0.1 + index * 0.05,
            }}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => onSelect(option)}
            className={cn(
              'px-4 py-2.5 rounded-full text-sm font-medium',
              'bg-surface-elevated border border-border',
              'hover:border-accent-cyan/50 hover:bg-surface-elevated/80',
              'hover:shadow-[0_0_15px_rgba(34,211,238,0.1)]',
              'text-text-muted hover:text-text',
              'transition-all duration-150',
              'focus:outline-none focus:ring-2 focus:ring-accent-cyan/30',
              'flex items-center gap-2'
            )}
          >
            {option.label}
            {option.generatesFile && (() => {
              const config = formatConfig[option.generatesFile.format];
              const FormatIcon = config.icon;
              return (
                <span className={cn(
                  'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold',
                  config.color
                )}>
                  <FormatIcon className="w-3 h-3" />
                  {config.label}
                </span>
              );
            })()}
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}
