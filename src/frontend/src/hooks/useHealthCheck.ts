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
  const { setConnectionState, updatePing, addNotification } =
    useStatusStore();

  const retriesRef = useRef(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const outageNotifiedRef = useRef(false);
  const wasConnectedRef = useRef(false);

  const performCheck = useCallback(async (): Promise<boolean> => {
    const start = Date.now();

    try {
      const health: HealthStatus = await checkHealth();
      const latency = Date.now() - start;

      setConnectionState('connected');
      updatePing(latency);
      retriesRef.current = 0;
      outageNotifiedRef.current = false;

      // Journaliser uniquement la première connexion ou une reconnexion.
      if (!wasConnectedRef.current) {
        console.log(`[THÉRÈSE] Connected to backend v${health.version}`);
      }
      wasConnectedRef.current = true;

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
      wasConnectedRef.current = false;
      console.warn(
        `[THÉRÈSE] Health check failed (attempt ${retriesRef.current}):`,
        error
      );

      // Une seule notification par coupure. Les contrôles continuent ensuite à
      // cadence normale afin qu'un backend revenu tardivement soit détecté.
      if (
        retriesRef.current >= MAX_RETRIES &&
        !outageNotifiedRef.current
      ) {
        outageNotifiedRef.current = true;
        addNotification({
          type: 'error',
          title: 'Backend injoignable',
          message: 'Nouvelle tentative automatique en arrière-plan',
        });
      }

      return false;
    }
  }, [setConnectionState, updatePing, addNotification]);

  // Boucle séquentielle : aucun contrôle ne se chevauche et une coupure ne peut
  // jamais arrêter définitivement la reconnexion automatique.
  useEffect(() => {
    if (!enabled) return;

    let cancelled = false;
    retriesRef.current = 0;
    outageNotifiedRef.current = false;

    const checkAndSchedule = async () => {
      const success = await performCheck();
      if (cancelled) return;

      const nextDelay =
        success || retriesRef.current >= MAX_RETRIES
          ? HEALTH_CHECK_INTERVAL
          : RETRY_DELAY;

      timeoutRef.current = setTimeout(() => {
        void checkAndSchedule();
      }, nextDelay);
    };

    void checkAndSchedule();

    return () => {
      cancelled = true;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [enabled, performCheck]);

  return {
    refresh: performCheck,
  };
}
