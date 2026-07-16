import { useCallback } from 'react';
import { Loader2, Mic, MicOff } from 'lucide-react';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { cn } from '../../lib/utils';
import { Button } from '../ui/Button';

interface VoiceDictationButtonProps {
  onTranscript: (text: string) => void;
  onError: (error: string) => void;
  disabled?: boolean;
  className?: string;
  testId?: string;
}

/**
 * Bouton de dictée partagé par le chat classique et la coque 0.40.
 *
 * Le hook existant reste l'unique point d'entrée pour l'enregistrement, les
 * permissions micro et le routage local/cloud tri-état de la transcription.
 */
export function VoiceDictationButton({
  onTranscript,
  onError,
  disabled = false,
  className,
  testId = 'chat-voice-btn',
}: VoiceDictationButtonProps) {
  const handleError = useCallback((error: string) => {
    console.error('Voice recording error:', error);
    onError(error);
  }, [onError]);

  const {
    isRecording,
    isProcessing,
    pluginReady,
    toggleRecording,
    cancelProcessing,
    elapsedSeconds,
  } = useVoiceRecorder({
    onTranscript,
    onError: handleError,
  });

  const label = !pluginReady
    ? 'Chargement du micro...'
    : isProcessing
      ? 'Transcription en cours...'
      : isRecording
        ? "Arrêter l'enregistrement"
        : 'Message vocal';

  const elapsedLabel = `${String(Math.floor(elapsedSeconds / 60)).padStart(2, '0')}:${String(elapsedSeconds % 60).padStart(2, '0')}`;

  return (
    <div className="relative flex shrink-0 items-center">
      {(isRecording || isProcessing) && (
        <div
          role="status"
          aria-live="polite"
          className="absolute bottom-full right-0 z-30 mb-2 min-w-52 rounded-[10px] border border-border bg-surface px-3 py-2 text-xs text-text shadow-lg"
          data-testid={`${testId}-status`}
        >
          {isRecording ? (
            <div>
              <div className="flex items-center gap-2 font-semibold text-error">
                <span className="h-2 w-2 animate-pulse rounded-full bg-error" />
                Écoute {elapsedLabel}
              </div>
              <div className="mt-1 flex items-end gap-0.5" aria-label="Aperçu live de la dictée">
                {[2, 4, 3, 5, 2].map((height, index) => (
                  <span key={`${height}-${index}`} className="w-1 animate-pulse rounded-full bg-accent-cyan" style={{ height: `${height * 2}px` }} />
                ))}
                <span className="ml-1 text-xs text-text-muted">Aperçu audio en direct</span>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between gap-3">
              <span className="inline-flex items-center gap-2 font-semibold"><Loader2 className="h-3.5 w-3.5 animate-spin" />Transcription en cours</span>
              <button type="button" onClick={cancelProcessing} className="rounded-[6px] border border-error px-2 py-1 font-semibold text-error">Annuler</button>
            </div>
          )}
        </div>
      )}
      <Button
      variant={isRecording ? 'primary' : 'ghost'}
      size="icon"
      data-testid={testId}
      className={cn(
        'h-11 w-11 flex-shrink-0 transition-all',
        isRecording && 'bg-error-fill text-error-ink hover:bg-error-fill/90 animate-pulse',
        className,
      )}
      disabled={disabled || isProcessing || !pluginReady}
      onClick={() => void toggleRecording()}
      title={label}
      aria-label={label}
      >
        {isProcessing ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : isRecording ? (
          <MicOff className="h-5 w-5" />
        ) : (
          <Mic className="h-5 w-5" />
        )}
      </Button>
    </div>
  );
}
