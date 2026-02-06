/**
 * THERESE v2 - Health Check Hook Tests
 *
 * Tests for backend health check functionality.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';

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

// Mock checkHealth from the api service (le hook utilise checkHealth, pas fetch directement)
const mockCheckHealth = vi.fn();
vi.mock('../services/api', () => ({
  checkHealth: (...args: unknown[]) => mockCheckHealth(...args),
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
      mockCheckHealth.mockResolvedValue({ status: 'ok', version: '1.0' });

      const { useHealthCheck } = await import('./useHealthCheck');

      const { result } = renderHook(() => useHealthCheck());

      // Hook returns refresh function
      expect(typeof result.current.refresh).toBe('function');
    });
  });

  describe('health check success', () => {
    it('should set connection state to connected when backend responds', async () => {
      mockCheckHealth.mockResolvedValue({ status: 'ok', version: '1.0' });

      const { useHealthCheck } = await import('./useHealthCheck');

      renderHook(() => useHealthCheck());

      // Avancer assez pour que le check initial s'exécute (pas runAll pour éviter boucle infinie)
      await vi.advanceTimersByTimeAsync(100);

      expect(mockSetConnectionState).toHaveBeenCalledWith('connected');
    });

    it('should call health endpoint', async () => {
      mockCheckHealth.mockResolvedValue({ status: 'ok' });

      const { useHealthCheck } = await import('./useHealthCheck');

      renderHook(() => useHealthCheck());

      await vi.advanceTimersByTimeAsync(100);

      expect(mockCheckHealth).toHaveBeenCalled();
    });
  });

  describe('health check failure', () => {
    it('should set connection state to disconnected when backend fails', async () => {
      mockCheckHealth.mockRejectedValue(new Error('Network error'));

      const { useHealthCheck } = await import('./useHealthCheck');

      renderHook(() => useHealthCheck());

      await vi.advanceTimersByTimeAsync(100);

      expect(mockSetConnectionState).toHaveBeenCalledWith('disconnected');
    });

    it('should handle non-ok response', async () => {
      mockCheckHealth.mockRejectedValue(new Error('Service unavailable'));

      const { useHealthCheck } = await import('./useHealthCheck');

      renderHook(() => useHealthCheck());

      await vi.advanceTimersByTimeAsync(100);

      // Should set to disconnected or error state
      expect(mockSetConnectionState).toHaveBeenCalled();
    });
  });

  describe('polling', () => {
    it('should poll health endpoint periodically', async () => {
      mockCheckHealth.mockResolvedValue({ status: 'ok' });

      const { useHealthCheck } = await import('./useHealthCheck');

      renderHook(() => useHealthCheck());

      // Initial check
      await vi.advanceTimersByTimeAsync(100);

      // Advance by polling interval (30 seconds)
      await vi.advanceTimersByTimeAsync(30000);

      // Should have been called multiple times
      expect(mockCheckHealth.mock.calls.length).toBeGreaterThan(1);
    });
  });

  describe('cleanup', () => {
    it('should stop polling on unmount', async () => {
      mockCheckHealth.mockResolvedValue({ status: 'ok' });

      const { useHealthCheck } = await import('./useHealthCheck');

      const { unmount } = renderHook(() => useHealthCheck());

      await vi.advanceTimersByTimeAsync(100);
      const callCount = mockCheckHealth.mock.calls.length;

      unmount();

      await vi.advanceTimersByTimeAsync(60000);

      // Should not have made more calls after unmount
      expect(mockCheckHealth.mock.calls.length).toBeLessThanOrEqual(callCount + 1);
    });
  });
});
