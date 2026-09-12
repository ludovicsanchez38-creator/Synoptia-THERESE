/**
 * THÉRÈSE v2 - Drop Zone Component
 *
 * Visual overlay for drag & drop file handling.
 */

import { motion, AnimatePresence } from 'framer-motion';
import { Upload, File, FileText, FileCode, FileImage, X } from 'lucide-react';
import { cn } from '../../lib/utils';
import { Z_LAYER } from '../../styles/z-layers';
import { Button } from '../ui/Button';

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
            'absolute inset-0', Z_LAYER.MODAL, 'flex items-center justify-center',
            'bg-bg/90 backdrop-blur-sm',
            className
          )}
        >
          <motion.div
            initial={{ y: 8, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 8, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className={cn(
              'flex flex-col items-center justify-center gap-4 p-12',
              'rounded-md border-2 border-dashed border-accent',
              'bg-surface'
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
              <Upload className="w-16 h-16 text-accent" />
            </motion.div>

            <div className="text-center">
              <h3 className="text-xl font-semibold text-text">
                Dépose tes fichiers
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
            'overflow-hidden rounded-md border border-dashed border-accent',
            'bg-accent-tint mb-2',
            className
          )}
        >
          <div className="flex items-center justify-center gap-2 py-3 px-4">
            <Upload className="w-4 h-4 text-accent" />
            <span className="text-sm text-accent">
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
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 4 }}
      className={cn(
        'inline-flex items-center gap-2 px-3 py-1.5 rounded-md',
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
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onRemove}
          className="flex-shrink-0 text-text-muted hover:text-error"
          aria-label={`Retirer ${name}`}
          title="Retirer"
        >
          <X className="w-4 h-4" aria-hidden="true" />
        </Button>
      )}
    </motion.div>
  );
}
