import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  Presentation,
  Table,
  Download,
  Check,
  Loader2,
  X,
  RefreshCw,
} from 'lucide-react';
import type { FileFormat } from './actionData';
import { cn } from '../../lib/utils';

export type SkillExecutionStatus = 'idle' | 'generating' | 'success' | 'error';

interface SkillExecutionPanelProps {
  skillId: string;
  format: FileFormat;
  status: SkillExecutionStatus;
  fileName?: string;
  fileSize?: number;
  downloadUrl?: string;
  error?: string;
  onDownload?: () => void;
  onRetry?: () => void;
  onClose?: () => void;
}

// Config par format
const formatConfig: Record<FileFormat, {
  icon: typeof FileText;
  color: string;
  bgGradient: string;
  label: string;
  description: string;
}> = {
  docx: {
    icon: FileText,
    color: 'text-blue-400',
    bgGradient: 'from-blue-500/20 to-blue-600/10',
    label: 'Document Word',
    description: 'Fichier .docx prêt à être téléchargé'
  },
  pptx: {
    icon: Presentation,
    color: 'text-orange-400',
    bgGradient: 'from-orange-500/20 to-orange-600/10',
    label: 'Présentation PowerPoint',
    description: 'Fichier .pptx prêt à être téléchargé'
  },
  xlsx: {
    icon: Table,
    color: 'text-green-400',
    bgGradient: 'from-green-500/20 to-green-600/10',
    label: 'Tableur Excel',
    description: 'Fichier .xlsx prêt à être téléchargé'
  },
  pdf: {
    icon: FileText,
    color: 'text-red-400',
    bgGradient: 'from-red-500/20 to-red-600/10',
    label: 'Document PDF',
    description: 'Fichier .pdf prêt à être téléchargé'
  },
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function SkillExecutionPanel({
  skillId: _skillId,
  format,
  status,
  fileName,
  fileSize,
  downloadUrl: _downloadUrl,
  error,
  onDownload,
  onRetry,
  onClose,
}: SkillExecutionPanelProps) {
  // _skillId et _downloadUrl réservés pour usage futur (preview, etc.)
  void _skillId;
  void _downloadUrl;
  const config = formatConfig[format];
  const FormatIcon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className={cn(
        'relative w-full max-w-md mx-auto',
        'bg-surface-elevated rounded-2xl border border-border',
        'overflow-hidden shadow-xl'
      )}
    >
      {/* Gradient background */}
      <div className={cn(
        'absolute inset-0 bg-gradient-to-br opacity-50',
        config.bgGradient
      )} />

      {/* Content */}
      <div className="relative p-6">
        {/* Close button */}
        {onClose && status !== 'generating' && (
          <button
            onClick={onClose}
            className={cn(
              'absolute top-4 right-4 p-1.5 rounded-lg',
              'text-text-muted hover:text-text',
              'hover:bg-white/5 transition-colors'
            )}
          >
            <X className="w-4 h-4" />
          </button>
        )}

        {/* Icon + Status */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className={cn(
            'relative w-16 h-16 rounded-2xl flex items-center justify-center mb-4',
            'bg-gradient-to-br',
            config.bgGradient
          )}>
            <FormatIcon className={cn('w-8 h-8', config.color)} />

            {/* Status indicator */}
            <AnimatePresence mode="wait">
              {status === 'generating' && (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0 }}
                  className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-surface flex items-center justify-center"
                >
                  <Loader2 className="w-4 h-4 text-accent-cyan animate-spin" />
                </motion.div>
              )}
              {status === 'success' && (
                <motion.div
                  key="success"
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0 }}
                  className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-green-500 flex items-center justify-center"
                >
                  <Check className="w-3.5 h-3.5 text-white" />
                </motion.div>
              )}
              {status === 'error' && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0 }}
                  className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-red-500 flex items-center justify-center"
                >
                  <X className="w-3.5 h-3.5 text-white" />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Title */}
          <h3 className="text-lg font-semibold text-text mb-1">
            {status === 'generating' && 'Génération en cours...'}
            {status === 'success' && config.label}
            {status === 'error' && 'Erreur de génération'}
            {status === 'idle' && 'Prêt à générer'}
          </h3>

          {/* Description */}
          <p className="text-sm text-text-muted">
            {status === 'generating' && 'THÉRÈSE prépare votre document'}
            {status === 'success' && config.description}
            {status === 'error' && (error || 'Une erreur est survenue')}
            {status === 'idle' && `Créer un fichier ${format.toUpperCase()}`}
          </p>
        </div>

        {/* File info (success state) */}
        {status === 'success' && fileName && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
              'mb-6 p-4 rounded-xl',
              'bg-white/5 border border-white/10'
            )}
          >
            <div className="flex items-center gap-3">
              <div className={cn(
                'w-10 h-10 rounded-lg flex items-center justify-center',
                'bg-gradient-to-br',
                config.bgGradient
              )}>
                <FormatIcon className={cn('w-5 h-5', config.color)} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text truncate">
                  {fileName}
                </p>
                {fileSize && (
                  <p className="text-xs text-text-muted">
                    {formatFileSize(fileSize)}
                  </p>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* Loading animation */}
        {status === 'generating' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-6"
          >
            <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-accent-cyan to-accent-magenta"
                initial={{ x: '-100%' }}
                animate={{ x: '100%' }}
                transition={{
                  repeat: Infinity,
                  duration: 1.5,
                  ease: 'linear'
                }}
                style={{ width: '50%' }}
              />
            </div>
          </motion.div>
        )}

        {/* Action buttons */}
        <div className="flex gap-3">
          {status === 'success' && onDownload && (
            <motion.button
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onDownload}
              className={cn(
                'flex-1 flex items-center justify-center gap-2',
                'px-4 py-3 rounded-xl font-medium',
                'bg-accent-cyan hover:bg-accent-cyan/90',
                'text-bg shadow-lg shadow-accent-cyan/20',
                'hover:shadow-accent-cyan/30 transition-all'
              )}
            >
              <Download className="w-4 h-4" />
              Télécharger
            </motion.button>
          )}

          {status === 'error' && onRetry && (
            <motion.button
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onRetry}
              className={cn(
                'flex-1 flex items-center justify-center gap-2',
                'px-4 py-3 rounded-xl font-medium',
                'bg-surface border border-border',
                'text-text hover:bg-surface-elevated',
                'transition-colors'
              )}
            >
              <RefreshCw className="w-4 h-4" />
              Réessayer
            </motion.button>
          )}
        </div>
      </div>
    </motion.div>
  );
}
