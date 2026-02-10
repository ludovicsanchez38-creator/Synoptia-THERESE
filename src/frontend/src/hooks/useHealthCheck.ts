/**
 * THÉRÈSE v2 - Health Check Hook
 *
 * Monitors backend health with periodic checks and latency tracking.
 */

import { useEffect, useCallback, useRef } from 'react';
import { useStatusStore } from '../stores/statusStore';
import { checkHealth, type HealthStatus } from '../services/api';

const HEALTH_CHECK_INTERVAL = 30000; // 30 seconds
const RETRY_DELAY = 2000; // 2 seconds on error
const MAX_RETRIES = 5;

export function useHealthCheck(enabled: boolean = true) {
  const { connectionState, setConnectionState, updatePing, addNotification } =
    useStatusStore();

  const retriesRef = useRef(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const performCheck = useCallback(async (): Promise<boolean> => {
    const start = Date.now();

    try {
      const health: HealthStatus = await checkHealth();
      const latency = Date.now() - start;

      setConnectionState('connected');
      updatePing(latency);
      retriesRef.current = 0;

      // Log version on first connect
      if (connectionState !== 'connected') {
        console.log(`[THÉRÈSE] Connected to backend v${health.version}`);
      }

      return true;
    } catch (error) {
      const latency = Date.now() - start;

      if (latency > 5000) {
        // Timeout
        setConnectionState('error');
      } else {
        setConnectionState('disconnected');
      }

      retriesRef.current++;
      console.warn(
        `[THÉRÈSE] Health check failed (attempt ${retriesRef.current}):`,
        error
      );

      return false;
    }
  }, [connectionState, setConnectionState, updatePing]);

  const scheduleRetry = useCallback(() => {
    if (retriesRef.current < MAX_RETRIES) {
      timeoutRef.current = setTimeout(async () => {
        const success = await performCheck();
        if (!success) {
          scheduleRetry();
        }
      }, RETRY_DELAY);
    } else {
      addNotification({
        type: 'error',
        title: 'Backend unreachable',
        message: 'Could not connect after multiple attempts',
      });
    }
  }, [performCheck, addNotification]);

  // Initial check and polling (seulement quand enabled = true)
  useEffect(() => {
    if (!enabled) return;

    // Reset retries quand on (re)démarre
    retriesRef.current = 0;

    // Initial check
    performCheck().then((success) => {
      if (!success) {
        scheduleRetry();
      }
    });

    // Start polling when connected
    intervalRef.current = setInterval(async () => {
      const success = await performCheck();
      if (!success) {
        // Stop polling and start retry logic
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        scheduleRetry();
      }
    }, HEALTH_CHECK_INTERVAL);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [enabled, performCheck, scheduleRetry]);

  return {
    refresh: performCheck,
  };
}
