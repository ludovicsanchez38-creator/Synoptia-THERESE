/**
 * THÉRÈSE v2 - Voice Recorder Hook
 *
 * Enregistrement audio via MediaRecorder API + transcription Groq Whisper
 */

import { useState, useRef, useCallback } from 'react';
import * as api from '../services/api';

export type RecordingState = 'idle' | 'recording' | 'processing';

interface UseVoiceRecorderOptions {
  onTranscript?: (text: string) => void;
  onError?: (error: string) => void;
}

interface UseVoiceRecorderReturn {
  state: RecordingState;
  isRecording: boolean;
  isProcessing: boolean;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<void>;
  toggleRecording: () => Promise<void>;
  error: string | null;
}

export function useVoiceRecorder(options: UseVoiceRecorderOptions = {}): UseVoiceRecorderReturn {
  const { onTranscript, onError } = options;

  const [state, setState] = useState<RecordingState>('idle');
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      console.log('[VoiceRecorder] Starting recording...');

      // Détecter si on est dans Tauri WebView (qui a un support limité)
      const isTauri = '__TAURI__' in window || '__TAURI_INTERNALS__' in window;

      // Vérifier si getUserMedia est supporté
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        if (isTauri) {
          throw new Error('La dictée vocale n\'est pas disponible dans l\'application desktop. Cette fonctionnalité sera ajoutée dans une prochaine version.');
        }
        throw new Error('Enregistrement audio non supporté par ce navigateur');
      }

      // Vérifier si MediaRecorder est supporté
      if (typeof MediaRecorder === 'undefined') {
        if (isTauri) {
          throw new Error('La dictée vocale nécessite une mise à jour de l\'application. Fonctionnalité à venir.');
        }
        throw new Error('MediaRecorder non supporté par ce navigateur');
      }

      // Demander l'accès au micro
      console.log('[VoiceRecorder] Requesting microphone access...');
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      streamRef.current = stream;
      chunksRef.current = [];

      // Trouver un mimeType supporté
      const mimeTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/mp4',
        'audio/ogg;codecs=opus',
        'audio/ogg',
        '', // Fallback: laisser le navigateur choisir
      ];

      let selectedMimeType = '';
      for (const mimeType of mimeTypes) {
        if (mimeType === '' || MediaRecorder.isTypeSupported(mimeType)) {
          selectedMimeType = mimeType;
          break;
        }
      }

      console.log('[VoiceRecorder] Using mimeType:', selectedMimeType || 'default');

      // Créer le MediaRecorder
      const options: MediaRecorderOptions = {};
      if (selectedMimeType) {
        options.mimeType = selectedMimeType;
      }
      const mediaRecorder = new MediaRecorder(stream, options);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      // Capturer le mimeType réel utilisé
      const actualMimeType = mediaRecorder.mimeType || selectedMimeType || 'audio/webm';
      console.log('[VoiceRecorder] Actual mimeType:', actualMimeType);

      mediaRecorder.onstop = async () => {
        setState('processing');
        console.log('[VoiceRecorder] Recording stopped, processing...');
        console.log('[VoiceRecorder] Chunks count:', chunksRef.current.length);

        try {
          // Créer le blob audio avec le bon type
          const audioBlob = new Blob(chunksRef.current, { type: actualMimeType });
          console.log('[VoiceRecorder] Audio blob size:', audioBlob.size, 'bytes');

          if (audioBlob.size === 0) {
            throw new Error('Enregistrement vide - vérifiez les permissions micro');
          }

          // Envoyer au backend pour transcription
          console.log('[VoiceRecorder] Sending to backend for transcription...');
          const transcript = await api.transcribeAudio(audioBlob);
          console.log('[VoiceRecorder] Transcript received:', transcript?.substring(0, 50));

          if (transcript && onTranscript) {
            onTranscript(transcript);
          }
        } catch (err) {
          console.error('[VoiceRecorder] Transcription error:', err);
          const errorMsg = err instanceof Error ? err.message : 'Erreur de transcription';
          setError(errorMsg);
          onError?.(errorMsg);
        } finally {
          setState('idle');
        }
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(100); // Chunks toutes les 100ms
      setState('recording');
      console.log('[VoiceRecorder] Recording started');
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Impossible d\'accéder au microphone';
      setError(errorMsg);
      onError?.(errorMsg);
      setState('idle');
    }
  }, [onTranscript, onError]);

  const stopRecording = useCallback(async () => {
    if (mediaRecorderRef.current && state === 'recording') {
      mediaRecorderRef.current.stop();

      // Arrêter le stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    }
  }, [state]);

  const toggleRecording = useCallback(async () => {
    if (state === 'recording') {
      await stopRecording();
    } else if (state === 'idle') {
      await startRecording();
    }
    // Si processing, on ne fait rien
  }, [state, startRecording, stopRecording]);

  return {
    state,
    isRecording: state === 'recording',
    isProcessing: state === 'processing',
    startRecording,
    stopRecording,
    toggleRecording,
    error,
  };
}

export default useVoiceRecorder;
