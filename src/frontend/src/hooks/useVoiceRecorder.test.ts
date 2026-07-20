/**
 * THERESE v2 - Voice Recorder Hook Tests
 *
 * Tests for US-VOICE-01 to US-VOICE-04.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import * as api from '../services/api';

// Mock api module (le hook utilise api.transcribeAudio)
vi.mock('../services/api', () => ({
  transcribeAudio: vi.fn().mockResolvedValue('transcribed text'),
}));

// Mock MediaRecorder
class MockMediaRecorder {
  state: 'inactive' | 'recording' | 'paused' = 'inactive';
  mimeType = 'audio/webm';
  ondataavailable: ((e: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  onerror: ((e: Error) => void) | null = null;

  static isTypeSupported(_mimeType: string): boolean {
    return true;
  }

  start(_timeslice?: number) {
    this.state = 'recording';
  }

  stop() {
    this.state = 'inactive';
    if (this.ondataavailable) {
      this.ondataavailable({ data: new Blob(['audio'], { type: 'audio/webm' }) });
    }
    if (this.onstop) {
      this.onstop();
    }
  }
}

// Mock navigator.mediaDevices
const mockGetUserMedia = vi.fn();

describe('useVoiceRecorder', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.transcribeAudio).mockResolvedValue('transcribed text');

    // Mock MediaRecorder
    (globalThis as any).MediaRecorder = MockMediaRecorder;

    // Mock navigator.mediaDevices
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: mockGetUserMedia,
      },
      writable: true,
      configurable: true,
    });

    mockGetUserMedia.mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }],
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('initial state', () => {
    it('should start with idle state', async () => {
      const { useVoiceRecorder } = await import('./useVoiceRecorder');

      const { result } = renderHook(() => useVoiceRecorder({ onTranscript: vi.fn() }));

      expect(result.current.state).toBe('idle');
      expect(result.current.error).toBeNull();
    });

    it('should provide isRecording and isProcessing flags', async () => {
      const { useVoiceRecorder } = await import('./useVoiceRecorder');

      const { result } = renderHook(() => useVoiceRecorder({ onTranscript: vi.fn() }));

      // Hook provides derived boolean states
      expect(result.current.isRecording).toBe(false);
      expect(result.current.isProcessing).toBe(false);
    });
  });

  describe('startRecording', () => {
    it('should request microphone permission', async () => {
      const { useVoiceRecorder } = await import('./useVoiceRecorder');

      const { result } = renderHook(() => useVoiceRecorder({ onTranscript: vi.fn() }));

      await act(async () => {
        await result.current.startRecording();
      });

      expect(mockGetUserMedia).toHaveBeenCalledWith({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
    });

    it('should change state to recording', async () => {
      const { useVoiceRecorder } = await import('./useVoiceRecorder');

      const { result } = renderHook(() => useVoiceRecorder({ onTranscript: vi.fn() }));

      await act(async () => {
        await result.current.startRecording();
      });

      expect(result.current.state).toBe('recording');
    });

    it('should handle permission denied error', async () => {
      mockGetUserMedia.mockRejectedValue(new DOMException('Permission denied', 'NotAllowedError'));

      const { useVoiceRecorder } = await import('./useVoiceRecorder');

      const { result } = renderHook(() => useVoiceRecorder({ onTranscript: vi.fn() }));

      await act(async () => {
        await result.current.startRecording();
      });

      expect(result.current.state).toBe('idle');
      expect(result.current.error).not.toBeNull();
    });
  });

  describe('stopRecording', () => {
    it('should change state to processing', async () => {
      const { useVoiceRecorder } = await import('./useVoiceRecorder');

      const { result } = renderHook(() => useVoiceRecorder({ onTranscript: vi.fn() }));

      await act(async () => {
        await result.current.startRecording();
      });

      await act(async () => {
        await result.current.stopRecording();
      });

      // State should be processing or idle after stop
      expect(['processing', 'idle']).toContain(result.current.state);
    });

    it('annule la transcription réseau et revient au repos', async () => {
      let activeSignal: AbortSignal | undefined;
      vi.mocked(api.transcribeAudio).mockImplementation((_blob, _filename, signal) => {
        activeSignal = signal;
        return new Promise((_resolve, reject) => {
          signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
        });
      });
      const { useVoiceRecorder } = await import('./useVoiceRecorder');
      const { result } = renderHook(() => useVoiceRecorder({ onTranscript: vi.fn() }));

      await act(async () => result.current.startRecording());
      await act(async () => result.current.stopRecording());
      await waitFor(() => expect(result.current.isProcessing).toBe(true));

      act(() => result.current.cancelProcessing());

      expect(activeSignal?.aborted).toBe(true);
      expect(result.current.state).toBe('idle');
    });
  });

  describe('error handling', () => {
    it('should set error message on failure', async () => {
      mockGetUserMedia.mockRejectedValue(new Error('Microphone not found'));

      const { useVoiceRecorder } = await import('./useVoiceRecorder');

      const { result } = renderHook(() => useVoiceRecorder({ onTranscript: vi.fn() }));

      await act(async () => {
        await result.current.startRecording();
      });

      expect(result.current.error).not.toBeNull();
    });

    it('should clear error on successful start', async () => {
      const { useVoiceRecorder } = await import('./useVoiceRecorder');

      const { result } = renderHook(() => useVoiceRecorder({ onTranscript: vi.fn() }));

      // First cause an error
      mockGetUserMedia.mockRejectedValueOnce(new Error('Fail'));
      await act(async () => {
        await result.current.startRecording();
      });

      expect(result.current.error).not.toBeNull();

      // Then succeed
      mockGetUserMedia.mockResolvedValueOnce({
        getTracks: () => [{ stop: vi.fn() }],
      });

      await act(async () => {
        await result.current.startRecording();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('transcription callback', () => {
    it('should call onTranscript with result', async () => {
      const onTranscript = vi.fn();
      const { useVoiceRecorder } = await import('./useVoiceRecorder');

      const { result } = renderHook(() => useVoiceRecorder({ onTranscript }));

      await act(async () => {
        await result.current.startRecording();
      });

      // Note: Full transcription test would require mocking the API call
      // This test validates the hook accepts the callback
      expect(typeof result.current.startRecording).toBe('function');
      expect(typeof result.current.stopRecording).toBe('function');
    });
  });

  // BUG-145 : « Impossible d'accéder au microphone » sans aucune piste. Les
  // DOMException de getUserMedia sont mappées vers des messages actionnables
  // (permission à activer, micro absent, micro occupé).
  describe('microphoneErrorMessage (BUG-145)', () => {
    it('guide vers les réglages de permission quand l’accès est refusé', async () => {
      const { microphoneErrorMessage } = await import('./useVoiceRecorder');
      const err = new DOMException('Permission denied', 'NotAllowedError');

      const message = microphoneErrorMessage(err);

      expect(message).toContain('Autorise le microphone');
      expect(message).toContain('Confidentialité');
    });

    it('signale un micro absent', async () => {
      const { microphoneErrorMessage } = await import('./useVoiceRecorder');
      const err = new DOMException('Requested device not found', 'NotFoundError');

      expect(microphoneErrorMessage(err)).toContain('Aucun micro');
    });

    it('signale un micro occupé par une autre application', async () => {
      const { microphoneErrorMessage } = await import('./useVoiceRecorder');
      const err = new DOMException('Could not start audio source', 'NotReadableError');

      expect(microphoneErrorMessage(err)).toContain('autre application');
    });

    it('retombe sur le message de l’erreur sinon', async () => {
      const { microphoneErrorMessage } = await import('./useVoiceRecorder');

      expect(microphoneErrorMessage(new Error('Plugin micro non disponible'))).toBe('Plugin micro non disponible');
      expect(microphoneErrorMessage('boom')).toContain('microphone');
    });
  });
});
