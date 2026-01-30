import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Sparkles, FileText, Presentation, Table } from 'lucide-react';
import type { SubOption, FileFormat } from './actionData';
import { cn } from '../../lib/utils';

interface SkillPromptPanelProps {
  option: SubOption;
  onGenerate: (customPrompt: string) => void;
  onBack: () => void;
}

// Config par format
const formatConfig: Record<FileFormat, {
  icon: typeof FileText;
  color: string;
  bgGradient: string;
}> = {
  docx: {
    icon: FileText,
    color: 'text-blue-400',
    bgGradient: 'from-blue-500/20 to-blue-600/10',
  },
  pptx: {
    icon: Presentation,
    color: 'text-orange-400',
    bgGradient: 'from-orange-500/20 to-orange-600/10',
  },
  xlsx: {
    icon: Table,
    color: 'text-green-400',
    bgGradient: 'from-green-500/20 to-green-600/10',
  },
  pdf: {
    icon: FileText,
    color: 'text-red-400',
    bgGradient: 'from-red-500/20 to-red-600/10',
  },
};

export function SkillPromptPanel({ option, onGenerate, onBack }: SkillPromptPanelProps) {
  const [prompt, setPrompt] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const format = option.generatesFile?.format || 'docx';
  const config = formatConfig[format];
  const FormatIcon = config.icon;

  // Focus textarea on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleGenerate = () => {
    if (prompt.trim()) {
      onGenerate(prompt.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Cmd/Ctrl + Enter to generate
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleGenerate();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.2 }}
      className="w-full max-w-lg mx-auto"
    >
      {/* Header with back button */}
      <div className="flex items-center gap-3 mb-6">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onBack}
          className={cn(
            'p-2 rounded-xl',
            'bg-surface-elevated border border-border',
            'text-text-muted hover:text-text',
            'transition-colors'
          )}
        >
          <ArrowLeft className="w-4 h-4" />
        </motion.button>

        <div className="flex items-center gap-3">
          <div className={cn(
            'w-10 h-10 rounded-xl flex items-center justify-center',
            'bg-gradient-to-br',
            config.bgGradient
          )}>
            <FormatIcon className={cn('w-5 h-5', config.color)} />
          </div>
          <div>
            <h3 className="font-semibold text-text">{option.label}</h3>
            <p className="text-xs text-text-muted">
              Fichier .{format} avec style Synoptïa
            </p>
          </div>
        </div>
      </div>

      {/* Prompt textarea */}
      <div className={cn(
        'rounded-2xl border border-border',
        'bg-surface-elevated/80 backdrop-blur-sm',
        'focus-within:border-accent-cyan/50',
        'focus-within:shadow-[0_0_20px_rgba(34,211,238,0.1)]',
        'transition-all duration-200'
      )}>
        <textarea
          ref={textareaRef}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Décris ce que tu veux créer..."
          rows={5}
          className={cn(
            'w-full p-4 bg-transparent resize-none',
            'text-text placeholder:text-text-muted',
            'focus:outline-none',
            'text-sm leading-relaxed'
          )}
        />

        {/* Footer with hints and generate button */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-border/50">
          <p className="text-xs text-text-muted">
            <kbd className="px-1.5 py-0.5 rounded bg-surface text-text-muted">⌘</kbd>
            <span className="mx-1">+</span>
            <kbd className="px-1.5 py-0.5 rounded bg-surface text-text-muted">↵</kbd>
            <span className="ml-2">pour générer</span>
          </p>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleGenerate}
            disabled={!prompt.trim()}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-xl',
              'font-medium text-sm',
              'bg-accent-cyan hover:bg-accent-cyan/90',
              'text-bg shadow-lg shadow-accent-cyan/20',
              'hover:shadow-accent-cyan/30 transition-all',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            <Sparkles className="w-4 h-4" />
            Générer
          </motion.button>
        </div>
      </div>

      {/* Suggestions */}
      <div className="mt-4 space-y-2">
        <p className="text-xs text-text-muted font-medium">Exemples :</p>
        <div className="flex flex-wrap gap-2">
          {getSuggestions(format).map((suggestion, i) => (
            <button
              key={i}
              onClick={() => setPrompt(suggestion)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-xs',
                'bg-surface border border-border',
                'text-text-muted hover:text-text',
                'hover:border-accent-cyan/30',
                'transition-colors'
              )}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

function getSuggestions(format: FileFormat): string[] {
  switch (format) {
    case 'docx':
      return [
        'Une proposition commerciale pour un client e-commerce',
        'Un compte-rendu de réunion projet',
        'Un contrat de prestation freelance',
      ];
    case 'pptx':
      return [
        'Une présentation de mon offre de services',
        'Un pitch deck pour lever des fonds',
        'Une formation sur les outils IA',
      ];
    case 'xlsx':
      return [
        'Un tableau de suivi de facturation',
        'Un budget prévisionnel annuel',
        'Un planning de projet avec Gantt',
      ];
    case 'pdf':
      return [
        'Un devis pour une prestation web',
        'Une facture avec TVA',
        'Un bon de commande',
      ];
    default:
      return [];
  }
}
