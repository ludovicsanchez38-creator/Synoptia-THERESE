/**
 * THÉRÈSE v2 - Drop Zone Component
 *
 * Visual overlay for drag & drop file handling.
 */

import { motion, AnimatePresence } from 'framer-motion';
import { Upload, File, FileText, FileCode, FileImage } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface DropZoneProps {
  isDragging: boolean;
  className?: string;
}

/**
 * Get icon for file type
 */
function getFileIcon(mimeType?: string) {
  if (!mimeType) return File;

  if (mimeType.startsWith('image/')) return FileImage;
  if (mimeType.startsWith('text/') || mimeType.includes('json')) return FileText;
  if (
    mimeType.includes('python') ||
    mimeType.includes('javascript') ||
    mimeType.includes('typescript')
  )
    return FileCode;

  return File;
}

/**
 * Full-screen drop zone overlay
 */
export function DropZone({ isDragging, className }: DropZoneProps) {
  return (
    <AnimatePresence>
      {isDragging && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className={cn(
            'absolute inset-0 z-50 flex items-center justify-center',
            'bg-background/90 backdrop-blur-sm',
            className
          )}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className={cn(
              'flex flex-col items-center justify-center gap-4 p-12',
              'rounded-3xl border-2 border-dashed border-accent-cyan/50',
              'bg-surface/50'
            )}
          >
            <motion.div
              animate={{
                y: [0, -8, 0],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            >
              <Upload className="w-16 h-16 text-accent-cyan" />
            </motion.div>

            <div className="text-center">
              <h3 className="text-xl font-semibold text-text">
                Déposez vos fichiers
              </h3>
              <p className="mt-2 text-sm text-text-muted">
                PDF, texte, code, images...
              </p>
            </div>

            {/* Supported file types */}
            <div className="flex items-center gap-3 mt-2">
              <FileText className="w-5 h-5 text-text-muted" />
              <FileCode className="w-5 h-5 text-text-muted" />
              <FileImage className="w-5 h-5 text-text-muted" />
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/**
 * Inline drop zone (for ChatInput area)
 */
export interface InlineDropZoneProps {
  isDragging: boolean;
  className?: string;
}

export function InlineDropZone({ isDragging, className }: InlineDropZoneProps) {
  return (
    <AnimatePresence>
      {isDragging && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.15 }}
          className={cn(
            'overflow-hidden rounded-xl border border-dashed border-accent-cyan/50',
            'bg-accent-cyan/5 mb-2',
            className
          )}
        >
          <div className="flex items-center justify-center gap-2 py-3 px-4">
            <Upload className="w-4 h-4 text-accent-cyan" />
            <span className="text-sm text-accent-cyan">
              Déposez ici pour joindre
            </span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/**
 * File chip for displaying attached files
 */
export interface FileChipProps {
  name: string;
  mimeType?: string;
  size?: number;
  onRemove?: () => void;
  className?: string;
}

export function FileChip({
  name,
  mimeType,
  size,
  onRemove,
  className,
}: FileChipProps) {
  const Icon = getFileIcon(mimeType);

  // Format size
  const formattedSize = size
    ? size < 1024
      ? `${size} B`
      : size < 1024 * 1024
        ? `${(size / 1024).toFixed(1)} KB`
        : `${(size / (1024 * 1024)).toFixed(1)} MB`
    : null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className={cn(
        'inline-flex items-center gap-2 px-3 py-1.5 rounded-lg',
        'bg-surface-elevated border border-border',
        'text-sm text-text',
        className
      )}
    >
      <Icon className="w-4 h-4 text-text-muted flex-shrink-0" />
      <span className="truncate max-w-[200px]">{name}</span>
      {formattedSize && (
        <span className="text-xs text-text-muted flex-shrink-0">
          ({formattedSize})
        </span>
      )}
      {onRemove && (
        <button
          onClick={onRemove}
          className={cn(
            'flex-shrink-0 p-0.5 rounded hover:bg-red-500/20',
            'text-text-muted hover:text-red-400 transition-colors'
          )}
          title="Retirer"
        >
          <svg
            className="w-3 h-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      )}
    </motion.div>
  );
}
