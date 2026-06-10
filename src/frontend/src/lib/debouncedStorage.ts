/**
 * US-010 : stockage localStorage débouncé pour le middleware persist de Zustand.
 *
 * Pendant le streaming, chaque flush de phrase déclenche un set() du store,
 * donc une sérialisation JSON de TOUTES les conversations vers localStorage.
 * Ce wrapper coalesce les écritures : au plus une écriture par fenêtre de
 * `delayMs`, flush forcé à la lecture (cohérence) et au déchargement de la
 * page (pas de perte de la dernière écriture).
 */

interface PendingWrite {
  key: string;
  value: string;
}

export function createDebouncedStorage(delayMs = 400): Storage {
  let timer: ReturnType<typeof setTimeout> | null = null;
  let pending: PendingWrite | null = null;

  const flush = () => {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
    if (pending) {
      const { key, value } = pending;
      pending = null;
      localStorage.setItem(key, value);
    }
  };

  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', flush);
  }

  return {
    getItem(key: string): string | null {
      // Lecture cohérente : pousser l'écriture en attente d'abord
      if (pending?.key === key) flush();
      return localStorage.getItem(key);
    },
    setItem(key: string, value: string): void {
      pending = { key, value };
      if (!timer) {
        timer = setTimeout(flush, delayMs);
      }
    },
    removeItem(key: string): void {
      if (pending?.key === key) {
        pending = null;
        if (timer) {
          clearTimeout(timer);
          timer = null;
        }
      }
      localStorage.removeItem(key);
    },
    get length(): number {
      return localStorage.length;
    },
    clear(): void {
      pending = null;
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
      localStorage.clear();
    },
    key(index: number): string | null {
      return localStorage.key(index);
    },
  };
}
