/**
 * THÉRÈSE v2 - Voice Recorder Hook
 *
 * Enregistrement audio via Tauri plugin mic-recorder + transcription Groq Whisper
 * Fallback sur MediaRecorder API pour les navigateurs web
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import * as api from '../services/api';

export type RecordingState = 'idle' | 'recording' | 'processing';

/**
 * BUG-145 : les DOMException de getUserMedia (« Permission denied »…) sont
 * cryptiques et en anglais. On les mappe vers des messages actionnables qui
 * disent QUELLE permission activer, comme attendu par la fiche testeur.
 */
export function microphoneErrorMessage(err: unknown): string {
  // F10 revue : le plugin Tauri (app packagée) rejette en CHAÎNE ou en Error
  // native, pas en DOMException - on mappe donc sur le TEXTE de l'erreur,
  // en incluant le name des DOMException du chemin Web getUserMedia.
  const text = err instanceof DOMException
    ? `${err.name} ${err.message}`
    : err instanceof Error
      ? err.message
      : typeof err === 'string'
        ? err
        : '';
  const lower = text.toLowerCase();

  if (/notallowed|permissiondenied|security|permission|denied|unauthorized/.test(lower)) {
    return (
      'Accès au micro refusé. Autorise le microphone pour THÉRÈSE : '
      + 'Windows : Paramètres > Confidentialité > Microphone ; '
      + 'macOS : Réglages Système > Confidentialité et sécurité > Microphone.'
    );
  }
  if (/notfound|devicesnotfound|overconstrained|no (input )?device|device not found|no such device/.test(lower)) {
    return 'Aucun micro détecté. Branche un micro ou vérifie qu\'il est activé dans le système.';
  }
  if (/notreadable|trackstart|abort|busy|in use|already in use/.test(lower)) {
    return 'Le micro est occupé par une autre application. Ferme-la puis réessaie.';
  }
  if (err instanceof Error && err.message) return err.message;
  if (typeof err === 'string' && err.trim()) return err;
  return 'Impossible d\'accéder au microphone';
}

interface UseVoiceRecorderOptions {
  onTranscript?: (text: string) => void;
  onError?: (error: string) => void;
}

interface UseVoiceRecorderReturn {
  state: RecordingState;
  isRecording: boolean;
  isProcessing: boolean;
  pluginReady: boolean;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<void>;
  toggleRecording: () => Promise<void>;
  cancelProcessing: () => void;
  elapsedSeconds: number;
  error: string | null;
}

// Check if we're in Tauri
const isTauri = () => '__TAURI__' in window || '__TAURI_INTERNALS__' in window;

// Dynamic import for Tauri plugin (only available in Tauri context)
let tauriMicRecorder: {
  startRecording: () => Promise<unknown>;
  stopRecording: () => Promise<string>;
} | null = null;

// BUG-034 : état de chargement du plugin, avec callbacks de notification
let _pluginLoaded = false;
const _pluginReadyCallbacks: Array<() => void> = [];

function _notifyPluginReady() {
  _pluginLoaded = true;
  _pluginReadyCallbacks.forEach((cb) => cb());
  _pluginReadyCallbacks.length = 0;
}

// Try to load Tauri plugin
if (isTauri()) {
  import('tauri-plugin-mic-recorder-api').then((module) => {
    tauriMicRecorder = module;
    console.log('[VoiceRecorder] Tauri mic-recorder plugin loaded');
    _notifyPluginReady();
  }).catch((err) => {
    console.warn('[VoiceRecorder] Failed to load Tauri mic-recorder plugin:', err);
    _notifyPluginReady(); // Prêt même en échec (fallback Web API)
  });
} else {
  // Pas en Tauri : le plugin Web est toujours prêt
  _pluginLoaded = true;
}

export function useVoiceRecorder(options: UseVoiceRecorderOptions = {}): UseVoiceRecorderReturn {
  const { onTranscript, onError } = options;

  const [state, setState] = useState<RecordingState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [pluginReady, setPluginReady] = useState(_pluginLoaded);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // BUG-034 : suivre le chargement async du plugin Tauri
  useEffect(() => {
    if (_pluginLoaded) {
      setPluginReady(true);
      return;
    }
    const cb = () => setPluginReady(true);
    _pluginReadyCallbacks.push(cb);
    return () => {
      const idx = _pluginReadyCallbacks.indexOf(cb);
      if (idx >= 0) _pluginReadyCallbacks.splice(idx, 1);
    };
  }, []);

  // For web fallback
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const transcriptionControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (state !== 'recording') return undefined;
    const startedAt = Date.now();
    setElapsedSeconds(0);
    const interval = window.setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000));
    }, 250);
    return () => window.clearInterval(interval);
  }, [state]);

  const startRecordingTauri = useCallback(async () => {
    if (!tauriMicRecorder) {
      throw new Error('Plugin micro non disponible');
    }

    console.log('[VoiceRecorder] Starting Tauri recording...');
    await tauriMicRecorder.startRecording();
    setState('recording');
  }, []);

  const stopRecordingTauri = useCallback(async () => {
    if (!tauriMicRecorder) {
      return;
    }

    console.log('[VoiceRecorder] Stopping Tauri recording...');
    const savePath = await tauriMicRecorder.stopRecording();
    console.log('[VoiceRecorder] Recording saved at:', savePath);
    setState('processing');
    const controller = new AbortController();
    transcriptionControllerRef.current = controller;

    try {
      // Read the recorded file and send for transcription
      const { readFile } = await import('@tauri-apps/plugin-fs');
      const audioData = await readFile(savePath);
      const audioBlob = new Blob([audioData], { type: 'audio/wav' });

      console.log('[VoiceRecorder] Audio blob size:', audioBlob.size, 'bytes');

      if (audioBlob.size === 0) {
        throw new Error('Enregistrement vide');
      }

      // Send to backend for transcription
      if (controller.signal.aborted) return;
      const transcript = await api.transcribeAudio(audioBlob, 'recording.wav', controller.signal);
      console.log('[VoiceRecorder] Transcript received:', transcript?.substring(0, 50));

      if (transcript && onTranscript) {
        onTranscript(transcript);
      }
    } catch (err) {
      if (controller.signal.aborted) return;
      console.error('[VoiceRecorder] Transcription error:', err);
      const errorMsg = err instanceof Error ? err.message : 'Erreur de transcription';
      setError(errorMsg);
      onError?.(errorMsg);
    } finally {
      if (transcriptionControllerRef.current === controller) {
        transcriptionControllerRef.current = null;
      }
      setState('idle');
    }
  }, [onTranscript, onError]);

  const startRecordingWeb = useCallback(async () => {
    // Check if getUserMedia is supported
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('Enregistrement audio non supporté par ce navigateur');
    }

    // Check if MediaRecorder is supported
    if (typeof MediaRecorder === 'undefined') {
      throw new Error('MediaRecorder non supporté par ce navigateur');
    }

    // Request microphone access
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

    // Find a supported mimeType
    const mimeTypes = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/ogg;codecs=opus',
      'audio/ogg',
      '',
    ];

    let selectedMimeType = '';
    for (const mimeType of mimeTypes) {
      if (mimeType === '' || MediaRecorder.isTypeSupported(mimeType)) {
        selectedMimeType = mimeType;
        break;
      }
    }

    console.log('[VoiceRecorder] Using mimeType:', selectedMimeType || 'default');

    const recorderOptions: MediaRecorderOptions = {};
    if (selectedMimeType) {
      recorderOptions.mimeType = selectedMimeType;
    }
    const mediaRecorder = new MediaRecorder(stream, recorderOptions);

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };

    const actualMimeType = mediaRecorder.mimeType || selectedMimeType || 'audio/webm';

    mediaRecorder.onstop = async () => {
      setState('processing');
      const controller = new AbortController();
      transcriptionControllerRef.current = controller;
      console.log('[VoiceRecorder] Recording stopped, processing...');

      try {
        const audioBlob = new Blob(chunksRef.current, { type: actualMimeType });
        console.log('[VoiceRecorder] Audio blob size:', audioBlob.size, 'bytes');

        if (audioBlob.size === 0) {
          throw new Error('Enregistrement vide - vérifiez les permissions micro');
        }

        if (controller.signal.aborted) return;
        const transcript = await api.transcribeAudio(audioBlob, 'recording.webm', controller.signal);
        console.log('[VoiceRecorder] Transcript received:', transcript?.substring(0, 50));

        if (transcript && onTranscript) {
          onTranscript(transcript);
        }
      } catch (err) {
        if (controller.signal.aborted) return;
        console.error('[VoiceRecorder] Transcription error:', err);
        const errorMsg = err instanceof Error ? err.message : 'Erreur de transcription';
        setError(errorMsg);
        onError?.(errorMsg);
      } finally {
        if (transcriptionControllerRef.current === controller) {
          transcriptionControllerRef.current = null;
        }
        setState('idle');
      }
    };

    mediaRecorderRef.current = mediaRecorder;
    mediaRecorder.start(100);
    setState('recording');
    console.log('[VoiceRecorder] Recording started');
  }, [onTranscript, onError]);

  const stopRecordingWeb = useCallback(async () => {
    if (mediaRecorderRef.current && state === 'recording') {
      mediaRecorderRef.current.stop();

      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    }
  }, [state]);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      console.log('[VoiceRecorder] Starting recording...');

      // Use Tauri plugin if available, otherwise fallback to Web API
      if (isTauri() && tauriMicRecorder) {
        await startRecordingTauri();
      } else {
        await startRecordingWeb();
      }
    } catch (err) {
      // BUG-145 : message actionnable (quelle permission activer) plutôt que
      // le libellé brut de getUserMedia.
      const errorMsg = microphoneErrorMessage(err);
      setError(errorMsg);
      onError?.(errorMsg);
      setState('idle');
    }
  }, [startRecordingTauri, startRecordingWeb, onError]);

  const stopRecording = useCallback(async () => {
    if (isTauri() && tauriMicRecorder) {
      await stopRecordingTauri();
    } else {
      await stopRecordingWeb();
    }
  }, [stopRecordingTauri, stopRecordingWeb]);

  const toggleRecording = useCallback(async () => {
    if (state === 'recording') {
      await stopRecording();
    } else if (state === 'idle') {
      await startRecording();
    }
  }, [state, startRecording, stopRecording]);

  const cancelProcessing = useCallback(() => {
    transcriptionControllerRef.current?.abort();
    transcriptionControllerRef.current = null;
    setState('idle');
  }, []);

  useEffect(() => () => {
    transcriptionControllerRef.current?.abort();
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  return {
    state,
    isRecording: state === 'recording',
    isProcessing: state === 'processing',
    pluginReady,
    startRecording,
    stopRecording,
    toggleRecording,
    cancelProcessing,
    elapsedSeconds,
    error,
  };
}

export default useVoiceRecorder;
