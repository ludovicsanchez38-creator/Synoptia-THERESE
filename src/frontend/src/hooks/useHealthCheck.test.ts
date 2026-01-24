/**
 * THERESE v2 - Health Check Hook Tests
 *
 * Tests for backend health check functionality.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';

// Mock fetch
const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

// Mock useStatusStore
const mockSetConnectionState = vi.fn();
const mockUpdatePing = vi.fn();
const mockAddNotification = vi.fn();

vi.mock('../stores/statusStore', () => ({
  useStatusStore: () => ({
    connectionState: 'disconnected',
    setConnectionState: mockSetConnectionState,
    updatePing: mockUpdatePing,
    addNotification: mockAddNotification,
  }),
}));

describe('useHealthCheck', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('initial state', () => {
    it('should return refresh function', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: 'ok', version: '1.0' }),
      });

      const { useHealthCheck } = await import('./useHealthCheck');

      const { result } = renderHook(() => useHealthCheck());

      // Hook returns refresh function
      expect(typeof result.current.refresh).toBe('function');
    });
  });

  describe('health check success', () => {
    it('should set connection state to connected when backend responds', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: 'ok', version: '1.0' }),
      });

      const { useHealthCheck } = await import('./useHealthCheck');

      renderHook(() => useHealthCheck());

      await vi.runAllTimersAsync();

      expect(mockSetConnectionState).toHaveBeenCalledWith('connected');
    });

    it('should call health endpoint', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: 'ok' }),
      });

      const { useHealthCheck } = await import('./useHealthCheck');

      renderHook(() => useHealthCheck());

      await vi.runAllTimersAsync();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/health'),
        expect.anything()
      );
    });
  });

  describe('health check failure', () => {
    it('should set connection state to disconnected when backend fails', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      const { useHealthCheck } = await import('./useHealthCheck');

      renderHook(() => useHealthCheck());

      await vi.runAllTimersAsync();

      expect(mockSetConnectionState).toHaveBeenCalledWith('disconnected');
    });

    it('should handle non-ok response', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 503,
      });

      const { useHealthCheck } = await import('./useHealthCheck');

      renderHook(() => useHealthCheck());

      await vi.runAllTimersAsync();

      // Should set to disconnected or error state
      expect(mockSetConnectionState).toHaveBeenCalled();
    });
  });

  describe('polling', () => {
    it('should poll health endpoint periodically', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: 'ok' }),
      });

      const { useHealthCheck } = await import('./useHealthCheck');

      renderHook(() => useHealthCheck());

      // Initial check
      await vi.advanceTimersByTimeAsync(100);

      // Advance by polling interval (typically 5-10 seconds)
      await vi.advanceTimersByTimeAsync(10000);

      // Should have been called multiple times
      expect(mockFetch.mock.calls.length).toBeGreaterThan(1);
    });
  });

  describe('cleanup', () => {
    it('should stop polling on unmount', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: 'ok' }),
      });

      const { useHealthCheck } = await import('./useHealthCheck');

      const { unmount } = renderHook(() => useHealthCheck());

      await vi.advanceTimersByTimeAsync(100);
      const callCount = mockFetch.mock.calls.length;

      unmount();

      await vi.advanceTimersByTimeAsync(20000);

      // Should not have made more calls after unmount
      expect(mockFetch.mock.calls.length).toBeLessThanOrEqual(callCount + 1);
    });
  });
});
