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

  return (
    <Button
      variant={isRecording ? 'primary' : 'ghost'}
      size="icon"
      data-testid={testId}
      className={cn(
        'flex-shrink-0 h-9 w-9 transition-all',
        isRecording && 'bg-error hover:bg-error/90 animate-pulse',
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
  );
}
