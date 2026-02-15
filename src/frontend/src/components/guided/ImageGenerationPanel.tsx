import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Image,
  Download,
  Check,
  Loader2,
  X,
  RefreshCw,
  Sparkles,
  ImageOff,
} from 'lucide-react';
import type { ImageProvider } from './actionData';
import { cn } from '../../lib/utils';

export type ImageGenerationStatus = 'idle' | 'generating' | 'success' | 'error';

interface ImageGenerationPanelProps {
  provider: ImageProvider;
  status: ImageGenerationStatus;
  prompt?: string;
  imageUrl?: string;
  fileName?: string;
  fileSize?: number;
  error?: string;
  onDownload?: () => void;
  onRetry?: () => void;
  onClose?: () => void;
}

// Config par provider
const providerConfig: Record<ImageProvider, {
  color: string;
  bgGradient: string;
  label: string;
  description: string;
}> = {
  'gpt-image-1.5': {
    color: 'text-emerald-400',
    bgGradient: 'from-emerald-500/20 to-teal-600/10',
    label: 'GPT Image 1.5',
    description: 'Image générée par OpenAI'
  },
  'nanobanan-pro': {
    color: 'text-purple-400',
    bgGradient: 'from-purple-500/20 to-pink-600/10',
    label: 'Nano Banana Pro',
    description: 'Image générée par Gemini'
  },
  'fal-flux-pro': {
    color: 'text-orange-400',
    bgGradient: 'from-orange-500/20 to-amber-600/10',
    label: 'Fal Flux Pro',
    description: 'Image générée par Fal (Flux Pro v1.1)'
  },
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function ImageGenerationPanel({
  provider,
  status,
  prompt,
  imageUrl,
  fileName,
  fileSize,
  error,
  onDownload,
  onRetry,
  onClose,
}: ImageGenerationPanelProps) {
  const config = providerConfig[provider];
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  // Reset states when imageUrl changes
  useEffect(() => {
    setImageLoaded(false);
    setImageError(false);
  }, [imageUrl]);

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
              'absolute top-4 right-4 p-1.5 rounded-lg z-10',
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
            <Image className={cn('w-8 h-8', config.color)} />

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
            {status === 'success' && 'Image générée'}
            {status === 'error' && 'Erreur de génération'}
            {status === 'idle' && 'Prêt à générer'}
          </h3>

          {/* Description */}
          <p className="text-sm text-text-muted">
            {status === 'generating' && (
              <span className="flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 animate-pulse" />
                {config.label} crée votre image
              </span>
            )}
            {status === 'success' && config.description}
            {status === 'error' && (error || 'Une erreur est survenue')}
            {status === 'idle' && `Générer avec ${config.label}`}
          </p>
        </div>

        {/* Image preview (success state) */}
        {status === 'success' && imageUrl && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
              'mb-6 rounded-xl overflow-hidden',
              'bg-black/20 border border-white/10'
            )}
          >
            {/* Loading placeholder */}
            {!imageLoaded && !imageError && (
              <div className="w-full h-48 flex items-center justify-center bg-black/30">
                <Loader2 className="w-8 h-8 text-text-muted animate-spin" />
              </div>
            )}

            {/* Error placeholder */}
            {imageError && (
              <div className="w-full h-48 flex flex-col items-center justify-center bg-black/30 gap-2">
                <ImageOff className="w-12 h-12 text-text-muted" />
                <p className="text-sm text-text-muted">Impossible de charger l'image</p>
                <p className="text-xs text-text-muted/60 max-w-xs text-center truncate">
                  {imageUrl}
                </p>
              </div>
            )}

            {/* Actual image */}
            <img
              src={imageUrl}
              alt={prompt || 'Image générée'}
              className={cn(
                'w-full h-auto max-h-64 object-contain',
                (!imageLoaded || imageError) && 'hidden'
              )}
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageError(true)}
            />

            {(fileName || fileSize) && (
              <div className="p-3 bg-black/30 flex items-center justify-between">
                <span className="text-sm text-text-muted truncate">
                  {fileName || 'image.png'}
                </span>
                {fileSize && (
                  <span className="text-xs text-text-muted">
                    {formatFileSize(fileSize)}
                  </span>
                )}
              </div>
            )}
          </motion.div>
        )}

        {/* Prompt preview (when generating or success) */}
        {(status === 'generating' || status === 'success') && prompt && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className={cn(
              'mb-6 p-3 rounded-lg',
              'bg-white/5 border border-white/10'
            )}
          >
            <p className="text-xs text-text-muted line-clamp-2 italic">
              "{prompt}"
            </p>
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
                  duration: 2,
                  ease: 'linear'
                }}
                style={{ width: '50%' }}
              />
            </div>
            <p className="text-xs text-text-muted text-center mt-2">
              Cela peut prendre quelques secondes...
            </p>
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
