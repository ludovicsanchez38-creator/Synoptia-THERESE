import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Image,
  Download,
  Check,
  X,
  RefreshCw,
  Sparkles,
  ImageOff,
} from 'lucide-react';
import type { ImageProvider } from './actionData';
import { cn } from '../../lib/utils';
import { fetchImageObjectUrl } from '../../services/api';
import { Spinner } from '../ui/Spinner';
import { Button } from '../ui/Button';

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
  onUse?: () => void;
}

// Config par provider
const providerConfig: Record<ImageProvider, {
  color: string;
  bgTint: string;
  label: string;
  description: string;
}> = {
  'gpt-image-2': {
    color: 'text-agent-green',
    bgTint: 'bg-agent-green/15',
    label: 'GPT Image 2',
    description: 'Image générée par OpenAI'
  },
  'nanobanan-pro': {
    color: 'text-agent-purple',
    bgTint: 'bg-agent-purple/15',
    label: 'Nano Banana 2',
    description: 'Image générée par Gemini'
  },
  'fal-flux-pro': {
    color: 'text-agent-amber',
    bgTint: 'bg-agent-amber/15',
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
  onUse,
}: ImageGenerationPanelProps) {
  const config = providerConfig[provider];
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  // US-001 : l'image est chargee via un fetch authentifie (en-tete X-Therese-Token)
  // puis affichee en object URL (blob) au lieu de <img src={url}?token=...>. Le
  // token ne transite donc plus jamais dans l'URL ni dans le DOM.
  const [resolvedSrc, setResolvedSrc] = useState<string | null>(null);

  useEffect(() => {
    setImageLoaded(false);
    setImageError(false);
    setResolvedSrc(null);
    if (!imageUrl) return;
    let cancelled = false;
    let objectUrl: string | null = null;
    fetchImageObjectUrl(imageUrl)
      .then((url) => {
        if (cancelled) { URL.revokeObjectURL(url); return; }
        objectUrl = url;
        setResolvedSrc(url);
      })
      .catch(() => { if (!cancelled) setImageError(true); });
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [imageUrl]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className={cn(
        'relative w-full max-w-md mx-auto',
        'bg-surface-elevated rounded-md border border-border',
        'overflow-hidden shadow-sm'
      )}
    >
      {/* Gradient background */}
      <div className={cn(
        'absolute inset-0 opacity-50',
        config.bgTint
      )} />

      {/* Content */}
      <div className="relative p-6">
        {/* Close button */}
        {onClose && status !== 'generating' && (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="absolute right-4 top-4 z-10"
            aria-label="Fermer"
          >
            <X className="w-4 h-4" />
          </Button>
        )}

        {/* Icon + Status */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className={cn(
            'relative w-16 h-16 rounded-md flex items-center justify-center mb-4',
            'border-[1.5px] border-[var(--btn-ink)]',
            config.bgTint
          )}>
            <Image className={cn('w-8 h-8', config.color)} />

            {/* Status indicator */}
            <AnimatePresence mode="wait">
              {status === 'generating' && (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-surface flex items-center justify-center"
                >
                  <Spinner taille="bouton" className="text-accent-cyan-ink" />
                </motion.div>
              )}
              {status === 'success' && (
                <motion.div
                  key="success"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-success flex items-center justify-center"
                >
                  <Check className="w-3.5 h-3.5 text-ink-on-fill" />
                </motion.div>
              )}
              {status === 'error' && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-error flex items-center justify-center"
                >
                  <X className="w-3.5 h-3.5 text-ink-on-fill" />
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
                {config.label} crée ton image
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
              'mb-6 rounded-md overflow-hidden',
              'bg-surface-2 border border-border'
            )}
          >
            {/* Loading placeholder */}
            {!imageLoaded && !imageError && (
              <div className="w-full h-48 flex items-center justify-center bg-surface-2">
                <Spinner taille="zone" className="text-text-muted" />
              </div>
            )}

            {/* Error placeholder */}
            {imageError && (
              <div className="w-full h-48 flex flex-col items-center justify-center bg-surface-2 gap-2">
                <ImageOff className="w-12 h-12 text-text-muted" />
                <p className="text-sm text-text-muted">Impossible de charger l'image</p>
                <p className="text-xs text-text-muted max-w-xs text-center truncate">
                  {imageUrl}
                </p>
              </div>
            )}

            {/* Actual image (blob authentifié, US-001) */}
            <img
              src={resolvedSrc ?? undefined}
              alt={prompt || 'Image générée'}
              className={cn(
                'w-full h-auto max-h-64 object-contain',
                (!imageLoaded || imageError) && 'hidden'
              )}
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageError(true)}
            />

            {(fileName || fileSize) && (
              <div className="p-3 bg-surface-2 flex items-center justify-between">
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
              'mb-6 p-3 rounded-md',
              'bg-surface-2 border border-border'
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
            <div className="h-1.5 bg-surface-2 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-accent-fill"
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
        <div className="flex flex-wrap gap-3">
          {status === 'success' && onUse && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="min-w-32 flex-1"
            >
              <Button type="button" variant="primary" onClick={onUse} className="w-full">
                <Check className="mr-2 w-4 h-4" />
                Utiliser
              </Button>
            </motion.div>
          )}

          {status === 'success' && onDownload && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="min-w-32 flex-1"
            >
              <Button type="button" variant={onUse ? 'secondary' : 'primary'} onClick={onDownload} className="w-full">
                <Download className="mr-2 w-4 h-4" />
                Télécharger
              </Button>
            </motion.div>
          )}

          {status === 'error' && onRetry && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="min-w-32 flex-1"
            >
              <Button type="button" variant="secondary" onClick={onRetry} className="w-full">
                <RefreshCw className="mr-2 w-4 h-4" />
                Réessayer
              </Button>
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
