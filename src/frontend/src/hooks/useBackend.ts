/**
 * THÉRÈSE v2 - Backend Connection Hook
 *
 * Manages connection to the Python backend with health checks and reconnection.
 */

import { useEffect, useCallback, useRef } from 'react';
import { create } from 'zustand';
import { checkHealth, type HealthStatus } from '../services/api';

interface BackendState {
  status: 'disconnected' | 'connecting' | 'connected' | 'error';
  version: string | null;
  lastCheck: Date | null;
  error: string | null;
  setStatus: (status: BackendState['status']) => void;
  setConnected: (health: HealthStatus) => void;
  setError: (error: string) => void;
  reset: () => void;
}

export const useBackendStore = create<BackendState>((set) => ({
  status: 'disconnected',
  version: null,
  lastCheck: null,
  error: null,
  setStatus: (status) => set({ status }),
  setConnected: (health) =>
    set({
      status: 'connected',
      version: health.version,
      lastCheck: new Date(),
      error: null,
    }),
  setError: (error) =>
    set({
      status: 'error',
      error,
      lastCheck: new Date(),
    }),
  reset: () =>
    set({
      status: 'disconnected',
      version: null,
      lastCheck: null,
      error: null,
    }),
}));

interface UseBackendOptions {
  /** Health check interval in ms (default: 30000) */
  checkInterval?: number;
  /** Retry delay when disconnected in ms (default: 2000) */
  retryDelay?: number;
  /** Auto-start health checks (default: true) */
  autoStart?: boolean;
}

export function useBackend(options: UseBackendOptions = {}) {
  const {
    checkInterval = 30000,
    retryDelay = 2000,
    autoStart = true,
  } = options;

  const { status, version, lastCheck, error, setStatus, setConnected, setError } =
    useBackendStore();

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const performHealthCheck = useCallback(async () => {
    try {
      const health = await checkHealth();
      setConnected(health);
      return true;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Connection failed';
      setError(message);
      return false;
    }
  }, [setConnected, setError]);

  const connect = useCallback(async () => {
    setStatus('connecting');

    const success = await performHealthCheck();

    if (!success) {
      // Schedule retry
      retryTimeoutRef.current = setTimeout(connect, retryDelay);
    }
  }, [performHealthCheck, retryDelay, setStatus]);

  const disconnect = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
    setStatus('disconnected');
  }, [setStatus]);

  // Start health check interval when connected
  useEffect(() => {
    if (status === 'connected' && !intervalRef.current) {
      intervalRef.current = setInterval(async () => {
        const success = await performHealthCheck();
        if (!success) {
          // Clear interval and start reconnection
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          connect();
        }
      }, checkInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [status, checkInterval, performHealthCheck, connect]);

  // Auto-start connection
  useEffect(() => {
    if (autoStart && status === 'disconnected') {
      connect();
    }

    return () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
    };
  }, [autoStart, status, connect]);

  return {
    status,
    version,
    lastCheck,
    error,
    isConnected: status === 'connected',
    isConnecting: status === 'connecting',
    connect,
    disconnect,
    refresh: performHealthCheck,
  };
}
