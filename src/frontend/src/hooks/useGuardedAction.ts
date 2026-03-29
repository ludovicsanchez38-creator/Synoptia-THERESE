/**
 * THÉRÈSE v2 - Hook useGuardedAction
 *
 * Vérifie des pré-conditions avant d'exécuter une action.
 * Affiche un message d'erreur explicite si une condition n'est pas remplie.
 * Élimine le pattern d'erreur silencieuse (BUG-100).
 */
import { useCallback, useState } from 'react';

interface GuardCondition {
  /** La valeur à vérifier (truthy = OK) */
  check: unknown;
  /** Message d'erreur si la condition échoue */
  message: string;
}

interface UseGuardedActionResult {
  /** Exécute l'action si toutes les conditions sont remplies */
  execute: (action: () => Promise<void>) => Promise<void>;
  /** Erreur courante (null si pas d'erreur) */
  error: string | null;
  /** Action en cours */
  loading: boolean;
  /** Effacer l'erreur manuellement */
  clearError: () => void;
}

export function useGuardedAction(guards: GuardCondition[]): UseGuardedActionResult {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const execute = useCallback(async (action: () => Promise<void>) => {
    // Vérifier toutes les pré-conditions
    for (const guard of guards) {
      if (!guard.check) {
        setError(guard.message);
        return;
      }
    }

    setError(null);
    setLoading(true);
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  }, [guards]);

  const clearError = useCallback(() => setError(null), []);

  return { execute, error, loading, clearError };
}
